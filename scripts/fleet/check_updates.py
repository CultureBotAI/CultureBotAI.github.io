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
against CLAW's main for membership and capabilities, a HEAD request for each
XREFS evidence URL, and, for the website feature table, which is judged on the
live sites rather than at the pins, whether each Mech site has redeployed since
the deployment its verdicts describe.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import check_cards
from roots import EXCLUDE_DIRS, RECORD_GLOBS

UPDATE_RECORD_GLOBS = RECORD_GLOBS

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "_fleet/data/site_audit.json"
FRAGMENT = REPO / "_fleet/fleet_fragment.html"
TEMPLATE = REPO / "_fleet/mechs_template.md"
FEATURES = REPO / "_fleet/data/site_features.json"
CLAW = "culturebotai-claw"
SITE_REPO = "CultureBotAI/CultureBotAI.github.io"
# The compare API lists at most this many files; past it the split is a floor.
FILE_CAP = 300
CLAIM_PATTERNS = ["README.md", "LICENSE*", "CITATION.cff", "src/**/schema/*.yaml",
                  "pages/index.html", "docs/index.html", "app/index.html", "index.html"]
# DUF freezes each worklist under a new date rather than replacing its source
# file. A new manifest changes the selected family corpus even if its rows match.
MECH_CLAIMS = {"DUFMech": ["data/worklists/interpro-pfam-duf-*.manifest.json"]}
# The files in CLAW that decide membership, capabilities and the vendored
# standard; site_audit.json's CLAW note names the same ones (#288).
CLAW_CLAIMS = ["src/kg_microbe_fleet/fleet.yaml", "vendored_artifacts.json", "docs/guides/MECH_STANDARD.md"]
# Path characters stop at anything Markdown or HTML wraps a link in (#299).
_PATH = r'([^\s"\'()<>|\]`&#?]+)'
BLOB = re.compile(r'https://github\.com/CultureBotAI/([^/\s"\'()<>|\]`&]+)/blob/[^/\s"\'()<>|\]`&]+/' + _PATH)
# A file cited through its Pages URL is served from the repository root or docs/ (#298).
PAGES = re.compile(r'https://culturebotai\.github\.io/([A-Za-z]+)/' + _PATH)


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
    return any(matches(path, g) for g in UPDATE_RECORD_GLOBS.get(mech, []))


def cited_paths(*texts: str) -> dict[str, set[str]]:
    """Repository (lower-cased) -> file paths linked on GitHub anywhere in the
    given sources: XREFS evidence, card and page links, pinned blob links (#287)."""
    paths: dict[str, set[str]] = {}
    def add(repo: str, path: str) -> None:
        path = urllib.parse.unquote(path).rstrip(".,;:")
        if path and not path.endswith("/"):
            paths.setdefault(repo.lower(), set()).add(path)
    for text in texts:
        for repo, path in BLOB.findall(text):
            add(repo, path)
        for repo, path in PAGES.findall(text):
            add(repo, path)
            add(repo, "docs/" + path)
    return paths


def watched(audit: dict, sources: list[str]) -> dict[str, set[str]]:
    """Every file the page's claims rest on, per repository (lower-cased):
    GitHub and Pages links in the sources, each audited data file as served and
    under docs/, card sources, and CLAW's membership files (#287, #288, #298)."""
    urls = [row.get("data_url", "") for row in audit.get("repositories", [])]
    urls.extend(check_cards.source_url(source[1]) for source in check_cards.SOURCES.values())
    cited = cited_paths(*sources, "\n".join(urls))
    for url in urls:
        if url.startswith("https://raw.githubusercontent.com/CultureBotAI/"):
            repo, _, path = url.removeprefix("https://raw.githubusercontent.com/CultureBotAI/").split("/", 2)
            cited.setdefault(repo.lower(), set()).add(path)
    cited.setdefault(CLAW, set()).update(CLAW_CLAIMS)
    return cited


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
        elif name in cited or any(matches(name, p) for p in CLAIM_PATTERNS + MECH_CLAIMS.get(mech, [])):
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
           "truncated": len(files) >= FILE_CAP, "unchecked": None,
           # "behind" or "diverged" means main lost commits the pin had (#300).
           "status": compare.get("status", "ahead"), "behind": compare.get("behind_by", 0)}
    row.update(classify(mech, files, cited))
    return row


