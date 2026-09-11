"""Count reviewed records per Mech and merged pull requests per repository.

Run from the site root: `python3 scripts/fleet/mech_stats.py`. Writes
_fleet/data/mech_stats.json, which assemble_page.py substitutes into the stat
strip and the Mech cards. Needs the checkouts (see roots.py) and a `gh` that
can read the CultureBotAI repositories; pass --no-prs to recount records only
and keep the pull-request numbers already on file.

Two facts per Mech, and they come from different places:

- Reviewed records are counted here, from the same record files the rest of the
  pipeline reads. Whether a Mech tracks review at all is decided by its LinkML
  schema, not by the values its records happen to carry: six declare a status
  slot whose enum permits REVIEWED, and for those a count of zero is a real
  zero. MediaIngredientMech and CultureMech do have a mapping_status, but its
  enum runs UNMAPPED to AMBIGUOUS and never reaches REVIEWED, so it grades
  mapping completeness rather than review; CommunityMech has no such slot.
  Those three are recorded as null rather than zero, because "nobody has
  reviewed one" and "this Mech does not track review" are different claims and
  the page should not make the second look like the first.
- Merged pull requests are asked of GitHub, since the local checkout knows only
  the branch it is on. The count is every merged pull request in the
  repository's history, curation and automation alike: seeding runs,
  regeneration and dependency updates land the same way human curation does.
  It measures development activity on a Mech, not how much of it was human.
"""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ModuleNotFoundError:  # the only pipeline script that needs it; see #68
    raise SystemExit(
        "mech_stats.py needs PyYAML to read each Mech's schema and find the slot "
        "that records review. Install it with `pip install pyyaml`."
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roots import ORDER, mech_root, record_paths

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "_fleet", "data", "mech_stats.json")

# The repository name is not always the Mech name: ProteinTraitsMech publishes
# from a lowercase repo, and GitHub redirects the mixed-case form, which the
# search API does not follow.
GH_REPO = {"ProteinTraitsMech": "proteintraitsmech"}

# Top-level only. A nested entry_status or a reviewed: true deeper in the file
# describes one entry inside a record, not the record, and counting those would
# report more reviewed records than a Mech has records.
STATUS = re.compile(r"^(mapping_status|curation_status)\s*:\s*[\"']?([A-Z_]+)[\"']?\s*$", re.M)


def review_slot(mech: str) -> str | None:
    """The record field whose schema enum permits REVIEWED, if the Mech has one.

    Asking the schema rather than the records is what separates a Mech with
    nothing reviewed yet from a Mech that grades something else entirely.
    MediaIngredientMech and CultureMech would otherwise report zero reviewed
    off a mapping_status that cannot take the value.
    """
    root = mech_root(mech)
    slots: dict = {}
    enums: dict = {}
    for path in sorted(glob.glob(os.path.join(root, "src", "**", "schema", "*.yaml"), recursive=True)):
        try:
            doc = yaml.safe_load(open(path, encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        slots.update(doc.get("slots") or {})
        enums.update(doc.get("enums") or {})
        for cls in (doc.get("classes") or {}).values():
            for name, defn in (cls.get("attributes") or {}).items():
                slots.setdefault(name, defn)
    for field in ("mapping_status", "curation_status"):
        defn = slots.get(field)
        rng = defn.get("range") if isinstance(defn, dict) else None
        allowed = (enums.get(rng) or {}).get("permissible_values") or {}
        if "REVIEWED" in allowed:
            return field
    return None


def review_census(mech: str) -> tuple[int, int | None, str | None]:
    """Records, reviewed records, and the field that said so."""
    paths = record_paths(mech)
    field = review_slot(mech)
    if field is None:
        return len(paths), None, None
    reviewed = 0
    for path in paths:
        for key, value in STATUS.findall(open(path, encoding="utf-8", errors="replace").read()):
            if key == field:
                reviewed += value == "REVIEWED"
                break
    return len(paths), reviewed, field


def merged_prs(mech: str) -> int:
    repo = GH_REPO.get(mech, mech)
    out = subprocess.run(
        ["gh", "api", "-X", "GET", "search/issues", "-f",
         f"q=repo:CultureBotAI/{repo} is:pr is:merged", "--jq", ".total_count"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"{mech}: gh could not count merged PRs for {repo}: {out.stderr.strip()}")
    return int(out.stdout.strip())


def main() -> None:
    keep_prs = "--no-prs" in sys.argv
    old = {}
    if keep_prs and os.path.exists(OUT):
        old = {m["mech"]: m for m in json.load(open(OUT))["mechs"]}

    mechs = []
    for name in ORDER:
        records, reviewed, field = review_census(name)
        prs = old[name]["merged_prs"] if keep_prs and name in old else merged_prs(name)
        mechs.append({"mech": name, "repo": GH_REPO.get(name, name), "records": records,
                      "reviewed": reviewed, "status_field": field, "merged_prs": prs})
        shown = "not tracked" if reviewed is None else f"{reviewed:,} reviewed"
        print(f"{name:<22} {records:>8,} records  {shown:<16} {prs:>5,} merged PRs")

    blob = {
        "as_of": _dt.date.today().isoformat(),
        "merged_prs_total": sum(m["merged_prs"] for m in mechs),
        "mechs": mechs,
    }
    json.dump(blob, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"\n{blob['merged_prs_total']:,} merged PRs across {len(mechs)} Mechs -> {OUT}")


if __name__ == "__main__":
    main()
