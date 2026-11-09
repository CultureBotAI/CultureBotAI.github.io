#!/usr/bin/env python3
"""Compare 2026-11-08 deployed revisions in site_features.json against 2026-11-09 pins and live deployments.

Inputs: _fleet/data/site_features.json, $SNAP/revisions.json, $SNAP/mechs/*, and optionally GitHub Pages API + HEAD requests.
Outputs: _fleet/reviews/refresh-20261109/site-deployment-diffs.json.
Date: 2026-11-09; serves X-Mech Suite November 9 refresh PR.
"""
import argparse
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
GIT_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
    XDG_CONFIG_HOME="/tmp",
)
GH_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
)


def git_out(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, env=GIT_ENV)


def check_live_deployment(repo_name: str, site_url: str) -> dict:
    deps = json.loads(
        subprocess.check_output(
            ["gh", "api", f"repos/CultureBotAI/{repo_name}/deployments?environment=github-pages&per_page=1"],
            text=True,
            env=GH_ENV,
        )
    )
    dep = deps[0]
    statuses = json.loads(
        subprocess.check_output(
            ["gh", "api", f"repos/CultureBotAI/{repo_name}/deployments/{dep['id']}/statuses?per_page=1"],
            text=True,
            env=GH_ENV,
        )
    )
    st = statuses[0]
    req = urllib.request.Request(site_url, method="HEAD", headers={"User-Agent": "CultureBotAI-FleetCheck/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        last_mod = resp.headers.get("Last-Modified")
        http_status = resp.status
    mod_dt = email.utils.parsedate_to_datetime(last_mod)
    created_dt = dt.datetime.fromisoformat(dep["created_at"].replace("Z", "+00:00"))
    return {
        "id": dep["id"],
        "sha": dep["sha"],
        "created_at": dep["created_at"],
        "state": st["state"],
        "status_created_at": st["created_at"],
        "environment_url": st.get("environment_url"),
        "site_url": site_url,
        "http_status": http_status,
        "last_modified": last_mod,
        "served_not_older_than_request": mod_dt >= created_dt,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--live", action="store_true", help="Also query GitHub deployments API and HEAD live sites")
    args = ap.parse_args()

    sf = json.loads((ROOT / "_fleet/data/site_features.json").read_text())
    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]

    report = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mechs": {},
    }

    for mech, entry in sf["mechs"].items():
        old_dep = entry["deployed_revision"]
        pin_sha = pins[mech]["sha"]
        repo_name = pins[mech]["repo"]
        clone = args.snapshot / "mechs" / mech

        live_info = None
        target_sha = pin_sha
        if args.live:
            live_info = check_live_deployment(repo_name, entry["site"])
            if live_info["state"] == "success" and live_info["served_not_older_than_request"]:
                target_sha = live_info["sha"]
            else:
                target_sha = old_dep

        has_old = subprocess.run(
            ["git", "-C", str(clone), "cat-file", "-e", f"{old_dep}^{{commit}}"],
            env=GIT_ENV,
            capture_output=True,
        ).returncode == 0
        has_target = subprocess.run(
            ["git", "-C", str(clone), "cat-file", "-e", f"{target_sha}^{{commit}}"],
            env=GIT_ENV,
            capture_output=True,
        ).returncode == 0

        diff_files = []
        commits = []
        if has_old and has_target:
            if old_dep != target_sha:
                for line in git_out(clone, "diff", "--name-status", old_dep, target_sha).splitlines():
                    parts = line.split("\t")
                    diff_files.append({"status": parts[0], "path": parts[-1]})
                for line in git_out(clone, "log", "--oneline", f"{old_dep}..{target_sha}").splitlines():
                    commits.append(line)

        groups = {}
        for item in diff_files:
            top = "/".join(item["path"].split("/")[:2])
            groups[top] = groups.get(top, 0) + 1

        report["mechs"][mech] = {
            "repo": repo_name,
            "site": entry["site"],
            "prior_deployed_revision": old_dep,
            "pin_sha": pin_sha,
            "target_sha": target_sha,
            "changed_since_prior_deployment": old_dep != target_sha,
            "has_old_in_clone": has_old,
            "has_target_in_clone": has_target,
            "commit_count": len(commits),
            "commits": commits[:30],
            "changed_file_count": len(diff_files),
            "changed_file_groups": groups,
            "live_deployment": live_info,
        }

    out = ROOT / "_fleet/reviews/refresh-20261109/site-deployment-diffs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    for mech, r in report["mechs"].items():
        print(
            f"{mech}: old={r['prior_deployed_revision'][:7]} pin={r['pin_sha'][:7]} "
            f"target={r['target_sha'][:7]} commits={r['commit_count']} files={r['changed_file_count']} groups={r['changed_file_groups']}"
        )


if __name__ == "__main__":
    main()
