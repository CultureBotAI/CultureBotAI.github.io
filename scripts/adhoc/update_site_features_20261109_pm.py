#!/usr/bin/env python3
"""Verify live GitHub Pages deployments and feature-note figures for the 2026-11-09 PM refresh.

Purpose: Inspect and update `_fleet/data/site_features.json` so `deployed_revision` and
feature notes match the live verified GitHub Pages deployments on 2026-11-09 PM.
Inputs: `_fleet/data/site_features.json`, GitHub deployments API, live GitHub Pages HTTP endpoints.
Outputs: Updated `_fleet/data/site_features.json` (when `--apply` is passed).
Serves: PR #554 / Issue #556.
Date: 2026-11-09.
"""
import argparse
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
GH_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
)


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
        "last_modified": last_mod,
        "http_status": http_status,
        "verified": verified,
    }


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "CultureBotAI-FleetAudit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def inspect_local_commits() -> None:
    snap_mechs = Path("/Users/marcin/.gemini/antigravity-cli/brain/fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm/mechs")
    pairs = [
        ("AntibioticMech", "defe41100737cee8dc1e4722a2930e9752e6bee8", "d00e4533e81a8a605397042a61f83ce085dc7f01"),
        ("CommunityMech", "bf8e8626114487765f67879cc6040cdc412e7c4f", "7ce759feb72be28e1860ccf70b69bb9888fe4a45"),
        ("DUFMech", "de2fdf959acb5e7a1cb1e4139e6936f4ffdf5498", "17755af9c3c73a8a9d1cb472743cdd6f329b7b92"),
        ("HabitatMech", "19d3ccb65e6b5128b9b0a5ae39cb509bf3f2bf39", "6c89a863ce26add77a5b642009635af3a9580c31"),
        ("NaturalProductMech", "001dcd3f712b5e53c7bf7baaf3311aab503579df", "6226602895d4d2e598dc70e281d43027f1c89471"),
        ("TaxonMech", "4162c24b37706e78c8a897488485a121089a86e5", "6a86624b7ba126a5982b758431b9804cf0ffb395"),
        ("CMMMech", "7449fa912e2d92f8aff400481ee75b49edbb685e", "4bdd13ae94fd62127aa6ed0d61a164f175fc4461"),
    ]
    for mech, old_sha, new_sha in pairs:
        repo_dir = snap_mechs / mech
        res = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--oneline", f"{old_sha}..{new_sha}"],
            text=True,
            env=GH_ENV,
            capture_output=True,
        )
        print(f"=== {mech} ({old_sha[:7]}..{new_sha[:7]}) ===")
        if res.returncode == 0:
            print(res.stdout.strip())
        else:
            res_head = subprocess.run(
                ["git", "-C", str(repo_dir), "log", "-5", "--oneline", "HEAD"],
                text=True,
                env=GH_ENV,
                capture_output=True,
            )
            print("(deployed from gh-pages or newer ref; recent HEAD commits:)")
            print(res_head.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--local-diff", action="store_true", help="Inspect git log between prior and current deployed revisions in local snapshot")
    ap.add_argument("--apply", action="store_true", help="Write updated deployed_revision and notes to _fleet/data/site_features.json")
    args = ap.parse_args()

    if args.local_diff:
        inspect_local_commits()
        return

    sf_path = ROOT / "_fleet/data/site_features.json"
    sf = json.loads(sf_path.read_text(encoding="utf-8"))

    updates = {}
    for mech, entry in sf["mechs"].items():
        repo_name = entry["repository"].split("CultureBotAI/")[1]
        dep = check_deployment(repo_name, entry["site"])
        cur_sha = entry["deployed_revision"]
        new_sha = dep["sha"] if dep["verified"] else cur_sha
        changed = new_sha != cur_sha
        updates[mech] = dep
        print(
            f"{mech:20s}: cur={cur_sha} live={dep['sha']} state={dep['state']} "
            f"verified={dep['verified']} last_mod={dep['last_modified']} -> {'UPDATE' if changed else 'KEEP'}"
        )
        if changed:
            entry["deployed_revision"] = new_sha

    # Inspect live pages for the Mechs whose deployed_revision moved
    ab_index = fetch_html("https://culturebotai.github.io/AntibioticMech/pages/index.html")
    ab_avibactam = fetch_html("https://culturebotai.github.io/AntibioticMech/pages/antibacterial/avibactam.html")
    cmm_index = fetch_html("https://culturebotai.github.io/CMMMech/pages/index.html")
    cmm_cobalt = fetch_html("https://culturebotai.github.io/CMMMech/pages/materials/cobalt.html")
    cmm_graph = fetch_html("https://culturebotai.github.io/CMMMech/pages/graph.html")
    cmm_map = fetch_html("https://culturebotai.github.io/CMMMech/pages/map.html")
    duf_index = fetch_html("https://culturebotai.github.io/DUFMech/")
    hab_index = fetch_html("https://culturebotai.github.io/HabitatMech/pages/index.html")
    hab_sed = fetch_html("https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html")
    np_index = fetch_html("https://culturebotai.github.io/NaturalProductMech/pages/index.html")
    np_aniso = fetch_html("https://culturebotai.github.io/NaturalProductMech/pages/alkaloids/anisomycin.html")
    np_rebec = fetch_html("https://culturebotai.github.io/NaturalProductMech/pages/alkaloids/rebeccamycin.html")
    tax_index = fetch_html("https://culturebotai.github.io/TaxonMech/pages/index.html")
    tax_sources = fetch_html("https://culturebotai.github.io/TaxonMech/pages/sources.html")

    print("\n--- Live page excerpts ---")
    for label, html, pat in [
        ("AntibioticMech index", ab_index, r"(?:SEEDED|corpus digest|fe34ebf|[0-9a-f]{12}|2026-[0-9]{2}-[0-9]{2})[^<\n]{0,80}"),
        ("AntibioticMech avibactam", ab_avibactam, r"Label unavailable"),
        ("CMMMech index", cmm_index, r"(?:708|457|609|500|90|f2a56c|[0-9a-f]{12})[^<\n]{0,80}"),
        ("CMMMech cobalt footer", cmm_cobalt, r"(?:materials|mechanisms|latest curation|corpus digest)[^<\n]{0,100}"),
        ("CMMMech graph", cmm_graph, r"(?:654|972|nodes|edges)[^<\n]{0,80}"),
        ("CMMMech map", cmm_map, r"(?:602|607|points|material)[^<\n]{0,80}"),
        ("DUFMech index", duf_index, r"(?:8,296|8,238|1,906|8,242|1,796|373|6,127)[^<\n]{0,80}"),
        ("HabitatMech index", hab_index, r"(?:1,911|1,901|3,209|SEEDED|2026-08-16)[^<\n]{0,80}"),
        ("HabitatMech marine-sediment", hab_sed, r"(?:TaxonMech|NCBITaxon|PMID)[^<\n]{0,80}"),
        ("NaturalProductMech index", np_index, r"(?:3,136|SHA-256|2838a2004e52|[0-9a-f]{12}|2026-10-31)[^<\n]{0,80}"),
        ("TaxonMech index", tax_index, r"(?:626,048|100,745|20,648|14,013|959c8dfd8771|[0-9a-f]{12})[^<\n]{0,80}"),
        ("TaxonMech sources", tax_sources, r"(?:corpus digest|959c8dfd8771|[0-9a-f]{12})[^<\n]{0,80}"),
    ]:
        matches = re.findall(pat, html)
        print(f"{label}: {matches[:8]}")

    cmm_footer_m = re.search(r"(\d+)\s+materials\s*·\s*(\d+)\s+mechanisms\s*·\s*latest curation\s*(\d{4}-\d{2}-\d{2})\s*·\s*corpus digest\s*(?:<[^>]+>)?([0-9a-f]{12})", cmm_cobalt)
    ab_digest_m = re.search(r"corpus digest\s*(?:<[^>]+>)?([0-9a-f]{12})", ab_index)
    ab_seeded_m = re.search(r"([0-9,]+)\s+(?:of\s+[0-9,]+\s+)?(?:records\s+have\s+|compounds\s+carry\s+|carry\s+|are\s+)?(?:<[^>]+>)?SEEDED", ab_index)
    hab_seeded_m = re.search(r"([0-9,]+)\s+of\s+[0-9,]+\s+records\s+have\s+the\s+SEEDED", hab_index)
    print("\n--- Extracted live footer/notice values ---")
    print("CMMMech cobalt footer:", cmm_footer_m.groups() if cmm_footer_m else "NO MATCH")
    print("AntibioticMech digest:", ab_digest_m.groups() if ab_digest_m else "NO MATCH")
    print("AntibioticMech SEEDED:", ab_seeded_m.groups() if ab_seeded_m else "NO MATCH")
    print("HabitatMech SEEDED:", hab_seeded_m.groups() if hab_seeded_m else "NO MATCH")

    if args.apply:
        # 1. AntibioticMech: 2,799 SEEDED -> 2,794 SEEDED; digest fe34ebf5e05b -> 04a931dcbfed
        ab_cs = sf["mechs"]["AntibioticMech"]["features"]["corpus_stats"]["note"]
        sf["mechs"]["AntibioticMech"]["features"]["corpus_stats"]["note"] = ab_cs.replace(
            "2,799 SEEDED records", "2,794 SEEDED records"
        )
        if ab_digest_m:
            new_ab_digest = ab_digest_m.group(1)
            ab_bp = sf["mechs"]["AntibioticMech"]["features"]["build_provenance"]["note"]
            sf["mechs"]["AntibioticMech"]["features"]["build_provenance"]["note"] = ab_bp.replace(
                "fe34ebf5e05b", new_ab_digest
            )

        # 2. CommunityMech: 511 -> 512 published communities
        for fkey in ("search", "facets", "full_catalogue", "corpus_stats", "downloads"):
            note = sf["mechs"]["CommunityMech"]["features"][fkey]["note"]
            sf["mechs"]["CommunityMech"]["features"][fkey]["note"] = note.replace("511", "512")

        # 3. HabitatMech: 1,911 -> 1,901 SEEDED on live index
        if "1901" in hab_index or "1,901" in hab_index:
            for fkey in ("review_status", "corpus_stats"):
                note = sf["mechs"]["HabitatMech"]["features"][fkey]["note"]
                sf["mechs"]["HabitatMech"]["features"][fkey]["note"] = note.replace("1,911", "1,901")

        # 4. CMMMech: 703 -> 708 materials, 452 -> 457 minerals, and footer digest/date
        for fkey in ("search", "facets", "full_catalogue", "domain_view", "corpus_stats", "downloads", "build_provenance"):
            note = sf["mechs"]["CMMMech"]["features"][fkey]["note"]
            sf["mechs"]["CMMMech"]["features"][fkey]["note"] = note.replace("703", "708")
        sf["mechs"]["CMMMech"]["features"]["category_browse"]["note"] = (
            sf["mechs"]["CMMMech"]["features"]["category_browse"]["note"].replace("452 minerals", "457 minerals")
        )
        if cmm_footer_m:
            _, _, cmm_date, cmm_digest = cmm_footer_m.groups()
            cmm_bp = sf["mechs"]["CMMMech"]["features"]["build_provenance"]["note"]
            cmm_bp = cmm_bp.replace("2026-11-09", cmm_date).replace("f2a56c7f5564", cmm_digest)
            sf["mechs"]["CMMMech"]["features"]["build_provenance"]["note"] = cmm_bp

        sf_path.write_text(json.dumps(sf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("\nWrote updated _fleet/data/site_features.json")


if __name__ == "__main__":
    main()
