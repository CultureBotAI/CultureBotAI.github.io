"""New Mechs remain watched without changing the historical vocabulary census."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))

import check_updates
import roots


class AdditionUpdateTests(unittest.TestCase):
    def setUp(self):
        self.additions = json.loads((ROOT / "_fleet/data/additions.json").read_text())

    def test_pathway_record_changes_are_reported_outside_the_census(self):
        entry = self.additions["PathwayMech"]
        compare = {"ahead_by": 1, "commits": [{"sha": "b" * 40}], "files": [
            {"filename": "data/pathways/new.yaml", "status": "added"},
            {"filename": "data/pathways/nested/old.yaml", "status": "modified"},
        ]}
        row = check_updates.drift(entry, "PathwayMech", set(), api=lambda _: compare)
        self.assertEqual((row["added"], len(row["records"])), (1, 2))
        self.assertIn("records: 1 added", check_updates.verdict(row))
        self.assertNotIn("PathwayMech", roots.RECORD_GLOBS)
        census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())
        self.assertNotIn("PathwayMech", census)
        self.assertNotIn("DUFMech", census)

    def test_supplemental_sources_are_watched_without_page_links(self):
        cited = check_updates.watched({"repositories": []}, [], self.additions)
        self.assertIn("pages/browse.html", cited["pathwaymech"])
        path = self.additions["DUFMech"]["source_path"]
        self.assertIn(path, cited["dufmech"])
        changes = check_updates.classify("DUFMech", [{"filename": path, "status": "modified"}], cited["dufmech"])
        self.assertEqual(changes["claims"], [path])
        self.assertEqual(changes["records"], [])
        self.assertNotIn("DUFMech", check_updates.UPDATE_RECORD_GLOBS)

    def test_declared_uncounted_status_is_not_a_failed_check(self):
        line = check_updates.summary([], [("uncounted", "DUFMech", "Seed worklist")], "matches", [], [])
        self.assertNotIn("Not checked", line)
        self.assertNotIn("DUFMech", line)


if __name__ == "__main__":
    unittest.main()
