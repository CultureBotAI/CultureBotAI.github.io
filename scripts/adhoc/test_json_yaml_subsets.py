#!/usr/bin/env python3
"""
Purpose: Inspect all prefix_census and build_subsets matches in CofactorMech
         and AssayMech records, comparing structured fields against prose
         fields so JSON-serialized YAML records are handled accurately.
Inputs:  Snapshot mechs/CofactorMech and mechs/AssayMech records.
Outputs: Console breakdown of all matched CURIEs by JSON path.
Date:    2026-11-10
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")
sys.path.insert(0, str(REPO / "scripts/fleet"))

import build_subsets
import prefix_census

SNAP = Path(
    "/Users/marcin/.gemini/antigravity-cli/brain/"
    "fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm"
)


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from walk_strings(item, f"{path}[]")
    elif isinstance(obj, str):
        yield path, obj


def main() -> None:
    for mech, rel in (
        ("CofactorMech", "data/cofactors"),
        ("AssayMech", "data/assays"),
    ):
        print(f"=== {mech} ===")
        mdir = SNAP / "mechs" / mech / rel
        by_path = {}
        for f in sorted(mdir.glob("*.yaml")):
            txt = f.read_text()
            doc = json.loads(txt)
            for jpath, val in walk_strings(doc):
                terms = build_subsets.terms_in(val)
                cands = [
                    prefix_census.norm.get(m.group(1), m.group(1))
                    for m in prefix_census.rx.finditer(val)
                ]
                if terms or cands:
                    by_path.setdefault(jpath, []).append(
                        (f.name, sorted(terms), cands)
                    )
        for jpath, items in sorted(by_path.items()):
            print(f"  path: {jpath} ({len(items)} hits)")
            for fname, terms, cands in items[:5]:
                print(f"    {fname}: subset_terms={terms} | census={cands}")


if __name__ == "__main__":
    main()
