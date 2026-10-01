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
from roots import CITATION, ORDER


class FullHeatmapTests(unittest.TestCase):
    @staticmethod
    def build(census, subsets=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return build_data.build(subsets or {"edges": {}, "cells": {}}, census)

    def test_every_dated_vocabulary_and_occurrence_is_displayed(self):
        census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())
        saved = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())
        expected = {v for m in ORDER for v in census[m]["prefixes"]}
        self.assertEqual(set(saved["voc"]), expected)
        self.assertEqual(len(saved["voc"]), len(expected))
        for mech in ORDER:
            self.assertEqual(saved["heat"][mech],
                             {v: census[mech]["prefixes"].get(v, 0) for v in expected})

    def test_new_census_namespace_appears_without_a_record_index(self):
        census = {m: {"prefixes": {}} for m in ORDER}
        census[ORDER[0]]["prefixes"] = {"AdditionalRegistry": 123}
        result = self.build(census)
        self.assertEqual(result["voc"], ["AdditionalRegistry"])
        self.assertEqual(result["heat"][ORDER[0]]["AdditionalRegistry"], 123)
        self.assertEqual(result["heat"][ORDER[-1]]["AdditionalRegistry"], 0)
        self.assertEqual(result["cells"], {})
        self.assertEqual(result["vocab_edges"], [])

    def test_unindexed_columns_sort_by_coverage_then_occurrences(self):
        census = {m: {"prefixes": {"DOI": 10000}} for m in ORDER}
        census[ORDER[0]]["prefixes"].update({"Wide": 1, "Many": 50, "Few": 5, "EqualA": 1, "EqualB": 1})
        census[ORDER[1]]["prefixes"]["Wide"] = 1
        result = self.build(census)
        self.assertEqual(result["voc"], ["Wide", "Many", "Few", "EqualA", "EqualB", "DOI"])

    def test_citable_works_stay_together_at_the_right(self):
        census = {m: {"prefixes": {v: 10 for v in CITATION}} for m in ORDER}
        census[ORDER[0]]["prefixes"]["Registry"] = 1
        self.assertEqual(self.build(census)["voc"], ["Registry", *CITATION])


if __name__ == "__main__":
    unittest.main()
