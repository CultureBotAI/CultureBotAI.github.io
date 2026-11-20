#!/usr/bin/env python3
"""Supplement the small-site feature receipts with cold mobile and licence checks.

Inputs: completed current CofactorMech/AssayMech audit receipt and deployed source.
Output: new compact evidence JSON for the November 19 feature revalidation PR.
2026-11-19. Run one site, inspect saved output, then repeat for the second site.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("small_sites", ROOT / "scripts/adhoc/audit_new_mech_sites_20261112.py")
small = importlib.util.module_from_spec(spec)
spec.loader.exec_module(small)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    prior = json.loads(args.receipt.read_text())
    assert prior["complete"] is True
    mech = prior["mech"]
    sha = prior["deployment_after"]["sha"]
    base = prior["deployment_after"]["site"]
    report = {"mech": mech, "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "deployment_before": small.deployment(mech, sha), "cold_390": {}}
    source = small.api(f"repos/CultureBotAI/{mech}/contents/LICENSE?ref={sha}")
    licensed = base64.b64decode(source["content"])
    with urllib.request.urlopen(base + "LICENSE.txt", timeout=30) as response:
        served = response.read()
    assert licensed == served, "Served licence differs from the deployed source"
    report["license"] = {"blob": source["sha"], "sha256": hashlib.sha256(served).hexdigest(),
                         "text": served.decode(), "same_as_repository": True}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless=True)
        for path in prior["pages"]:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.goto(base + path, wait_until="networkidle")
            page.locator("main h1").wait_for()
            page.evaluate("document.fonts.ready")
            report["cold_390"][path] = page.evaluate("""() => ({
                width: innerWidth, scroll_width: document.documentElement.scrollWidth,
                heading: document.querySelector('main h1').innerText,
                text_length: document.querySelector('main').innerText.length,
                tables: [...document.querySelectorAll('.table-scroll')].map(e=>({
                    client_width:e.clientWidth,scroll_width:e.scrollWidth,
                    overflow:getComputedStyle(e).overflowX,tabindex:e.tabIndex}))})""")
            assert report["cold_390"][path]["text_length"] > 200
            context.close()
        browser.close()
    report["deployment_after"] = small.deployment(mech, sha)
    assert report["deployment_before"]["id"] == report["deployment_after"]["id"]
    report["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    assert json.loads(args.output.read_text()) == report
    print(json.dumps({"mech": mech, "pages": len(report["cold_390"]), "receipt": str(args.output)}))


if __name__ == "__main__":
    main()
