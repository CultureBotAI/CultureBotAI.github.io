#!/usr/bin/env python3
"""Render Mech landing pages for the 2026-10-30 Pages refresh PR.

Inputs: pinned fleet CLI inventory and the site's existing feature URLs.
Outputs: per-site browser JSON and desktop/mobile screenshots in --output.
This is a rendering smoke check, not a complete feature or accessibility audit.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only")
    parser.add_argument("--browser", help="Optional installed Chromium executable")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    features = json.loads(args.features.read_text())["mechs"]
    selected = [m for m in inventory if not args.only or args.only == m["key"]]
    if not selected:
        parser.error("selection not in manifest")
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser)
        for mech in selected:
            target = args.output / mech["key"]
            target.mkdir(parents=True, exist_ok=True)
            result = {"repository": mech["github"], "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "views": []}
            for width in (1440, 390):
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                errors, requests = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("response", lambda response: requests.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
                view = {"width": width}
                try:
                    response = page.goto(features[mech["display_name"]]["site"], wait_until="networkidle", timeout=60000)
                    page.locator("body").wait_for()
                    view.update({"url": page.url, "status": response.status if response else None, "title": page.title(), "text": page.locator("body").inner_text()[:25000]})
                    view["layout"] = page.evaluate("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,main:document.querySelectorAll('main,[role=main]').length})")
                    page.screenshot(path=str(target / f"landing-{width}.png"), full_page=False)
                    if not response or response.status >= 400 or len(view["text"].strip()) < 100:
                        failures.append(f"{mech['key']}:{width}: content not confirmed")
                except Exception as exc:
                    view["error"] = str(exc)
                    failures.append(f"{mech['key']}:{width}: {exc}")
                view.update({"page_errors": errors, "http_errors": requests})
                if errors or requests:
                    failures.append(f"{mech['key']}:{width}: browser errors require review")
                result["views"].append(view)
                context.close()
            (target / "browser.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({"repository": mech["github"], "views": [{k: v for k, v in view.items() if k != "text"} for view in result["views"]]}), flush=True)
        browser.close()
    if failures:
        print(json.dumps({"needs_review": failures}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
