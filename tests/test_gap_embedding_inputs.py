"""Pinned record enrichment and deterministic embedding composition (#609)."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
import embedding_inputs as inputs
import terms
import vocabulary


class GapEmbeddingInputsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gap-embedding-inputs-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repo = self.directory / "TraitMech"
        self.repo.mkdir()
        self.git("init", "-b", "fixture")
        self.git("config", "user.name", "Embedding fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/CultureBotAI/TraitMech.git")
        schema, license_ = b"name: fixture\n", b"Fixture data license\n"
        (self.repo / "schema.yaml").write_bytes(schema)
        (self.repo / "LICENSE-DATA").write_bytes(license_)
        self.documents = {
            "iron.yaml": {"identifier": "CHEBI:18248", "label": "iron", "definition": "A metallic element.",
                          "definition_source": "CHEBI:18248", "notes": "Never embed arbitrary curation notes."},
            "iron-copy.yaml": {"identifier": "CHEBI:18248", "label": "iron", "definition": "A metallic element."},
            "water.yaml": {"identifier": "CHEBI:15377", "label": "water", "notes": "Not a native definition."},
        }
        (self.repo / "data").mkdir()
        for name, document in self.documents.items():
            (self.repo / "data" / name).write_text(json.dumps(document))
        self.git("add", "--all")
        self.git("commit", "-qm", "Fixture records")
        revision = self.git("rev-parse", "HEAD")
        root = {"name": "records", "globs": ["data/*.yaml"], "exclude_globs": [],
                "id_field": "identifier", "name_fields": ["label"], "alias_fields": [],
                "alias_value_fields": [], "supported": True, "schema_path": "schema.yaml",
                "schema_sha256": inputs.digest(schema)}
        self.config = {"sources": [{"name": "TraitMech", "repository": "CultureBotAI/TraitMech",
            "revision": revision, "acquired_at": "2026-11-15T00:00:00Z", "data_license": "CC-BY-4.0",
            "license_url": f"https://github.com/CultureBotAI/TraitMech/blob/{revision}/LICENSE-DATA",
            "license_sha256": inputs.digest(license_), "publication_allowed": True, "roots": [root]}]}
        self.snapshot = {"schema_version": 1, "source_config_sha256": inputs.digest(inputs.json_bytes(self.config)),
                         "sources": [{"name": "TraitMech", "repository": "CultureBotAI/TraitMech"}],
                         "items": [{"id": "d1", "prompt": "iron iron", "rationale": "",
                                    "proposed_experiments": [{"name": "iron uptake"}]},
                                   {"id": "d2", "prompt": "Which mechanism remains unresolved?"},
                                   {"id": "d3", "prompt": "water"}]}
        with mock.patch.object(vocabulary, "ORDER", ["TraitMech"]), redirect_stdout(io.StringIO()):
            self.vocabulary = vocabulary.acquire(self.config, self.snapshot, self.directory, self.directory / "fallback")
        self.terms = terms.build_term_document(self.snapshot, self.vocabulary)
        with mock.patch.object(vocabulary, "ORDER", ["TraitMech"]):
            self.selected = inputs.matched_records(self.snapshot, self.terms, self.config, self.vocabulary)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE, text=True).strip()

    def acquire(self, *, canary=False):
        with redirect_stdout(io.StringIO()):
            return inputs.acquire_records(self.selected, self.config, self.directory, self.directory / "fallback",
                                          self.directory / "record-cache", canary=canary)

    def validate(self, document):
        with mock.patch.object(vocabulary, "ORDER", ["TraitMech"]):
            inputs.validate_inputs(document, self.snapshot, self.terms, self.config, self.vocabulary)

    def test_canary_persists_one_record_then_full_reads_pinned_blobs(self):
        for name in self.documents:
            (self.repo / "data" / name).write_text("definition: dirty working copy\n")
        first, paths = self.acquire(canary=True)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(list((self.directory / "record-cache").glob("*.json"))), 1)
        cache = Path(paths[0])
        self.assertTrue(cache.stat().st_size)
        self.assertEqual(json.loads(cache.read_bytes())["record"], first[0])
        retained = cache.read_bytes()
        all_records, all_paths = self.acquire()
        self.assertEqual(len(all_records), 3)
        self.assertEqual(len(all_paths), 3)
        self.assertEqual(cache.read_bytes(), retained)
        self.assertEqual(self.git("branch", "--show-current"), "fixture")
        self.assertEqual({row["description"] for row in all_records}, {"", "A metallic element."})

    def test_complete_owner_metadata_with_deduplicated_text_and_unmatched_points(self):
        records, _ = self.acquire()
        original = copy.deepcopy((self.snapshot, self.terms, records))
        document = inputs.build_inputs(self.snapshot, self.terms, records)
        self.validate(document)
        self.assertEqual(original, (self.snapshot, self.terms, records))
        self.assertEqual(document, inputs.build_inputs(self.snapshot, self.terms, list(reversed(records))))
        first, unmatched, missing = document["items"]
        self.assertEqual(len(first["record_ids"]), 2)
        self.assertEqual(first["matched_terms"][0]["occurrence_count"], 3)
        self.assertEqual(first["input_text"].count("Description: A metallic element."), 1)
        self.assertNotIn("curation notes", first["input_text"])
        self.assertEqual(unmatched["matched_terms"], [])
        self.assertEqual(unmatched["record_ids"], [])
        self.assertNotIn("Matched Mech records", unmatched["input_text"])
        self.assertNotIn("Not a native definition", missing["input_text"])
        self.assertEqual(document["coverage"]["gap_text_only_discussions"], 1)
        self.assertEqual(document["coverage"]["label_only_matched_discussions"], 1)
        self.assertEqual(document["coverage"]["records_with_descriptions"], 2)
        self.assertEqual(first["input_sha256"], inputs.digest(first["input_text"].encode()))

    def test_missing_and_unsupported_native_description_fields_are_explicit(self):
        records, _ = self.acquire()
        water = next(record for record in records if record["label"] == "water")
        self.assertEqual((water["description"], water["description_status"]), ("", "missing_native_field"))
        original = next(record for record in self.selected if record["label"] == "water")
        raw = inputs.json_bytes(self.documents["water.yaml"] | {"definition": "Do not import an undeclared field."})
        changed = copy.deepcopy(original)
        changed["mech"] = "MediaIngredientMech"
        changed["source"]["sha256"] = inputs.digest(raw)
        source = self.config["sources"][0] | {"name": "MediaIngredientMech"}
        projected = inputs.project_record(raw, changed, source, source["roots"][0])
        self.assertEqual(projected["description"], "")
        self.assertIsNone(projected["description_field"])
        self.assertEqual(projected["description_status"], "unsupported_field")
        iron = next(record for record in records if record["source"]["path"] == "data/iron.yaml")
        self.assertEqual(iron["definition_sources"], ["CHEBI:18248"])

    def test_offline_gate_rejects_stale_inputs_extra_records_and_note_fallbacks(self):
        records, _ = self.acquire()
        original = inputs.build_inputs(self.snapshot, self.terms, records)
        changes = [lambda row: row.update(terms_sha256="0" * 64),
                   lambda row: row["items"][0].update(input_text="modified independently"),
                   lambda row: row["coverage"].update(discussions=1000),
                   lambda row: row["records"].append(copy.deepcopy(row["records"][0])),
                   lambda row: row["records"][0].update(description_field="notes"),
                   lambda row: row["records"][0]["source"].update(sha256="0" * 64)]
        for change in changes:
            with self.subTest(change=change):
                row = copy.deepcopy(original)
                change(row)
                with self.assertRaises(ValueError):
                    self.validate(row)

    def test_bad_mentions_and_unknown_owners_cannot_enter_inputs(self):
        records, _ = self.acquire()
        document = copy.deepcopy(self.terms)
        document["terms"][0]["postings"][0]["mentions"][0]["text"] = "invented"
        with self.assertRaisesRegex(ValueError, "original gap text"):
            inputs.build_inputs(self.snapshot, document, records)
        with self.assertRaisesRegex(ValueError, "cover every exact matched owner"):
            inputs.build_inputs(self.snapshot, self.terms, records[1:])
        document = copy.deepcopy(self.terms)
        document["terms"][0]["postings"] = []
        with self.assertRaisesRegex(ValueError, "no discussion postings"):
            inputs.build_inputs(self.snapshot, document, records)

    def test_public_membership_publication_holds_and_license_hashes_are_enforced(self):
        config = copy.deepcopy(self.config)
        config["sources"][0]["repository"] = "CultureBotAI/NotPublicMech"
        with self.assertRaisesRegex(ValueError, "canonical public repository"):
            inputs.acquire_records(self.selected, config, self.directory, self.directory, self.directory / "cache")
        config = copy.deepcopy(self.config)
        config["sources"][0]["publication_allowed"] = False
        with self.assertRaisesRegex(ValueError, "permitted source root"):
            inputs.acquire_records(self.selected, config, self.directory, self.directory, self.directory / "cache")
        config = copy.deepcopy(self.config)
        config["sources"][0]["license_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "license bytes"):
            inputs.acquire_records(self.selected, config, self.directory, self.directory, self.directory / "cache")
        selected = copy.deepcopy(self.selected)
        selected[0]["source"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            inputs.acquire_records(selected, self.config, self.directory, self.directory, self.directory / "cache", canary=True)


if __name__ == "__main__":
    unittest.main()
