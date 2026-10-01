"""New Mechs remain watched without changing the historical vocabulary census."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

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

    def test_a_new_dated_duf_worklist_requires_a_claim_refresh(self):
        # The snapshot writer creates a fresh filename for every date. Watching
        # only the original pin silently treats a later snapshot as tooling.
        cited = check_updates.watched({"repositories": []}, [], self.additions)
        paths = [f"data/worklists/interpro-pfam-duf-2026-10-02.{extension}"
                 for extension in ("json", "tsv", "manifest.json")]
        compare = {"ahead_by": 1, "commits": [{"sha": "b" * 40}], "files": [
            {"filename": path, "status": "added"} for path in paths]}
        row = check_updates.drift(self.additions["DUFMech"], "DUFMech", cited["dufmech"],
                                  api=lambda _: compare)
        self.assertEqual(row["claims"], [paths[-1]])
        self.assertEqual(row["records"], [])
        line = check_updates.summary([row], [("uncounted", "DUFMech", "Seed worklist")], "matches", [], [])
        self.assertIn("DUFMech", line)
        self.assertNotIn("nothing found", line)
        # An unrelated repository must not acquire DUF-specific claim paths.
        self.assertEqual(check_updates.classify("PathwayMech", compare["files"], set())["claims"], [])

        # Exercise main's identity lookup too: uncounted DUF has no corpus glob
        # and previously reached drift() as None, bypassing Mech-specific rules.
        drift = check_updates.drift
        def compare_repo(entry, mech, watched):
            response = compare if entry["repo"] == "DUFMech" else {"ahead_by": 0, "files": []}
            return drift(entry, mech, watched, api=lambda _: response)
        output = io.StringIO()
        with (mock.patch.object(check_updates, "drift", side_effect=compare_repo),
              mock.patch.object(check_updates, "pages_check", return_value=("current", "current")),
              mock.patch.object(check_updates, "manifest_check", return_value="matches"),
              mock.patch.object(check_updates, "dead_links", return_value=([], [])),
              mock.patch.object(check_updates.check_cards, "check", return_value=[]),
              contextlib.redirect_stdout(output)):
            self.assertEqual(check_updates.main(), 0)
        self.assertIn("**Refresh would change:** repositories: DUFMech.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
