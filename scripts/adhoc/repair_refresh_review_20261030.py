#!/usr/bin/env python3
"""Verify and repair refresh review findings #528-530, 2026-10-30.

Inputs: immutable baseline commit, existing pinned Mech snapshot, PR527 files.
Outputs: verified XREF pin updates, supported feature baseline, count evidence.
Default is dry-run; --apply writes only the two maintained sources and feature
audit. The normal builders remain responsible for generated site output.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "de11a2ce0816ff71d5914eee10310a8c3da86cde"
PATHS = ("_fleet/mechs_template.md", "_fleet/fleet_fragment.html")


def blob(root, revision, path):
    return subprocess.check_output(["git", "-C", str(root), "show", f"{revision}:{path}"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    old = json.loads(blob(ROOT, BASE, "_fleet/data/mech_stats.json"))
    new = json.loads((ROOT / "_fleet/data/mech_stats.json").read_text())
    by_repo = {row["repo"]: row for row in new["mechs"]}
    replacements = {}
    changed = {}
    for path in PATHS:
        original = (ROOT / path).read_text()
        rewritten = original
        for row in old["mechs"]:
            previous = row["source_revision"]
            current = by_repo[row["repo"]]["source_revision"]
            if previous == current or previous not in original:
                continue
            pattern = rf"https://github\.com/CultureBotAI/{re.escape(row['repo'])}/blob/{previous}/([^\s\"'#<>]+)"
            evidence_paths = set(re.findall(pattern, original))
            evidence_paths.update(re.findall(rf"([A-Za-z0-9_./-]+)@{previous}", original))
            if not evidence_paths:
                raise ValueError(f"no evidence URLs for {row['repo']} in {path}")
            checkout = args.snapshot / "mechs" / row["mech"]
            for evidence in sorted(evidence_paths):
                before = blob(checkout, previous, evidence)
                after = blob(checkout, current, evidence)
                if before != after:
                    raise ValueError(f"evidence changed: {row['repo']}:{evidence}")
                print(f"UNCHANGED evidence: {row['repo']}:{evidence}")
            replacements[previous] = current
            rewritten = rewritten.replace(previous, current)
        changed[path] = rewritten
    features = blob(ROOT, BASE, "_fleet/data/site_features.json")
    notes_path = ROOT / "_fleet/audit_notes.json"
    notes = json.loads(notes_path.read_text())
    old_scope = "Website features were reassessed on live sites independently of source pins, using headless Chrome and successful deployment statuses."
    new_scope = "Website feature verdicts retain their separately recorded October 26, 2026 browser-audit baseline. This corpus refresh and the October 30 deployment-freshness check do not constitute a new feature-by-feature browser review."
    if old_scope not in notes["scope"] and new_scope not in notes["scope"]:
        raise ValueError("unexpected website-feature audit scope")
    notes["scope"] = notes["scope"].replace(old_scope, new_scope)
    if args.apply:
        for path, content in changed.items():
            (ROOT / path).write_text(content)
        (ROOT / "_fleet/data/site_features.json").write_bytes(features)
        notes_path.write_text(json.dumps(notes, indent=2) + "\n")
    print(f"{'Applied' if args.apply else 'Planned'} {len(replacements)} pin mappings; feature audit retains its supported baseline.")
    print(f"Repository-record total: {sum(row['records'] for row in new['mechs']):,}")
    old_prs = {row['repo']: row['merged_prs'] for row in old['mechs'] + old['additional_repositories']}
    print("| Repository | Previous merged PRs | Snapshot merged PRs |")
    print("| --- | ---: | ---: |")
    for row in new['mechs'] + new['additional_repositories']:
        print(f"| {row['repo']} | {old_prs[row['repo']]:,} | {row['merged_prs']:,} |")
    total = sum(row['merged_prs'] for row in new['mechs'] + new['additional_repositories'])
    assert total == new['merged_prs_total']
    print(f"Merged PR total: {old['merged_prs_total']:,} -> {total:,}")


if __name__ == "__main__":
    main()
