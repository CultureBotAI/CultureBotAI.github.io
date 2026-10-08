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
        self.assertIn("data/worklists/interpro-pfam-duf-2026-10-05.json", cited["dufmech"])

    def test_a_new_dated_duf_worklist_requires_a_refresh(self):
        cited = check_updates.watched({"repositories": []}, [])
        paths = [f"data/worklists/interpro-pfam-duf-2026-10-08.{extension}"
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
              mock.patch.object(check_updates, "site_feature_check", return_value=[]),
              contextlib.redirect_stdout(output)):
            self.assertEqual(check_updates.main(), 0)
        self.assertIn("**Refresh would change:** repositories: DUFMech.", output.getvalue())

    def test_a_redeployed_site_flags_its_feature_verdicts(self):
        # #373: the feature table is judged on live sites, so a new deployment
        # since its recorded revision is what can make a verdict stale.
        features = {"mechs": {
            "AMech": {"site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
                      "deployed_revision": "a" * 40},
            "BMech": {"site": "https://example.org/b/", "repository": "https://github.com/CultureBotAI/BMech",
                      "deployed_revision": "b" * 40},
            "CMech": {"site": "https://example.org/c/", "repository": "https://github.com/CultureBotAI/CMech",
                      "deployed_revision": "c" * 40},
            "DMech": {"site": None, "note": "No site."},
        }}
        def api(path):
            if "/statuses?" in path:
                return [{"state": "success"}]
            if "AMech" in path:
                return [{"id": 1, "sha": "a" * 40, "created_at": "2026-10-05T09:00:00Z"}]
            if "BMech" in path:
                return [{"id": 2, "sha": "d" * 40, "created_at": "2026-10-06T09:00:00Z"}]
            raise check_updates.Unchecked(["HTTP 502"])
        rows = check_updates.site_feature_check(features, api=api)
        self.assertEqual([(s, m) for s, m, _ in rows], [("same", "AMech"), ("redeployed", "BMech"), ("NOT CHECKED", "CMech")])
        self.assertIn("bbbbbbb when checked, now ddddddd", rows[1][2])
        self.assertIn("HTTP 502", rows[2][2])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("website feature verdicts to re-check on redeployed sites: BMech", line)
        self.assertIn("site deployment CMech", line)
        self.assertNotIn("AMech", line)

    def feature_check_output(self, *, duf_recheck=False):
        features = {"checked_on": "2026-10-05", "scope": "Baseline browser audit.", "mechs": {
            "TraitMech": {"site": "https://example.org/trait/",
                          "repository": "https://github.com/CultureBotAI/TraitMech",
                          "deployed_revision": "a" * 40},
            "DUFMech": {"site": "https://example.org/duf/",
                        "repository": "https://github.com/CultureBotAI/DUFMech",
                        "deployed_revision": "b" * 40},
        }}
        if duf_recheck:
            features["mechs"]["DUFMech"].update(checked_on="2026-10-07", scope="DUF-only browser audit.")

        def api(path):
            if "/statuses?" in path:
                return [{"state": "success"}]
            sha = "a" * 40 if "TraitMech" in path else "c" * 40
            return [{"id": 1, "sha": sha, "created_at": "2026-10-07T09:00:00Z"}]

        drift = check_updates.drift
        site_check = check_updates.site_feature_check
        output = io.StringIO()
        with (mock.patch.object(check_updates, "FEATURES") as source,
              mock.patch.object(check_updates, "drift", side_effect=lambda entry, mech, watched:
                                drift(entry, mech, watched, api=lambda _: {"ahead_by": 0, "files": []})),
              mock.patch.object(check_updates, "pages_check", return_value=("current", "current")),
              mock.patch.object(check_updates, "manifest_check", return_value="matches"),
              mock.patch.object(check_updates, "dead_links", return_value=([], [])),
              mock.patch.object(check_updates.check_cards, "check", return_value=[]),
              mock.patch.object(check_updates, "site_feature_check", side_effect=lambda f: site_check(f, api=api)),
              contextlib.redirect_stdout(output)):
            source.read_text.return_value = json.dumps(features)
            self.assertEqual(check_updates.main(), 0)
        return output.getvalue()

    def test_feature_check_labels_baseline_and_inherited_row_dates(self):
        output = self.feature_check_output()
        self.assertIn("## Website feature table (baseline audit: 2026-10-05)", output)
        self.assertIn("- same TraitMech (audit date: 2026-10-05): still serves aaaaaaa", output)
        self.assertIn("- redeployed DUFMech (audit date: 2026-10-05): bbbbbbb when checked, now ccccccc", output)
        self.assertNotIn("judged on the live sites on", output)

    def test_feature_check_preserves_mixed_duf_recheck_and_baseline_dates(self):
        output = self.feature_check_output(duf_recheck=True)
        self.assertIn("## Website feature table (baseline audit: 2026-10-05)", output)
        self.assertIn("- same TraitMech (audit date: 2026-10-05): still serves aaaaaaa", output)
        self.assertIn("- redeployed DUFMech (audit date: 2026-10-07): bbbbbbb when checked, now ccccccc", output)
        self.assertNotIn("DUFMech (audit date: 2026-10-05)", output)
        self.assertNotIn("TraitMech (audit date: 2026-10-07)", output)
        self.assertIn("website feature verdicts to re-check on redeployed sites: DUFMech", output)
        self.assertNotIn("judged on the live sites on", output)

    def test_unsuccessful_deployment_requests_are_not_claimed_as_served(self):
        features = {"mechs": {"AMech": {
            "site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
            "deployed_revision": "a" * 40,
        }}}
        for state in ("queued", "pending", "in_progress", "failure", "error", "inactive"):
            for sha in ("a" * 40, "b" * 40):
                with self.subTest(state=state, sha=sha):
                    calls = []
                    def api(path):
                        calls.append(path)
                        if path.endswith("/statuses?per_page=1"):
                            return [{"state": state}]
                        return [{"id": 7, "sha": sha, "created_at": "2026-10-05T16:00:00Z"}]
                    rows = check_updates.site_feature_check(features, api=api)
                    self.assertEqual([(s, m) for s, m, _ in rows], [("NOT CHECKED", "AMech")])
                    self.assertIn(f"latest deployment is {state}", rows[0][2])
                    self.assertEqual(calls[-1], "repos/CultureBotAI/AMech/deployments/7/statuses?per_page=1")
                    line = check_updates.summary([], [], "matches", [], [], sites=rows)
                    self.assertIn("site deployment AMech", line)
                    self.assertNotIn("verdicts to re-check on redeployed sites", line)

    def test_missing_deployment_status_is_reported_as_not_checked(self):
        features = {"mechs": {"AMech": {
            "site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
            "deployed_revision": "a" * 40,
        }}}
        def api(path):
            if "/statuses?" in path:
                raise check_updates.Unchecked(["HTTP 502"])
            return [{"id": 8, "sha": "a" * 40}]
        rows = check_updates.site_feature_check(features, api=api)
        self.assertEqual(rows, [("NOT CHECKED", "AMech", "HTTP 502")])

    def test_invalid_site_repository_metadata_does_not_crash_the_check(self):
        for repository in (None, 12, [], "https://example.org/AMech", "https://github.com/CultureBotAI"):
            with self.subTest(repository=repository):
                entry = {"site": "https://example.org/a/", "deployed_revision": "a" * 40}
                if repository is not None:
                    entry["repository"] = repository
                api = mock.Mock(side_effect=AssertionError("Invalid metadata must not make an API request"))
                rows = check_updates.site_feature_check({"mechs": {"AMech": entry}}, api=api)
                self.assertEqual([(s, m) for s, m, _ in rows], [("NOT CHECKED", "AMech")])
                self.assertIn("repository", rows[0][2])
                api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
