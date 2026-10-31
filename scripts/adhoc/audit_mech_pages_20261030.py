#!/usr/bin/env python3
"""Audit published Mech Pages freshness, 2026-10-30.

Inputs: inventory JSON from the pinned claw fleet CLI; GitHub read-only APIs.
Outputs: one evidence JSON and workflow source directory per selected Mech.
Serves the fleet Pages refresh PR; never dispatches workflows or edits records.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import re
import subprocess
import urllib.request
from pathlib import Path


def api(path):
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
    if proc.returncode:
        raise RuntimeError(f"{path}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def paginated(path):
    rows = []
    for page in range(1, 100):
        batch = api(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise RuntimeError(f"pagination limit: {path}")


def deployment_succeeded(statuses):
    # GitHub returns deployment statuses newest first (#531).
    return bool(statuses) and statuses[0].get("state") == "success"


def audit_verified(row):
    live = row.get("live") or {}
    return bool(
        not row.get("error")
        and row.get("successful_deployment")
        and not live.get("error")
        and 200 <= live.get("status", 0) < 400
    )


def audit(mech, output):
    repo = mech["github"]
    prefix = f"repos/{repo}"
    row = {"repository": repo, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    target = output / mech["key"]
    target.mkdir(parents=True, exist_ok=True)
    try:
        metadata = api(prefix)
        if metadata["full_name"].lower() != repo.lower():
            raise RuntimeError("repository identity changed")
        row["default_branch"] = metadata["default_branch"]
        row["main"] = api(f"{prefix}/commits/{row['default_branch']}")["sha"]
        row["pages"] = api(f"{prefix}/pages")
        deployments = api(f"{prefix}/deployments?environment=github-pages&per_page=30")
        row["deployments"] = []
        success = None
        for deployment in deployments:
            statuses = api(f"{prefix}/deployments/{deployment['id']}/statuses?per_page=10")
            brief = {k: deployment[k] for k in ("id", "sha", "created_at")}
            brief["statuses"] = [{k: s.get(k) for k in ("state", "created_at", "environment_url", "log_url", "description")} for s in statuses]
            row["deployments"].append(brief)
            if deployment_succeeded(statuses):
                success = brief
                break
        row["successful_deployment"] = success
        if success and success["sha"] != row["main"]:
            compare = api(f"{prefix}/compare/{success['sha']}...{row['main']}")
            row["difference"] = {k: compare[k] for k in ("status", "ahead_by", "behind_by", "total_commits")}
            row["difference"]["files"] = [{k: f.get(k) for k in ("filename", "status", "additions", "deletions")} for f in compare.get("files", [])]
            row["difference"]["files_may_be_capped"] = len(compare.get("files", [])) >= 300
        workflows = api(f"{prefix}/actions/workflows?per_page=100")["workflows"]
        row["workflows"] = []
        for workflow in workflows:
            if not re.search(r"pages|deploy|documentation|docs", workflow["name"] + workflow["path"], re.I):
                continue
            brief = {k: workflow[k] for k in ("id", "name", "path", "state")}
            runs = api(f"{prefix}/actions/workflows/{workflow['id']}/runs?per_page=5&branch={row['default_branch']}")["workflow_runs"]
            brief["runs"] = [{k: run.get(k) for k in ("id", "status", "conclusion", "head_sha", "event", "created_at", "html_url")} for run in runs]
            if workflow["path"].startswith(".github/"):
                source = api(f"{prefix}/contents/{workflow['path']}?ref={row['main']}")
                (target / Path(workflow["path"]).name).write_bytes(base64.b64decode(source["content"]))
            row["workflows"].append(brief)
        row["open_prs"] = [{k: p.get(k) for k in ("number", "title", "html_url", "body")} for p in paginated(f"{prefix}/pulls?state=open")]
        issues = paginated(f"{prefix}/issues?state=open")
        row["site_issues"] = [{k: i.get(k) for k in ("number", "title", "html_url", "body")} for i in issues if "pull_request" not in i and re.search(r"pages|website|deployment|browser|site|html", i["title"], re.I)]
        url = row["pages"]["html_url"]
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mech-Pages-Freshness-Audit"})
            with urllib.request.urlopen(request, timeout=45) as response:
                html = response.read(300000)
                row["live"] = {"url": response.url, "status": response.status, "last_modified": response.headers.get("Last-Modified"), "github_request_id": response.headers.get("X-GitHub-Request-Id"), "bytes_read": len(html)}
                (target / "live-root.html").write_bytes(html)
        except Exception as exc:
            row["live"] = {"url": url, "error": str(exc)}
    except Exception as exc:
        row["error"] = str(exc)
    path = target / "audit.json"
    path.write_text(json.dumps(row, indent=2) + "\n")
    assert path.stat().st_size > 0
    print(json.dumps({"repository": repo, "main": row.get("main"), "deployed": (row.get("successful_deployment") or {}).get("sha"), "difference": {k: v for k, v in row.get("difference", {}).items() if k != "files"}, "live": row.get("live"), "error": row.get("error")}), flush=True)
    return audit_verified(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", action="append")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    selected = [m for m in inventory if not args.only or m["key"] in args.only]
    if not selected or (args.only and set(args.only) != {m["key"] for m in selected}):
        parser.error("selection does not match fleet inventory")
    results = [audit(mech, args.output) for mech in selected]
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
