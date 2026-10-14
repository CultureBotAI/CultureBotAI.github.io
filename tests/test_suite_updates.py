"""New suite corpora and subsequently dated DUF worklists remain watched."""
import contextlib
import http.client
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import urllib.error
import urllib.response

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))

import check_updates
import roots

# What GitHub Pages sent for https://culturebotai.github.io/AIMech/ on 2026-10-14.
PAGES_ANSWER = {"Server": "GitHub.com", "X-GitHub-Request-Id": "2DC2:26D7FE:9C091:AF2C7:6ACFF425"}


def head_requests(answer=None):
    """A stand-in for urlopen that records each request. It raises answer if it
    is an exception, and otherwise answers with answer's headers, by default
    those of a GitHub Pages answer."""
    requests = []
    def opener(request, timeout):
        requests.append((request.get_method(), request.full_url, timeout))
        if isinstance(answer, Exception):
            raise answer
        headers = http.client.HTTPMessage()
        for name, value in (PAGES_ANSWER if answer is None else answer).items():
            headers[name] = value
        return urllib.response.addinfourl(io.BytesIO(), headers, request.full_url, 200)
    return opener, requests


def no_request(request, timeout):
    raise AssertionError(f"unexpected request to {request.full_url}")


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
        self.assertIn("data/worklists/interpro-pfam-duf-2026-10-10.json", cited["dufmech"])

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
            "DMech": {"site": None, "repository": "https://github.com/CultureBotAI/DMech", "note": "No site."},
            "EMech": {"site": None, "repository": "https://github.com/CultureBotAI/EMech", "note": "No site."},
        }}
        def api(path):
            if "/statuses?" in path:
                return [{"state": "success"}]
            if "AMech" in path:
                return [{"id": 1, "sha": "a" * 40, "created_at": "2026-10-05T09:00:00Z"}]
            if "BMech" in path:
                return [{"id": 2, "sha": "d" * 40, "created_at": "2026-10-06T09:00:00Z"}]
            if path == "repos/CultureBotAI/DMech":
                return {"has_pages": False}
            raise check_updates.Unchecked(["HTTP 502"])
        rows = check_updates.site_feature_check(features, api=api, opener=no_request)
        self.assertEqual(rows, [
            ("same", "AMech", "still serves aaaaaaa"),
            ("redeployed", "BMech", "bbbbbbb when checked, now ddddddd (deployed 2026-10-06T09:00:00Z)"),
            ("NOT CHECKED", "CMech", "HTTP 502"),
            ("no site", "DMech", "GitHub Pages is not enabled"),
            ("NOT CHECKED", "EMech", "HTTP 502"),
        ])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("website feature verdicts to re-check on redeployed sites: BMech", line)
        self.assertIn("**Not checked:** site deployment CMech, site deployment EMech.", line)
        self.assertNotIn("AMech", line)
        # A Mech that still has no site gives a refresh nothing to do, but one
        # whose check failed must stay visible (#413).
        self.assertNotIn("DMech", line)
        self.assertNotIn("new sites", line)

    def test_a_mech_recorded_without_a_site_is_reported_once_it_deploys(self):
        # #405: CMMMech and AIMech began publishing while the table still said
        # they had no website, and the check skipped every Mech without a site.
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        calls = []
        def api(path):
            calls.append(path)
            if path == "repos/CultureBotAI/AIMech":
                return {"has_pages": True}
            if path.endswith("/statuses?per_page=1"):
                return [{"state": "success"}]
            if path.endswith("/pages"):
                return {"html_url": "https://culturebotai.github.io/AIMech/"}
            return [{"id": 9, "sha": "e" * 40, "created_at": "2026-10-12T23:48:02Z"}]
        opener, requests = head_requests()
        rows = check_updates.site_feature_check(features, api=api, opener=opener)
        self.assertEqual(rows, [("new site", "AIMech", "GitHub Pages now serves eeeeeee (deployed 2026-10-12T23:48:02Z)"
                                                      " at https://culturebotai.github.io/AIMech/")])
        self.assertEqual(calls, ["repos/CultureBotAI/AIMech",
                                 "repos/CultureBotAI/AIMech/deployments?environment=github-pages&per_page=1",
                                 "repos/CultureBotAI/AIMech/deployments/9/statuses?per_page=1",
                                 "repos/CultureBotAI/AIMech/pages"])
        # #419: the site itself has to answer before it counts as new.
        self.assertEqual(requests, [("HEAD", "https://culturebotai.github.io/AIMech/", 30)])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("website feature verdicts to judge on new sites: AIMech", line)
        self.assertNotIn("Not checked", line)

    def test_a_mech_without_a_site_is_not_new_while_pages_is_off(self):
        # #407: Pages deployments keep their success status after Pages is
        # turned off, so a successful deployment alone does not mean a site.
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        served = [{"id": 9, "sha": "e" * 40, "created_at": "2023-01-29T13:38:48Z"}]
        for deployments in (served, []):
            with self.subTest(deployments=bool(deployments)):
                def api(path):
                    if path == "repos/CultureBotAI/AIMech":
                        return {"has_pages": False}
                    if path.endswith("/statuses?per_page=1"):
                        return [{"state": "success"}]
                    return deployments
                rows = check_updates.site_feature_check(features, api=api, opener=no_request)
                self.assertEqual(rows, [("no site", "AIMech", "GitHub Pages is not enabled")])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                self.assertNotIn("AIMech", line)

    def test_pages_enabled_without_a_deployment_record_is_not_checked(self):
        # #418: a deploy job that names no environment, or a build older than
        # the deployment records, serves a site without recording a deployment,
        # so an empty list cannot pass for "no site", which the summary leaves out.
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        def api(path):
            if path == "repos/CultureBotAI/AIMech":
                return {"has_pages": True}
            if path == "repos/CultureBotAI/AIMech/deployments?environment=github-pages&per_page=1":
                return []
            raise AssertionError(f"unexpected request to {path}")
        rows = check_updates.site_feature_check(features, api=api, opener=no_request)
        self.assertEqual(rows, [("NOT CHECKED", "AIMech", "GitHub Pages is enabled but has no deployment record")])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("**Not checked:** site deployment AIMech.", line)
        self.assertIn("Refresh would change:** nothing found", line)

    def test_a_new_site_must_answer_before_it_is_reported(self):
        # #419: a successful deployment outlives an unpublished or transferred
        # site, and a run that skips publishing still records one, so a Mech
        # without a site is new only once its site answers.
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        url = "https://culturebotai.github.io/AIMech/"
        def answers(pages):
            def api(path):
                if path == "repos/CultureBotAI/AIMech":
                    return {"has_pages": True}
                if path.endswith("/statuses?per_page=1"):
                    return [{"state": "success"}]
                if path == "repos/CultureBotAI/AIMech/pages":
                    if isinstance(pages, Exception):
                        raise pages
                    return pages
                return [{"id": 9, "sha": "e" * 40, "created_at": "2026-10-12T23:48:02Z"}]
            return api
        site = {"html_url": url}
        cases = [
            (site, urllib.error.HTTPError(url, 404, "Not Found", {}, None),
             f"deployment eeeeeee succeeded, but {url} answers 404"),
            (site, urllib.error.HTTPError(url, 503, "Service Unavailable", {}, None),
             f"deployment eeeeeee succeeded, but {url} answers 503"),
            (site, urllib.error.URLError("no route"), f"{url} did not answer (<urlopen error no route>)"),
            (site, TimeoutError("timed out"), f"{url} did not answer (timed out)"),
            (site, http.client.BadStatusLine("garbage"), f"{url} did not answer (garbage)"),
            # #428: a custom domain served by another host.
            (site, {"Server": "Netlify"}, f"deployment eeeeeee succeeded, but {url} is served by Netlify, "
                                          "not GitHub Pages"),
            (site, {}, f"deployment eeeeeee succeeded, but {url} is served by an unnamed server, not GitHub Pages"),
            # #429: the Pages request needs gh's repo scope and answers 404 without it.
            (check_updates.Unchecked(["gh: Not Found (HTTP 404)"]), None,
             "repos/CultureBotAI/AIMech/pages failed (gh: Not Found (HTTP 404)); it needs gh's repo scope"),
            ({}, None, "Pages response has no site URL"),
            ({"html_url": None}, None, "Pages response has no site URL"),
            ({"html_url": "ftp://culturebotai.github.io/AIMech/"}, None, "Pages response has no site URL"),
            ({"html_url": "https://culturebotai.github.io/Ai Mech/"}, None, "Pages response has no site URL"),
            ([], None, "Pages response has no site URL"),
            (None, None, "Pages response has no site URL"),
        ]
        for pages, answer, detail in cases:
            with self.subTest(detail=detail):
                opener, requests = head_requests(answer)
                rows = check_updates.site_feature_check(features, api=answers(pages), opener=opener)
                self.assertEqual(rows, [("NOT CHECKED", "AIMech", detail)])
                self.assertEqual(requests, [("HEAD", url, 30)] if answer is not None else [])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                self.assertIn("**Not checked:** site deployment AIMech.", line)
                self.assertNotIn("new sites", line)

    def test_a_new_site_on_a_custom_domain_must_be_served_by_github_pages(self):
        # #428: html_url follows a custom domain, which another host can serve
        # while Pages keeps an old successful deployment. GitHub Pages marks its
        # answers with a request id, also behind a CDN, and header names can
        # arrive in lower case.
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        url = "https://www.example.org/"
        def api(path):
            if path == "repos/CultureBotAI/AIMech":
                return {"has_pages": True}
            if path == "repos/CultureBotAI/AIMech/deployments?environment=github-pages&per_page=1":
                return [{"id": 9, "sha": "e" * 40, "created_at": "2021-10-27T10:41:39Z"}]
            if path == "repos/CultureBotAI/AIMech/deployments/9/statuses?per_page=1":
                return [{"state": "success"}]
            if path == "repos/CultureBotAI/AIMech/pages":
                return {"html_url": url, "cname": "www.example.org"}
            raise AssertionError(f"unexpected request to {path}")
        behind_a_cdn = {"server": "cloudflare", "x-github-request-id": "F538:1170F3:1359F:16B00:6ACCE13C"}
        cases = [
            (behind_a_cdn, ("new site", "AIMech", f"GitHub Pages now serves eeeeeee (deployed 2021-10-27T10:41:39Z) "
                                                  f"at {url}")),
            ({"Server": "Netlify"}, ("NOT CHECKED", "AIMech", f"deployment eeeeeee succeeded, but {url} is served "
                                                              "by Netlify, not GitHub Pages")),
        ]
        for answer, row in cases:
            with self.subTest(answer=answer):
                opener, requests = head_requests(answer)
                rows = check_updates.site_feature_check(features, api=api, opener=opener)
                self.assertEqual(rows, [row])
                self.assertEqual(requests, [("HEAD", url, 30)])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                if row[0] == "new site":
                    self.assertIn("website feature verdicts to judge on new sites: AIMech", line)
                    self.assertNotIn("Not checked", line)
                else:
                    self.assertIn("**Not checked:** site deployment AIMech.", line)
                    self.assertNotIn("new sites", line)

    def test_an_unconfirmed_first_deployment_is_not_claimed_as_a_new_site(self):
        features = {"mechs": {"AIMech": {
            "site": None, "repository": "https://github.com/CultureBotAI/AIMech",
            "note": "No published website.",
        }}}
        for state in ("queued", "in_progress", "failure", "inactive"):
            with self.subTest(state=state):
                def api(path):
                    if path == "repos/CultureBotAI/AIMech":
                        return {"has_pages": True}
                    if path.endswith("/statuses?per_page=1"):
                        return [{"state": state}]
                    return [{"id": 9, "sha": "e" * 40, "created_at": "2026-10-12T23:48:02Z"}]
                rows = check_updates.site_feature_check(features, api=api, opener=no_request)
                self.assertEqual(rows, [("NOT CHECKED", "AIMech",
                                         f"latest deployment is {state}; currently served revision not verified")])
                line = check_updates.summary([], [], "matches", [], [], sites=rows)
                self.assertIn("**Not checked:** site deployment AIMech.", line)
                self.assertNotIn("new sites", line)

    def test_a_recorded_site_with_no_deployment_is_not_checked(self):
        features = {"mechs": {"AMech": {
            "site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
            "deployed_revision": "a" * 40,
        }}}
        rows = check_updates.site_feature_check(features, api=lambda path: [], opener=no_request)
        self.assertEqual(rows, [("NOT CHECKED", "AMech", "no GitHub Pages deployment")])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("**Not checked:** site deployment AMech.", line)

    def test_every_failed_or_malformed_answer_is_not_checked(self):
        # #413, #414: a check that could not finish must say so for either kind
        # of entry, never pass for "no site", which the summary leaves out.
        recorded = {"site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
                    "deployed_revision": "a" * 40}
        siteless = {"site": None, "repository": "https://github.com/CultureBotAI/AMech", "note": "No site."}
        good = {"id": 9, "sha": "a" * 40, "created_at": "2026-10-12T23:48:02Z"}
        usual = object()
        def answers(repo=usual, deployments=usual, statuses=usual):
            def api(path):
                if path == "repos/CultureBotAI/AMech":
                    reply = {"has_pages": True} if repo is usual else repo
                elif path.endswith("/statuses?per_page=1"):
                    reply = [{"state": "success"}] if statuses is usual else statuses
                elif "/deployments?" in path:
                    reply = [good] if deployments is usual else deployments
                else:
                    raise AssertionError(f"unexpected request to {path}")
                if isinstance(reply, Exception):
                    raise reply
                return reply
            return api
        no_gh = FileNotFoundError(2, "No such file or directory", "gh")
        # CPython 3.11 added ", not 'str'" to this message, so take it from the
        # running interpreter (#430).
        with self.assertRaises(TypeError) as str_index:
            "x"["sha"]
        shared = [
            (answers(deployments=check_updates.Unchecked(["HTTP 502"])), "HTTP 502"),
            (answers(statuses=check_updates.Unchecked(["HTTP 503"])), "HTTP 503"),
            (answers(deployments=no_gh), str(no_gh)),
            (answers(statuses=[]), "latest deployment has no status yet"),
            (answers(statuses=[{}]), "'state'"),
            (answers(deployments=[dict(good, id=0)]), "deployment response has no valid id"),
            (answers(deployments=[dict(good, id="9")]), "deployment response has no valid id"),
            (answers(deployments=[dict(good, id=None)]), "deployment response has no valid id"),
            (answers(deployments=[dict(good, sha=None)]), "deployment response has no valid commit SHA"),
            (answers(deployments=[dict(good, sha="abc")]), "deployment response has no valid commit SHA"),
            # #422: null, non-list and non-object answers end as NOT CHECKED too.
            (answers(deployments=None), "'NoneType' object is not subscriptable"),
            (answers(deployments=""), "string index out of range"),
            (answers(deployments=["x"]), str(str_index.exception)),
            (answers(statuses=None), "'NoneType' object is not subscriptable"),
            (answers(statuses=[None]), "'NoneType' object is not subscriptable"),
        ]
        cases = [(recorded, api, detail) for api, detail in shared]
        cases += [(siteless, api, detail) for api, detail in shared]
        cases += [
            (siteless, answers(repo=check_updates.Unchecked(["HTTP 404"])), "HTTP 404"),
            (siteless, answers(repo={}), "repository response has no has_pages flag"),
            (siteless, answers(repo={"has_pages": "yes"}), "repository response has no has_pages flag"),
            (siteless, answers(repo=[]), "repository response has no has_pages flag"),
            (dict(recorded, deployed_revision="abc"), answers(), "deployed_revision must be a full commit SHA"),
        ]
        for entry, api, detail in cases:
            with self.subTest(site=entry["site"], detail=detail):
                rows = check_updates.site_feature_check({"mechs": {"AMech": entry}}, api=api, opener=no_request)
                self.assertEqual(rows, [("NOT CHECKED", "AMech", detail)])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                self.assertIn("**Not checked:** site deployment AMech.", line)
                self.assertIn("Refresh would change:** nothing found", line)

    def feature_check_output(self, *, duf_recheck=False, new_site=False, not_checked=False):
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
        if new_site or not_checked:
            for name in ("AIMech", "CMMMech"):
                features["mechs"][name] = {"site": None, "repository": f"https://github.com/CultureBotAI/{name}",
                                           "note": "No published website."}
        if not_checked:
            features["mechs"]["HabitatMech"] = {"site": "https://example.org/habitat/",
                                                "repository": "https://github.com/CultureBotAI/HabitatMech",
                                                "deployed_revision": "d" * 40}

        def api(path):
            # not_checked: AIMech's repository and HabitatMech's deployments do
            # not answer, and CMMMech's first deployment is still queued.
            if not_checked and (path == "repos/CultureBotAI/AIMech" or "/HabitatMech/deployments?" in path):
                raise check_updates.Unchecked(["HTTP 502"])
            if "/statuses?" in path:
                return [{"state": "queued" if not_checked and "/CMMMech/" in path else "success"}]
            if path.endswith("/pages"):
                return {"html_url": "https://culturebotai.github.io/" + path.split("/")[2] + "/"}
            if "/deployments?" not in path:
                return {"has_pages": not path.endswith("/AIMech")}
            sha = "a" * 40 if "TraitMech" in path else "c" * 40
            return [{"id": 1, "sha": sha, "created_at": "2026-10-07T09:00:00Z"}]
        opener, self.site_requests = head_requests()

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
              mock.patch.object(check_updates, "site_feature_check",
                                side_effect=lambda f: site_check(f, api=api, opener=opener)),
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

    def test_feature_check_reports_a_new_site_in_its_section_and_summary(self):
        output = self.feature_check_output(new_site=True)
        # #415: a Mech without a site has no audit date of its own to print.
        self.assertIn("- new site CMMMech (recorded without a site): GitHub Pages now serves ccccccc "
                      "(deployed 2026-10-07T09:00:00Z) at https://culturebotai.github.io/CMMMech/\n", output)
        self.assertIn("- no site AIMech (recorded without a site): GitHub Pages is not enabled\n", output)
        self.assertEqual(self.site_requests, [("HEAD", "https://culturebotai.github.io/CMMMech/", 30)])
        self.assertNotIn("CMMMech (audit date", output)
        self.assertIn("website feature verdicts to re-check on redeployed sites: DUFMech; "
                      "website feature verdicts to judge on new sites: CMMMech.", output)
        self.assertNotIn("AIMech", output.rsplit("\n\n", 1)[-1])

    def test_feature_check_labels_not_checked_rows_by_their_entry(self):
        # #420: NOT CHECKED is the one state both kinds of entry produce, so it
        # is where a label keyed on the status instead of the entry would differ.
        output = self.feature_check_output(not_checked=True)
        self.assertIn("- NOT CHECKED AIMech (recorded without a site): HTTP 502\n", output)
        self.assertIn("- NOT CHECKED CMMMech (recorded without a site): latest deployment is queued; "
                      "currently served revision not verified\n", output)
        self.assertIn("- NOT CHECKED HabitatMech (audit date: 2026-10-05): HTTP 502\n", output)
        self.assertIn("**Not checked:** site deployment AIMech, site deployment CMMMech, "
                      "site deployment HabitatMech.", output)
        self.assertEqual(self.site_requests, [])

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
                    rows = check_updates.site_feature_check(features, api=api, opener=no_request)
                    self.assertEqual(rows, [("NOT CHECKED", "AMech",
                                             f"latest deployment is {state}; currently served revision not verified")])
                    self.assertEqual(calls[-1], "repos/CultureBotAI/AMech/deployments/7/statuses?per_page=1")
                    line = check_updates.summary([], [], "matches", [], [], sites=rows)
                    self.assertIn("**Not checked:** site deployment AMech.", line)
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
        rows = check_updates.site_feature_check(features, api=api, opener=no_request)
        self.assertEqual(rows, [("NOT CHECKED", "AMech", "HTTP 502")])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("**Not checked:** site deployment AMech.", line)

    def test_invalid_site_repository_metadata_does_not_crash_the_check(self):
        recorded = {"site": "https://example.org/a/", "deployed_revision": "a" * 40}
        siteless = {"site": None, "note": "No site."}
        for base in (recorded, siteless):
            for repository in (None, 12, [], "https://example.org/AMech", "https://github.com/CultureBotAI"):
                with self.subTest(site=base["site"], repository=repository):
                    entry = dict(base)
                    if repository is not None:
                        entry["repository"] = repository
                    api = mock.Mock(side_effect=AssertionError("Invalid metadata must not make an API request"))
                    rows = check_updates.site_feature_check({"mechs": {"AMech": entry}}, api=api, opener=no_request)
                    self.assertEqual(rows, [("NOT CHECKED", "AMech", "repository must be a GitHub repository URL")])
                    api.assert_not_called()
                    line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                    self.assertIn("**Not checked:** site deployment AMech.", line)


if __name__ == "__main__":
    unittest.main()
