#!/usr/bin/env python3
"""Collect TraitMech/AIMech browser evidence for the November 19 feature PR.

Inputs: retained rubric, live Pages and immutable deployed GitHub source.
Outputs: new per-attempt JSON receipts and screenshots; no scientific-data edits.
Use --plan first, then one complete site and verify persistence before the next.
2026-11-19. Reuses observation selectors from the retained November 4 audit.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
from email.utils import parsedate_to_datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("prior_observations", ROOT / "scripts/adhoc/audit_browser_group_b_20261104.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
PROFILES = {
    "TraitMech": {
        "query": "#record-query", "queries": ["METPO:1004002", "traitmech:000616", "bipolar mating system"],
        "sort": "#record-sort", "facets": ["#record-category", "#record-kind"],
        "combined": {"#record-category": "ECOLOGY", "#record-kind": "CLASS"}, "combined_query": "pathogen",
        "reset": "#facet-clear-btn", "data_prefixes": ["data/traits/"],
        "record_prefixes": ["pages/traits/"],
        "extra": ["pages/category/ecology.html", "pages/category/quantitative_property.html", "pages/umap.html", "pages/map.html", "pages/graph.html", "pages/sequence-map.html", "app/discussions/index.html"],
    },
    "AIMech": {
        "query": "#searchInput", "queries": ["AIMech:KernelPCA", "Adam", "SoftDTW"],
        "sort": "#sortSelect", "facets": ["#originSelect", "#kindSelect", "#branchSelect"],
        "combined": {"#originSelect": "curated", "#kindSelect": "architecture"}, "combined_query": "attention",
        "reset": "#resetFilters", "data_prefixes": ["data/curated/", "data/aio/"],
        "record_prefixes": ["pages/curated/", "pages/aio/"],
        "extra": ["pages/map.html", "pages/graph.html", "pages/schema.html", "pages/curated/SoftDTW.html"],
    },
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def deployment(repo, url):
    dep = api(f"repos/CultureBotAI/{repo}/deployments?environment=github-pages&per_page=1")[0]
    status = api(f"repos/CultureBotAI/{repo}/deployments/{dep['id']}/statuses?per_page=1")[0]
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
        receipt = {"http_status": response.status, "url": response.url,
                   "last_modified": response.headers.get("Last-Modified"),
                   "github_request_id": response.headers.get("X-GitHub-Request-Id")}
    assert status["state"] == "success"
    assert receipt["http_status"] == 200 and receipt["github_request_id"]
    assert parsedate_to_datetime(receipt["last_modified"]) >= dt.datetime.fromisoformat(dep["created_at"].replace("Z", "+00:00"))
    return {**{key: dep[key] for key in ("id", "sha", "created_at")},
            "state": status["state"], "status_created_at": status["created_at"], **receipt}


def snapshot(page):
    result = prior.compact(page.evaluate(prior.SNAPSHOT_JS))
    result["body"] = page.locator("body").inner_text()
    result["record_links"] = page.locator("a[href]").evaluate_all("xs => xs.map(x=>({text:x.textContent.trim(),url:x.href})).filter(x=>/\\/pages\\/(traits|curated|aio)\\//.test(x.url))")
    return result


def settled(page):
    page.locator("body").wait_for()
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    assert len(page.locator("body").inner_text()) > 100, "Unpopulated page shell"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", choices=PROFILES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path, required=True)
    parser.add_argument("--browser", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "_fleet/data/site_features.json").read_text())["mechs"][args.mech]
    profile = PROFILES[args.mech]
    repo = config["repository"].rsplit("/", 1)[-1]
    base = f"https://culturebotai.github.io/{repo}/"
    urls = [config["site"], config["features"]["search"]["url"]]
    urls += [value["url"].split("?", 1)[0] for value in config["features"].values()
             if value["url"].startswith(base) and urllib.parse.urlsplit(value["url"]).path.endswith((".html", "/"))]
    urls += [base + path for path in profile["extra"]]
    urls = list(dict.fromkeys(urls))
    if args.plan:
        print(json.dumps({"mech": args.mech, "urls": urls, "output": str(args.output)}, indent=2))
        return
    assert not args.output.exists() and not args.screenshots.exists(), "Use fresh output paths"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.screenshots.mkdir(parents=True, exist_ok=False)
    report = {"mech": args.mech, "started_at": now(), "pages": {}, "actions": {}, "failures": {}, "complete": False}

    def save():
        temporary = args.output.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(args.output)

    save()
    try:
        report["deployment_before"] = deployment(repo, config["site"])
        sha = report["deployment_before"]["sha"]
        tree = api(f"repos/CultureBotAI/{repo}/git/trees/{sha}?recursive=1")
        assert tree.get("truncated") is False, "Incomplete source inventory"
        paths = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
        records = [path for path in paths if path.startswith(tuple(profile["data_prefixes"])) and path.endswith((".yaml", ".yml"))]
        html = [path for path in paths if path.startswith(tuple(profile["record_prefixes"])) and path.endswith(".html")]
        report["source_inventory"] = {"revision": sha, "truncated": False, "records": len(records),
                                      "record_html": len(html), "record_paths_sha256": hashlib.sha256("\n".join(sorted(records)).encode()).hexdigest()}
        report["license_sources"] = {}
        for path in paths:
            if "/" not in path and path.upper().startswith("LICENSE"):
                blob = api(f"repos/CultureBotAI/{repo}/contents/{path}?ref={sha}")
                report["license_sources"][path] = {"blob": blob["sha"], "text": base64.b64decode(blob["content"]).decode()}
        save()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=args.browser, headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="light")
            page = context.new_page()
            page.set_default_timeout(12000)
            for number, url in enumerate(urls):
                requests, errors = [], []
                probe = context.new_page()
                probe.on("request", lambda request: requests.append({"url": request.url, "type": request.resource_type}))
                probe.on("pageerror", lambda error: errors.append(str(error)))
                response = None
                try:
                    response = probe.goto(url, wait_until="networkidle", timeout=60000)
                    settled(probe)
                    if url == config["site"]:
                        toggle = probe.locator(".theme-toggle,#theme-toggle")
                        if toggle.count():
                            toggle.first.click()
                    desktop = snapshot(probe)
                    assert response and response.status == 200, f"HTTP {response.status if response else 'no response'}"
                    probe.screenshot(path=str(args.screenshots / f"{number:02d}-desktop.png"))
                    probe.set_viewport_size({"width": 390, "height": 844})
                    settled(probe)
                    narrow = snapshot(probe)
                    probe.screenshot(path=str(args.screenshots / f"{number:02d}-narrow.png"))
                    fresh_context = browser.new_context(viewport={"width": 390, "height": 844})
                    fresh = fresh_context.new_page()
                    fresh.goto(url, wait_until="networkidle", timeout=60000)
                    settled(fresh)
                    fresh_result = snapshot(fresh)
                    fresh_context.close()
                    report["pages"][url] = {"status": response.status, "desktop": desktop, "resized_390": narrow,
                                             "fresh_390": fresh_result, "requests": requests, "errors": errors}
                except Exception as error:
                    report["pages"][url] = {"error": f"{type(error).__name__}: {error}", "status": response.status if response else None,
                                             "requests": requests, "errors": errors}
                probe.close()
                save()
                print("PAGE " + url, flush=True)

            browse = config["features"]["search"]["url"]
            page.goto(browse, wait_until="networkidle", timeout=60000)
            settled(page)

            def action(name, operation):
                try:
                    operation()
                    page.wait_for_timeout(400)
                    report["actions"][name] = snapshot(page)
                except Exception as error:
                    report["actions"][name] = {"error": str(error)}
                save()

            action("initial", lambda: None)
            for query in profile["queries"] + ["no-such-record-20261119", "<b>literal markup</b>"]:
                action("query:" + query, lambda query=query: page.locator(profile["query"]).fill(query))
            action("clear_query", lambda: page.locator(profile["query"]).fill(""))
            options = page.locator(profile["sort"] + " option").evaluate_all("xs=>xs.map(x=>x.value)")
            for option in options[:2] + options[-1:]:
                action("sort:" + option, lambda option=option: page.locator(profile["sort"]).select_option(option))
            for selector in profile["facets"]:
                action("before_facet_reset:" + selector, lambda: page.locator(profile["reset"]).click())
                values = page.locator(selector + " option").evaluate_all("xs=>xs.filter(x=>!x.disabled&&x.value&&!['all','any','*'].includes(x.value.toLowerCase())).map(x=>x.value)")
                if values:
                    action("facet:" + selector, lambda selector=selector, value=values[0]: page.locator(selector).select_option(value))
            action("combined_reset", lambda: page.locator(profile["reset"]).click())
            for selector, value in profile["combined"].items():
                action("combined:" + selector, lambda selector=selector, value=value: page.locator(selector).select_option(value))
            action("combined_query", lambda: page.locator(profile["query"]).fill(profile["combined_query"]))
            action("reload_filtered", lambda: page.reload(wait_until="networkidle"))
            saved_url = page.url
            cold = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
            cold.goto(saved_url, wait_until="networkidle")
            settled(cold)
            report["actions"]["cold_filtered"] = snapshot(cold)
            cold.context.close()
            action("keyboard_reset", lambda: (page.locator(profile["reset"]).focus(), page.keyboard.press("Enter")))
            for url, capture in report["pages"].items():
                if not any(request["type"] in ("fetch", "xhr") or request["url"].endswith("/data.js") for request in capture["requests"]):
                    continue
                failed_context = browser.new_context()
                blocked = []

                def block(route):
                    if route.request.resource_type in ("fetch", "xhr") or route.request.url.endswith("/data.js"):
                        blocked.append(route.request.url)
                        route.abort()
                    else:
                        route.continue_()

                failed_context.route("**/*", block)
                failed = failed_context.new_page()
                try:
                    failed.goto(url, wait_until="networkidle", timeout=60000)
                    settled(failed)
                    item = {"blocked": blocked, "failed": snapshot(failed)}
                    failed_context.unroute("**/*", block)
                    retry = failed.locator("#map-retry,#retry-load,button").filter(has_text="Retry")
                    if retry.count() and retry.first.is_visible():
                        retry.first.click()
                        failed.wait_for_load_state("networkidle")
                    else:
                        failed.reload(wait_until="networkidle")
                    settled(failed)
                    item["recovered"] = snapshot(failed)
                    report["failures"][url] = item
                except Exception as error:
                    report["failures"][url] = {"error": str(error), "blocked": blocked}
                failed_context.close()
                save()
            browser.close()
        report["deployment_after"] = deployment(repo, config["site"])
        assert report["deployment_before"]["id"] == report["deployment_after"]["id"], "Deployment moved during audit"
        report["finished_at"] = now()
        report["complete"] = True
        report["completion_meaning"] = "Observation collection finished; errors and unsupported criteria require judgment, not an automatic present verdict."
        save()
        assert json.loads(args.output.read_text()) == report
        print(json.dumps({"mech": args.mech, "receipt": str(args.output), "pages": len(report["pages"])}))
    except Exception as error:
        report["fatal_error"] = str(error)
        save()
        raise


if __name__ == "__main__":
    main()
