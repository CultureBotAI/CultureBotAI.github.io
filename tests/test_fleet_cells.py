"""Every heatmap occurrence has a record-list explanation at the census pin."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))

import build_cells
import build_data
import build_subsets
from roots import ORDER

PIN = "1" * 40


class CellScanTests(unittest.TestCase):
    def scan(self, mech, documents, cap=300):
        config = {"root": "/example/" + mech,
                  "base": build_subsets.SITE_BASE[mech]}
        with (mock.patch.dict(build_cells.MECHS, {mech: config}),
              mock.patch.object(build_cells, "record_documents", return_value=iter(documents))):
            return build_cells.scan(mech, cap_cell=cap, source_revision=PIN)

    def test_aliases_count_each_mention_but_each_record_once(self):
        documents = [
            ("/example/TraitMech/data/traits/a.yaml",
             "id: TraitMech:a\nlabel: First trait\n"
             "grounding: ChEBI:1\nnotes: CHEBI:1 ChEBI:2\n"
             "references: PubMed:42 PIMD:42 PMID:42 DOI:10.1/a doi:10.1/a\n"
             "source: gold.ecosystem:1 gold:2 gomodel:YeastPathways_GLYCOLYSIS\n"),
            ("/example/TraitMech/data/traits/b.yaml",
             "id: TraitMech:b\nlabel: Second trait\nnotes: CHEBI:3\n"),
        ]
        cells = self.scan("TraitMech", documents)
        expected = {"CHEBI": (2, 4), "PMID": (1, 3), "DOI": (1, 2),
                    "GOLD": (1, 2), "gomodel": (1, 1)}
        self.assertEqual(set(cells), set(expected))
        for prefix, (records, occurrences) in expected.items():
            with self.subTest(prefix=prefix):
                self.assertEqual(cells[prefix]["total"], records)
                self.assertEqual(cells[prefix]["occurrences"], occurrences)
                self.assertEqual(len(cells[prefix]["records"]), records)
                self.assertEqual(cells[prefix]["mech"], "TraitMech")
                self.assertEqual(cells[prefix]["prefix"], prefix)
        self.assertEqual([row[1] for row in cells["CHEBI"]["records"]],
                         ["First trait", "Second trait"])

    def test_citation_and_prose_cells_do_not_change_overlap_evidence(self):
        text = ("id: TraitMech:a\nlabel: First trait\n"
                "notes: CHEBI:999 PMID:42 MetaCyc:RXN_1\n"
                "reference: DOI:10.1/a\ncurator: GOC:curator\n"
                "internal: kgmicrobe.compound:99 TraitMech:private\n")
        cells = self.scan("TraitMech", [("/example/TraitMech/data/traits/a.yaml", text)])
        self.assertEqual(set(cells), {"CHEBI", "PMID", "MetaCyc", "DOI"})
        self.assertEqual(build_subsets.mentions_and_citations(text)[1], {"DOI:10.1/a"})

    def test_logical_duf_records_share_one_file_but_are_distinct_links(self):
        path = "/example/DUFMech/data/worklists/interpro-pfam-duf-2026-10-01.json"
        documents = [(path, f"identifier: Pfam:PF0000{n}\nlabel: Family {n}\n"
                            "description: PMID:42 Pfam:PF99999\n") for n in (1, 2)]
        cells = self.scan("DUFMech", documents)
        self.assertEqual(cells["Pfam"]["total"], 2)
        self.assertEqual(cells["Pfam"]["occurrences"], 4)
        self.assertEqual(cells["PMID"]["total"], 2)
        self.assertEqual([row[0] for row in cells["Pfam"]["records"]],
                         ["PF00001.html", "PF00002.html"])

    def test_unpublished_isolate_links_to_the_exact_source_pin(self):
        path = "/example/CommunityMech/data/isolates/strain with #.yaml"
        cells = self.scan("CommunityMech", [(path,
                         "id: CommunityMech:isolate\nlabel: Isolate record\nterm: ENVO:1\n")])
        cell = cells["ENVO"]
        self.assertEqual(cell["total"], 1)
        self.assertEqual(cell["occurrences"], 1)
        row, = cell["records"]
        self.assertEqual(row[1], "Isolate record")
        self.assertEqual(row[2], "https://github.com/CultureBotAI/CommunityMech/blob/" + PIN +
                         "/data/isolates/strain%20with%20%23.yaml")

    def test_first_300_links_are_stable_and_do_not_truncate_totals(self):
        documents = [(f"/example/TraitMech/data/traits/{n:04d}.yaml",
                      f"id: TraitMech:{n}\nlabel: Trait {n}\nterms: PMID:42 PMID:42\n")
                     for n in range(307)]
        first = self.scan("TraitMech", documents)["PMID"]
        second = self.scan("TraitMech", documents)["PMID"]
        self.assertEqual(first, second)
        self.assertEqual(first["total"], 307)
        self.assertEqual(first["occurrences"], 614)
        self.assertEqual(len(first["records"]), 300)
        self.assertEqual([row[0] for row in first["records"]],
                         [f"{n:04d}.html" for n in range(300)])

    def test_no_counted_namespace_produces_no_cell_asset(self):
        cells = self.scan("TraitMech", [("/example/TraitMech/data/traits/a.yaml",
                         "id: TraitMech:a\nlabel: Trait\ncurator: GOC:curator\n")])
        self.assertEqual(cells, {})


class CellProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.data = self.directory / "data"
        self.data.mkdir()
        self.out = self.directory / "fleet"
        (self.out / "cells").mkdir(parents=True)
        self.summary = self.data / "cells_summary.json"
        self.asset = self.out / "cells/TraitMech--CHEBI.json"
        self.summary.write_bytes(b"existing summary\n")
        self.asset.write_bytes(b"existing cell\n")
        self.census = {"_revisions": {"TraitMech": PIN},
                       "TraitMech": {"files": 1, "prefixes": {"CHEBI": 2}}}
        self.document = ("/example/TraitMech/data/traits/a.yaml",
                         "id: TraitMech:a\nlabel: Trait\nterm: CHEBI:1\nnotes: ChEBI:1\n")

    def run_main(self, *, revision=PIN, moved=False, final_revision=None):
        (self.data / "prefix_census.json").write_text(json.dumps(self.census))
        with (mock.patch.object(build_cells, "DATA", str(self.data)),
              mock.patch.object(build_cells, "OUT", str(self.out)),
              mock.patch.object(build_cells, "ORDER", ["TraitMech"]),
              mock.patch.object(build_cells, "prepare"),
              mock.patch.dict(build_cells.MECHS, {"TraitMech": {
                  "root": "/example/TraitMech", "base": build_subsets.SITE_BASE["TraitMech"]}}),
              mock.patch.object(build_cells, "record_paths", return_value=[self.document[0]]),
              mock.patch.object(build_cells, "record_documents", side_effect=lambda *args: iter([self.document])),
              mock.patch.object(build_cells, "revision", return_value=revision,
                                side_effect=[revision, final_revision] if final_revision else None),
              mock.patch.object(build_cells, "unchanged",
                                side_effect=SystemExit("HEAD moved") if moved else None),
              contextlib.redirect_stdout(io.StringIO())):
            build_cells.main()

    def assert_outputs_preserved(self):
        self.assertEqual(self.summary.read_bytes(), b"existing summary\n")
        self.assertEqual(self.asset.read_bytes(), b"existing cell\n")
        self.assertEqual(sorted(p.name for p in (self.out / "cells").iterdir()),
                         ["TraitMech--CHEBI.json"])

    def test_clean_matching_pin_writes_exact_counts_and_revision(self):
        self.run_main()
        summary = json.loads(self.summary.read_text())
        asset = json.loads(self.asset.read_text())
        self.assertEqual(summary["_revisions"], {"TraitMech": PIN})
        cell_summary = summary["cells"]["TraitMech|CHEBI"]
        self.assertEqual(cell_summary["records"], 1)
        self.assertEqual(cell_summary["occurrences"], 2)
        self.assertEqual(cell_summary["sha256"], hashlib.sha256(self.asset.read_bytes()).hexdigest())
        self.assertEqual(asset["total"], 1)
        self.assertEqual(asset["occurrences"], 2)

    def test_missing_dirty_or_mismatched_source_pin_preserves_existing_outputs(self):
        for revision in (None, PIN + "+dirty", "2" * 40):
            with self.subTest(revision=revision), self.assertRaises((SystemExit, ValueError)):
                self.run_main(revision=revision)
            self.assert_outputs_preserved()

    def test_missing_census_pin_preserves_existing_outputs(self):
        self.census["_revisions"] = {}
        with self.assertRaises((SystemExit, ValueError)):
            self.run_main()
        self.assert_outputs_preserved()

    def test_revision_moving_during_scan_preserves_existing_outputs(self):
        with self.assertRaises((SystemExit, ValueError)):
            self.run_main(moved=True)
        self.assert_outputs_preserved()

    def test_source_becoming_dirty_after_scan_preserves_existing_outputs(self):
        with self.assertRaises((SystemExit, ValueError)):
            self.run_main(final_revision=PIN + "+dirty")
        self.assert_outputs_preserved()

    def test_logical_record_count_mismatch_preserves_existing_outputs(self):
        self.census["TraitMech"]["files"] = 2
        with self.assertRaises((SystemExit, ValueError)):
            self.run_main()
        self.assert_outputs_preserved()

    def test_any_occurrence_mismatch_preserves_existing_outputs(self):
        for prefixes in ({"CHEBI": 1}, {"CHEBI": 3}, {"CHEBI": 2, "PMID": 1}, {}):
            self.census["TraitMech"]["prefixes"] = prefixes
            with self.subTest(prefixes=prefixes), self.assertRaises((SystemExit, ValueError)):
                self.run_main()
            self.assert_outputs_preserved()

    def test_subset_only_regeneration_preserves_full_cell_assets_and_summary(self):
        # A graph-only refresh must never replace all-census lists with its
        # narrower structured-overlap prefix list.
        mechs = ["TraitMech", "ProteinTraitsMech", "TaxonMech"]
        narrow = {"terms": {}, "cells": {"CHEBI": [1, [("narrow.html", "Narrow record")]]},
                  "votes": {}, "own": {}}
        with (mock.patch.object(build_subsets, "DATA", str(self.data)),
              mock.patch.object(build_subsets, "OUT", str(self.out)),
              mock.patch.object(build_subsets, "ORDER", mechs),
              mock.patch.object(build_subsets, "prepare"),
              mock.patch.object(build_subsets, "scan", return_value=narrow),
              mock.patch.object(build_subsets, "revision", return_value=PIN),
              mock.patch.object(build_subsets, "unchanged"),
              contextlib.redirect_stdout(io.StringIO())):
            build_subsets.main()
        self.assert_outputs_preserved()
        generated = json.loads((self.data / "subsets_summary.json").read_text())
        self.assertEqual(generated["cells"], {m + "|CHEBI": 1 for m in mechs})


class FullCellIntegrationTests(unittest.TestCase):
    def test_record_lists_do_not_expand_graph_edges_or_graph_vocabulary_filters(self):
        census = {m: {"files": 1, "prefixes": {}} for m in ORDER}
        revisions = {m: PIN for m in ORDER}
        census["_revisions"] = revisions
        census[ORDER[0]]["prefixes"] = {"DOI": 2, "PMID": 1, "MetaCyc": 1, "CHEBI": 3,
                                          "PATO": 1}
        sub = {"_revisions": revisions, "edges": {}, "cells": {ORDER[0] + "|CHEBI": 1}}
        summary = {"_revisions": revisions,
                   "cells": {ORDER[0] + "|" + prefix: {"records": 1, "occurrences": n,
                                                        "sha256": "a" * 64}
                             for prefix, n in census[ORDER[0]]["prefixes"].items()}}
        with contextlib.redirect_stdout(io.StringIO()):
            result = build_data.build(sub, census, summary)
        self.assertEqual(result["vocab_edges"], [])
        self.assertEqual(result["voc"][:2], ["DOI", "PMID"])
        self.assertEqual(result["cells"], {ORDER[0] + "--" + prefix: 1
                                          for prefix in census[ORDER[0]]["prefixes"]})
        self.assertEqual(set(result["indexed_voc"]), {"CHEBI"})
        self.assertNotIn("MetaCyc", result["indexed_voc"])
        self.assertNotIn("PATO", result["indexed_voc"])

    def test_every_committed_positive_cell_matches_its_census_and_asset(self):
        census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())
        summary = json.loads((ROOT / "_fleet/data/cells_summary.json").read_text())
        fleet = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())
        expected = {mech + "|" + prefix
                    for mech in ORDER for prefix, n in census[mech]["prefixes"].items() if n}
        self.assertEqual(summary["_revisions"], census["_revisions"])
        self.assertEqual(set(summary["cells"]), expected)
        self.assertEqual({key for key in fleet["cells"] if not key.startswith("kg-microbe--")},
                         {key.replace("|", "--") for key in expected})
        assets = ROOT / "assets/fleet/cells"
        # Path.rglob includes ignored and hidden entries, so extra generated
        # cells cannot remain unnoticed after a vocabulary disappears.
        self.assertEqual({str(path.relative_to(assets)) for path in assets.rglob("*")},
                         {key.replace("|", "--") + ".json" for key in expected})
        for key in sorted(expected):
            with self.subTest(cell=key):
                mech, prefix = key.split("|")
                metadata = summary["cells"][key]
                content = (ROOT / "assets/fleet/cells" / (key.replace("|", "--") + ".json")).read_bytes()
                asset = json.loads(content)
                self.assertEqual(hashlib.sha256(content).hexdigest(), metadata["sha256"])
                self.assertEqual(asset["mech"], mech)
                self.assertEqual(asset["prefix"], prefix)
                self.assertEqual(asset["occurrences"], census[mech]["prefixes"][prefix])
                self.assertEqual(metadata["occurrences"], asset["occurrences"])
                self.assertEqual(metadata["records"], asset["total"])
                self.assertEqual(fleet["cells"][key.replace("|", "--")], asset["total"])
                self.assertGreater(asset["total"], 0)
                self.assertLessEqual(asset["total"], census[mech]["files"])
                self.assertEqual(len(asset["records"]), min(300, asset["total"]))
                self.assertTrue(asset["base"].startswith("https://"))
                for row in asset["records"]:
                    self.assertIn(len(row), (2, 3))
                    self.assertIsInstance(row[0], str)
                    self.assertIsInstance(row[1], str)
                    if len(row) == 3:
                        repo = "proteintraitsmech" if mech == "ProteinTraitsMech" else mech
                        self.assertTrue(row[2].startswith("https://github.com/CultureBotAI/" + repo +
                            "/blob/" + census["_revisions"][mech] + "/"))

    def test_import_does_not_read_checkouts_or_write_outputs(self):
        program = (
            "import builtins, sys; from unittest import mock; "
            f"sys.path.insert(0, {str(ROOT / 'scripts/fleet')!r}); "
            "import roots, build_subsets; "
            "roots.record_paths = mock.Mock(side_effect=AssertionError('read checkout')); "
            "roots.record_documents = mock.Mock(side_effect=AssertionError('scan checkout')); "
            "build_subsets.prepare = mock.Mock(side_effect=AssertionError('prepare checkouts')); "
            "original_open = builtins.open; "
            "\ndef guarded_open(file, mode='r', *args, **kwargs):\n"
            "    if any(flag in mode for flag in 'wax+'): raise AssertionError('write during import')\n"
            "    return original_open(file, mode, *args, **kwargs)\n"
            "builtins.open = guarded_open\nimport build_cells\n"
        )
        result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
