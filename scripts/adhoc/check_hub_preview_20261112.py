#!/usr/bin/env python3
"""Smoke-check refreshed hub body in the currently published site shell.

Inputs: current mechs.md/assets and live /mechs/ shell/main.css. Ruby Kramdown
renders the body; this is explicitly not a Jekyll build or deployment check.
Outputs: .temp preview plus evidence JSON/screenshots under _fleet/reviews.
Serves: November 12 combined refresh PR. Date: 2026-11-12.
"""
import argparse
import datetime as dt
import functools
import hashlib
import http.server
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_fleet/reviews/refresh-20261112"
PREVIEW = ROOT / ".temp/hub-preview-20261112"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "culturebotai-hub-preview"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        assert response.status == 200 and data
        return data


def prepare():
    (PREVIEW / "mechs").mkdir(parents=True, exist_ok=True)
    (PREVIEW / "assets").mkdir(exist_ok=True)
    fragment = PREVIEW / "body.html"
    subprocess.run(["ruby", str(ROOT / "scripts/adhoc/render_hub_preview_20261112.rb"),
                    str(ROOT / "mechs.md"), str(fragment)], check=True)
    shell = fetch("https://culturebotai.github.io/mechs/").decode()
    shell, count = re.subn(r'(<main\b[^>]*>).*?(</main>)',
                          lambda match: match[1] + '<div class="wrapper">' + fragment.read_text() + '</div>' + match[2],
                          shell, count=1, flags=re.S)
    assert count == 1
    (PREVIEW / "mechs/index.html").write_text(shell)
    (PREVIEW / "assets/main.css").write_bytes(fetch("https://culturebotai.github.io/assets/main.css"))
    shutil.copy2(ROOT / "assets/custom.css", PREVIEW / "assets/custom.css")
    target = PREVIEW / "assets/fleet"
    if not target.exists():
        target.symlink_to(ROOT / "assets/fleet", target_is_directory=True)
    return {"source_sha256": hashlib.sha256((ROOT / "mechs.md").read_bytes()).hexdigest(),
            "preview_sha256": hashlib.sha256(shell.encode()).hexdigest(),
            "main_css_sha256": hashlib.sha256((PREVIEW / "assets/main.css").read_bytes()).hexdigest()}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def inspect(page, width, output, layout_only=False, keyboard=False):
    page.set_viewport_size({"width": width, "height": 900})
    errors, bad_responses = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: bad_responses.append({"url": response.url, "status": response.status})
            if response.status >= 400 else None)
    response = page.goto(page._preview_url, wait_until="networkidle")
    assert response.status == 200
    page.wait_for_selector("#fleet-nodes a")
    assert page.locator("#fleet-nodes a").count() == 16
    row = {"width": width, "graph_nodes": 16, "site_links": {}}
    for mech in ("CofactorMech", "AssayMech"):
        node = page.locator(f'#fleet-nodes a[aria-label^="Open {mech},"]')
        href = node.get_attribute("href")
        assert href == f"https://culturebotai.github.io/{mech}/"
        node.focus()
        assert page.locator("#fleet-detail h3").inner_text() == mech
        assert page.locator(f'#fleet-detail a[href="{href}"]').count() >= 1
        row["site_links"][mech] = href
    if not layout_only:
        cell = page.locator('#fleet-heat button[data-mech="CofactorMech"][data-voc="CHEBI"]')
        if keyboard:
            cell.focus()
            cell.press("Enter")
            row["heatmap_activation"] = "keyboard focus and Enter; pointer success not asserted"
        else:
            cell.click()
        page.wait_for_selector("#fleet-cell-panel ol.reclist a")
        row["heatmap_records"] = page.locator("#fleet-cell-panel ol.reclist a").count()
        row["heatmap_summary"] = page.locator("#fleet-cell-panel").inner_text()
        assert row["heatmap_records"] == 14
    else:
        row["heatmap_check"] = "Not repeated; prior mobile pointer attempt timed out with sticky header interception."
    row["layout"] = page.evaluate("""() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
      overflowing:Array.from(document.querySelectorAll('body *')).filter(e => {
        let r=e.getBoundingClientRect(); return r.width > 0 && r.right > innerWidth+1 && !e.closest('.fleet-heat-wrap,.fleet-cap-wrap,.fleet-feat-wrap');
      }).slice(0,20).map(e=>({tag:e.tagName,class:e.className,id:e.id,right:e.getBoundingClientRect().right}))})""")
    page.locator("h1").scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"hub-{width}-light.png"))
    toggle = page.get_by_role("button", name="Switch to dark theme", exact=True)
    toggle.click()
    assert page.locator("html").get_attribute("data-theme") == "dark"
    page.reload(wait_until="networkidle")
    assert page.locator("html").get_attribute("data-theme") == "dark"
    row["theme_persists"] = True
    page.screenshot(path=str(output / f"hub-{width}-dark.png"))
    row["page_errors"] = errors
    row["http_errors"] = bad_responses
    assert not errors and not bad_responses, (errors, bad_responses)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["canary", "remaining", "layout", "keyboard"])
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    output = OUT / ("hub-preview-" + args.phase + f"-{args.attempt}")
    output.mkdir(parents=True, exist_ok=False)
    provenance = prepare()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(PREVIEW)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "method": "Kramdown body in published shell with local custom CSS and local fleet assets; not a full Jekyll build",
              "provenance": provenance, "views": [], "complete": False}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            context = browser.new_context(color_scheme="light")
            page = context.new_page()
            page._preview_url = f"http://127.0.0.1:{server.server_port}/mechs/"
            report["views"].append(inspect(page, 1440 if args.phase == "canary" else 390, output,
                                          args.phase == "layout", args.phase == "keyboard"))
            context.close()
            browser.close()
            report["complete"] = True
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        receipt = output / "browser.json"
        receipt.write_text(json.dumps(report, indent=2) + "\n")
        assert json.loads(receipt.read_text()) == report
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
