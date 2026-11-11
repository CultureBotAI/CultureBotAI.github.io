#!/usr/bin/env python3
"""
Purpose: Pin culturebotai-claw and all 16 public corpus Mechs at their current
         GitHub main revisions on 2026-11-11, fetch new objects into the shared
         source checkouts, detach-checkout the scratch snapshot at the new pins,
         verify clean revisions via roots.revision(), and write revisions.json.
Inputs:  GitHub API (repos/CultureBotAI/<repo>/commits/main), shared checkouts
         under /Users/marcin/Documents/VIMSS/ontology/Mechs, and scratch
         snapshot under scratch/xmech-refresh-20261109-pm.
Outputs: Updated scratch/xmech-refresh-20261109-pm/revisions.json and verified
         detached checkouts.
Date:    2026-11-11
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")
sys.path.insert(0, str(REPO / "scripts/fleet"))
import roots

SRC = Path("/Users/marcin/Documents/VIMSS/ontology/Mechs")
SNAP = Path(
    "/Users/marcin/.gemini/antigravity-cli/brain/"
    "fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261109-pm"
)
GH_REPO = {"ProteinTraitsMech": "proteintraitsmech"}


def run_cmd(cmd: list[str], cwd: Path | None = None) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    out = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, env=env
    )
    if out.returncode != 0:
        raise SystemExit(
            f"Command failed ({' '.join(cmd)} in {cwd}): {out.stderr.strip()}"
        )
    return out.stdout.strip()


def gh_main_sha(repo: str) -> str:
    out = subprocess.run(
        ["gh", "api", f"repos/CultureBotAI/{repo}/commits/main", "--jq", ".sha"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"gh api failed for {repo}: {out.stderr.strip()}")
    sha = out.stdout.strip()
    if len(sha) != 40:
        raise SystemExit(f"Unexpected SHA for {repo}: {sha}")
    return sha


def main() -> None:
    pinned_at_utc = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
    claw_sha = gh_main_sha("culturebotai-claw")
    claw_dir = SNAP / "claw"
    run_cmd(
        [
            "git",
            "fetch",
            "-q",
            "--depth",
            "1",
            "https://github.com/CultureBotAI/culturebotai-claw.git",
            claw_sha,
        ],
        cwd=claw_dir,
    )
    run_cmd(
        ["git", "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"],
        cwd=claw_dir,
    )
    print(f"CLAW pinned at {claw_sha}")

    old_rev_file = SNAP / "revisions.json"
    old_revs = (
        json.loads(old_rev_file.read_text()).get("mechs", {})
        if old_rev_file.exists()
        else {}
    )

    mechs_out: dict[str, dict[str, str]] = {}
    os.environ["MECHS_ROOT"] = str(SNAP / "mechs")
    roots.MECHS_ROOT = str(SNAP / "mechs")

    for mech in roots.ORDER:
        repo = GH_REPO.get(mech, mech)
        sha = gh_main_sha(repo)
        old_sha = (old_revs.get(mech) or {}).get("sha")
        snap_mech = SNAP / "mechs" / mech
        src_mech = SRC / mech
        if sha != old_sha:
            if src_mech.is_dir():
                run_cmd(["git", "fetch", "-q", "origin"], cwd=src_mech)
            else:
                run_cmd(
                    [
                        "git",
                        "fetch",
                        "-q",
                        f"https://github.com/CultureBotAI/{repo}.git",
                        sha,
                    ],
                    cwd=snap_mech,
                )
            run_cmd(["git", "checkout", "-q", "--detach", sha], cwd=snap_mech)
        cdate = run_cmd(
            ["git", "log", "-1", "--format=%cI", sha], cwd=snap_mech
        )
        ver = roots.revision(mech)
        if ver != sha:
            raise SystemExit(
                f"{mech}: revision() returned {ver!r}, expected clean {sha!r}"
            )
        status_note = "MOVED" if sha != old_sha else "unchanged"
        print(
            f"  {mech:20s} {sha[:7]} ({cdate}) [{status_note}]"
        )
        mechs_out[mech] = {
            "repo": repo,
            "sha": sha,
            "commit_date": cdate,
        }

    revs_payload = {
        "pinned_at_utc": pinned_at_utc,
        "mechs": mechs_out,
        "claw": claw_sha,
    }
    old_rev_file.write_text(json.dumps(revs_payload, indent=2) + "\n")
    print(f"Wrote {old_rev_file} (pinned_at_utc={pinned_at_utc})")


if __name__ == "__main__":
    main()