def verdict(row: dict) -> str:
    if row.get("unchecked"):
        return f"UNCHECKED: {row['unchecked']}"
    if row.get("status") in ("behind", "diverged"):
        return (f"main is {row['status']} ({row.get('behind', 0)} commits the pin had are gone); "
                "check by hand")
    if row["ahead"] == 0:
        return "at pin"
    if row["records"] or row["claims"]:
        parts = []
        if row["records"]:
            changed = len(row["records"]) - row["added"] - row["removed"]
            unit = "worklist source files" if row.get("mech") == "DUFMech" else "records"
            parts.append(f"{unit}: {row['added']} added, {row['removed']} removed, {changed} edited")
        if row["claims"]:
            parts.append(f"claims: {', '.join(sorted(row['claims'])[:4])}"
                         + (f" +{len(row['claims']) - 4} more" if len(row["claims"]) > 4 else ""))
        return "; ".join(parts) + (" (API lists only 300 files: counts are floors; the card"
                                   " figures below are the live totals)" if row["truncated"] else "")
    return "moved, nothing the page uses" + (" in the first 300 files the API lists; check the rest"
                                             " by hand" if row["truncated"] else "")


def pages_check(api=gh) -> tuple[str, str]:
    """Is GitHub Pages serving this repository's current main? (state, line).

    States: current, building, behind (the last finished build is of an older
    commit, so the live site lags main), errored, and NOT CHECKED when the API
    does not answer. Read-only: two GET calls.
    """
    try:
        head = api(f"repos/{SITE_REPO}/commits/main")["sha"]
        build = api(f"repos/{SITE_REPO}/pages/builds/latest")
    except (Unchecked, KeyError, ValueError, OSError) as error:  # OSError: no gh (#289, #343)
        reason = "; ".join(error.args[0]) if error.args and isinstance(error.args[0], list) else str(error)
        return "NOT CHECKED", f"NOT CHECKED: GitHub Pages ({reason})"
    status, commit = build.get("status", "?"), build.get("commit") or ""
    when = build.get("updated_at", "?")
    if status == "errored":
        message = (build.get("error") or {}).get("message") or "no message"
        return "errored", f"errored: the latest build ({commit[:7]}, {when}) failed: {message}"
    if status in ("building", "queued"):
        return "building", f"building: {commit[:7]} is being deployed; main is {head[:7]}"
    if commit != head:
        return "behind", f"behind: Pages serves {commit[:7]} (built {when}); main is {head[:7]}"
    return "current", f"current: Pages serves main ({head[:7]}, built {when})"


