#!/usr/bin/env python3
"""Restore evidenced website observations while retaining the new-site audits.

Inputs: verified PR 570 feature snapshot at e6c8cbf; combined refresh sources.
Output: _fleet/data/site_features.json, preserving Nov 9 and Nov 12 audit dates.
Serves: issue #571 and the November 12 refresh PR. Date: 2026-11-12.
"""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "e6c8cbf084418de4d6675d361e83105f50015081"
path = ROOT / "_fleet/data/site_features.json"
verified = subprocess.check_output(
    ["git", "show", f"{SOURCE}:_fleet/data/site_features.json"], cwd=ROOT
)
data = json.loads(verified)
assert data["checked_on"] == "2026-11-09"
for mech in ("CofactorMech", "AssayMech"):
    assert data["mechs"][mech]["checked_on"] == "2026-11-12"
path.write_bytes(verified)
