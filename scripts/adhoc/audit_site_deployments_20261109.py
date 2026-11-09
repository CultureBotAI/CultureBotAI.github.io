#!/usr/bin/env python3
"""Audit live GitHub Pages deployments and exercise browser controls for the Nov 9 refresh PR.

Inputs: _fleet/data/site_features.json, $SNAP/revisions.json, GitHub deployments API, live Pages via Playwright.
Outputs: _fleet/reviews/refresh-20261109/site-deployments-auditor.json.
Date: 2026-11-09.
"""
import argparse
import datetime as dt
import email.utils
import glob
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
GH_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
)


def resolve_chrome_executable(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    env_path = os.environ.get("PLAYWRIGHT_CHROME_EXECUTABLE")
    if env_path and Path(env_path).is_file():
        return env_path
    candidates = sorted(
        glob.glob(str(Path.home() / "Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell")),
        reverse=True,
    )
    return candidates[0] if candidates else None


PAGE_STATE_JS = """() => ({
  url: location.href,
  title: document.title,
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  theme: document.documentElement.dataset.theme || document.body.dataset.theme || null,
  savedTheme: localStorage.getItem('mech-theme') || localStorage.getItem('theme') || null,
  h1: document.querySelector('h1')?.innerText || null,
  footer: [...document.querySelectorAll('footer')].map(x => x.innerText).join('\\n'),
  textExcerpt: document.body ? document.body.innerText.slice(0, 4000) : '',
  statuses: [...document.querySelectorAll('[role=status], [id*=count], [id*=status], .results-count, #result-count')].filter(x => x.offsetParent !== null).map(x => ({id: x.id, text: x.innerText.slice(0, 400)}))
})"""


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def check_deployment(repo_name: str, site_url: str) -> dict:
    deps = json.loads(
        subprocess.check_output(
            ["gh", "api", f"repos/CultureBotAI/{repo_name}/deployments?environment=github-pages&per_page=1"],
            text=True,
            env=GH_ENV,
        )
    )
    dep = deps[0]
    statuses = json.loads(
        subprocess.check_output(
            ["gh", "api", f"repos/CultureBotAI/{repo_name}/deployments/{dep['id']}/statuses?per_page=1"],
            text=True,
            env=GH_ENV,
        )
    )
    st = statuses[0]
    req = urllib.request.Request(site_url, method="HEAD", headers={"User-Agent": "CultureBotAI-FleetAudit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        last_mod = resp.headers.get("Last-Modified")
        http_status = resp.status
    mod_dt = email.utils.parsedate_to_datetime(last_mod)
    created_dt = dt.datetime.fromisoformat(dep["created_at"].replace("Z", "+00:00"))
    verified = (st["state"] == "success") and (mod_dt >= created_dt)
    return {
        "id": dep["id"],
        "sha": dep["sha"],
        "created_at": dep["created_at"],
        "state": st["state"],
        "status_created_at": st["created_at"],
        "environment_url": st.get("environment_url"),
        "site_url": site_url,
        "http_status": http_status,
        "last_modified": last_mod,
        "served_not_older_than_request": mod_dt >= created_dt,
        "verified": verified,
        "preserve_prior_deployed_revision": not verified,
    }


def visit_page(browser, ctx, page, url: str, check_390: bool = True) -> dict:
    resp = page.goto(url, wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(350)
    desktop = page.evaluate(PAGE_STATE_JS)
    out = {
        "url": url,
        "http_status": resp.status if resp else None,
        "desktop_width": desktop["scrollWidth"],
        "h1": desktop["h1"],
        "theme": desktop["theme"],
        "savedTheme": desktop["savedTheme"],
        "footer": desktop["footer"],
        "statuses": desktop["statuses"],
        "text_sha256": hashlib.sha256(desktop["textExcerpt"].encode()).hexdigest(),
        "text_excerpt": desktop["textExcerpt"][:900],
    }
    if check_390:
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(200)
        out["resized_390"] = page.evaluate("document.documentElement.scrollWidth")
        narrow = browser.new_context(viewport={"width": 390, "height": 844})
        np = narrow.new_page()
        np.goto(url, wait_until="networkidle", timeout=90000)
        np.wait_for_timeout(250)
        out["fresh_390"] = np.evaluate("document.documentElement.scrollWidth")
        narrow.close()
        page.set_viewport_size({"width": 1280, "height": 900})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--only", help="Canary a single Mech first")
    ap.add_argument("--chrome-executable", help="Optional path to headless Chromium binary")
    args = ap.parse_args()

    sf_path = ROOT / "_fleet/data/site_features.json"
    sf = json.loads(sf_path.read_text())
    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]

    routes_by_mech = {
        "AntibioticMech": [
            "https://culturebotai.github.io/AntibioticMech/pages/index.html",
            "https://culturebotai.github.io/AntibioticMech/pages/browse.html",
            "https://culturebotai.github.io/AntibioticMech/pages/chemical-map.html",
            "https://culturebotai.github.io/AntibioticMech/pages/sequence-map.html",
            "https://culturebotai.github.io/AntibioticMech/pages/antibacterial/amikacin.html",
            "https://culturebotai.github.io/AntibioticMech/pages/antibacterial/avibactam.html",
            "https://culturebotai.github.io/AntibioticMech/pages/antimycobacterial/d-cycloserine.html",
        ],
        "CellStructureMech": [
            "https://culturebotai.github.io/CellStructureMech/pages/index.html",
            "https://culturebotai.github.io/CellStructureMech/pages/browse.html",
            "https://culturebotai.github.io/CellStructureMech/pages/embedding-map.html",
            "https://culturebotai.github.io/CellStructureMech/pages/structures/appendage/attachment_organelle_membrane.html",
        ],
        "CommunityMech": [
            "https://culturebotai.github.io/CommunityMech/",
            "https://culturebotai.github.io/CommunityMech/browser.html",
            "https://culturebotai.github.io/CommunityMech/community_umap.html",
            "https://culturebotai.github.io/CommunityMech/schema.html",
            "https://culturebotai.github.io/CommunityMech/communities/ANME_SRB_Marine_Methane_Seep_Consortium.html",
            "https://culturebotai.github.io/CommunityMech/communities/Copper_Biomining_Heap_Leach.html",
        ],
        "CultureMech": [
            "https://culturebotai.github.io/CultureMech/app/",
            "https://culturebotai.github.io/CultureMech/app/browser.html",
            "https://culturebotai.github.io/CultureMech/pages/normalized/000252.html",
        ],
        "DUFMech": [
            "https://culturebotai.github.io/DUFMech/",
            "https://culturebotai.github.io/DUFMech/categories.html",
            "https://culturebotai.github.io/DUFMech/sources.html",
            "https://culturebotai.github.io/DUFMech/schema.html",
            "https://culturebotai.github.io/DUFMech/families/PF04149.html",
        ],
        "HabitatMech": [
            "https://culturebotai.github.io/HabitatMech/pages/index.html",
            "https://culturebotai.github.io/HabitatMech/pages/browse.html",
            "https://culturebotai.github.io/HabitatMech/pages/text-map/",
            "https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html",
            "https://culturebotai.github.io/HabitatMech/pages/habitats/aquatic-macrophyte-associated-environment-habitatmech-bacdive-38260eea00.html",
        ],
        "MediaIngredientMech": [
            "https://culturebotai.github.io/MediaIngredientMech/",
            "https://culturebotai.github.io/MediaIngredientMech/browser.html",
            "https://culturebotai.github.io/MediaIngredientMech/records/ingredient/mapped/Nacl.html",
        ],
        "NaturalProductMech": [
            "https://culturebotai.github.io/NaturalProductMech/pages/index.html",
            "https://culturebotai.github.io/NaturalProductMech/pages/browse.html",
            "https://culturebotai.github.io/NaturalProductMech/pages/chemical-map.html",
            "https://culturebotai.github.io/NaturalProductMech/pages/alkaloids/anisomycin.html",
        ],
        "PathwayMech": [
            "https://culturebotai.github.io/PathwayMech/pages/index.html",
            "https://culturebotai.github.io/PathwayMech/pages/browse.html",
            "https://culturebotai.github.io/PathwayMech/pages/records/MetaCyc_PWY-6543.html",
            "https://culturebotai.github.io/PathwayMech/pages/records/GO_0036040.html",
        ],
        "ProteinTraitsMech": [
            "https://culturebotai.github.io/proteintraitsmech/",
            "https://culturebotai.github.io/proteintraitsmech/browse.html#cat=STRUCT_ACTIVE_SITE&q=racemase",
            "https://culturebotai.github.io/proteintraitsmech/browse.html#record=MCSA%3A1",
            "https://culturebotai.github.io/proteintraitsmech/schema.html",
        ],
        "TaxonMech": [
            "https://culturebotai.github.io/TaxonMech/pages/index.html",
            "https://culturebotai.github.io/TaxonMech/pages/browse.html",
            "https://culturebotai.github.io/TaxonMech/pages/taxon.html?id=NCBITaxon:2173",
            "https://culturebotai.github.io/TaxonMech/pages/sources.html",
        ],
        "TraitMech": [
            "https://culturebotai.github.io/TraitMech/pages/index.html",
            "https://culturebotai.github.io/TraitMech/pages/browse.html",
            "https://culturebotai.github.io/TraitMech/pages/umap.html",
            "https://culturebotai.github.io/TraitMech/pages/map.html",
            "https://culturebotai.github.io/TraitMech/pages/sequence-map.html",
            "https://culturebotai.github.io/TraitMech/pages/traits/ecology/animal_pathogen.html",
            "https://culturebotai.github.io/TraitMech/pages/traits/metabolism/wood_ljungdahl_pathway.html",
        ],
        "CMMMech": [
            "https://culturebotai.github.io/CMMMech/pages/index.html",
            "https://culturebotai.github.io/CMMMech/pages/browse.html",
            "https://culturebotai.github.io/CMMMech/pages/graph.html",
            "https://culturebotai.github.io/CMMMech/pages/map.html",
            "https://culturebotai.github.io/CMMMech/pages/kinds/mineral.html",
            "https://culturebotai.github.io/CMMMech/pages/materials/cobalt.html",
            "https://culturebotai.github.io/CMMMech/pages/materials/akaganeite.html",
            "https://culturebotai.github.io/CMMMech/pages/materials/copper.html",
        ],
        "AIMech": [
            "https://culturebotai.github.io/AIMech/pages/index.html",
            "https://culturebotai.github.io/AIMech/pages/browse.html",
            "https://culturebotai.github.io/AIMech/pages/graph.html",
            "https://culturebotai.github.io/AIMech/pages/map.html",
            "https://culturebotai.github.io/AIMech/pages/curated/Adam.html",
            "https://culturebotai.github.io/AIMech/pages/curated/KernelPCA.html",
            "https://culturebotai.github.io/AIMech/pages/aio/TrainingStrategy.html",
        ],
    }

    mechs_to_run = [args.only] if args.only else list(sf["mechs"].keys())
    auditor_receipt = {
        "started_at_utc": now_utc(),
        "reviewer": "central_directory live-site auditor",
        "mechs": {},
    }

    chrome_exec = resolve_chrome_executable(args.chrome_executable)
    with sync_playwright() as pw:
        launch_kwargs = {"headless": True}
        if chrome_exec:
            launch_kwargs["executable_path"] = chrome_exec
        browser = pw.chromium.launch(**launch_kwargs)
        for mech in mechs_to_run:
            entry = sf["mechs"][mech]
            repo_name = pins[mech]["repo"]
            dep_before = check_deployment(repo_name, entry["site"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            pages_out = {}
            actions_out = {}
            for idx, url in enumerate(routes_by_mech[mech]):
                pages_out[url] = visit_page(browser, ctx, page, url, check_390=(idx < 4 or "materials/" in url or "map.html" in url))

            if mech == "AntibioticMech":
                page.goto("https://culturebotai.github.io/AntibioticMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search]").first
                for term in ("CHEBI:2637", "amikacin", "no-such-compound-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]
            elif mech == "CommunityMech":
                page.goto("https://culturebotai.github.io/CommunityMech/browser.html", wait_until="networkidle")
                q = page.locator("input[type=search], #search-input").first
                for term in ("ANME", "CommunityMech:000134", "no-such-community-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate("document.getElementById('results-count')?.innerText || document.body.innerText.slice(0, 600)")
                q.fill("")
                page.wait_for_timeout(300)
                biotech = page.locator("input[type=checkbox][value='BIOTECHNOLOGY']")
                if biotech.count():
                    biotech.first.check()
                    page.wait_for_timeout(300)
                    actions_out["facet:BIOTECHNOLOGY"] = page.evaluate("document.getElementById('results-count')?.innerText || ''")
            elif mech == "HabitatMech":
                page.goto("https://culturebotai.github.io/HabitatMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search]").first
                for term in ("ENVO:03000033", "marine sediment", "no-such-habitat-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(500)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]
            elif mech == "PathwayMech":
                page.goto("https://culturebotai.github.io/PathwayMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search]").first
                for term in ("MetaCyc:PWY-6543", "trehalose", "no-such-pathway-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]
            elif mech == "TraitMech":
                page.goto("https://culturebotai.github.io/TraitMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search]").first
                for term in ("METPO:1004002", "traitmech:000616", "bipolar mating system", "no-such-trait-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]
            elif mech == "CMMMech":
                page.goto("https://culturebotai.github.io/CMMMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search]").first
                for term in ("CHEBI:27638", "cmmmech:copper", "Cobalt", "no-such-material-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]
                q.fill("")
                page.wait_for_timeout(300)
                selects = page.locator("select")
                if selects.count() >= 2:
                    selects.nth(0).select_option("element")
                    page.wait_for_timeout(250)
                    actions_out["facet:element"] = page.evaluate(PAGE_STATE_JS)["statuses"]
                    selects.nth(1).select_option("bioleaching")
                    page.wait_for_timeout(250)
                    actions_out["facet:element+bioleaching"] = page.evaluate(PAGE_STATE_JS)["statuses"]
            elif mech == "AIMech":
                page.goto("https://culturebotai.github.io/AIMech/pages/browse.html", wait_until="networkidle")
                q = page.locator("input[type=search], #search-input").first
                for term in ("AIMech:KernelPCA", "Adam", "no-such-concept-20261109"):
                    q.fill(term)
                    page.wait_for_timeout(400)
                    actions_out[f"search:{term}"] = page.evaluate(PAGE_STATE_JS)["statuses"]

            ctx.close()
            dep_after = check_deployment(repo_name, entry["site"])
            if dep_before["sha"] != dep_after["sha"]:
                raise ValueError(f"{mech}: deployment changed mid-audit ({dep_before['sha']} -> {dep_after['sha']})")

            auditor_receipt["mechs"][mech] = {
                "pin": pins[mech]["sha"],
                "prior_deployed_revision": entry["deployed_revision"],
                "deployment_before": dep_before,
                "deployment_after": dep_after,
                "pages": pages_out,
                "actions": actions_out,
            }
            print(
                f"AUDITED {mech}: deployed={dep_after['sha'][:7]} state={dep_after['state']} verified={dep_after['verified']} pages={len(pages_out)} actions={len(actions_out)}",
                flush=True,
            )
        browser.close()

    auditor_receipt["finished_at_utc"] = now_utc()
    out_dir = ROOT / "_fleet/reviews/refresh-20261109"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"-{args.only}" if args.only else ""
    (out_dir / f"site-deployments-auditor{suffix}.json").write_text(json.dumps(auditor_receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
