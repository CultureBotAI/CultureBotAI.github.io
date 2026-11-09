#!/usr/bin/env python3
"""Inspect changed XREF primary sources and secondary figures for the Nov 8 refresh.

Inputs: _fleet/reviews/refresh-20261108/hand-claims-sources.json, source-excerpts-fleet.json,
secondary-fleet.json, and the isolated --snapshot directory.
Outputs: console summary of changed XREF primary sources, license files, and stat tiles.
Serves #542 and #544; Date: 2026-11-08.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Path to isolated refresh snapshot ($SNAP)")
    args = parser.parse_args()

    rev = ROOT / "_fleet/reviews/refresh-20261108"
    sources = json.loads((rev / "hand-claims-sources.json").read_text())
    excerpts = json.loads((rev / "source-excerpts-fleet.json").read_text())
    _secondary = json.loads((rev / "secondary-fleet.json").read_text())

    print("=== CHANGED XREF PRIMARY SOURCES ===")
    for row in sources["xrefs"]:
        ps = row.get("primary_source", {})
        if not ps.get("unchanged"):
            print(f"#{row['number']} {row['locator']}: {row['claim']['url']}")
            print(f"  anchor_excerpt: {ps.get('anchor_excerpt')}")
            print(f"  diff:\n{ps.get('diff')}")
        for aux in row.get("auxiliary_sources", []):
            if not aux.get("unchanged"):
                print(f"  AUX CHANGED #{row['number']} {aux['path']}:\n{aux.get('diff')}")

    print("\n=== CHANGED LICENSE FILES ===")
    for mech, info in sources["schema_licenses"].items():
        for lic in info["licenses"]:
            if not lic["unchanged"]:
                print(f"{mech} {lic['path']} changed:\n{lic.get('diff')}")
        print(f"{mech} tree_roots: {info['tree_roots']}")

    print("\n=== README EXCERPTS FOR CHANGED MECHS ===")
    for mech in ["HabitatMech", "CommunityMech", "TraitMech", "PathwayMech", "AntibioticMech", "CMMMech"]:
        doc = excerpts[mech]["documents"].get("README.md", {})
        print(f"\n--- {mech} (card_at_pin={excerpts[mech]['card_at_pin']}) ---")
        for ex in doc.get("excerpts", [])[:60]:
            print(f"  L{ex['line']}: {ex['text']}")

    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1", XDG_CONFIG_HOME="/tmp")
    snap = args.snapshot
    pins = json.loads((snap / "revisions.json").read_text())["mechs"]
    for mech, path in [("HabitatMech", "pages/index.html"), ("CommunityMech", "docs/index.html")]:
        sha = pins[mech]["sha"]
        html = subprocess.check_output(["git", "-C", str(snap / "mechs" / mech), "show", f"{sha}:{path}"], text=True, env=env)
        print(f"\n=== {mech}:{path} stat tiles ===")
        for m in re.finditer(r'stat-num[^>]*>([^<]+)<|stat-value[^>]*>([^<]+)<|(\d[\d,]+)\s+(?:communities|reviewed|grounded|PaCMAP|graph)', html, re.I):
            print(" ", m.group(0))
        for line in html.splitlines():
            if any(k in line.lower() for k in ["stat", "reviewed", "grounded", "pacmap", "communit", "categor"]):
                if len(line.strip()) < 240:
                    print("  LINE:", line.strip())


if __name__ == "__main__":
    main()
