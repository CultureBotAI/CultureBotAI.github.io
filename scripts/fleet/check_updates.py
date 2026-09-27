"""Report what an X-Mech page refresh would change, without doing one.

Run from the site root: `python3 scripts/fleet/check_updates.py`. Read-only: it
reads _fleet/, the live sites and the GitHub API, clones CLAW shallowly into a
temporary directory, and writes nothing in this repository or in the shared Mech
checkouts. The check-xmech-updates skill runs it and then judges the flagged
hand-curated claims; update-xmech-page is what acts on the result.

For each Mech it compares the pin recorded in _fleet/data/site_audit.json with
the repository's main and sorts the files changed since into what they would
move on the page:

  records   files under the census record globs (roots.RECORD_GLOBS): the
            census, overlaps, record lists and stats would change
  claims    files the hand-curated layer cites or describes: the README, the
            schema, the published landing page, and every file an XREFS arrow
            links as its evidence
  other     anything else (review reports, CI, tooling); a Mech that moved only
            here has nothing for a refresh to do

It also runs check_cards.check() for the card figures, refresh_manifest --check
against CLAW's main for membership and capabilities, and a HEAD request for each
XREFS evidence URL.
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import check_cards
from roots import RECORD_GLOBS

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "_fleet/data/site_audit.json"
FRAGMENT = REPO / "_fleet/fleet_fragment.html"
TEMPLATE = REPO / "_fleet/mechs_template.md"
CLAW = "culturebotai-claw"
# The compare API lists at most this many files; past it the split is a floor.
FILE_CAP = 300
CLAIM_PATTERNS = ["README.md", "src/**/schema/*.yaml", "pages/index.html", "docs/index.html",
                  "app/index.html", "index.html"]


def gh(path: str) -> dict:
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def matches(path: str, pattern: str) -> bool:
    """fnmatch with ** spanning directories, as the record globs use it."""
    return fnmatch.fnmatch(path, pattern) or ("/**/" in pattern and fnmatch.fnmatch(path, pattern.replace("/**/", "/")))


def evidence_paths(fragment: str) -> dict[str, set[str]]:
    """Repository -> file paths the XREFS arrows cite as evidence."""
    paths: dict[str, set[str]] = {}
    for repo, path in re.findall(r'url: "https://github\.com/CultureBotAI/([^/]+)/blob/[^/]+/([^"#]+)', fragment):
        paths.setdefault(repo.lower(), set()).add(path)
    return paths


def evidence_urls(fragment: str) -> list[str]:
    return sorted(set(re.findall(r'url: "(https://github\.com/CultureBotAI/[^"]+)"', fragment)))


def classify(mech: str | None, files: list[dict], cited: set[str]) -> dict:
    """Sort changed files into records / claims / other, with record adds and removals."""
    globs = RECORD_GLOBS.get(mech, []) if mech else []
    out = {"records": [], "claims": [], "other": [], "added": 0, "removed": 0}
    for f in files:
        name = f["filename"]
        if any(matches(name, g) for g in globs):
            out["records"].append(name)
            if f["status"] == "added":
                out["added"] += 1
            elif f["status"] == "removed":
                out["removed"] += 1
        elif name in cited or any(matches(name, p) for p in CLAIM_PATTERNS):
            out["claims"].append(name)
        else:
            out["other"].append(name)
    return out


def drift(entry: dict, mech: str | None, cited: set[str], api=gh) -> dict:
    """How far one repository has moved since its pin, and what the moves touch."""
    repo, pin = entry["repo"], entry["sha"]
    compare = api(f"repos/CultureBotAI/{repo}/compare/{pin}...main")
    files = compare.get("files", [])
    row = {"repo": repo, "mech": mech, "pin": pin[:7], "ahead": compare.get("ahead_by", 0),
           "main": (compare.get("commits") or [{"sha": pin}])[-1]["sha"][:7],
           "truncated": len(files) >= FILE_CAP}
    row.update(classify(mech, files, cited))
    return row


def verdict(row: dict) -> str:
    if row["ahead"] == 0:
        return "at pin"
    if row["records"] or row["claims"]:
        parts = []
        if row["records"]:
            changed = len(row["records"]) - row["added"] - row["removed"]
            parts.append(f"records: {row['added']} added, {row['removed']} removed, {changed} edited")
        if row["claims"]:
            parts.append(f"claims: {', '.join(sorted(row['claims'])[:4])}"
                         + (f" +{len(row['claims']) - 4} more" if len(row["claims"]) > 4 else ""))
        return "; ".join(parts) + (" (API lists only 300 files: counts are floors; the card"
                                   " figures below are the live totals)" if row["truncated"] else "")
    return "moved, nothing the page uses" + (" in the first 300 files the API lists; check the rest"
                                             " by hand" if row["truncated"] else "")


def manifest_check() -> str:
    """refresh_manifest --check against CLAW's current main, from a shallow clone."""
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "claw"
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/CultureBotAI/{CLAW}.git",
                        str(clone)], check=True)
        done = subprocess.run([sys.executable, str(REPO / "scripts/fleet/refresh_manifest.py"),
                               "--claw-root", str(clone), "--check"], capture_output=True, text=True, cwd=REPO)
    if "No module named" in done.stderr:
        return (f"NOT CHECKED: {sys.executable} lacks a requirement "
                f"({done.stderr.strip().splitlines()[-1]}); run with python3.12, "
                "which CI uses, or install scripts/fleet/requirements.txt")
    return (done.stdout + done.stderr).strip() or f"exit {done.returncode}"


def dead_links(urls: list[str]) -> list[str]:
    dead = []
    for url in urls:
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="HEAD",
                                   headers={"User-Agent": "culturebotai-update-check"}), timeout=30)
        except urllib.error.HTTPError as error:
            if error.code != 429:
                dead.append(f"{url} ({error.code})")
        except (urllib.error.URLError, TimeoutError, OSError):
            pass  # unreachable is not dead
    return dead


def main() -> int:
    audit = json.loads(AUDIT.read_text())
    fragment = FRAGMENT.read_text()
    cited = evidence_paths(fragment)
    mech_of = {m.lower(): m for m in RECORD_GLOBS} | {"proteintraitsmech": "ProteinTraitsMech"}
    print(f"# X-Mech update check against the pins of {audit['pinned_at_utc']}\n")
    print("## Repositories since their pins\n")
    print("| repository | pin | main | commits | what moved |\n|---|---|---|---:|---|")
    moved = []
    for entry in audit["repositories"]:
        row = drift(entry, mech_of.get(entry["repo"].lower()), cited.get(entry["repo"].lower(), set()))
        moved.append(row)
        print(f"| {row['repo']} | {row['pin']} | {row['main']} | {row['ahead']} | {verdict(row)} |")
    print("\n## Card figures (check_cards)\n")
    for status, mech, detail in check_cards.check(TEMPLATE.read_text(), audit=audit):
        print(f"- {status} {mech} {detail}")
    print("\n## Fleet membership and capabilities (CLAW main)\n")
    print(manifest_check())
    print("\n## XREFS evidence links\n")
    dead = dead_links(evidence_urls(fragment))
    print("\n".join(f"- dead: {d}" for d in dead) or "All resolve.")
    needs = [r["repo"] for r in moved if r["records"] or r["claims"]]
    print(f"\n**Refresh would change:** {', '.join(needs) or 'nothing from the repositories'}"
          f"{'; dead evidence links: ' + str(len(dead)) if dead else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
