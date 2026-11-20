#!/usr/bin/env python3
"""Retain the public scope for the November 19 website-feature revalidation PR.

Inputs: an isolated canonical CLAW checkout and this site's existing feature rows.
Output: a new public-only scope receipt; no manifest, corpus or membership edits.
2026-11-19. Canonical projection executes committed CLAW bytes at its exact SHA.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from refresh_manifest import read_canonical, semantic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Use a new scope receipt; prior observations are immutable")
    public = read_canonical(args.claw_root.resolve())
    retained = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
    features = json.loads((ROOT / "_fleet/data/site_features.json").read_text())
    infrastructure = json.loads((ROOT / "_fleet/infrastructure.json").read_text())
    if set(features["mechs"]) - set(public["mechs"]):
        raise SystemExit("Feature rows are outside current public membership")
    report = {
        "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "website_base": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "canonical_source": public["source"],
        "retained_manifest_source": retained["source"],
        "retained_manifest_semantics_match": semantic(public) == semantic(retained),
        "public_members": {name: {"key": value["key"], "github": value["github"]}
                           for name, value in public["mechs"].items()},
        "feature_audit_sites": sorted(features["mechs"]),
        "other_public_members": sorted(set(public["mechs"]) - set(features["mechs"])),
        "infrastructure_declaration": infrastructure,
        "scope": "Revalidate all existing published corpus sites against the unchanged 24-feature catalogue. EdgeMech browser implementation is a separate repository PR; no unpublished browser is rated as live.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    reread = json.loads(args.output.read_text())
    assert reread == report and args.output.stat().st_size > 0
    print(json.dumps({"receipt": str(args.output), "sites": len(report["feature_audit_sites"]),
                      "public_members": len(report["public_members"]),
                      "manifest_matches": report["retained_manifest_semantics_match"]}))


if __name__ == "__main__":
    main()