def site_feature_check(features: dict, api=gh) -> list[tuple[str, str, str]]:
    """(status, mech, detail) for each Mech site in the website feature table.

    The table describes live sites, not pins, so a site that GitHub Pages has
    successfully deployed again since its recorded deployed_revision may no
    longer match its verdicts (#373). A deployment request can still be queued
    or have failed, so its latest status must confirm success before calling it
    the served revision. States: same, redeployed and NOT CHECKED when success
    cannot be verified. Read-only: at most two GETs per site.
    """
    rows = []
    for mech, entry in sorted(features["mechs"].items()):
        if entry.get("site") is None:
            continue
        try:
            repository = entry["repository"]
            if not (isinstance(repository, str) and
                    re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", repository)):
                raise ValueError("repository must be a GitHub repository URL")
            repo = repository.removeprefix("https://github.com/").rstrip("/")
            recorded = entry["deployed_revision"]
            if not (isinstance(recorded, str) and re.fullmatch(r"[0-9a-f]{40}", recorded)):
                raise ValueError("deployed_revision must be a full commit SHA")
            latest = api(f"repos/{repo}/deployments?environment=github-pages&per_page=1")[0]
            sha, when = latest["sha"], latest.get("created_at", "?")
            deployment_id = latest["id"]
            if type(deployment_id) is not int or deployment_id <= 0:
                raise ValueError("deployment response has no valid id")
            if not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha)):
                raise ValueError("deployment response has no valid commit SHA")
            status = api(f"repos/{repo}/deployments/{deployment_id}/statuses?per_page=1")[0]["state"]
            if status != "success":
                rows.append(("NOT CHECKED", mech,
                             f"latest deployment is {status}; currently served revision not verified"))
                continue
        except (Unchecked, KeyError, IndexError, TypeError, ValueError, OSError) as error:
            reason = "; ".join(error.args[0]) if error.args and isinstance(error.args[0], list) else str(error)
            rows.append(("NOT CHECKED", mech, reason or "no deployment"))
            continue
        if sha == recorded:
            rows.append(("same", mech, f"still serves {sha[:7]}"))
        else:
            rows.append(("redeployed", mech, f"{recorded[:7]} when checked, now {sha[:7]} (deployed {when})"))
    return rows


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
    out = (done.stdout + done.stderr).strip()
    if "No module named" in done.stderr:
        return (f"NOT CHECKED: {sys.executable} lacks a requirement "
                f"({done.stderr.strip().splitlines()[-1]}); run with python3.12, "
                "which CI uses, or install scripts/fleet/requirements.txt")
    if done.returncode != 0 and "stale" not in out.lower():
        # Any other failure (a moved fleet.yaml, a validation error) checked nothing (#295).
        return f"NOT CHECKED: refresh_manifest --check failed ({(out.splitlines() or ['exit ' + str(done.returncode)])[-1]})"
    return out or f"exit {done.returncode}"


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
            dead: list[str], unchecked_links: list[str], pages: tuple[str, str] = ("", ""),
            sites: list[tuple[str, str, str]] = ()) -> str:
    """One line naming everything a refresh would change, from every section (#288),
    led by whether the live site is the deployed main at all."""
    parts = []
    moved = [r["repo"] for r in rows if r["records"] or r["claims"]]
    if moved:
        parts.append("repositories: " + ", ".join(moved))
    # Only these say a card no longer matches its site; the rest say it could
    # not be checked (#296).
    behind = [f"{m} ({s})" for s, m, _ in cards if s in ("grew", "STALE", "SHRANK", "WRONG")]
    if behind:
        parts.append("cards: " + ", ".join(behind))
    if "stale" in manifest.lower():
        parts.append("fleet membership or capabilities (CLAW manifest)")
    if dead:
        parts.append(f"{len(dead)} dead evidence link(s)")
    redeployed = [m for s, m, _ in sites if s == "redeployed"]
    if redeployed:
        parts.append("website feature verdicts to re-check on redeployed sites: " + ", ".join(redeployed))
    not_checked = [r["repo"] for r in rows if r.get("unchecked")]
    not_checked += [f"{r['repo']} (past the 300-file cap)" for r in rows  # #297
                    if r.get("truncated") and not r["records"] and not r["claims"]]
    not_checked += [f"{r['repo']} (main {r['status']})" for r in rows if r.get("status") in ("behind", "diverged")]
    not_checked += [f"card {m} ({s})" if m != "-" else f"cards ({d})" for s, m, d in cards
                    if s not in ("ok", "grew", "STALE", "SHRANK", "WRONG")]
    if manifest.startswith("NOT CHECKED"):
        not_checked.append("CLAW manifest")
    if unchecked_links:
        not_checked.append(f"{len(unchecked_links)} evidence link(s)")
    if pages[0] == "NOT CHECKED":
        not_checked.append("GitHub Pages deployment")
    not_checked += [f"site deployment {m}" for s, m, _ in sites if s == "NOT CHECKED"]
    line = (f"**GitHub Pages:** {pages[1].rstrip('.')}. " if pages[0] not in ("", "NOT CHECKED") else "")
    line += "**Refresh would change:** " + ("; ".join(parts) if parts else "nothing found") + "."
    if not_checked:
        line += " **Not checked:** " + ", ".join(not_checked) + "."
    return line


def main() -> int:
    audit = json.loads(AUDIT.read_text())
    fragment = FRAGMENT.read_text()
    cited = watched(audit, site_sources())
    mech_of = {m.lower(): m for m in UPDATE_RECORD_GLOBS}
    print(f"# X-Mech update check against the pins of {audit['pinned_at_utc']}\n")
    print("## GitHub Pages deployment\n")
    pages = pages_check()
    print(pages[1] + "\n")
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
    features = json.loads(FEATURES.read_text())
    print(f"\n## Website feature table (baseline audit: {features['checked_on']})\n")
    sites = site_feature_check(features)
    for status, mech, detail in sites:
        checked_on = features["mechs"][mech].get("checked_on", features["checked_on"])
        print(f"- {status} {mech} (audit date: {checked_on}): {detail}")
    print("\n" + summary(moved, cards, manifest, dead, unchecked, pages, sites))
    return 0


if __name__ == "__main__":
    sys.exit(main())
