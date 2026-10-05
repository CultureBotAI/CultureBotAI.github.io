"""The full dated census must remain visible without changing its evidence."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import build_data
from roots import ORDER


class FullHeatmapTests(unittest.TestCase):
    @staticmethod
    def build(census, subsets=None):
        census = json.loads(json.dumps(census))
        pins = {m: "a" * 40 for m in ORDER}
        census["_revisions"] = pins
        for m in ORDER:
            census[m].setdefault("files", 1)
        cells = {"_revisions": pins, "cells": {
            m + "|" + v: {"records": 1, "occurrences": n, "sha256": "0" * 64}
            for m in ORDER for v, n in census[m]["prefixes"].items() if n}}
        subsets = dict(subsets or {"edges": {}, "cells": {}})
        subsets["_revisions"] = pins
        with contextlib.redirect_stdout(io.StringIO()):
            return build_data.build(subsets, census, cells)

    def test_every_dated_vocabulary_and_occurrence_is_displayed(self):
        census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())
        saved = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())
        expected = {v for m in ORDER for v in census[m]["prefixes"]}
        self.assertEqual(set(saved["voc"]), expected)
        self.assertEqual(len(saved["voc"]), len(expected))
        for mech in ORDER:
            self.assertEqual(saved["heat"][mech],
                             {v: census[mech]["prefixes"].get(v, 0) for v in expected})

    def test_new_census_namespace_has_records_without_becoming_a_graph_filter(self):
        census = {m: {"prefixes": {}} for m in ORDER}
        census[ORDER[0]]["prefixes"] = {"AdditionalRegistry": 123}
        result = self.build(census)
        self.assertEqual(result["voc"], ["AdditionalRegistry"])
        self.assertEqual(result["heat"][ORDER[0]]["AdditionalRegistry"], 123)
        self.assertEqual(result["heat"][ORDER[-1]]["AdditionalRegistry"], 0)
        self.assertEqual(result["cells"], {ORDER[0] + "--AdditionalRegistry": 1})
        self.assertEqual(result["indexed_voc"], [])
        self.assertEqual(result["vocab_edges"], [])

    def test_unindexed_columns_sort_by_coverage_then_occurrences(self):
        census = {m: {"prefixes": {"DOI": 10000}} for m in ORDER}
        census[ORDER[0]]["prefixes"].update({"Wide": 1, "Many": 50, "Few": 5, "EqualA": 1, "EqualB": 1})
        census[ORDER[1]]["prefixes"]["Wide"] = 1
        result = self.build(census)
        self.assertEqual(result["voc"], ["DOI", "Wide", "Many", "Few", "EqualA", "EqualB"])

    def test_doi_and_pmid_lead_then_citable_works_sort_with_other_vocabularies(self):
        census = {m: {"prefixes": {}} for m in ORDER}
        census[ORDER[0]]["prefixes"] = {"DOI": 1, "PMID": 1, "CHEBI": 900,
                                         "PMCID": 1, "Wikipedia": 50, "Registry": 1}
        census[ORDER[1]]["prefixes"] = {"PMCID": 1, "Wikipedia": 1}
        census[ORDER[2]]["prefixes"] = {"PMCID": 1}
        self.assertEqual(self.build(census)["voc"],
                         ["DOI", "PMID", "PMCID", "Wikipedia", "CHEBI", "Registry"])


if __name__ == "__main__":
    unittest.main()
