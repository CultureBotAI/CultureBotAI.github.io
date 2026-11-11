#!/usr/bin/env python3
"""
Purpose: Inspect the freshly seeded CofactorMech (14 records) and AssayMech
         (9 records) corpora, update the snapshot revisions.json and claw
         checkout to origin/main (3daf94e), and summarize categories,
         groundings, cross-corpus links, and JSON/YAML structure for onboarding
         into CultureBotAI.github.io (while keeping ScaleupMech withheld).
Inputs:  Snapshot directory under scratch/xmech-refresh-20261109-pm and
         repository files in CultureBotAI.github.io.
Outputs: Console summary + updated scratch snapshot revisions.json.
Date:    2026-11-10
"""

from __future__ import annotations

import collections
import json
import os
import subprocess
from pathlib import Path

SNAP = Path(
    "/Users/marcin/.gemini/antigravity-cli/brain/"
    "fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm"
)


def git_out(cwd: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    return subprocess.check_output(
        ["git", "-C", str(cwd), *args], text=True, env=env
    ).strip()


def main() -> None:
    claw_dir = SNAP / "claw"
    fleet_yaml = (claw_dir / "src/kg_microbe_fleet/fleet.yaml").read_text()
    print("=== fleet.yaml CofactorMech / AssayMech / ScaleupMech ===")
    lines = fleet_yaml.splitlines()
    for i, line in enumerate(lines):
        if any(m in line for m in ("CofactorMech", "AssayMech", "ScaleupMech")):
            start = max(0, i - 2)
            end = min(len(lines), i + 20)
            print("\n".join(lines[start:end]))
            print("---")

    # Inspect CofactorMech records
    cf_dir = SNAP / "mechs" / "CofactorMech" / "data" / "cofactors"
    cf_files = sorted(cf_dir.glob("*.yaml"))
    cf_cats = collections.Counter()
    cf_xref_corpora = collections.Counter()
    cf_xref_relations = collections.Counter()
    cf_xref_statuses = collections.Counter()
    cf_xref_targets = collections.defaultdict(set)
    cf_records_with_corpus = collections.defaultdict(set)
    print(f"\n=== CofactorMech ({len(cf_files)} records) ===")
    for p in cf_files:
        doc = json.loads(p.read_text())
        for c in doc.get("categories", []):
            cf_cats[c] += 1
        for rel in doc.get("related_records", []):
            corp = rel.get("corpus")
            ident = rel.get("identifier")
            rel_type = rel.get("relation")
            st = rel.get("status")
            cf_xref_corpora[corp] += 1
            cf_xref_relations[(corp, rel_type)] += 1
            cf_xref_statuses[(corp, st)] += 1
            cf_xref_targets[corp].add(ident)
            cf_records_with_corpus[corp].add(doc.get("id"))
        print(
            f"  {p.name}: id={doc.get('id')} | name={doc.get('name')} | "
            f"chem={doc.get('chemical_id')} | cats={doc.get('categories')} | "
            f"related={[(r.get('corpus'), r.get('identifier'), r.get('relation')) for r in doc.get('related_records', [])]}"
        )
    print("Cofactor categories:", dict(cf_cats))
    print("Cofactor related_records counts by corpus:", dict(cf_xref_corpora))
    print("Cofactor related_records by (corpus, relation):", dict(cf_xref_relations))
    print("Cofactor related_records by (corpus, status):", dict(cf_xref_statuses))
    for corp, targets in sorted(cf_xref_targets.items()):
        print(
            f"  -> {corp}: {cf_xref_corpora[corp]} links across "
            f"{len(cf_records_with_corpus[corp])}/14 cofactors to "
            f"{len(targets)} unique targets: {sorted(targets)}"
        )

    # Inspect AssayMech records
    as_dir = SNAP / "mechs" / "AssayMech" / "data" / "assays"
    as_files = sorted(as_dir.glob("*.yaml"))
    as_cats = collections.Counter()
    as_kinds = collections.Counter()
    as_xref_corpora = collections.Counter()
    as_xref_relations = collections.Counter()
    as_xref_targets = collections.defaultdict(set)
    as_records_with_corpus = collections.defaultdict(set)
    print(f"\n=== AssayMech ({len(as_files)} records) ===")
    for p in as_files:
        doc = json.loads(p.read_text())
        as_kinds[doc.get("record_kind")] += 1
        for c in doc.get("categories", []):
            as_cats[c] += 1
        for rel in doc.get("related_records", []):
            corp = rel.get("corpus")
            ident = rel.get("identifier")
            rel_type = rel.get("relation")
            as_xref_corpora[corp] += 1
            as_xref_relations[(corp, rel_type)] += 1
            as_xref_targets[corp].add(ident)
            as_records_with_corpus[corp].add(doc.get("id"))
        print(
            f"  {p.name}: id={doc.get('id')} | name={doc.get('name')} | "
            f"kind={doc.get('record_kind')} | cats={doc.get('categories')} | "
            f"groundings={[(g.get('term_id'), g.get('relation')) for g in doc.get('ontology_groundings', [])]} | "
            f"related={[(r.get('corpus'), r.get('identifier'), r.get('relation')) for r in doc.get('related_records', [])]}"
        )
    print("Assay record_kind:", dict(as_kinds))
    print("Assay categories:", dict(as_cats))
    print("Assay related_records counts by corpus:", dict(as_xref_corpora))
    print("Assay related_records by (corpus, relation):", dict(as_xref_relations))
    for corp, targets in sorted(as_xref_targets.items()):
        print(
            f"  -> {corp}: {as_xref_corpora[corp]} links across "
            f"{len(as_records_with_corpus[corp])}/9 assays to "
            f"{len(targets)} unique targets: {sorted(targets)}"
        )


if __name__ == "__main__":
    main()
