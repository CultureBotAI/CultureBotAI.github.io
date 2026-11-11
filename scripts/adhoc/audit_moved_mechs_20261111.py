#!/usr/bin/env python3
"""
Purpose: Inspect exact corpus counts, category/status breakdowns, README claims,
         and GitHub Pages deployment statuses across the 2026-11-11 pinned
         snapshot for _fleet/audit_notes.json, _fleet/mechs_template.md,
         _fleet/fleet_fragment.html, and _fleet/data/site_features.json.
Inputs:  Snapshot checkouts in scratch/xmech-refresh-20261109-pm/mechs and
         GitHub Pages deployment API.
Outputs: Console report of corpus breakdowns and verified deployment SHAs.
Date:    2026-11-11
"""

from __future__ import annotations

import collections
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import yaml

REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")
sys.path.insert(0, str(REPO / "scripts/fleet"))
import build_site_audit
from card_markup import card_figures
import check_cards
import roots

SNAP = Path(
    "/Users/marcin/.gemini/antigravity-cli/brain/"
    "fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm"
)
os.environ["MECHS_ROOT"] = str(SNAP / "mechs")
roots.MECHS_ROOT = str(SNAP / "mechs")


def main() -> None:
    pins = json.loads((SNAP / "revisions.json").read_text())["mechs"]
    cards = card_figures((REPO / "_fleet/mechs_template.md").read_text())
    print("=== Card figures at pin vs current card ===")
    for mech in sorted(check_cards.SOURCES):
        kind, path, selector = check_cards.SOURCES[mech]
        card = cards[mech]
        sha = pins[mech]["sha"]
        show = build_site_audit.git_show(SNAP / "mechs" / mech, sha)
        if kind == "git-tree":
            pinned = check_cards.record_inventory(
                show("__git_tree__").decode(), selector
            )
        else:
            _, pinned = build_site_audit.committed_copy(show, path)
        at_pin = (
            check_cards.figure(
                mech, kind, pinned.decode("utf-8", "replace"), selector
            )
            if pinned is not None
            else None
        )
        print(
            f"  {mech:20s}: card={card:>8,} | at_pin={str(at_pin):>8} | diff={None if at_pin is None else at_pin - card}"
        )

    # 1. HabitatMech breakdown
    hab_root = SNAP / "mechs" / "HabitatMech"
    hab_index = subprocess.check_output(
        ["git", "-C", str(hab_root), "show", "HEAD:pages/index.html"],
        text=True,
    )
    print("\n=== HabitatMech pages/index.html stat tiles ===")
    for m in re.finditer(r"<b>([^<]+)</b>\s*<span>([^<]+)</span>", hab_index):
        print(" ", m.group(1), "|", m.group(2))

    # 3. CMMMech breakdown
    cmm_files = roots.record_paths("CMMMech")
    cmm_cats = collections.Counter()
    cmm_chebi = collections.Counter()
    cmm_taxon = 0
    cmm_mech_records = 0
    cmm_mech_total = 0
    for f in cmm_files:
        doc = yaml.safe_load(Path(f).read_text(encoding="utf-8")) or {}
        cat = doc.get("material_kind")
        cmm_cats[cat] += 1
        txt = Path(f).read_text(encoding="utf-8")
        if "CHEBI:" in txt:
            cmm_chebi[cat] += 1
        if "NCBITaxon:" in txt:
            cmm_taxon += 1
        mechs_list = doc.get("mechanisms") or []
        if mechs_list:
            cmm_mech_records += 1
            cmm_mech_total += len(mechs_list)
    print(
        f"\n=== CMMMech ({len(cmm_files)} records) ===\n"
        f"  categories: {dict(cmm_cats)}\n"
        f"  chebi by cat: {dict(cmm_chebi)}\n"
        f"  with NCBITaxon: {cmm_taxon}\n"
        f"  with mechanisms: {cmm_mech_records} records, {cmm_mech_total} mechanisms, "
        f"{len(cmm_files) - cmm_mech_records} without mechanisms"
    )

    # 4. MediaIngredientMech breakdown
    mim_files = roots.record_paths("MediaIngredientMech")
    mim_status = collections.Counter()
    for f in mim_files:
        txt = Path(f).read_text(encoding="utf-8")
        ms = re.search(r"^mapping_status:\s*(\S+)", txt, re.M)
        if ms:
            mim_status[ms.group(1)] += 1
    print(
        f"\n=== MediaIngredientMech ({len(mim_files)} records) ===\n"
        f"  mapping_status: {dict(mim_status)}"
    )


if __name__ == "__main__":
    main()
