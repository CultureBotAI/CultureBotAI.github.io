"""Reproducible bundles, coverage integrity and read-only checks for gap Pages."""
import copy
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
SPEC = importlib.util.spec_from_file_location("gap_build", ROOT / "scripts/gaps/build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class FixtureExporter:
    def validate_items(self, items):
        if len({item["id"] for item in items}) != len(items):
            raise ValueError("Duplicate fixture item")


class GapBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gap-build-tests-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.provenance = {"repository": "CultureBotAI/culturebotai-claw", "revision": "a" * 40,
                           "module_sha256": "b" * 64, "schema_sha256": "c" * 64, "dirty": False}
        source = {"name": "TraitMech", "repository": "CultureBotAI/TraitMech", "revision": "1" * 40,
                  "acquired_at": "2026-11-14T00:00:00Z", "data_license": "CC-BY-4.0",
                  "license_url": "https://github.com/CultureBotAI/TraitMech/blob/" + "1" * 40 + "/LICENSE-DATA",
                  "publication_allowed": True,
                  "roots": [{"name": "traits", "globs": ["data/traits/**/*.yaml"],
                             "exclude_globs": ["data/traits/backups/**"], "supported": True}]}
        self.config = {"sources": [source]}
        coverage = {key: source[key] for key in ("name", "repository", "revision", "acquired_at",
                                                "data_license", "license_url")}
        coverage.update({"source_url": "https://github.com/CultureBotAI/TraitMech/tree/" + "1" * 40,
            "coverage_status": "complete", "items": 2,
            "roots": [{"name": "traits", "globs": source["roots"][0]["globs"],
                       "exclude_globs": source["roots"][0]["exclude_globs"],
                       "support": "supported", "status": "complete", "eligible_records": 1,
                       "inspected_records": 1, "discussion_count": 2, "reason": ""}]})
        self.snapshot = {"schema_version": 1, "source_config_sha256": build.digest(build.json_bytes(self.config)),
                         "exporter": self.provenance, "sources": [coverage],
                         "items": [self.item("one", "native"), self.item("two", "candidate")]}
        self.exporter = FixtureExporter()

    def item(self, key, lane):
        path = "data/traits/ecology/example.yaml"
        return {"id": "fixture:" + key, "mech": "TraitMech", "record_id": "TraitMech:example",
                "record_label": "Example trait", "aliases": ["Alternate term"],
                "discussion_id": key, "prompt": "Question " + key, "rationale": "Evidence is incomplete",
                "kind": "KNOWLEDGE_GAP", "status": "OPEN", "origin": "unspecified",
                "review_state": "unspecified", "lane": lane, "evidence_refs": ["DOI:10.1234/example"],
                "attaches_to": ["causal_graphs#edge"],
                "source": {"repository": "CultureBotAI/TraitMech", "revision": "1" * 40,
                           "path": path, "license": "CC-BY-4.0", "sha256": "d" * 64,
                           "url": "https://github.com/CultureBotAI/TraitMech/blob/" + "1" * 40 + "/" + path}}

    def validate(self, snapshot=None, config=None, provenance=None):
        with mock.patch.object(build, "ORDER", ["TraitMech"]):
            return build.validate(snapshot or self.snapshot, config or self.config,
                                  self.exporter, provenance or self.provenance)

    def config_changed(self, snapshot, config):
        snapshot["source_config_sha256"] = build.digest(build.json_bytes(config))

    def test_deterministic_bundle_hashes_counts_and_all_index_details_correspond(self):
        self.validate()
        first = build.artifacts(self.snapshot)
        self.assertEqual(first, build.artifacts(copy.deepcopy(self.snapshot)))
        files, summary, manifest = first
        self.assertEqual(manifest["counts"], {"items": 2, "candidates": 1, "records_with_discussions": 1})
        index_ref = manifest["index"]
        self.assertEqual(hashlib.sha256(files[index_ref["url"]]).hexdigest(), index_ref["sha256"])
        index = json.loads(files[index_ref["url"]])
        detail_items = {}
        for reference in manifest["details"].values():
            payload = files[reference["url"]]
            self.assertEqual(hashlib.sha256(payload).hexdigest(), reference["sha256"])
            shard = json.loads(payload)
            self.assertEqual(shard["build_id"], manifest["build_id"])
            detail_items.update(shard["items"])
        self.assertEqual(set(detail_items), {item["id"] for item in index["items"]})
        self.assertEqual(detail_items, {item["id"]: item for item in self.snapshot["items"]})
        self.assertIn("2 recorded discussion items", summary)

    def test_large_details_split_without_losing_or_duplicating_items(self):
        candidate = copy.deepcopy(self.snapshot)
        candidate["items"] = []
        for index in range(20):
            item = self.item(str(index), "recorded")
            item["prompt"] = " ".join(hashlib.sha256(f"{index}-{part}".encode()).hexdigest()
                                      for part in range(12))
            candidate["items"].append(item)
        with mock.patch.object(build, "MAX_DETAIL_GZIP", 2000):
            first = build.artifacts(candidate)
            self.assertEqual(first, build.artifacts(copy.deepcopy(candidate)))
        files, _, manifest = first
        self.assertGreater(len(manifest["details"]), 1)
        indexed = json.loads(files[manifest["index"]["url"]])["items"]
        seen = []
        for key, descriptor in manifest["details"].items():
            payload = files[descriptor["url"]]
            self.assertLessEqual(len(gzip.compress(payload, mtime=0)), 2000)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), descriptor["sha256"])
            details = json.loads(payload)["items"]
            expected = {item["id"] for item in indexed if item["detail_shard"] == key}
            self.assertEqual(set(details), expected)
            self.assertTrue(all("detail_shard" not in item for item in details.values()))
            seen.extend(details)
        self.assertEqual(sorted(seen), sorted(item["id"] for item in candidate["items"]))
        self.assertEqual(len(seen), len(set(seen)))
        with mock.patch.object(build, "MAX_DETAIL_GZIP", 1):
            with self.assertRaisesRegex(ValueError, "One discussion exceeds"):
                build.artifacts(candidate)

    def test_term_sidecar_is_hashed_snapshot_bound_and_budgeted(self):
        document = {"schema_version": 1, "build_id": build.digest(build.json_bytes(self.snapshot)),
                    "terms": [{"id": "term-example", "label": "Example",
                               "postings": [{"discussion_id": "fixture:one", "count": 2}]}]}
        vocabulary = {"schema_version": 1}
        with mock.patch.object(build, "build_term_document", return_value=document) as recognize:
            files, _, manifest = build.artifacts(self.snapshot, vocabulary)
            recognize.assert_called_once_with(self.snapshot, vocabulary)
            descriptor = manifest["terms"]
            content = files[descriptor["url"]]
            self.assertEqual(build.digest(content), descriptor["sha256"])
            self.assertEqual(json.loads(content), document)
            self.assertEqual(manifest["sizes"]["terms_bytes"], len(content))
            self.assertEqual(manifest["sizes"]["terms_gzip_bytes"], len(gzip.compress(content, mtime=0)))
            with mock.patch.object(build, "MAX_TERMS_GZIP", 1):
                with self.assertRaisesRegex(ValueError, "Term projection exceeds"):
                    build.artifacts(self.snapshot, vocabulary)
        document["build_id"] = "f" * 64
        with mock.patch.object(build, "build_term_document", return_value=document):
            with self.assertRaisesRegex(ValueError, "same gap snapshot"):
                build.artifacts(self.snapshot, vocabulary)

    def test_explicit_unsupported_root_remains_unknown_and_valid(self):
        config, snapshot = copy.deepcopy(self.config), copy.deepcopy(self.snapshot)
        config["sources"][0]["roots"][0]["supported"] = False
        snapshot["items"] = []
        source = snapshot["sources"][0]
        source.update(coverage_status="unsupported", items=0)
        source["roots"][0].update(status="unsupported", support="unsupported", eligible_records=None,
                                  inspected_records=0, discussion_count=None, reason="No native gap field")
        self.config_changed(snapshot, config)
        self.validate(snapshot, config)
        manifest = build.artifacts(snapshot)[2]
        self.assertIsNone(manifest["sources"][0]["roots"][0]["discussion_count"])
        self.assertEqual(manifest["details"], {})

    def test_config_exporter_bytes_and_item_provenance_mismatches_rejected(self):
        mutations = [lambda s: s.update(source_config_sha256="e" * 64),
                     lambda s: s["exporter"].update(module_sha256="e" * 64),
                     lambda s: s["items"][0]["source"].update(revision="2" * 40),
                     lambda s: s["items"][0]["source"].update(license="CC0-1.0"),
                     lambda s: s["sources"][0].update(source_url="javascript:alert(1)")]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(self.snapshot)
                mutation(candidate)
                with self.assertRaises(ValueError):
                    self.validate(candidate)

    def test_false_complete_root_and_uninspected_records_rejected(self):
        for field, value in (("eligible_records", 0), ("inspected_records", 0)):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.snapshot)
                candidate["sources"][0]["roots"][0][field] = value
                with self.assertRaisesRegex(ValueError, "complete coverage"):
                    self.validate(candidate)
        config, candidate = copy.deepcopy(self.config), copy.deepcopy(self.snapshot)
        config["sources"][0]["roots"][0]["supported"] = False
        self.config_changed(candidate, config)
        with self.assertRaisesRegex(ValueError, "complete coverage|Root support"):
            self.validate(candidate, config)

    def test_complete_coverage_requires_both_source_and_root_publication_permission(self):
        for source_allowed, root_allowed in ((True, False), (False, True)):
            with self.subTest(source_allowed=source_allowed, root_allowed=root_allowed):
                config, candidate = copy.deepcopy(self.config), copy.deepcopy(self.snapshot)
                config["sources"][0]["publication_allowed"] = source_allowed
                config["sources"][0]["roots"][0]["publication_allowed"] = root_allowed
                self.config_changed(candidate, config)
                with self.assertRaisesRegex(ValueError, "publication hold"):
                    self.validate(candidate, config)

    def test_root_publication_hold_preserves_unknown_coverage_without_items(self):
        config, candidate = copy.deepcopy(self.config), copy.deepcopy(self.snapshot)
        config["sources"][0]["roots"][0]["publication_allowed"] = False
        candidate["items"] = []
        source = candidate["sources"][0]
        source.update(coverage_status="unavailable", items=0)
        source["roots"][0].update(status="unavailable", eligible_records=None,
            inspected_records=0, discussion_count=None, reason="Root redistribution not established")
        self.config_changed(candidate, config)
        self.validate(candidate, config)
        manifest = build.artifacts(candidate)[2]
        self.assertEqual(manifest["details"], {})
        self.assertIsNone(manifest["sources"][0]["roots"][0]["eligible_records"])

    def test_discussions_in_one_pinned_document_must_agree_on_source_hash(self):
        candidate = copy.deepcopy(self.snapshot)
        candidate["items"][1]["source"]["sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "Conflicting source hashes"):
            self.validate(candidate)

    def test_item_documents_cannot_exceed_inspected_records_but_empty_records_are_allowed(self):
        # Multiple discussions in one document consume one record, and an
        # inspected record without discussions need not appear in the item list.
        for inspected in (1, 3):
            candidate = copy.deepcopy(self.snapshot)
            candidate["sources"][0]["roots"][0].update(
                eligible_records=inspected, inspected_records=inspected)
            self.validate(candidate)

        candidate = copy.deepcopy(self.snapshot)
        path = "data/traits/ecology/second.yaml"
        candidate["items"][1]["source"].update(path=path,
            url="https://github.com/CultureBotAI/TraitMech/blob/" + "1" * 40 + "/" + path)
        with self.assertRaisesRegex(ValueError, "Item documents exceed inspected records"):
            self.validate(candidate)
        candidate["sources"][0]["roots"][0].update(eligible_records=2, inspected_records=2)
        self.validate(candidate)

    def test_source_summary_cannot_claim_complete_when_root_is_unsupported(self):
        config, candidate = copy.deepcopy(self.config), copy.deepcopy(self.snapshot)
        config["sources"][0]["roots"][0]["supported"] = False
        candidate["items"] = []
        candidate["sources"][0]["items"] = 0
        candidate["sources"][0]["roots"][0].update(status="unsupported", support="unsupported",
            eligible_records=None, inspected_records=0, discussion_count=None, reason="No native gap field")
        self.config_changed(candidate, config)
        with self.assertRaises(ValueError):
            self.validate(candidate, config)

    def test_item_path_must_belong_to_exactly_one_complete_nonexcluded_root(self):
        for path in ("data/unrelated/other.yaml", "data/traits/backups/old.yaml"):
            with self.subTest(path=path):
                candidate = copy.deepcopy(self.snapshot)
                candidate["items"][0]["source"]["path"] = path
                candidate["items"][0]["source"]["url"] = (
                    "https://github.com/CultureBotAI/TraitMech/blob/" + "1" * 40 + "/" + path)
                with self.assertRaises(ValueError):
                    self.validate(candidate)

    def test_check_detects_stale_or_extraneous_generated_asset_without_writing(self):
        files, summary, _ = build.artifacts(self.snapshot)
        config_path, snapshot_path = self.directory / "sources.json", self.directory / "snapshot.json"
        config_path.write_text(json.dumps(self.config))
        snapshot_path.write_text(json.dumps(self.snapshot))
        for failure in ("stale", "extra"):
            with self.subTest(failure=failure):
                output = self.directory / failure
                for path, payload in files.items():
                    target = output / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
                summary_path = output / "summary.html"
                summary_path.write_text(summary)
                if failure == "stale":
                    (output / "manifest.json").write_text("{}")
                else:
                    (output / "data/obsolete.json").write_text("{}")
                before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
                argv = ["build.py", "--snapshot", str(snapshot_path), "--config", str(config_path),
                        "--claw-root", str(self.directory), "--output", str(output),
                        "--summary", str(summary_path), "--check"]
                with (mock.patch.object(build, "ORDER", ["TraitMech"]),
                      mock.patch.object(build, "load_exporter", return_value=(self.exporter, self.provenance)),
                      mock.patch.object(build, "load_vocabulary", return_value=None),
                      mock.patch.object(build, "write_atomic", side_effect=AssertionError("check tried to write")),
                      mock.patch("sys.argv", argv), redirect_stdout(io.StringIO())):
                    with self.assertRaisesRegex(ValueError, "Generated gap"):
                        build.main()
                after = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
                self.assertEqual(after, before)

    def test_static_summary_renders_record_prose_as_text(self):
        source = copy.deepcopy(self.snapshot["sources"][0])
        source["roots"][0].update(status="unsupported", reason="Missing <script>alert(1)</script> & evidence")
        summary = build.summary_html([source], {"items": 2, "candidates": 1})
        self.assertNotIn("<script>", summary)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; evidence", summary)

    def test_publication_failure_restores_all_previous_assets(self):
        staging, output = self.directory / "staging", self.directory / "published"
        (staging / "data").mkdir(parents=True)
        (output / "data").mkdir(parents=True)
        (staging / "data/new.json").write_text("new-data")
        (staging / "manifest.json").write_text("new-manifest")
        (staging / "summary.html").write_text("new-summary")
        (output / "data/old.json").write_text("old-data")
        (output / "manifest.json").write_text("old-manifest")
        summary = self.directory / "summary.html"
        summary.write_text("old-summary")
        original_replace = Path.replace
        def fail_manifest(path, target):
            if path == staging / "manifest.json" and target == output / "manifest.json":
                raise OSError("Simulated publication failure")
            return original_replace(path, target)
        with mock.patch.object(Path, "replace", fail_manifest):
            with self.assertRaisesRegex(OSError, "Simulated"):
                build.publish(staging, output, summary)
        self.assertEqual((output / "manifest.json").read_text(), "old-manifest")
        self.assertEqual((output / "data/old.json").read_text(), "old-data")
        self.assertFalse((output / "data/new.json").exists())
        self.assertEqual(summary.read_text(), "old-summary")


if __name__ == "__main__":
    unittest.main()
