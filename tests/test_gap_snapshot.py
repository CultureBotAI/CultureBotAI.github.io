"""Pinned Git acquisition and native gap semantics for the public gap snapshot."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gap_snapshot", ROOT / "scripts/gaps/snapshot.py")
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class RecordingExporter:
    """Isolate source acquisition; the actual export contract has its own tests."""
    def __init__(self):
        self.documents = []

    def normalize_record(self, doc, **kwargs):
        self.documents.append((copy.deepcopy(doc), kwargs))
        return [{
            "id": kwargs["repository"] + "/" + kwargs["path"] + "#" + d["discussion_id"],
            "discussion_id": d["discussion_id"], "prompt": d["prompt"],
            "kind": d.get("kind", "UNSPECIFIED"),
            "status": d.get("status", "UNSPECIFIED"), "evidence": d.get("evidence", []),
            "source": {"path": kwargs["path"], "revision": kwargs["revision"],
                       "sha256": kwargs["source_sha256"]},
        } for d in doc.get("discussions", [])]

    def validate_item(self, item):
        if not item["id"] or not item["prompt"]:
            raise ValueError("Malformed fixture export")


class GapSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gap-snapshot-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "TraitMech"
        self.repo.mkdir()
        self.git("init", "-b", "fixture")
        self.git("config", "user.name", "Snapshot test fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/CultureBotAI/TraitMech.git")
        self.exporter = RecordingExporter()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args],
                                       stderr=subprocess.PIPE, text=True).strip()

    def write(self, path, value):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", "Pin source fixture")
        return self.git("rev-parse", "HEAD")

    def record(self, identifier="TraitMech:first", prompt="Pinned scientific question"):
        return {"identifier": identifier, "label": "Fixture trait",
                "discussions": [{"discussion_id": "question", "prompt": prompt,
                                 "kind": "KNOWLEDGE_GAP", "status": "OPEN"}]}

    def root_config(self, name="traits", globs=None, **extra):
        result = {"name": name, "globs": globs or ["data/traits/**/*.yaml"],
                  "exclude_globs": [], "supported": True, "adapter": "discussions",
                  "id_field": "identifier", "name_fields": ["label"]}
        result.update(extra)
        return result

    def config(self, revision, roots=None):
        return {"sources": [{"name": "TraitMech", "repository": "CultureBotAI/TraitMech",
            "revision": revision, "acquired_at": "2026-11-14T00:00:00Z",
            "data_license": "CC-BY-4.0", "license_url": "https://example.invalid/license",
            "publication_allowed": True, "roots": roots or [self.root_config()]}]}

    def acquire(self, config):
        with mock.patch.object(snapshot, "ORDER", ["TraitMech"]), redirect_stdout(io.StringIO()):
            return snapshot.acquire(config, self.root, self.root / "cache", self.exporter, {})

    def test_immutable_git_records_include_tracked_ignored_files_and_exclude_worktree_changes(self):
        path = "data/traits/direct.yaml"
        original = self.write(path, self.record()).read_bytes()
        self.write(".gitignore", "data/traits/ignored.yaml\n")
        self.write("data/traits/ignored.yaml", self.record("TraitMech:ignored"))
        self.git("add", "-f", "data/traits/ignored.yaml")
        revision = self.commit()
        self.write(path, self.record(prompt="Uncommitted replacement"))
        self.write("data/traits/untracked.yaml", self.record("TraitMech:untracked"))
        result = self.acquire(self.config(revision))
        self.assertEqual({i["source"]["path"] for i in result["items"]},
                         {path, "data/traits/ignored.yaml"})
        first = next(i for i in result["items"] if i["source"]["path"] == path)
        self.assertEqual(first["prompt"], "Pinned scientific question")
        self.assertEqual(first["source"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(first["source"]["revision"], revision)
        self.assertEqual(self.git("branch", "--show-current"), "fixture")

    def test_source_repository_must_belong_to_its_public_name_before_acquisition(self):
        self.write("data/traits/direct.yaml", self.record())
        revision = self.commit()
        self.assertEqual(len(self.acquire(self.config(revision))["items"]), 1)
        for repository in ("TraitMech/private_lab", "CultureBotAI/private_lab",
                           "CultureBotAI/CultureMech"):
            with self.subTest(repository=repository):
                config = self.config(revision)
                config["sources"][0]["repository"] = repository
                self.git("remote", "set-url", "origin", "https://github.com/" + repository)
                self.exporter.documents.clear()
                with self.assertRaises(ValueError):
                    self.acquire(config)
                self.assertEqual(self.exporter.documents, [])

    def test_multiple_roots_exclusions_and_star_directory_boundaries(self):
        for path in ("data/traits/direct.yaml", "data/traits/nested/child.yml",
                     "data/traits/backups/old.yaml", "data/isolates/direct.yaml",
                     "data/isolates/deeper/outside.yaml"):
            self.write(path, self.record(path))
        revision = self.commit()
        roots = [self.root_config(globs=["data/traits/**/*.yaml", "data/traits/**/*.yml"],
                                  exclude_globs=["data/traits/backups/**"]),
                 self.root_config("isolates", ["data/isolates/*.yaml"])]
        result = self.acquire(self.config(revision, roots))
        self.assertEqual({i["source"]["path"] for i in result["items"]},
                         {"data/traits/direct.yaml", "data/traits/nested/child.yml",
                          "data/isolates/direct.yaml"})
        self.assertEqual([r["inspected_records"] for r in result["sources"][0]["roots"]], [2, 1])

    def test_one_root_with_multiple_disjoint_globs_scans_all_declared_paths(self):
        self.write("data/traits/direct.yaml", self.record())
        self.write("data/isolates/direct.yaml", self.record("TraitMech:second"))
        revision = self.commit()
        config = self.config(revision, [self.root_config(globs=["data/traits/*.yaml", "data/isolates/*.yaml"])])
        result = self.acquire(config)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["sources"][0]["roots"][0]["eligible_records"], 2)

    def test_json_in_yaml_research_gaps_use_scope_identity_without_parent_evidence(self):
        self.write("data/traits/assay.yaml", {"identifier": "AssayMech:example", "name": "Assay",
            "evidence": [{"reference": "DOI:10.1234/parent-only"}],
            "research_gaps": [{"scope": "controls", "reason": "Control protocol requires curation"},
                              {"scope": "measurement", "reason": "Measurement limits are unspecified"}]})
        revision = self.commit()
        cfg = self.root_config(adapter="research_gaps", gap_key="scope",
                               gap_key_values=["controls", "measurement"])
        result = self.acquire(self.config(revision, [cfg]))
        self.assertEqual({i["discussion_id"] for i in result["items"]},
                         {"research-gap:controls", "research-gap:measurement"})
        for item in result["items"]:
            self.assertEqual(item["kind"], "CURATION_TODO")
            self.assertEqual(item["status"], "UNSPECIFIED")
            self.assertEqual(item["evidence"], [])
            self.assertTrue(item["source"]["locator"].startswith("research_gaps[scope="))
        normalized = self.exporter.documents[0][0]["discussions"]
        self.assertTrue(all("status" not in d and "evidence" not in d for d in normalized))

    def test_duplicate_research_gap_scope_rejected_even_with_different_prose(self):
        doc = {"research_gaps": [{"corpus": "proteintraitsmech", "reason": "First"},
                                 {"corpus": "proteintraitsmech", "reason": "Second"}]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            snapshot.adapt(doc, {"adapter": "research_gaps", "gap_key": "corpus"})

    def test_supported_root_with_no_records_fails_but_empty_discussions_are_complete(self):
        self.write("README.md", "No records yet")
        revision = self.commit()
        with self.assertRaisesRegex(ValueError, "matched no records"):
            self.acquire(self.config(revision))
        self.write("data/traits/no-gaps.yaml", {"identifier": "TraitMech:first", "label": "Known trait"})
        revision = self.commit()
        result = self.acquire(self.config(revision))
        self.assertEqual(result["items"], [])
        row = result["sources"][0]["roots"][0]
        self.assertEqual((row["status"], row["eligible_records"], row["discussion_count"]),
                         ("complete", 1, 0))

    def test_unsupported_root_has_unknown_denominator_and_never_false_complete(self):
        self.write("README.md", "Unsupported schema")
        revision = self.commit()
        result = self.acquire(self.config(revision, [self.root_config(supported=False,
            unsupported_reason="Schema has no native gap field")]))
        source = result["sources"][0]
        self.assertEqual(source["coverage_status"], "unsupported")
        self.assertIsNone(source["roots"][0]["eligible_records"])
        self.assertIsNone(source["roots"][0]["discussion_count"])
        self.assertEqual(self.exporter.documents, [])

    def test_root_publication_hold_prevents_reading_supported_records(self):
        self.write("data/traits/allowed.yaml", self.record())
        # This file would fail parsing if a publication hold were bypassed.
        self.write("data/held/blocked.yaml", "- not a record mapping\n")
        revision = self.commit()
        roots = [self.root_config(), self.root_config("held", ["data/held/*.yaml"],
                                                       publication_allowed=False)]
        result = self.acquire(self.config(revision, roots))
        source = result["sources"][0]
        self.assertEqual(source["coverage_status"], "partial")
        self.assertEqual(len(result["items"]), 1)
        held = source["roots"][1]
        self.assertEqual((held["support"], held["status"], held["inspected_records"]),
                         ("supported", "unavailable", 0))
        self.assertIsNone(held["eligible_records"])
        self.assertIsNone(held["discussion_count"])
        self.assertEqual(len(self.exporter.documents), 1)

    def test_source_publication_hold_cannot_be_overridden_by_root(self):
        self.write("data/traits/blocked.yaml", self.record())
        revision = self.commit()
        config = self.config(revision, [self.root_config(publication_allowed=True)])
        config["sources"][0]["publication_allowed"] = False
        result = self.acquire(config)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["sources"][0]["coverage_status"], "unavailable")
        self.assertEqual(self.exporter.documents, [])

    def test_failed_acquisition_preserves_existing_snapshot(self):
        self.write("data/traits/a.yaml", self.record())
        self.write("data/traits/z.yaml", "- invalid\n- root\n")
        revision = self.commit()
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps(self.config(revision)))
        output = self.root / "snapshot.json"
        previous = b'{"previous":"last good snapshot"}\n'
        output.write_bytes(previous)
        argv = ["snapshot.py", "--config", str(config_path), "--claw-root", str(self.root),
                "--repos-root", str(self.root), "--output", str(output)]
        with (mock.patch.object(snapshot, "ORDER", ["TraitMech"]),
              mock.patch.object(snapshot, "load_exporter", return_value=(self.exporter, {})),
              mock.patch("sys.argv", argv), redirect_stdout(io.StringIO())):
            with self.assertRaisesRegex(ValueError, "Not a record mapping"):
                snapshot.main()
        self.assertEqual(output.read_bytes(), previous)

    def test_withheld_source_rejected_before_any_records_can_publish(self):
        config = {"sources": [{"name": "ScaleupMech", "repository": "CultureBotAI/ScaleupMech"}]}
        with mock.patch.object(snapshot, "ORDER", ["ScaleupMech"]):
            with self.assertRaisesRegex(ValueError, "Non-public"):
                snapshot.acquire(config, self.root, self.root / "cache", self.exporter, {})
        self.assertEqual(self.exporter.documents, [])

    def test_withheld_name_in_coverage_metadata_is_not_publishable(self):
        self.write("README.md", "Unsupported schema")
        revision = self.commit()
        config = self.config(revision, [self.root_config(supported=False,
            unsupported_reason="Requires ScaleupMech source access")])
        with self.assertRaises(ValueError):
            self.acquire(config)


if __name__ == "__main__":
    unittest.main()
