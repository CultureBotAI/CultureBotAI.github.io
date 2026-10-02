"""New suite corpora and subsequently dated DUF worklists remain watched."""
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


class SuiteUpdateTests(unittest.TestCase):
    def setUp(self):
        audit = json.loads((ROOT / "_fleet/data/site_audit.json").read_text())
        self.entries = {entry["repo"]: entry for entry in audit["repositories"]}

    def test_pathway_changes_are_part_of_the_measured_corpus(self):
        compare = {"ahead_by": 1, "commits": [{"sha": "b" * 40}], "files": [
            {"filename": "data/pathways/new.yaml", "status": "added"},
            {"filename": "data/pathways/nested/old.yaml", "status": "modified"},
        ]}
        row = check_updates.drift(self.entries["PathwayMech"], "PathwayMech", set(), api=lambda _: compare)
        self.assertEqual((row["added"], len(row["records"])), (1, 2))
        self.assertIn("records: 1 added", check_updates.verdict(row))
        self.assertIn("PathwayMech", roots.RECORD_GLOBS)

    def test_raw_worklist_sources_are_watched_without_page_links(self):
        cited = check_updates.watched({"repositories": []}, [])
        self.assertIn("pages/browse.html", cited["pathwaymech"])
        self.assertIn("data/worklists/interpro-pfam-duf-2026-10-01.json", cited["dufmech"])

    def test_a_new_dated_duf_worklist_requires_a_refresh(self):
        cited = check_updates.watched({"repositories": []}, [])
        paths = [f"data/worklists/interpro-pfam-duf-2026-10-02.{extension}"
                 for extension in ("json", "tsv", "manifest.json")]
        compare = {"ahead_by": 1, "commits": [{"sha": "b" * 40}], "files": [
            {"filename": path, "status": "added"} for path in paths]}
        row = check_updates.drift(self.entries["DUFMech"], "DUFMech", cited["dufmech"], api=lambda _: compare)
        # The selected snapshot's JSON and manifest both affect the measured
        # family corpus. Exact partition depends on the adapter's source globs.
        self.assertTrue({paths[0], paths[-1]} <= set(row["claims"] + row["records"]))
        self.assertIn("worklist source files: 2 added", check_updates.verdict(row))
        self.assertNotIn("records: 2 added", check_updates.verdict(row))
        line = check_updates.summary([row], [("ok", "DUFMech", "Seed families")], "matches", [], [])
        self.assertIn("DUFMech", line)
        self.assertNotIn("nothing found", line)
        self.assertEqual(check_updates.classify("PathwayMech", compare["files"], set())["claims"], [])

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
