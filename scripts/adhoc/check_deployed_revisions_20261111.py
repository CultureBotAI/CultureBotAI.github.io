#!/usr/bin/env python3
"""
Purpose: Verify the latest successful github-pages deployment SHA and HTTP
         Last-Modified header for each deployed site in _fleet/data/site_features.json,
         and inspect any feature notes that mention record/category counts.
Inputs:  GitHub Pages deployments API, live HTTP HEAD requests, and
         _fleet/data/site_features.json.
Outputs: Console table of verified deployed_revision SHAs and note matches.
Date:    2026-11-11
"""

from __future__ import annotations

import email.utils
import json
import re
import subprocess
import urllib.request
from pathlib import Path

REPO = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")
SF_PATH = REPO / "_fleet/data/site_features.json"


def gh_json(endpoint: str):
    out = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout)


def head_last_modified(url: str) -> str | None:
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "culturebotai-site-check"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.headers.get("Last-Modified")


def main() -> None:
    sf = json.loads(SF_PATH.read_text())
    for mech, entry in sf["mechs"].items():
        site = entry.get("site")
        if not site:
            print(f"{mech:20s}: no site")
            continue
        repo = entry["repository"].rsplit("/", 1)[-1]
        old_sha = entry.get("deployed_revision", "")
        deps = gh_json(
            f"repos/CultureBotAI/{repo}/deployments?environment=github-pages&per_page=5"
        )
        verified_sha = old_sha
        dep_created = None
        dep_state = None
        for d in deps:
            did = d["id"]
            statuses = gh_json(
                f"repos/CultureBotAI/{repo}/deployments/{did}/statuses?per_page=1"
            )
            st = statuses[0]["state"] if statuses else "none"
            if dep_state is None:
                dep_state = st
            if st == "success":
                verified_sha = d["sha"]
                dep_created = d["created_at"]
                break
        lm = head_last_modified(site)
        print(
            f"{mech:20s}: old={old_sha} -> latest_success={verified_sha} "
            f"(top_state={dep_state}, created={dep_created}, Last-Modified={lm})"
        )
        # Check for numeric counts in feature notes for CMMMech, HabitatMech, CommunityMech
        if mech in ("CMMMech", "HabitatMech", "CommunityMech", "TaxonMech"):
            for feat, fobj in (entry.get("features") or {}).items():
                note = fobj.get("note", "")
                if re.search(r"\b(708|457|208|1,298|1,911|2,147|535|549)\b", note):
                    print(f"  [{mech}.{feat}] note match: {note}")


if __name__ == "__main__":
    main()
