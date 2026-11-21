#!/usr/bin/env python3
"""Check AIMech map controls and linked exports for the November 19 feature PR.

Inputs: live deployed AIMech site and completed root browser receipt.
Output: new JSON of filter states, export structure and source-link responses.
2026-11-19; no record editing, inference, or writes to a remote service.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("root_audit", ROOT / "scripts/adhoc/revalidate_root_sites_20261119.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
BASE = "https://culturebotai.github.io/AIMech/pages/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    prior = json.loads(args.receipt.read_text())
    assert prior["complete"]
    result = {"started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "deployment_before": audit.deployment("AIMech", BASE + "index.html"), "exports": {}, "maps": {}}
    assert result["deployment_before"]["sha"] == prior["deployment_after"]["sha"]
    for name in ("index.json", "corpus_map.json"):
        with urllib.request.urlopen(BASE + name, timeout=45) as response:
            body = response.read()
        payload = json.loads(body)
        arrays = {"$": payload} if isinstance(payload, list) else {key: value for key, value in payload.items() if isinstance(value, list)}
        result["exports"][name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
            "keys": sorted(payload) if isinstance(payload, dict) else None,
            "arrays": {key: {"count": len(value), "first_record_keys": sorted(value[0]) if value and isinstance(value[0], dict) else None}
                       for key, value in arrays.items()}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless=True)
        for name, selector in (("map", "#map-search"), ("graph", "#graph-search")):
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + name + ".html", wait_until="networkidle")
            audit.settled(page)
            states = {"initial": audit.snapshot(page)}
            for query in ("KernelPCA", "no-such-concept-20261119", ""):
                page.locator(selector).fill(query)
                page.wait_for_timeout(400)
                states["query:" + query] = audit.snapshot(page)
            if name == "graph":
                page.locator("#graph-origin").select_option("aio")
                states["origin:aio"] = audit.snapshot(page)
            result["maps"][name] = states
            page.close()
        browser.close()
    result["deployment_after"] = audit.deployment("AIMech", BASE + "index.html")
    assert result["deployment_before"]["id"] == result["deployment_after"]["id"]
    result["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    assert json.loads(args.output.read_text()) == result
    print(json.dumps({"receipt": str(args.output), "maps": len(result["maps"]), "exports": len(result["exports"])}))


if __name__ == "__main__":
    main()
