#!/usr/bin/env python3
"""Run the 2026-11-09 PM X-Mech Suite snapshot update and pipeline.

Purpose: Pin the 14 public Mech corpora and culturebotai-claw at their 2026-11-09 PM
main SHAs, run the PathwayMech canary, and execute the full fleet refresh pipeline.
Inputs: GitHub commits API (`repos/CultureBotAI/<repo>/commits/main`), local Mech
clones under `/Users/marcin/Documents/VIMSS/ontology/Mechs`, and snapshot directory.
Outputs: `$SNAP/revisions.json`, `$SNAP/*.log`, and updated JSON artifacts in `_fleet/data/`.
Serves: PR #554 / Issue #557.
Date: 2026-11-09.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO_ROOT = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")
SRC_ROOT = Path("/Users/marcin/Documents/VIMSS/ontology/Mechs")
SCRATCH = Path("/Users/marcin/.gemini/antigravity-cli/brain/fce06610-c3eb-40c8-ab6b-48056807ad41/scratch")
OLD_SNAP = SCRATCH / "xmech-refresh-20261109"
SNAP_DIR = SCRATCH / "xmech-refresh-20261109-pm"
MECHS_SNAP = SNAP_DIR / "mechs"
CLAW_SNAP = SNAP_DIR / "claw"


def run(cmd, **kwargs):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def check_output(cmd, **kwargs):
    return subprocess.check_output(cmd, text=True, **kwargs).strip()


def main():
    SNAP_DIR.mkdir(exist_ok=True)
    if not MECHS_SNAP.exists() and (OLD_SNAP / "mechs").exists():
        shutil.move(str(OLD_SNAP / "mechs"), str(MECHS_SNAP))
    if not CLAW_SNAP.exists() and (OLD_SNAP / "claw").exists():
        shutil.move(str(OLD_SNAP / "claw"), str(CLAW_SNAP))

    old_revisions = json.loads((OLD_SNAP / "revisions.json").read_text())
    claw_sha = check_output(["gh", "api", "repos/CultureBotAI/culturebotai-claw/commits/main", "--jq", ".sha"])
    print(f"CLAW main SHA: {claw_sha}", flush=True)
    run(["git", "-C", str(CLAW_SNAP), "fetch", "-q", "--depth", "1",
         "https://github.com/CultureBotAI/culturebotai-claw.git", claw_sha])
    run(["git", "-C", str(CLAW_SNAP), "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"])
    run([sys.executable, str(REPO_ROOT / "scripts/fleet/refresh_manifest.py"), "--claw-root", str(CLAW_SNAP)])

    pinned_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    revisions = {"pinned_at_utc": pinned_at, "claw": claw_sha, "mechs": {}}

    for mech, prev in old_revisions["mechs"].items():
        repo = prev["repo"]
        gh_sha = check_output(["gh", "api", f"repos/CultureBotAI/{repo}/commits/main", "--jq", ".sha"])
        src_mech = SRC_ROOT / mech
        snap_mech = MECHS_SNAP / mech
        cur_sha = check_output(["git", "-C", str(snap_mech), "rev-parse", "HEAD"])
        if cur_sha != gh_sha:
            print(f"Updating {mech}: {cur_sha[:7]} -> {gh_sha[:7]}", flush=True)
            run(["git", "-C", str(src_mech), "fetch", "-q", "origin"])
            origin_sha = check_output(["git", "-C", str(src_mech), "rev-parse", "origin/main"])
            if origin_sha != gh_sha:
                raise RuntimeError(f"{mech}: origin/main {origin_sha} != GitHub {gh_sha}")
            run(["git", "-C", str(snap_mech), "checkout", "-q", "--detach", gh_sha])
        commit_date = check_output(["git", "-C", str(snap_mech), "log", "-1", "--format=%cI", gh_sha])
        revisions["mechs"][mech] = {
            "repo": repo,
            "sha": gh_sha,
            "commit_date": commit_date,
        }

    (SNAP_DIR / "revisions.json").write_text(json.dumps(revisions, indent=2) + "\n")
    print("Wrote updated revisions.json:", pinned_at, flush=True)

    # Step 3: Free checks before any scan
    os.environ["MECHS_ROOT"] = str(MECHS_SNAP)
    sys.path.insert(0, str(REPO_ROOT / "scripts/fleet"))
    import roots
    for mech, info in revisions["mechs"].items():
        rev = roots.revision(mech)
        if rev != info["sha"]:
            raise RuntimeError(f"{mech}: expected {info['sha']}, got {rev}")
    print("All 14 Mech snapshots verified clean at their pins.", flush=True)

    # Step 4: Canary first (PathwayMech record count + revision + prefix regex), then pipeline
    import prefix_census
    canary_paths = roots.record_paths("PathwayMech")
    canary_rev = roots.revision("PathwayMech", canary_paths)
    canary_docs = sum(1 for _, text in roots.record_documents("PathwayMech", canary_paths) if prefix_census.rx.search(text))
    if canary_rev != revisions["mechs"]["PathwayMech"]["sha"] or canary_docs < 1:
        raise RuntimeError(f"Canary failed: PathwayMech rev={canary_rev}, docs={canary_docs}")
    (SNAP_DIR / "prefix_census-canary.log").write_text(
        f"Canary PathwayMech OK: rev={canary_rev} files={len(canary_paths)} matched_docs={canary_docs}\n"
    )
    print(f"Canary PathwayMech OK: rev={canary_rev[:7]} files={len(canary_paths)}", flush=True)

    env = os.environ.copy()
    env["MECHS_ROOT"] = str(MECHS_SNAP)
    stages = [
        ("prefix_census.py", "prefix_census.log"),
        ("build_subsets.py", "build_subsets.log"),
        ("build_cells.py", "build_cells.log"),
        ("recent_terms.py", "recent_terms.log"),
        ("build_data.py", "build_data.log"),
        ("mech_stats.py", "mech_stats.log"),
    ]
    for script, log_name in stages:
        print(f"=== Running {script} ===", flush=True)
        log_path = SNAP_DIR / log_name
        with log_path.open("w", encoding="utf-8") as log_file:
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts/fleet" / script)],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log_file.write(proc.stdout)
            print(proc.stdout, end="", flush=True)
            if proc.returncode != 0:
                raise RuntimeError(f"{script} failed with exit code {proc.returncode}")

    print("=== 2026-11-09 PM pipeline complete ===", flush=True)


if __name__ == "__main__":
    main()
