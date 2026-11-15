"""Pinned vocabulary acquisition, collision retention and publication gates (#583)."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
SPEC = importlib.util.spec_from_file_location("gap_vocabulary", ROOT / "scripts/gaps/vocabulary.py")
vocabulary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vocabulary)


class GapVocabularyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gap-vocabulary-tests-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.repo = self.directory / "TraitMech"
        self.repo.mkdir()
        self.git("init", "-b", "fixture")
        self.git("config", "user.name", "Vocabulary fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/CultureBotAI/TraitMech.git")
        self.schema = b"name: vocabulary_fixture\n"
        (self.repo / "schema.yaml").write_bytes(self.schema)
        self.write("data/records/iron.yaml", {"identifier": "CHEBI:18248", "label": "iron",
            "synonyms": [{"synonym_text": "Fe", "synonym_type": "EXACT_SYNONYM"},
                         {"synonym_text": "metal", "synonym_type": "BROAD_SYNONYM"}]})
        self.pin = self.commit()
        root = {"name": "records", "globs": ["data/records/**/*.yaml"], "exclude_globs": [],
                "id_field": "identifier", "name_fields": ["label"], "alias_fields": ["synonyms"],
                "alias_value_fields": ["synonym_text"], "supported": True,
                "schema_path": "schema.yaml", "schema_sha256": vocabulary.digest(self.schema)}
        self.config = {"sources": [{"name": "TraitMech", "repository": "CultureBotAI/TraitMech",
            "revision": self.pin, "acquired_at": "2026-11-15T00:00:00Z", "data_license": "CC-BY-4.0",
            "license_url": "https://github.com/CultureBotAI/TraitMech/blob/" + self.pin + "/LICENSE-DATA",
            "publication_allowed": True, "roots": [root]}]}
        self.snapshot = {"source_config_sha256": vocabulary.digest(vocabulary.json_bytes(self.config)),
                         "items": [{"prompt": "How do iron and Fe affect metal uptake?", "rationale": ""}]}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args],
                                       stderr=subprocess.PIPE, text=True).strip()

    def write(self, path, document):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(document if isinstance(document, str) else json.dumps(document))

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "-qm", "Pinned vocabulary fixture")
        return self.git("rev-parse", "HEAD")

    def refresh(self):
        revision = self.commit()
        self.config["sources"][0]["revision"] = revision
        self.config["sources"][0]["license_url"] = (
            "https://github.com/CultureBotAI/TraitMech/blob/" + revision + "/LICENSE-DATA")
        self.config_hash()

    def config_hash(self):
        self.snapshot["source_config_sha256"] = vocabulary.digest(vocabulary.json_bytes(self.config))

    def acquire(self):
        with mock.patch.object(vocabulary, "ORDER", ["TraitMech"]), redirect_stdout(io.StringIO()):
            return vocabulary.acquire(self.config, self.snapshot, self.directory, self.directory / "cache")

    def validate(self, candidate):
        with mock.patch.object(vocabulary, "ORDER", ["TraitMech"]):
            vocabulary.validate_vocabulary(candidate, self.snapshot, self.config)

    def test_pinned_records_ignore_dirty_prose_and_nonexact_aliases(self):
        self.write("data/records/iron.yaml", {"identifier": "changed", "label": "metal"})
        result = self.acquire()
        self.assertEqual(len(result["terms"]), 1)
        self.assertEqual(result["terms"][0]["label"], "iron")
        self.assertEqual(result["terms"][0]["aliases"], ["Fe"])
        self.assertEqual(result["terms"][0]["canonical_id"], "CHEBI:18248")
        self.assertEqual(result["terms"][0]["source"]["revision"], self.pin)
        self.assertEqual(self.git("branch", "--show-current"), "fixture")

    def test_all_colliding_records_survive_prefilter_and_nonmatching_records_count(self):
        self.write("data/records/second.yaml", {"identifier": "OTHER:iron", "label": "iron"})
        self.write("data/records/third.yaml", {"identifier": "CHEBI:18248", "label": "iron"})
        self.write("data/records/unmentioned.yaml", {"identifier": "OTHER:absent", "label": "unmentioned entity"})
        self.refresh()
        result = self.acquire()
        self.assertEqual(len(result["terms"]), 3)
        self.assertEqual(len({term["id"] for term in result["terms"]}), 3)
        self.assertEqual({term["canonical_id"] for term in result["terms"]}, {"CHEBI:18248", "OTHER:iron"})
        row = result["sources"][0]["roots"][0]
        self.assertEqual((row["eligible_records"], row["inspected_records"], row["candidate_records"]), (4, 4, 3))

    def test_gap_unsupported_root_can_supply_vocabulary_but_publication_hold_cannot(self):
        root = self.config["sources"][0]["roots"][0]
        root["supported"] = False
        self.config_hash()
        self.assertEqual(len(self.acquire()["terms"]), 1)
        root["publication_allowed"] = False
        self.config_hash()
        result = self.acquire()
        self.assertEqual(result["terms"], [])
        row = result["sources"][0]["roots"][0]
        self.assertEqual(row["status"], "unavailable")
        self.assertIsNone(row["eligible_records"])
        self.assertEqual(row["inspected_records"], 0)

    def test_exact_scope_simple_aliases_and_native_label_overrides(self):
        root = self.config["sources"][0]["roots"][0]
        root["alias_value_fields"] = ["value"]
        values = vocabulary.aliases({"synonyms": ["unqualified", {"value": "exact", "scope": "exact"},
            {"value": "broader", "scope": "broad"}, {"value": "narrower", "synonym_type": "NARROW_SYNONYM"},
            {"value": "related", "synonym_type": "RELATED_SYNONYM"}]}, root)
        self.assertEqual(values, ["exact", "unqualified"])
        source = self.config["sources"][0] | {"name": "CultureMech"}
        self.assertEqual(vocabulary.label_fields(source, {"name_fields": ["name"]}), ["original_name", "name"])
        source = source | {"name": "CofactorMech"}
        root = root | {"id_field": "id", "name_fields": ["name"], "alias_fields": []}
        term = vocabulary.project_record({"id": "CofactorMech:iron", "name": "iron", "chemical_id": "CHEBI:18248"},
            source, root, "data/records/iron.yaml", b"fixture", lambda _: True)
        self.assertEqual((term["record_id"], term["canonical_id"]), ("CofactorMech:iron", "CHEBI:18248"))

    def test_snapshot_schema_and_config_drift_fail_before_publication(self):
        result = self.acquire()
        for key in ("snapshot_sha256", "source_config_sha256"):
            candidate = copy.deepcopy(result)
            candidate[key] = "0" * 64
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(candidate)
        self.config["sources"][0]["roots"][0]["schema_sha256"] = "0" * 64
        self.config_hash()
        with self.assertRaisesRegex(ValueError, "schema digest"):
            self.acquire()

    def test_forged_vocabulary_cannot_bypass_hold_or_scope(self):
        result = self.acquire()
        self.config["sources"][0]["roots"][0]["publication_allowed"] = False
        self.config_hash()
        result["source_config_sha256"] = self.snapshot["source_config_sha256"]
        result["snapshot_sha256"] = vocabulary.digest(vocabulary.json_bytes(self.snapshot))
        with self.assertRaisesRegex(ValueError, "publication hold"):
            self.validate(result)
        self.config["sources"][0]["roots"][0].pop("publication_allowed")
        self.config_hash()
        result = self.acquire()
        result["terms"][0]["source"].update(path="data/elsewhere/iron.yaml",
            url="https://github.com/CultureBotAI/TraitMech/blob/" + self.pin + "/data/elsewhere/iron.yaml")
        with self.assertRaisesRegex(ValueError, "publishable vocabulary root"):
            self.validate(result)

    def test_empty_root_and_bad_native_record_are_errors_not_complete_zero(self):
        self.config["sources"][0]["roots"][0]["globs"] = ["missing/*.yaml"]
        self.config_hash()
        with self.assertRaisesRegex(ValueError, "matched no records"):
            self.acquire()
        self.config["sources"][0]["roots"][0]["globs"] = ["data/records/**/*.yaml"]
        self.write("data/records/bad.yaml", {"identifier": "OTHER:bad"})
        self.refresh()
        with self.assertRaisesRegex(ValueError, "preferred label"):
            self.acquire()

    def test_failed_acquisition_retains_previous_output(self):
        self.write("data/records/bad.yaml", "- invalid record mapping\n")
        self.refresh()
        config_path, snapshot_path, output = [self.directory / name for name in ("config.json", "snapshot.json", "vocabulary.json")]
        config_path.write_text(json.dumps(self.config))
        snapshot_path.write_text(json.dumps(self.snapshot))
        output.write_bytes(b"previous-vocabulary\n")
        argv = ["vocabulary.py", "--config", str(config_path), "--snapshot", str(snapshot_path),
                "--repos-root", str(self.directory), "--output", str(output)]
        with (mock.patch.object(vocabulary, "ORDER", ["TraitMech"]), mock.patch("sys.argv", argv),
              redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "not a mapping")):
            vocabulary.main()
        self.assertEqual(output.read_bytes(), b"previous-vocabulary\n")


if __name__ == "__main__":
    unittest.main()
