"""Separately pinned introductions that are not part of the dated fleet census.

The site may introduce a project before CLAW admits it or a corpus scan measures
it. These entries add neither capability declarations nor invented zero counts.
"""
import datetime
import json
from pathlib import Path
import re

PATH = Path(__file__).resolve().parents[2] / "_fleet/data/additions.json"


def validate(additions):
    for name, entry in additions.items():
        if entry.get("repo") != name or not re.fullmatch(r"[0-9a-f]{40}", entry.get("sha", "")):
            raise ValueError(f"{name}: invalid addition provenance")
        pinned = datetime.datetime.fromisoformat(entry["pinned_at_utc"])
        committed = datetime.datetime.fromisoformat(entry["commit_date"].replace("Z", "+00:00"))
        if not pinned.tzinfo or committed > pinned or pinned > datetime.datetime.now(datetime.timezone.utc):
            raise ValueError(f"{name}: invalid addition pin time")
        count = entry.get("figure_at_pin")
        if count is None:
            if not entry.get("status_label") or not entry.get("notes"):
                raise ValueError(f"{name}: an uncounted introduction needs a status and explanation")
        elif type(count) is not int or count < 0 or len(entry.get("source", [])) != 3:
            raise ValueError(f"{name}: invalid addition count or source")


def load():
    additions = json.loads(PATH.read_text())
    validate(additions)
    return additions


def uncounted(additions):
    return {name for name, entry in additions.items() if entry["figure_at_pin"] is None}
