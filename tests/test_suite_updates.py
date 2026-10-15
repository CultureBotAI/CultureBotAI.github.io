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

# What GitHub Pages sent for https://culturebotai.github.io/AIMech/ on
# 2026-10-15 (UTC), 14 seconds after the deployment it published was created.
PAGES_ANSWER = {"Server": "GitHub.com", "Last-Modified": "Thu, 15 Oct 2026 00:48:08 GMT",
                "X-GitHub-Request-Id": "D1A0:FFAF7:DAD40:F635C:6AD025B3"}


def message(answer):
    headers = http.client.HTTPMessage()
    for name, value in answer.items():
        headers[name] = value
    return headers


def head_requests(answer=None, final=None):
    """A stand-in for urlopen that records each request. It raises answer if it
    is an exception, and otherwise answers with answer's headers, by default
    those of a GitHub Pages answer, from final if a redirect ended there."""
    requests = []
    def opener(request, timeout):
        requests.append((request.get_method(), request.full_url, timeout))
        if isinstance(answer, Exception):
            raise answer
        headers = message(PAGES_ANSWER if answer is None else answer)
        return urllib.response.addinfourl(io.BytesIO(), headers, final or request.full_url, 200)
    return opener, requests


def pages_error(url, code, answer=PAGES_ANSWER):
    """The HTTPError urlopen raises for an error status that GitHub Pages sent."""
    return urllib.error.HTTPError(url, code, "Not Found" if code == 404 else "Error", message(answer), None)


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
            if path in ("repos/CultureBotAI/AMech", "repos/CultureBotAI/BMech"):
                return {"has_pages": True}
            if "/statuses?" in path:
                return [{"state": "success"}]
            if "AMech" in path:
                return [{"id": 1, "sha": "a" * 40, "created_at": "2026-10-05T09:00:00Z"}]
            if "BMech" in path:
                return [{"id": 2, "sha": "d" * 40, "created_at": "2026-10-06T09:00:00Z"}]
            if path == "repos/CultureBotAI/DMech":
                return {"has_pages": False}
            raise check_updates.Unchecked(["HTTP 502"])
        opener, requests = head_requests()
        rows = check_updates.site_feature_check(features, api=api, opener=opener)
        self.assertEqual(rows, [
            ("same", "AMech", "still serves aaaaaaa"),
            ("redeployed", "BMech", "bbbbbbb when checked, now ddddddd (deployed 2026-10-06T09:00:00Z)"),
            ("NOT CHECKED", "CMech", "HTTP 502"),
            ("no site", "DMech", "GitHub Pages is not enabled"),
            ("NOT CHECKED", "EMech", "HTTP 502"),
        ])
        # #408: a recorded site counts as served only once a HEAD request succeeds.
        self.assertEqual(requests, [("HEAD", "https://example.org/a/", 30), ("HEAD", "https://example.org/b/", 30)])
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
        # #419: a HEAD request to the site has to succeed before it counts as new.
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
        # without a site is new only once a HEAD request to its site succeeds.
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
        # #434, #440: a detail names where a redirect ended, and a GitHub page,
        # which carries a request id too, is not a GitHub Pages site.
        repository = "https://github.com/CultureBotAI/AIMech"
        for answer, final, detail in (
                (PAGES_ANSWER, repository, f"{url} (redirected to {repository}) is on github.com, "
                                           "where GitHub Pages serves no site"),
                ({"Server": "Netlify"}, "https://www.example.org/", f"{url} (redirected to https://www.example.org/) "
                                                                    "is served by Netlify, not GitHub Pages")):
            with self.subTest(final=final):
                opener, requests = head_requests(answer, final)
                rows = check_updates.site_feature_check(features, api=answers(site), opener=opener)
                self.assertEqual(rows, [("NOT CHECKED", "AIMech", f"deployment eeeeeee succeeded, but {detail}")])
                self.assertEqual(requests, [("HEAD", url, 30)])
        # A redirect to a custom domain that GitHub Pages serves is still a new
        # site, named where it ended, which is what a refresh would record.
        opener, requests = head_requests(final="https://www.example.org/")
        rows = check_updates.site_feature_check(features, api=answers(site), opener=opener)
        self.assertEqual(rows, [("new site", "AIMech", f"GitHub Pages now serves eeeeeee (deployed 2026-10-12T23:48:02Z) "
                                                       f"at {url} (redirected to https://www.example.org/)")])

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
        # What Cloudflare sent for GitHub Pages at https://getbootstrap.com/ on 2026-10-15.
        behind_a_cdn = {"server": "cloudflare", "last-modified": "Thu, 08 Oct 2026 17:12:02 GMT",
                        "x-github-request-id": "F538:1170F3:1359F:16B00:6ACCE13C"}
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
        def api(path):
            return {"has_pages": True} if path == "repos/CultureBotAI/AMech" else []
        rows = check_updates.site_feature_check(features, api=api, opener=no_request)
        self.assertEqual(rows, [("NOT CHECKED", "AMech", "no GitHub Pages deployment")])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("**Not checked:** site deployment AMech.", line)

    def test_a_recorded_site_is_gone_once_pages_is_turned_off(self):
        # #408: a deployment keeps its success after Pages is turned off, so a
        # recorded site whose repository no longer has Pages enabled is no
        # longer published, and its row is something a refresh has to change.
        features = {"mechs": {"AMech": {
            "site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
            "deployed_revision": "a" * 40,
        }}}
        def api(path):
            if path == "repos/CultureBotAI/AMech":
                return {"has_pages": False}
            raise AssertionError(f"unexpected request to {path}")
        rows = check_updates.site_feature_check(features, api=api, opener=no_request)
        self.assertEqual(rows, [("gone", "AMech", "GitHub Pages is no longer enabled; the table still describes "
                                                  "https://example.org/a/")])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("website feature rows of sites no longer published: AMech.", line)
        self.assertNotIn("Not checked", line)

    def test_a_recorded_site_must_still_be_served_by_github_pages(self):
        # #408: an unpublished site keeps both Pages and its successful
        # deployment, so a recorded site counts as served only once a HEAD
        # request to it succeeds, with an answer from GitHub Pages rather than
        # another host (#428) or a GitHub page (#440). The deployment record
        # settles a redeployment, so one is still reported when that request
        # fails (#435). Details name where a redirect ended (#434).
        features = {"mechs": {"AMech": {
            "site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
            "deployed_revision": "a" * 40,
        }}}
        url = "https://example.org/a/"
        def answers(sha, created="2026-10-05T16:00:00Z"):
            def api(path):
                if path == "repos/CultureBotAI/AMech":
                    return {"has_pages": True}
                if path == "repos/CultureBotAI/AMech/deployments?environment=github-pages&per_page=1":
                    return [{"id": 7, "sha": sha, "created_at": created}]
                if path == "repos/CultureBotAI/AMech/deployments/7/statuses?per_page=1":
                    return [{"state": "success"}]
                raise AssertionError(f"unexpected request to {path}")
            return api
        moved = "https://www.example.org/a/"
        repository = "https://github.com/CultureBotAI/AMech"
        readme = "https://raw.githubusercontent.com/CultureBotAI/AMech/main/README.md"
        undated = {name: value for name, value in PAGES_ANSWER.items() if name != "Last-Modified"}
        since = "aaaaaaa when checked, now bbbbbbb (deployed 2026-10-05T16:00:00Z)"
        failures = [  # (answer, where a redirect ended, why it does not confirm the site)
            (urllib.error.HTTPError(url, 503, "Service Unavailable", {}, None), None, f"{url} answers 503"),
            (urllib.error.HTTPError(url, 404, "Not Found", {}, None), None, f"{url} answers 404"),
            (pages_error(moved, 503), None, f"{url} (redirected to {moved}) answers 503"),
            (pages_error(repository + "/gone", 404), None, f"{url} (redirected to {repository}/gone) answers 404"),
            (urllib.error.URLError("no route"), None, f"{url} did not answer (<urlopen error no route>)"),
            (TimeoutError("timed out"), None, f"{url} did not answer (timed out)"),
            ({"Server": "Netlify"}, None, f"{url} is served by Netlify, not GitHub Pages"),
            ({"Server": "Netlify"}, moved, f"{url} (redirected to {moved}) is served by Netlify, not GitHub Pages"),
            (PAGES_ANSWER, repository, f"{url} (redirected to {repository}) is on github.com, "
                                       "where GitHub Pages serves no site"),
            (PAGES_ANSWER, readme, f"{url} (redirected to {readme}) is on raw.githubusercontent.com, "
                                   "where GitHub Pages serves no site"),
            (undated, None, f"{url} sends no Last-Modified date"),
            (dict(PAGES_ANSWER, **{"Last-Modified": "yesterday"}), None, f"{url} sends no Last-Modified date"),
        ]
        cases = []
        for answer, final, failure in failures:
            unverified = failure if "did not answer" in failure else f"deployment aaaaaaa succeeded, but {failure}"
            cases.append(("a" * 40, answer, final, ("NOT CHECKED", "AMech", unverified)))
            cases.append(("b" * 40, answer, final, ("redeployed", "AMech", f"{since}, but {failure}")))
        cases += [
            ("a" * 40, None, None, ("same", "AMech", "still serves aaaaaaa")),
            ("b" * 40, None, None, ("redeployed", "AMech", since)),
            # Published in the second its deployment was created (#448).
            ("a" * 40, dict(PAGES_ANSWER, **{"Last-Modified": "Mon, 05 Oct 2026 16:00:00 GMT"}), None,
             ("same", "AMech", "still serves aaaaaaa")),
        ]
        for sha, answer, final, row in cases:
            with self.subTest(sha=sha[:1], row=row):
                opener, requests = head_requests(answer, final)
                rows = check_updates.site_feature_check(features, api=answers(sha), opener=opener)
                self.assertEqual(rows, [row])
                self.assertEqual(requests, [("HEAD", url, 30)])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                if row[0] == "same":
                    self.assertIn("Refresh would change:** nothing found.", line)
                    self.assertNotIn("Not checked", line)
                elif row[0] == "redeployed":
                    self.assertIn("website feature verdicts to re-check on redeployed sites: AMech.", line)
                    self.assertNotIn("Not checked", line)
                else:
                    self.assertIn("**Not checked:** site deployment AMech.", line)
                    self.assertIn("Refresh would change:** nothing found.", line)
        with self.subTest(created="?"):
            opener, requests = head_requests()
            rows = check_updates.site_feature_check(features, api=answers("a" * 40, created="?"), opener=opener)
            self.assertEqual(rows, [("NOT CHECKED", "AMech", "deployment response has no valid creation time")])
        for site in ("http://example.org/a/", "example.org/a/", "https://example.org/a b/", 12):
            with self.subTest(site=site):
                api = mock.Mock(side_effect=AssertionError("an invalid site must not make an API request"))
                rows = check_updates.site_feature_check({"mechs": {"AMech": dict(features["mechs"]["AMech"], site=site)}},
                                                        api=api, opener=no_request)
                self.assertEqual(rows, [("NOT CHECKED", "AMech", "site must be an https URL")])
                api.assert_not_called()

    def test_a_recorded_page_github_pages_answers_404_for_is_not_found(self):
        # #436: a transferred or unpublished site keeps Pages and its successful
        # deployment, and a redeploy can remove or move the recorded page; then
        # GitHub Pages itself answers 404, which a refresh has to act on. Other
        # hosts' 404s stay unverified, and so does a new site's (its root can
        # 404 while its pages exist).
        recorded = {"site": "https://example.org/a/", "repository": "https://github.com/CultureBotAI/AMech",
                    "deployed_revision": "a" * 40}
        url = "https://example.org/a/"
        moved = "https://example.org/a/pages/"
        def answers(sha):
            def api(path):
                if path == "repos/CultureBotAI/AMech":
                    return {"has_pages": True}
                if path == "repos/CultureBotAI/AMech/deployments?environment=github-pages&per_page=1":
                    return [{"id": 7, "sha": sha, "created_at": "2026-10-05T16:00:00Z"}]
                if path == "repos/CultureBotAI/AMech/deployments/7/statuses?per_page=1":
                    return [{"state": "success"}]
                if path == "repos/CultureBotAI/AMech/pages":
                    return {"html_url": url}
                raise AssertionError(f"unexpected request to {path}")
            return api
        cases = [
            (recorded, "a" * 40, pages_error(url, 404),
             ("not found", "AMech", f"GitHub Pages answers 404 at {url}; the latest deployment is still aaaaaaa")),
            (recorded, "b" * 40, pages_error(url, 404),
             ("not found", "AMech", f"GitHub Pages answers 404 at {url}; aaaaaaa when checked, now bbbbbbb "
                                    "(deployed 2026-10-05T16:00:00Z)")),
            (recorded, "a" * 40, pages_error(moved, 404),
             ("not found", "AMech", f"GitHub Pages answers 404 at {url} (redirected to {moved}); the latest "
                                    "deployment is still aaaaaaa")),
            ({"site": None, "repository": recorded["repository"], "note": "No site."}, "a" * 40, pages_error(url, 404),
             ("NOT CHECKED", "AMech", f"deployment aaaaaaa succeeded, but {url} answers 404")),
        ]
        for entry, sha, answer, row in cases:
            with self.subTest(row=row):
                opener, requests = head_requests(answer)
                rows = check_updates.site_feature_check({"mechs": {"AMech": entry}}, api=answers(sha), opener=opener)
                self.assertEqual(rows, [row])
                self.assertEqual(requests, [("HEAD", url, 30)])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                if row[0] == "not found":
                    self.assertIn("website feature rows whose page GitHub Pages no longer serves: AMech.", line)
                    self.assertNotIn("Not checked", line)
                    self.assertNotIn("re-check", line)
                else:
                    self.assertIn("**Not checked:** site deployment AMech.", line)

    def test_a_site_counts_as_served_only_once_its_deployment_published_it(self):
        # #448: a run that skips publishing still ends in success while GitHub
        # Pages serves an earlier artifact, which it stamped with the time it
        # published it. Anything published before the deployment was created
        # came from an earlier one, for every kind of entry.
        url = "https://example.org/a/"
        entries = {
            "aaaaaaa": {"site": url, "repository": "https://github.com/CultureBotAI/AMech", "deployed_revision": "a" * 40},
            "bbbbbbb": {"site": url, "repository": "https://github.com/CultureBotAI/AMech", "deployed_revision": "b" * 40},
            "siteless": {"site": None, "repository": "https://github.com/CultureBotAI/AMech", "note": "No site."},
            "judged": {"site": None, "repository": "https://github.com/CultureBotAI/AMech", "note": "Placeholder.",
                       "deployed_revision": "b" * 40},
        }
        def api(path):
            if path == "repos/CultureBotAI/AMech":
                return {"has_pages": True}
            if path == "repos/CultureBotAI/AMech/deployments?environment=github-pages&per_page=1":
                return [{"id": 7, "sha": "a" * 40, "created_at": "2026-10-08T00:42:55Z"}]
            if path == "repos/CultureBotAI/AMech/deployments/7/statuses?per_page=1":
                return [{"state": "success"}]
            if path == "repos/CultureBotAI/AMech/pages":
                return {"html_url": url}
            raise AssertionError(f"unexpected request to {path}")
        # Modelled on DUFMech's deployment of b313e7c, created at 00:42:55 on
        # 2026-10-08, which skipped its deploy step while Pages went on serving
        # what an earlier deployment had published at about 20:44 the day before.
        stale = dict(PAGES_ANSWER, **{"Last-Modified": "Wed, 07 Oct 2026 20:44:01 GMT"})
        for name, entry in entries.items():
            with self.subTest(entry=name):
                opener, requests = head_requests(stale)
                rows = check_updates.site_feature_check({"mechs": {"AMech": entry}}, api=api, opener=opener)
                self.assertEqual(rows, [("NOT CHECKED", "AMech", f"deployment aaaaaaa succeeded, but {url} was last "
                                                                 "published at 2026-10-07T20:44:01Z, before that "
                                                                 "deployment was created")])
                self.assertEqual(requests, [("HEAD", url, 30)])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                self.assertIn("**Not checked:** site deployment AMech.", line)
                self.assertIn("Refresh would change:** nothing found.", line)

    def test_a_deployment_judged_not_to_be_a_website_is_not_reported_again(self):
        # #409: an audit can find that what Pages serves for a Mech is not a
        # website (a placeholder, a rendered README); the site-less entry records
        # that deployment, and only a later one is reported.
        judged = {"site": None, "repository": "https://github.com/CultureBotAI/AIMech",
                  "note": "GitHub Pages serves only a placeholder page.", "deployed_revision": "e" * 40}
        def answers(sha, state="success", calls=None):
            def api(path):
                if calls is not None:
                    calls.append(path)
                if path == "repos/CultureBotAI/AIMech":
                    return {"has_pages": True}
                if path == "repos/CultureBotAI/AIMech/deployments?environment=github-pages&per_page=1":
                    return [{"id": 9, "sha": sha, "created_at": "2026-10-14T08:22:48Z"}]
                if path == "repos/CultureBotAI/AIMech/deployments/9/statuses?per_page=1":
                    return [{"state": state}]
                if path == "repos/CultureBotAI/AIMech/pages":
                    # As without gh's repo scope (#429): only a later deployment needs this request.
                    if sha == "e" * 40:
                        raise check_updates.Unchecked(["gh: Not Found (HTTP 404)"])
                    return {"html_url": "https://culturebotai.github.io/AIMech/"}
                raise AssertionError(f"unexpected request to {path}")
            return api
        calls = []
        rows = check_updates.site_feature_check({"mechs": {"AIMech": judged}}, api=answers("e" * 40, calls=calls),
                                                opener=no_request)
        # #444: the row comes from the deployment record; no request is made to the site.
        self.assertEqual(rows, [("no site", "AIMech", "latest deployment is still eeeeeee, judged not to be a website")])
        self.assertEqual(calls, ["repos/CultureBotAI/AIMech",
                                 "repos/CultureBotAI/AIMech/deployments?environment=github-pages&per_page=1",
                                 "repos/CultureBotAI/AIMech/deployments/9/statuses?per_page=1"])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("Refresh would change:** nothing found.", line)
        self.assertNotIn("Not checked", line)
        # #437: the judged revision is compared only once its status confirms
        # success; an unconfirmed re-run of it may sit above a later real site.
        for state in ("queued", "failure"):
            with self.subTest(state=state):
                rows = check_updates.site_feature_check({"mechs": {"AIMech": judged}}, api=answers("e" * 40, state),
                                                        opener=no_request)
                self.assertEqual(rows, [("NOT CHECKED", "AIMech",
                                         f"latest deployment is {state}; currently served revision not verified")])
                line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
                self.assertIn("**Not checked:** site deployment AIMech.", line)
        opener, requests = head_requests()
        rows = check_updates.site_feature_check({"mechs": {"AIMech": judged}}, api=answers("f" * 40), opener=opener)
        self.assertEqual(rows, [("new site", "AIMech", "GitHub Pages now serves fffffff (deployed 2026-10-14T08:22:48Z) "
                                                       "at https://culturebotai.github.io/AIMech/; the table judged "
                                                       "eeeeeee not to be a website")])
        self.assertEqual(requests, [("HEAD", "https://culturebotai.github.io/AIMech/", 30)])
        line = check_updates.summary([], [], "matches", [], [], ("current", "current"), rows)
        self.assertIn("website feature verdicts to judge on new sites: AIMech.", line)
        for revision in ("e" * 39, "E" * 40, 7, None):
            with self.subTest(deployed_revision=revision):
                api = mock.Mock(side_effect=AssertionError("an invalid revision must not make an API request"))
                rows = check_updates.site_feature_check({"mechs": {"AIMech": dict(judged, deployed_revision=revision)}},
                                                        api=api, opener=no_request)
                self.assertEqual(rows, [("NOT CHECKED", "AIMech", "deployed_revision must be a full commit SHA")])
                api.assert_not_called()

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
        # running interpreter (#430), by the code's own deployments[0]["sha"]:
        # a literal "x"["sha"] would be a SyntaxWarning (#438).
        with self.assertRaises(TypeError) as str_index:
            ["x"][0]["sha"]
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
            # #408: recorded sites read the repository's has_pages flag too.
            (answers(repo=check_updates.Unchecked(["HTTP 404"])), "HTTP 404"),
            (answers(repo={}), "repository response has no has_pages flag"),
            (answers(repo={"has_pages": "yes"}), "repository response has no has_pages flag"),
            (answers(repo=[]), "repository response has no has_pages flag"),
        ]
        cases = [(recorded, api, detail) for api, detail in shared]
        cases += [(siteless, api, detail) for api, detail in shared]
        cases += [
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
        self.assertEqual(self.site_requests, [("HEAD", "https://culturebotai.github.io/CMMMech/", 30),
                                              ("HEAD", "https://example.org/duf/", 30),
                                              ("HEAD", "https://example.org/trait/", 30)])
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
        # Only the two sites that reached a successful deployment are requested.
        self.assertEqual(self.site_requests, [("HEAD", "https://example.org/duf/", 30),
                                              ("HEAD", "https://example.org/trait/", 30)])

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
                        if path == "repos/CultureBotAI/AMech":
                            return {"has_pages": True}
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
            if path == "repos/CultureBotAI/AMech":
                return {"has_pages": True}
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
