"""A frozen DUF worklist is counted by family, without inventing evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))

import build_subsets
import duf_records
import prefix_census
import roots


class DUFRecordTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.rows = [
            {"pfam_id": "PF00001", "interpro_id": "IPR000001", "name": "First family",
             "unknown_status": "UNKNOWN_CANDIDATE",
             "description": "Related to Pfam:PF09999 and PMID:123; [[cite:PUB00055555]]."},
            {"pfam_id": "PF00002", "interpro_id": "", "name": "Second family",
             "unknown_status": "KNOWN_HISTORICAL_DUF", "description": ""},
        ]

    def freeze(self, date="2026-10-01", rows=None):
        rows = self.rows if rows is None else rows
        base = "interpro-pfam-duf-" + date
        payload = self.directory / (base + ".json")
        content = json.dumps(rows).encode()
        payload.write_bytes(content)
        manifest = self.directory / (base + ".manifest.json")
        counts = {}
        for row in rows:
            status = row["unknown_status"]
            counts[status] = counts.get(status, 0) + 1
        manifest.write_text(json.dumps({
            "snapshot": {"date": date, "id": base},
            "files": {"json": {"path": payload.name, "bytes": len(content),
                               "sha256": hashlib.sha256(content).hexdigest()}},
            "rows": {"total": len(rows), "by_unknown_status": counts},
        }))
        return payload, manifest

    def paths(self):
        return [str(path) for path in self.directory.glob("*.json")]

    def edit_manifest(self, manifest, change):
        blob = json.loads(manifest.read_text())
        change(blob)
        manifest.write_text(json.dumps(blob))

    def test_one_record_per_family_with_missing_interpro_allowed(self):
        self.freeze()
        documents = list(roots.record_documents("DUFMech", self.paths()))
        self.assertEqual(roots.record_count("DUFMech", self.paths()), 2)
        self.assertEqual(len(documents), 2)
        self.assertIn("identifier: Pfam:PF00001", documents[0][1])
        self.assertIn("interpro_id: InterPro:IPR000001", documents[0][1])
        self.assertNotIn("interpro_id:", documents[1][1])
        self.assertNotIn("PMID:PUB00055555", documents[0][1])
        self.assertIn("cite:PUB00055555", documents[0][1])

    def test_mentions_count_but_prose_does_not_create_shared_term_evidence(self):
        self.freeze()
        text = next(roots.record_documents("DUFMech", self.paths()))[1]
        mentions, citations = build_subsets.mentions_and_citations(text)
        self.assertIn("Pfam:PF09999", mentions)
        self.assertEqual(citations, {"Pfam:PF00001", "InterPro:IPR000001"})
        prefixes = prefix_census.rx.findall(text)
        self.assertEqual(prefixes.count("Pfam"), 2)
        self.assertEqual(prefixes.count("InterPro"), 1)
        self.assertEqual(prefixes.count("PMID"), 1)

    def test_newest_snapshot_only_and_bad_latest_never_falls_back(self):
        self.freeze("2026-09-30", self.rows[:1])
        newest, _ = self.freeze()
        self.assertEqual(roots.record_count("DUFMech", self.paths()), 2)
        newest.write_text(newest.read_text().replace("First family", "Other family"))
        with self.assertRaisesRegex(SystemExit, "SHA-256"):
            list(roots.record_documents("DUFMech", self.paths()))

    def test_manifest_cannot_point_outside_counted_sources(self):
        payload, manifest = self.freeze()
        with self.assertRaisesRegex(SystemExit, "missing from the record paths"):
            duf_records.snapshot([str(manifest)])
        self.edit_manifest(manifest, lambda doc: doc["files"]["json"].update(path="../outside.json"))
        with self.assertRaisesRegex(SystemExit, "matching snapshot filename"):
            duf_records.snapshot(self.paths())

    def test_duplicate_or_invalid_identifiers_fail_closed(self):
        for change, message in (
                (lambda rows: rows[1].update(pfam_id="PF00001"), "duplicate Pfam"),
                (lambda rows: rows[0].update(pfam_id="00001"), "valid Pfam"),
                (lambda rows: rows[0].update(pfam_id="PF１２３４５"), "valid Pfam"),
                (lambda rows: rows[0].update(interpro_id="IPR１２３４５６"), "invalid InterPro"),
                (lambda rows: rows[0].update(interpro_id="IPRbad"), "invalid InterPro")):
            with self.subTest(message=message):
                rows = deepcopy(self.rows)
                change(rows)
                self.freeze(rows=rows)
                with self.assertRaisesRegex(SystemExit, message):
                    duf_records.snapshot(self.paths())

    def test_manifest_identity_counts_and_hash_are_checked(self):
        changes = [
            (lambda doc: doc["snapshot"].update(date="2026-09-30"), "snapshot identity"),
            (lambda doc: doc["rows"].update(total=99), "family count"),
            (lambda doc: doc["rows"]["by_unknown_status"].update(UNKNOWN_CANDIDATE=99), "unknown-status counts"),
            (lambda doc: doc["files"]["json"].update(bytes=1), "byte count"),
            (lambda doc: doc["files"]["json"].update(sha256="0" * 64), "SHA-256"),
        ]
        for change, message in changes:
            with self.subTest(message=message):
                _, manifest = self.freeze()
                self.edit_manifest(manifest, change)
                with self.assertRaisesRegex(SystemExit, message):
                    duf_records.snapshot(self.paths())

    def test_no_manifest_is_an_error_not_an_empty_corpus(self):
        with self.assertRaisesRegex(SystemExit, "no dated worklist manifest"):
            duf_records.snapshot([])

    def test_yaml_records_keep_existing_text_and_physical_count(self):
        path = self.directory / "record.yaml"
        path.write_text("id: PathwayMech:test\nlabel: Example\n")
        with mock.patch.object(roots, "read_record", wraps=roots.read_record) as read:
            self.assertEqual(roots.record_count("PathwayMech", [str(path)]), 1)
            read.assert_not_called()
            self.assertEqual(list(roots.record_documents("PathwayMech", [str(path)])),
                             [(str(path), path.read_text())])


if __name__ == "__main__":
    unittest.main()
