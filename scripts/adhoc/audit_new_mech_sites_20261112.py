#!/usr/bin/env python3
"""Read-only live browser evidence for the two new directory sites (2026-11-12).

Inputs: one Mech, its expected deployed revision, public Pages/API responses.
Output: a public-safe JSON receipt for the site-only directory promotion PR.
Run CofactorMech end to end and review its receipt before running AssayMech.
Requires Python 3.12, PyYAML 6.0.3 and Playwright 1.61.0. Does not change remote
services or scientific records; only the requested audit receipts are written.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright
import yaml

UPLOADER = "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b"
BUILD_MARKERS = {".nojekyll", ".site-generated"}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def require_site_url(url, root):
    parsed, base = urllib.parse.urlsplit(url), urllib.parse.urlsplit(root)
    assert parsed.scheme == base.scheme == "https" and parsed.netloc == base.netloc
    assert not parsed.query and not parsed.fragment
    assert parsed.path.startswith(base.path) and urllib.parse.unquote(parsed.path) == parsed.path
    assert ".." not in parsed.path.split("/") and "\\" not in parsed.path


def asset_url(root, path):
    assert re.fullmatch(r"[A-Za-z0-9_.\-/]+", path), "Nonliteral asset path"
    parsed = urllib.parse.urlsplit(path)
    assert not (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
    assert not path.startswith("/") and all(part not in ("", ".", "..") for part in path.split("/"))
    url = urllib.parse.urljoin(root, path)
    require_site_url(url, root)
    return url


class SiteRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, root):
        self.root = root

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        require_site_url(newurl, self.root)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch(url, root):
    require_site_url(url, root)
    request = urllib.request.Request(url, headers={"User-Agent": "culturebotai-site-review"})
    opener = urllib.request.build_opener(SiteRedirect(root))
    with opener.open(request, timeout=30) as response:
        require_site_url(response.url, root)
        body = response.read()
        return body, {"url": response.url, "status": response.status,
                      "last_modified": response.headers.get("Last-Modified"),
                      "github_request_id": response.headers.get("X-GitHub-Request-Id"),
                      "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def deployment(mech, expected):
    root = f"repos/CultureBotAI/{mech}"
    repo = api(root)
    assert repo["full_name"] == f"CultureBotAI/{mech}" and repo["has_pages"]
    pages = api(root + "/pages")
    rows = api(root + "/deployments?environment=github-pages&per_page=1")
    assert rows, "No recorded Pages deployment"
    row = rows[0]
    states = api(root + f"/deployments/{row['id']}/statuses?per_page=1")
    assert states and states[0]["state"] == "success", "Latest deployment is not successful"
    assert row["sha"] == expected, "Deployment revision moved or differs from reviewed source"
    url = pages["html_url"]
    assert url == f"https://culturebotai.github.io/{mech}/"
    body, served = fetch(url, url)
    assert served["status"] == 200 and served["github_request_id"] and body
    assert urllib.parse.urlsplit(served["url"]).hostname == "culturebotai.github.io"
    modified = parsedate_to_datetime(served["last_modified"])
    created = dt.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    assert modified >= created, "Served page predates latest deployment"
    return {"observed_at": now(), "id": row["id"], "sha": row["sha"],
            "created_at": row["created_at"], "state": states[0]["state"],
            "status_created_at": states[0]["created_at"], "site": url,
            "pages_build_type": pages.get("build_type"), "served": served}


SNAPSHOT = """() => ({
 url:location.href,title:document.title,body:document.body.innerText,
 headings:Array.from(document.querySelectorAll('h1,h2,h3')).map(e=>e.innerText),
 links:Array.from(document.querySelectorAll('a[href]')).map(e=>({text:e.innerText,url:e.href})),
 controls:Array.from(document.querySelectorAll('input,select,button')).map(e=>({
   tag:e.tagName,id:e.id,type:e.type,value:e.value,text:e.tagName==='SELECT'?null:e.innerText,
   options:e.tagName==='SELECT'?Array.from(e.options).map(o=>({value:o.value,text:o.text})):null})),
 counts:Array.from(document.querySelectorAll('[role=status]')).map(e=>e.innerText),
 record_links:Array.from(document.querySelectorAll('[data-record] a')).map(e=>e.href),
 visible_rows:Array.from(document.querySelectorAll('[data-record]')).filter(e=>!e.hidden).map(e=>e.innerText),
 page_width:innerWidth,scroll_width:document.documentElement.scrollWidth,
 tables:Array.from(document.querySelectorAll('.table-scroll')).map(e=>({
   width:e.clientWidth,scroll:e.scrollWidth,overflow:getComputedStyle(e).overflowX,tabindex:e.tabIndex})),
 body_background:getComputedStyle(document.body).backgroundColor,
 theme:document.documentElement.getAttribute('data-theme'),
 visuals:{svg:document.querySelectorAll('svg').length,canvas:document.querySelectorAll('canvas').length},
 main:document.querySelectorAll('main').length
})"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", choices=["CofactorMech", "AssayMech"], required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser", help="Optional installed Chromium executable")
    parser.add_argument("--screenshots", type=Path, help="Optional directory for catalogue screenshots")
    args = parser.parse_args()
    assert re.fullmatch(r"[0-9a-f]{40}", args.revision), "Expected full commit SHA"
    assert not args.output.exists(), "Refuse to overwrite a prior audit receipt"
    if args.screenshots:
        assert not args.screenshots.exists(), "Use a new screenshot directory for each attempt"
        args.screenshots.mkdir(parents=True, exist_ok=False)
    report = {"mech": args.mech, "started_at": now(), "expected_revision": args.revision}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    save()
    try:
        report["deployment_before"] = deployment(args.mech, args.revision)
        base = report["deployment_before"]["site"]
        raw, receipt = fetch(asset_url(base, "site-manifest.json"), base)
        manifest = json.loads(raw)
        assert manifest["project"] == args.mech and manifest["revision"] == args.revision
        report["manifest"] = {"receipt": receipt, "data": manifest}
        workflow = api(f"repos/CultureBotAI/{args.mech}/contents/.github/workflows/pages.yaml?ref={args.revision}")
        workflow_bytes = base64.b64decode(workflow["content"])
        jobs = yaml.safe_load(workflow_bytes)["jobs"]
        uploaders = [step["uses"] for job in jobs.values() for step in job.get("steps", [])
                     if step.get("uses", "").startswith("actions/upload-pages-artifact@")]
        assert uploaders == [UPLOADER], "Re-review changed Pages packaging before excluding files"
        uploader_ref = UPLOADER.split("@", 1)[1]
        uploader = api(f"repos/actions/upload-pages-artifact/contents/action.yml?ref={uploader_ref}")
        uploader_bytes = base64.b64decode(uploader["content"])
        assert b'--exclude=".[^/]*"' in uploader_bytes
        assert BUILD_MARKERS <= manifest["files_sha256"].keys()
        report["packaging"] = {
            "workflow_blob": workflow["sha"], "uploader": UPLOADER,
            "uploader_blob": uploader["sha"], "uploader_source_sha256": hashlib.sha256(uploader_bytes).hexdigest(),
            "excluded_build_markers": [{"path": path, "build_sha256": manifest["files_sha256"][path],
                                        "reason": "Internal marker omitted by the pinned Pages archive; not publicly verified"}
                                       for path in sorted(BUILD_MARKERS)],
        }
        report["asset_integrity"] = []
        report["source_records"] = []
        all_html = []
        for path, digest in sorted(manifest["files_sha256"].items()):
            url = asset_url(base, path)
            if path in BUILD_MARKERS:
                continue
            data, observation = fetch(url, base)
            assert observation["sha256"] == digest, f"Manifest hash mismatch: {path}"
            report["asset_integrity"].append({"path": path, **observation})
            if path.endswith(".html"):
                all_html.append(path)
            if path.startswith("sources/") and path.endswith(".yaml"):
                record = yaml.safe_load(data)
                report["source_records"].append({"id": record["id"], "name": record["name"],
                                               "path": path, "keys": sorted(record),
                                               "evidence_count": len(record.get("evidence", [])),
                                               "relationship_count": len(record.get("related_records", []))})
        assert len(report["source_records"]) == manifest["record_count"]
        report["pages"] = {}
        report["actions"] = {}
        save()
        with sync_playwright() as playwright:
            launch = {"headless": True}
            if args.browser:
                launch["executable_path"] = args.browser
            browser = playwright.chromium.launch(**launch)
            context = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="light")
            page = context.new_page()
            page.set_default_timeout(10000)
            requests, errors = [], []
            page.on("request", lambda request: requests.append({"url": request.url, "type": request.resource_type}))
            page.on("pageerror", lambda error: errors.append(str(error)))
            for path in sorted(all_html):
                requests.clear()
                errors.clear()
                response = page.goto(urllib.parse.urljoin(base, path), wait_until="networkidle")
                assert response and response.status == 200
                page.locator("main h1").wait_for()
                page.evaluate("document.fonts.ready")
                desktop = page.evaluate(SNAPSHOT)
                if path == "index.html" and args.screenshots:
                    page.screenshot(path=str(args.screenshots / f"{args.mech}-desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                narrow = page.evaluate(SNAPSHOT)
                if path == "index.html" and args.screenshots:
                    page.screenshot(path=str(args.screenshots / f"{args.mech}-narrow.png"), full_page=True)
                report["pages"][path] = {"desktop": desktop, "narrow": narrow,
                                           "requests": list(requests), "page_errors": list(errors)}
                page.set_viewport_size({"width": 1280, "height": 900})
                save()
            page.goto(base, wait_until="networkidle")
            snapshot = page.evaluate(SNAPSHOT)
            assert len(snapshot["record_links"]) == manifest["record_count"]
            first = report["source_records"][0]
            queries = [first["id"], first["name"], "no-such-record-site-review-20261112", "<b>literal markup</b>"]
            for query in queries:
                page.locator("#query").fill(query)
                report["actions"]["query:" + query] = page.evaluate(SNAPSHOT)
            page.locator("button[type=reset]").click()
            category = page.locator("#category option").nth(1).get_attribute("value")
            page.locator("#category").select_option(category)
            report["actions"]["category"] = page.evaluate(SNAPSHOT)
            if args.mech == "AssayMech":
                page.locator("button[type=reset]").click()
                page.locator("#kind").select_option("OPERATIONAL_ASSAY")
                report["actions"]["record_kind"] = page.evaluate(SNAPSHOT)
            page.locator("button[type=reset]").focus()
            page.keyboard.press("Enter")
            report["actions"]["keyboard_reset"] = {"snapshot": page.evaluate(SNAPSHOT),
                                                    "active_id": page.evaluate("document.activeElement.id")}
            page.locator("#query").fill(first["name"])
            report["actions"]["url_after_search"] = page.url
            page.reload(wait_until="networkidle")
            report["actions"]["reload_after_search"] = page.evaluate(SNAPSHOT)
            linked = base + "?" + urllib.parse.urlencode({"q": first["name"]})
            page.goto(linked, wait_until="networkidle")
            report["actions"]["explicit_query_url"] = page.evaluate(SNAPSHOT)
            page.goto(base, wait_until="networkidle")
            page.emulate_media(color_scheme="dark")
            report["actions"]["system_dark"] = page.evaluate(SNAPSHOT)
            page.keyboard.press("Tab")
            report["actions"]["keyboard_focus"] = page.evaluate("({tag:document.activeElement.tagName,text:document.activeElement.innerText,outline:getComputedStyle(document.activeElement).outlineStyle})")
            no_js = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
            fallback = no_js.new_page()
            fallback.goto(base, wait_until="networkidle")
            report["no_javascript"] = fallback.evaluate(SNAPSHOT)
            no_js.close()
            failed = context.new_page()
            blocked = []
            def abort_data(route):
                if route.request.resource_type in ("fetch", "xhr"):
                    blocked.append(route.request.url)
                    route.abort()
                else:
                    route.continue_()
            failed.route("**/*", abort_data)
            failed.goto(base, wait_until="networkidle")
            failed.locator("#query").fill(first["name"])
            report["data_failure_probe"] = {"blocked": blocked, "snapshot": failed.evaluate(SNAPSHOT)}
            failed.close()
            browser.close()
        report["deployment_after"] = deployment(args.mech, args.revision)
        assert report["deployment_after"]["id"] == report["deployment_before"]["id"], "Deployment changed during review"
        report["summary"] = {
            "html_pages": len(report["pages"]), "records": manifest["record_count"],
            "hashed_assets": len(report["asset_integrity"]),
            "narrow_overflow": [path for path, item in report["pages"].items()
                                if item["narrow"]["scroll_width"] > 390],
            "pages_with_errors": [path for path, item in report["pages"].items() if item["page_errors"]],
            "data_requests": [request for item in report["pages"].values()
                              for request in item["requests"] if request["type"] in ("fetch", "xhr")],
        }
        report["finished_at"] = now()
        report["completion_meaning"] = "Evidence collection completed; feature verdicts require independent review of the observations"
        report["complete"] = True
        save()
        print(json.dumps({"mech": args.mech, "revision": args.revision,
                          "pages": len(all_html), "assets": len(report["asset_integrity"]),
                          "receipt": str(args.output)}, indent=2))
    except Exception as error:
        report["failure"] = {"type": type(error).__name__, "message": str(error), "at": now()}
        save()
        raise


if __name__ == "__main__":
    main()
