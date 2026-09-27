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
            schema, the licence and citation files, the published landing page,
            every file the fleet page or any content page links on GitHub, and
            for CLAW the files that set membership and capabilities
  other     anything else (review reports, CI, tooling); a Mech that moved only
            here has nothing for a refresh to do

It also runs check_cards.check() for the card figures, refresh_manifest --check
against CLAW's main for membership and capabilities, and a HEAD request for each
XREFS evidence URL.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import check_cards
from roots import EXCLUDE_DIRS, RECORD_GLOBS

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "_fleet/data/site_audit.json"
FRAGMENT = REPO / "_fleet/fleet_fragment.html"
TEMPLATE = REPO / "_fleet/mechs_template.md"
CLAW = "culturebotai-claw"
# The compare API lists at most this many files; past it the split is a floor.
FILE_CAP = 300
CLAIM_PATTERNS = ["README.md", "LICENSE*", "CITATION.cff", "src/**/schema/*.yaml",
                  "pages/index.html", "docs/index.html", "app/index.html", "index.html"]
# The files in CLAW that decide membership, capabilities and the vendored
# standard; site_audit.json's CLAW note names the same ones (#288).
CLAW_CLAIMS = ["src/kg_microbe_fleet/fleet.yaml", "vendored_artifacts.json", "docs/guides/MECH_STANDARD.md"]
BLOB = re.compile(r'https://github\.com/CultureBotAI/([^/\s"\')]+)/blob/[^/\s"\')]+/([^\s"\')#?]+)')


class Unchecked(Exception):
    """A GitHub API call that did not answer; reported, never raised past main()."""


def gh(path: str) -> dict:
    done = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if done.returncode != 0:
        raise Unchecked((done.stderr or done.stdout).strip().splitlines()[-1:] or [f"exit {done.returncode}"])
    return json.loads(done.stdout)


def glob_regex(pattern: str) -> re.Pattern:
    """A record glob as glob.glob reads it: * and ? stay within one path segment,
    and a /**/ segment spans zero or more directories (#292)."""
    out = ""
    for part in re.split(r"(/\*\*/|\*|\?)", pattern):
        out += {"/**/": "/(?:[^/]+/)*", "*": "[^/]*", "?": "[^/]"}.get(part, re.escape(part))
    return re.compile(out + r"\Z")


def matches(path: str, pattern: str) -> bool:
    return bool(glob_regex(pattern).match(path))


def is_record(mech: str | None, path: str) -> bool:
    if not mech:
        return False
    if any(path.startswith(d) for d in EXCLUDE_DIRS.get(mech, [])):
        return False
    return any(matches(path, g) for g in RECORD_GLOBS.get(mech, []))


def cited_paths(*texts: str) -> dict[str, set[str]]:
    """Repository (lower-cased) -> file paths linked on GitHub anywhere in the
    given sources: XREFS evidence, card and page links, pinned blob links (#287)."""
    paths: dict[str, set[str]] = {}
    for text in texts:
        for repo, path in BLOB.findall(text):
            paths.setdefault(repo.lower(), set()).add(path.rstrip(".,;:"))
    return paths


def site_sources() -> list[str]:
    """The fleet page's sources and every content page that can cite a Mech file."""
    files = [FRAGMENT, TEMPLATE] + sorted(REPO.glob("*.md"))
    return [f.read_text() for f in files if f.name != "mechs.md"]


def evidence_urls(fragment: str) -> list[str]:
    return sorted(set(re.findall(r'url: "(https://github\.com/CultureBotAI/[^"]+)"', fragment)))


def classify(mech: str | None, files: list[dict], cited: set[str]) -> dict:
    """Sort changed files into records / claims / other, with record adds and removals."""
    out = {"records": [], "claims": [], "other": [], "added": 0, "removed": 0}
    for f in files:
        name = f["filename"]
        if is_record(mech, name):
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
    try:
        compare = api(f"repos/CultureBotAI/{repo}/compare/{pin}...main")
    except (Unchecked, ValueError, OSError) as error:  # #289: one repository, not the report
        return {"repo": repo, "mech": mech, "pin": pin[:7], "ahead": None, "main": "?",
                "unchecked": str(error), "truncated": False, "records": [], "claims": [], "other": [],
                "added": 0, "removed": 0}
    files = compare.get("files", [])
    # The compare API returns the newest 250 commits, oldest first, so the last
    # is main's head even past the cap.
    row = {"repo": repo, "mech": mech, "pin": pin[:7], "ahead": compare.get("ahead_by", 0),
           "main": (compare.get("commits") or [{"sha": pin}])[-1]["sha"][:7],
           "truncated": len(files) >= FILE_CAP, "unchecked": None}
    row.update(classify(mech, files, cited))
    return row


