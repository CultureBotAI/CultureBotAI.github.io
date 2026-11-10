#!/usr/bin/env python3
"""Verify all XREF files at exact 2026-11-09 PM SHA pins using git show.

Purpose: Confirm every GitHub blob URL and `#L...` line anchor in `_fleet/mechs_template.md`
and `_fleet/fleet_fragment.html` resolves at the new 2026-11-09 PM repository pins.
Inputs: `_fleet/mechs_template.md`, `_fleet/fleet_fragment.html`, `$SNAP/revisions.json`, `$SNAP/mechs/*`.
Outputs: Console verification report of all blob URLs and line ranges.
Serves: PR #554 / Issue #557.
Date: 2026-11-09.
"""
import json
import os
from pathlib import Path
import re
import subprocess

SNAP_DIR = Path("/Users/marcin/.gemini/antigravity-cli/brain/fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm")
MECHS_SNAP = SNAP_DIR / "mechs"
REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")


def main():
    revs = json.loads((SNAP_DIR / "revisions.json").read_text())["mechs"]

    env = os.environ.copy()
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"

    for fname in ["_fleet/mechs_template.md", "_fleet/fleet_fragment.html"]:
        content = (REPO / fname).read_text(encoding="utf-8")
        urls = re.findall(
            r"https://github\.com/CultureBotAI/([^/]+)/blob/[0-9a-f]{40}/([^#\"')]+)(#L\d+(?:-L\d+)?)?",
            content,
        )
        print(f"=== Checking {len(urls)} blob links in {fname} at new pins ===")
        for repo_name, rel_path, line_ref in urls:
            mech_dir_name = "ProteinTraitsMech" if repo_name == "proteintraitsmech" else repo_name
            sha = revs[mech_dir_name]["sha"]
            repo_dir = MECHS_SNAP / mech_dir_name
            res = subprocess.run(
                ["git", "-C", str(repo_dir), "show", f"{sha}:{rel_path}"],
                env=env,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                print(f"  MISSING AT NEW PIN {mech_dir_name}@{sha[:7]}:{rel_path} -> {res.stderr.strip()}")
                continue
            if line_ref:
                lines = res.stdout.splitlines()
                m = re.match(r"#L(\d+)(?:-L(\d+))?", line_ref)
                l1 = int(m.group(1))
                l2 = int(m.group(2)) if m.group(2) else l1
                snippet = " | ".join(lines[max(0, l1 - 1):min(len(lines), l2)])
                print(f"  OK {repo_name}@{sha[:7]}:{rel_path}{line_ref}: {snippet[:100]}")


if __name__ == "__main__":
    main()
