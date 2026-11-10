#!/usr/bin/env python3
"""Inspect secondary figures and claims at the 2026-11-09 PM pins.

Purpose: Compute secondary figures (CMMMech material kinds and ChEBI/taxon/mechanism counts,
CommunityMech community vs isolate counts, AntibioticMech workflow and mechanism counts,
HabitatMech workflow and multi-source counts, and CLAW manifest summary) from the pinned snapshots.
Inputs: `$SNAP/revisions.json`, `$SNAP/mechs/*`, `_fleet/data/manifest.json`.
Outputs: Console summary used to update `_fleet/mechs_template.md`, `_fleet/fleet_fragment.html`,
`_fleet/audit_notes.json`, `CLAUDE.md`, `index.md`, `resources.md`, and `communitymech.md`.
Serves: PR #554 / Issue #557.
Date: 2026-11-09.
"""
import collections
import json
from pathlib import Path
import yaml

SCRATCH = Path("/Users/marcin/.gemini/antigravity-cli/brain/fce06610-c3eb-40c8-ab6b-48056807ad41/scratch")
SNAP = SCRATCH / "xmech-refresh-20261109-pm"
MECHS = SNAP / "mechs"
REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")


def main():
    revs = json.loads((SNAP / "revisions.json").read_text())
    print("Pinned at:", revs["pinned_at_utc"])
    print("CLAW:", revs["claw"])
    for m, info in revs["mechs"].items():
        print(f"  {m:20s} {info['sha']} ({info['commit_date']})")

    # 1. CMMMech
    cmm_files = sorted((MECHS / "CMMMech/data/records").rglob("*.y*ml"))
    kinds = collections.Counter()
    chebi_records = 0
    taxon_records = 0
    mech_records = 0
    mech_total = 0
    for f in cmm_files:
        doc = yaml.safe_load(f.read_text())
        kinds[doc.get("material_kind") or doc.get("kind") or "unknown"] += 1
        text = f.read_text()
        if "CHEBI:" in text:
            chebi_records += 1
        if "NCBITaxon:" in text:
            taxon_records += 1
        mechs = doc.get("mechanisms") or []
        if mechs:
            mech_records += 1
            mech_total += len(mechs)
    print("\nCMMMech:")
    print("  total:", len(cmm_files), "kinds:", dict(kinds))
    print("  chebi_records:", chebi_records, "taxon_records:", taxon_records)
    print("  mech_records:", mech_records, "mech_total:", mech_total, "without_mech:", len(cmm_files) - mech_records)

    # 2. CommunityMech
    comm_files = list((MECHS / "CommunityMech/kb/communities").glob("*.yaml"))
    iso_files = list((MECHS / "CommunityMech/data/isolates").glob("*.yaml"))
    print("\nCommunityMech:")
    print("  communities:", len(comm_files), "isolates:", len(iso_files), "total:", len(comm_files) + len(iso_files))

    # 3. AntibioticMech
    ab_files = sorted((MECHS / "AntibioticMech/data/antibiotics").rglob("*.yaml"))
    ab_status = collections.Counter()
    ab_moa = 0
    ab_target = 0
    ab_cg = 0
    for f in ab_files:
        doc = yaml.safe_load(f.read_text())
        ab_status[doc.get("curation_status") or doc.get("status")] += 1
        if doc.get("modes_of_action") or doc.get("mode_of_action"):
            ab_moa += 1
        if doc.get("molecular_targets") or doc.get("targets"):
            ab_target += 1
        if doc.get("causal_graphs") or doc.get("causal_graph"):
            ab_cg += 1
    print("\nAntibioticMech:")
    print("  total:", len(ab_files), "status:", dict(ab_status))
    print("  moa:", ab_moa, "target:", ab_target, "causal_graphs:", ab_cg)

    # 4. HabitatMech
    hab_files = sorted((MECHS / "HabitatMech/data/habitats").rglob("*.yaml"))
    hab_status = collections.Counter()
    hab_multi = 0
    for f in hab_files:
        doc = yaml.safe_load(f.read_text())
        hab_status[doc.get("curation_status") or doc.get("status")] += 1
        sources = {a.get("source") for a in (doc.get("source_attestations") or []) if isinstance(a, dict) and a.get("source")}
        if len(sources) >= 2:
            hab_multi += 1
    print("\nHabitatMech:")
    print("  total:", len(hab_files), "status:", dict(hab_status), "multi_source:", hab_multi)

    # 5. Manifest summary
    manifest = json.loads((REPO / "_fleet/data/manifest.json").read_text())
    ev_enabled = [
        m for m, d in manifest["mechs"].items()
        if d["capabilities"]["evidence_reference_validation"]["status"] == "enabled"
    ]
    print("\nManifest:")
    print("  members:", len(manifest["mechs"]), "artifacts:", manifest["artifact_count"],
          "capabilities:", len(manifest["capability_catalogue"]))
    print("  evidence_reference_validation enabled:", ev_enabled)


if __name__ == "__main__":
    main()