def verdict(row: dict) -> str:
    if row.get("unchecked"):
        return f"UNCHECKED: {row['unchecked']}"
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
        cloned = subprocess.run(["git", "clone", "-q", "--depth", "1",
                                 f"https://github.com/CultureBotAI/{CLAW}.git", str(clone)],
                                capture_output=True, text=True)
        if cloned.returncode != 0:  # #289
            return f"NOT CHECKED: could not clone {CLAW} ({cloned.stderr.strip()})"
        done = subprocess.run([sys.executable, str(REPO / "scripts/fleet/refresh_manifest.py"),
                               "--claw-root", str(clone), "--check"], capture_output=True, text=True, cwd=REPO)
    if "No module named" in done.stderr:
        return (f"NOT CHECKED: {sys.executable} lacks a requirement "
                f"({done.stderr.strip().splitlines()[-1]}); run with python3.12, "
                "which CI uses, or install scripts/fleet/requirements.txt")
    return (done.stdout + done.stderr).strip() or f"exit {done.returncode}"


def dead_links(urls: list[str], opener=urllib.request.urlopen) -> tuple[list[str], list[str]]:
    """(dead, unchecked): a 4xx other than a throttle is dead; a throttle or a
    fetch that did not arrive is unchecked, never counted as resolving (#290)."""
    dead, unchecked = [], []
    for url in urls:
        try:
            opener(urllib.request.Request(url, method="HEAD",
                                          headers={"User-Agent": "culturebotai-update-check"}), timeout=30)
        except urllib.error.HTTPError as error:
            if 400 <= error.code < 500 and error.code not in check_cards.THROTTLES:
                dead.append(f"{url} ({error.code})")
            else:
                unchecked.append(f"{url} ({error.code})")
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            unchecked.append(f"{url} ({error})")
    return dead, unchecked


def summary(rows: list[dict], cards: list[tuple[str, str, str]], manifest: str,
            dead: list[str], unchecked_links: list[str]) -> str:
    """One line naming everything a refresh would change, from every section (#288)."""
    parts = []
    moved = [r["repo"] for r in rows if r["records"] or r["claims"]]
    if moved:
        parts.append("repositories: " + ", ".join(moved))
    behind = [f"{m} ({s})" for s, m, _ in cards if s not in ("ok", "unread")]
    if behind:
        parts.append("cards: " + ", ".join(behind))
    if "stale" in manifest.lower():
        parts.append("fleet membership or capabilities (CLAW manifest)")
    if dead:
        parts.append(f"{len(dead)} dead evidence link(s)")
    not_checked = [r["repo"] for r in rows if r.get("unchecked")]
    if manifest.startswith("NOT CHECKED"):
        not_checked.append("CLAW manifest")
    if unchecked_links:
        not_checked.append(f"{len(unchecked_links)} evidence link(s)")
    line = "**Refresh would change:** " + ("; ".join(parts) if parts else "nothing found") + "."
    if not_checked:
        line += " **Not checked:** " + ", ".join(not_checked) + "."
    return line


def main() -> int:
    audit = json.loads(AUDIT.read_text())
    fragment = FRAGMENT.read_text()
    cited = cited_paths(*site_sources())
    cited.setdefault(CLAW, set()).update(CLAW_CLAIMS)
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
    cards = check_cards.check(TEMPLATE.read_text(), audit=audit)
    for status, mech, detail in cards:
        print(f"- {status} {mech} {detail}")
    print("\n## Fleet membership and capabilities (CLAW main)\n")
    manifest = manifest_check()
    print(manifest)
    print("\n## XREFS evidence links\n")
    urls = evidence_urls(fragment)
    dead, unchecked = dead_links(urls)
    for line in [f"- dead: {d}" for d in dead] + [f"- not checked: {u}" for u in unchecked]:
        print(line)
    print(f"{len(urls) - len(dead) - len(unchecked)} of {len(urls)} distinct links resolve.")
    print("\n" + summary(moved, cards, manifest, dead, unchecked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
