"""Repository activity includes governance and the website without adding corpora."""
import contextlib
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
import mech_stats
import roots


class PRActivityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "stats.json"
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(mech_stats, "OUT", str(self.output)).start()
        self.census = mock.patch.object(
            mech_stats, "review_census", return_value=(7, 2, "mapping_status", "a" * 40)
        ).start()
        self.gh = mock.patch.object(mech_stats.subprocess, "run").start()

    def run_stats(self, *arguments):
        with (mock.patch.object(sys, "argv", ["mech_stats.py", *arguments]),
              contextlib.redirect_stdout(io.StringIO())):
            mech_stats.main()
        return json.loads(self.output.read_text())

    def cached_snapshot(self):
        return {
            "as_of": "2026-01-01",
            "mechs": [{"mech": name, "repo": "proteintraitsmech" if name == "ProteinTraitsMech" else name,
                       "merged_prs": number}
                      for number, name in enumerate(roots.ORDER)],
            "additional_repositories": [
                {"repo": "culturebotai-claw", "merged_prs": 301},
                {"repo": "CultureBotAI.github.io", "merged_prs": 17},
            ],
            # Recompute the aggregate from its components, not a stale total.
            "merged_prs_total": -1,
        }

    def test_queries_all_fourteen_repositories_and_keeps_twelve_record_rows(self):
        expected_repos = ["proteintraitsmech" if name == "ProteinTraitsMech" else name
                          for name in roots.ORDER] + ["culturebotai-claw", "CultureBotAI.github.io"]
        values = dict(zip(expected_repos, range(10, 24)))

        def answer(command, **kwargs):
            query = command[command.index("-f") + 1]
            repo = query.removeprefix("q=repo:CultureBotAI/").removesuffix(" is:pr is:merged")
            return subprocess.CompletedProcess(command, 0, stdout=str(values[repo]), stderr="")

        self.gh.side_effect = answer
        actual = self.run_stats()
        self.assertEqual(len(expected_repos), 14)
        self.assertEqual(self.gh.call_args_list, [mock.call(
            ["gh", "api", "-X", "GET", "search/issues", "-f",
             f"q=repo:CultureBotAI/{repo} is:pr is:merged", "--jq", ".total_count"],
            capture_output=True, text=True,
        ) for repo in expected_repos])
        self.assertEqual([row["mech"] for row in actual["mechs"]], list(roots.ORDER))
        self.assertEqual(self.census.call_args_list, [mock.call(name) for name in roots.ORDER])
        self.assertEqual([row["merged_prs"] for row in actual["mechs"]], list(range(10, 22)))
        self.assertEqual(actual["additional_repositories"], [
            {"repo": "culturebotai-claw", "merged_prs": 22},
            {"repo": "CultureBotAI.github.io", "merged_prs": 23},
        ])
        self.assertEqual(actual["merged_prs_total"], sum(range(10, 24)))
        self.assertEqual(sum(row["records"] for row in actual["mechs"]), 12 * 7)

    def test_no_prs_preserves_every_cached_count_without_querying(self):
        cached = self.cached_snapshot()
        self.output.write_text(json.dumps(cached))
        actual = self.run_stats("--no-prs")
        self.gh.assert_not_called()
        self.assertEqual([row["merged_prs"] for row in actual["mechs"]],
                         [row["merged_prs"] for row in cached["mechs"]])
        self.assertEqual(actual["additional_repositories"], cached["additional_repositories"])
        self.assertEqual(actual["merged_prs_total"], sum(range(12)) + 301 + 17)
        self.assertTrue(all(row["records"] == 7 for row in actual["mechs"]))

    def test_no_prs_missing_cache_fails_before_queries_or_record_scan(self):
        for absent in (None, "culturebotai-claw", "CultureBotAI.github.io", "TaxonMech"):
            with self.subTest(absent=absent):
                cached = self.cached_snapshot()
                if absent is None:
                    cached.pop("additional_repositories")
                else:
                    cached["mechs"] = [row for row in cached["mechs"] if row["mech"] != absent]
                    cached["additional_repositories"] = [row for row in cached["additional_repositories"]
                                                          if row["repo"] != absent]
                original = json.dumps(cached)
                self.output.write_text(original)
                with self.assertRaisesRegex(SystemExit, absent or "culturebotai-claw"):
                    self.run_stats("--no-prs")
                self.assertEqual(self.output.read_text(), original)
        self.gh.assert_not_called()
        self.census.assert_not_called()

    def test_no_prs_without_a_file_does_not_fall_back_to_github(self):
        with self.assertRaisesRegex(SystemExit, "requires cached PR counts"):
            self.run_stats("--no-prs")
        self.gh.assert_not_called()
        self.census.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_no_prs_cannot_relabel_counts_from_another_repository(self):
        for missing_repo in (False, True):
            with self.subTest(missing_repo=missing_repo):
                cached = self.cached_snapshot()
                if missing_repo:
                    cached["mechs"][0].pop("repo")
                else:
                    first, second = cached["mechs"][:2]
                    first["repo"], second["repo"] = second["repo"], first["repo"]
                original = json.dumps(cached)
                self.output.write_text(original)
                with self.assertRaisesRegex(SystemExit, "cached repository HabitatMech"):
                    self.run_stats("--no-prs")
                self.assertEqual(self.output.read_text(), original)
        self.gh.assert_not_called()
        self.census.assert_not_called()

    def test_no_prs_rejects_invalid_or_duplicate_additional_counts(self):
        for invalid in (None, -1, True, "17", "duplicate"):
            with self.subTest(invalid=invalid):
                cached = self.cached_snapshot()
                if invalid == "duplicate":
                    cached["additional_repositories"].append(cached["additional_repositories"][0])
                else:
                    cached["additional_repositories"][0]["merged_prs"] = invalid
                original = json.dumps(cached)
                self.output.write_text(original)
                with self.assertRaisesRegex(SystemExit, "culturebotai-claw"):
                    self.run_stats("--no-prs")
                self.assertEqual(self.output.read_text(), original)
        self.gh.assert_not_called()
        self.census.assert_not_called()


if __name__ == "__main__":
    unittest.main()
