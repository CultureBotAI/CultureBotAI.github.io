#!/usr/bin/env python3
"""Spot-check current Mech landing counts and links for the Nov 12 refresh PR.

Inputs: one named public Mech's live Pages root and GitHub deployment API.
Outputs: timestamped browser text, headings, links and deployment receipt JSON.
This is a content spot-check, not a complete website-feature audit. 2026-11-12.
"""
import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright

SITES = {
    "CofactorMech": "https://culturebotai.github.io/CofactorMech/",
    "AssayMech": "https://culturebotai.github.io/AssayMech/",
    "CMMMech": "https://culturebotai.github.io/CMMMech/",
    "HabitatMech": "https://culturebotai.github.io/HabitatMech/pages/index.html",
    "CommunityMech": "https://culturebotai.github.io/CommunityMech/",
}


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def deployment(mech):
    base = f"repos/CultureBotAI/{mech}"
    rows = api(base + "/deployments?environment=github-pages&per_page=1")
    assert rows
    row = rows[0]
    state = api(base + f"/deployments/{row['id']}/statuses?per_page=1")[0]
    return {key: row[key] for key in ("id", "sha", "created_at")} | {"state": state["state"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mech", choices=SITES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Refusing to overwrite previous evidence"
    result = {"mech": args.mech, "scope": "Landing-page content spot-check; not a full feature audit",
              "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "before": deployment(args.mech)}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(SITES[args.mech], wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        # A root can be a client-side redirect shell. Associate the headers with
        # the final rendered page, rather than page.goto's initial response.
        response = page.request.get(page.url)
        assert response.url == page.url
        text = page.locator("body").inner_text()
        result.update({"url": page.url, "status": response.status,
                       "headers": {key: response.headers.get(key) for key in
                                   ("last-modified", "x-github-request-id", "content-type")},
                       "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                       "headings": page.locator("h1,h2,h3").all_inner_texts(),
                       "links": page.locator("a[href]").evaluate_all(
                           "els => els.map(e => ({text:e.textContent.trim(), href:e.href}))"),
                       "page_errors": errors})
        browser.close()
    result["after"] = deployment(args.mech)
    assert result["before"] == result["after"], "Deployment changed during spot-check"
    assert result["after"]["state"] == "success"
    assert result["status"] == 200 and result["headers"]["x-github-request-id"] and text.strip()
    assert parsedate_to_datetime(result["headers"]["last-modified"]) >= dt.datetime.fromisoformat(
        result["after"]["created_at"].replace("Z", "+00:00")), "Page predates deployment"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    saved = json.loads(args.output.read_text())
    assert saved["text_sha256"] == hashlib.sha256(saved["text"].encode()).hexdigest()
    print(f"Verified {args.mech}: {saved['after']['sha']}; {len(saved['text'])} characters; {args.output}")
    print(text[:1800])


if __name__ == "__main__":
    main()
