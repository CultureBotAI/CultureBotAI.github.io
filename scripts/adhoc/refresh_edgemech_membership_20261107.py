#!/usr/bin/env python3
"""Refresh only CLAW membership/audit provenance for site #540, 2026-11-07.

Input: explicit CLAW checkout at the reviewed feature pin. Outputs: committed
manifest snapshot and its CLAW-only audit note. Historical corpus data stays intact.
Run while holding the companion-site source-edit lease through CLAW.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from refresh_manifest import ARTIFACT_PATH, MANIFEST_PATH, project

PIN = "64cd157ecd37cbd5a1550465d89eb804c5b59409"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    args = parser.parse_args()
    def pinned_file(path):
        return subprocess.check_output(["git", "-C", str(args.claw_root), "show", f"{PIN}:{path}"], text=True)
    snapshot = project(yaml.safe_load(pinned_file(MANIFEST_PATH)),
                       json.loads(pinned_file(ARTIFACT_PATH)), PIN)
    if "EdgeMech" not in snapshot["mechs"]:
        raise ValueError("Expected the reviewed EdgeMech registration pin")
    note = (
        f"The {PIN[:7]} canonical snapshot declares {len(snapshot['mechs'])} members, "
        f"{snapshot['artifact_count']} governed artifacts and "
        f"{len(snapshot['capability_catalogue'])} capabilities per member. "
        "This November 7 membership-only update adds EdgeMech as curation infrastructure; "
        "it does not add a scientific corpus, published browser, record count or historical "
        "PR total. The fourteen-corpus November 4 census, cards, source pins and website "
        "feature verdicts remain unchanged. Capability tooltips preserve canonical "
        "statuses and reasons; inherited native review is not independent scientific approval."
    )
    manifest_path = ROOT / "_fleet/data/manifest.json"
    manifest_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    notes_path = ROOT / "_fleet/audit_notes.json"
    notes = json.loads(notes_path.read_text())
    notes["notes"]["culturebotai-claw"] = note
    notes_path.write_text(json.dumps(notes, indent=2) + "\n")
    audit_path = ROOT / "_fleet/data/site_audit.json"
    audit = json.loads(audit_path.read_text())
    rows = [row for row in audit["repositories"] if row["repo"] == "culturebotai-claw"]
    if len(rows) != 1:
        raise ValueError("Expected one CLAW audit row")
    rows[0].update(
        sha=PIN,
        commit_date=subprocess.check_output(
            ["git", "-C", str(args.claw_root), "show", "-s", "--format=%cI", PIN], text=True
        ).strip(),
        readme_url=f"https://github.com/CultureBotAI/culturebotai-claw/blob/{PIN}/README.md",
        notes=note,
    )
    audit_path.write_text(json.dumps(audit, indent=1, ensure_ascii=False) + "\n")
    print(f"Updated membership and CLAW-only audit provenance at {PIN}")


if __name__ == "__main__":
    main()
