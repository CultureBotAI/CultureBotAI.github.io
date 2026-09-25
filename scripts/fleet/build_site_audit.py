"""Write _fleet/data/site_audit.json for a refresh (update-xmech-page, step 7).

Run from the site root after the pipeline, with the snapshot the refresh built:

    python3 scripts/fleet/build_site_audit.py --snapshot "$SNAP"

Every mechanical field is derived here rather than typed: the pins and commit
dates from $SNAP/revisions.json, merged PRs from mech_stats.json, each source's
live figure and figure_at_pin through check_cards.figure() (the nightly's own
parser, REGIONS applied), and the sha256 of the served file and of its committed
copy at the pin. What only a person can check, the notes on how each site's
figure relates to its records and the audit's scope, comes from
_fleet/audit_notes.json. The builder adds one sentence per source saying whether
the live copy still matches the pin, so no note ever claims that by hand (#155).

It refuses to write when a card differs from the figure its source stated at the
pin, or when a site states fewer than its card: either is a wrong card, not a
site that grew (#231). Until #238 this script lived only in a session
scratchpad, and each refresh rewrote it from the skill's prose.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import check_cards
from card_markup import card_figures

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "_fleet/data/site_audit.json"
NOTES = REPO / "_fleet/audit_notes.json"
STATS = REPO / "_fleet/data/mech_stats.json"
CLAW = "culturebotai-claw"


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "culturebotai-site-audit"})
    return urllib.request.urlopen(request, timeout=60).read()


def committed_candidates(path: str) -> list[str]:
    """Where a SOURCES path's file sits in its repository, most likely first.

    Pages sites here publish from the repository root, pages/ or docs/, and
    CultureMech's source is a file read straight from the repository.
    """
    if path.startswith("https://raw.githubusercontent.com/"):
        return [path.split("/main/", 1)[1]]
    rel = path.split("/", 1)[1] if "/" in path else ""
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return [rel, "docs/" + rel]


def committed_copy(show, path: str) -> tuple[str | None, bytes | None]:
    """The first candidate that show(candidate) finds, as (path, bytes)."""
    for candidate in committed_candidates(path):
        body = show(candidate)
        if body is not None:
            return candidate, body
    return None, None


def git_show(clone: Path, sha: str):
    """show(candidate) for one Mech's snapshot clone at its pin."""
    def show(candidate: str) -> bytes | None:
        done = subprocess.run(["git", "-C", str(clone), "show", f"{sha}:{candidate}"], capture_output=True)
        return done.stdout if done.returncode == 0 else None
    return show


def match_sentence(key: str, live: bytes, path: str | None, pinned: bytes | None) -> str:
    """Whether the live copy still matches the pin, in the audit's words."""
    if pinned is None:
        return " The served file is built in CI rather than committed, so there is no copy at the pin to compare."
    name = path.rsplit("/", 1)[-1]
    if pinned == live:
        return f" The live {name} is byte-identical to {path} at the pin."
    return (f" The live {name} had moved past the pin when this audit was written; "
            f"{key} is the live copy and {key.replace('sha256', 'sha256_at_pin')} is {path} at the pin.")


def read_figure(mech: str, kind: str, body: bytes, selector: str, what: str) -> int:
    value = check_cards.figure(mech, kind, body.decode("utf-8", "replace"), selector)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SystemExit(f"{mech}: no figure could be read from {what}")
    return value


def build_entry(mech: str, source: tuple[str, str, str], pin: dict, stats: dict, card: int,
                note: str, fetch, show) -> dict:
    """One repository's audit entry. fetch(url) and show(path) supply the bytes."""
    kind, path, selector = source
    url = check_cards.source_url(path)
    if stats["source_revision"] != pin["sha"]:
        raise SystemExit(f"{mech}: mech_stats.json was not counted at the pin")
    body = fetch(url)
    live = read_figure(mech, kind, body, selector, url)
    pinned_path, pinned = committed_copy(show, path)
    entry = {
        "repo": stats["repo"],
        "sha": pin["sha"],
        "commit_date": pin["commit_date"],
        "readme_url": f"https://github.com/CultureBotAI/{stats['repo']}/blob/{pin['sha']}/README.md",
        "card_records": card,
    }
    if pinned is not None:
        at_pin = read_figure(mech, kind, pinned, selector, f"{pinned_path} at the pin")
        if at_pin != card:
            raise SystemExit(f"{mech}: the card says {card:,} but {pinned_path} stated {at_pin:,} at the pin")
        entry["figure_at_pin"] = at_pin
    elif mech not in check_cards.NO_PIN_COPY:
        raise SystemExit(f"{mech}: no committed copy of {path} at the pin; if it is built in CI, "
                         "add it to check_cards.NO_PIN_COPY")
    if live < card:
        raise SystemExit(f"{mech}: the site says {live:,}, below the card's {card:,}; that is not growth")
    entry["merged_prs"] = stats["merged_prs"]
    if kind == "json":
        # The page's markup carries a placeholder; hash both it and the data.
        page = url.rsplit("/data/", 1)[0] + "/"
        entry["site"] = page
        entry["site_html_sha256"] = hashlib.sha256(fetch(page)).hexdigest()
        entry["data_url"] = url
        entry["data_sha256"] = hashlib.sha256(body).hexdigest()
        key = "data_sha256"
    else:
        entry["site"] = url
        entry["site_html_sha256"] = hashlib.sha256(body).hexdigest()
        key = "site_html_sha256"
    if pinned is not None:
        entry[key.replace("sha256", "sha256_at_pin")] = hashlib.sha256(pinned).hexdigest()
    entry["notes"] = note + match_sentence(key, body, pinned_path, pinned)
    if live > card:
        # The corpus grew between the pin and this fetch. The page stays a
        # snapshot at the pins; the audit says what the site showed instead.
        entry["site_figure_at_check"] = live
        entry["notes"] += (f" The site moved past the pin during the refresh and showed {live:,} when this"
                           f" audit was written; the card keeps the pinned figure, {card:,}.")
    return entry


def utc(iso: str) -> str:
    """A commit date with its offset, as UTC. One with no offset is refused: read
    as local time it would shift by the machine's zone without a word (#274)."""
    moment = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise SystemExit(f"revisions.json: commit_date {iso} has no offset")
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build(pins: dict, notes: dict, template: str, stats: dict, fetch, shower, claw_date: str,
          now: datetime.datetime, notes_path: str = "_fleet/audit_notes.json") -> dict:
    """The whole audit. shower(mech, sha) returns that Mech's show(path)."""
    cards = card_figures(template)
    by_mech = {m["mech"]: m for m in stats["mechs"]}
    missing = sorted((set(check_cards.SOURCES) | {CLAW}) - set(notes["notes"]))
    if missing:
        raise SystemExit(f"{notes_path} has no notes for: {', '.join(missing)}")  # #267
    # The nightly reads this pin time; refuse one it would report as AUDIT (#269).
    try:
        pinned = check_cards.pin_time(pins)
    except ValueError as error:
        raise SystemExit(f"revisions.json: {error}")
    if pinned > now:
        raise SystemExit(f"revisions.json: pinned_at_utc {pins['pinned_at_utc']} is in the future")
    repositories = []
    for mech, source in sorted(check_cards.SOURCES.items()):
        pin = dict(pins["mechs"][mech], commit_date=utc(pins["mechs"][mech]["commit_date"]))
        repositories.append(build_entry(mech, source, pin, by_mech[mech], cards[mech],
                                        notes["notes"][mech], fetch, shower(mech, pin["sha"])))
    claw = pins["claw"]
    repositories.append({
        "repo": CLAW,
        "sha": claw,
        "commit_date": claw_date,
        "readme_url": f"https://github.com/CultureBotAI/{CLAW}/blob/{claw}/README.md",
        "notes": notes["notes"][CLAW],
    })
    repositories.sort(key=lambda r: r["repo"].lower())
    return {
        "checked_at_utc": now.astimezone(datetime.timezone.utc).isoformat(timespec="seconds"),
        # The local date of that same moment, not a typed one (#178).
        "local_date": now.astimezone().date().isoformat(),
        "pinned_at_utc": pins["pinned_at_utc"],
        "scope": notes["scope"],
        "repositories": repositories,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--snapshot", required=True, help="the refresh's $SNAP")
    parser.add_argument("--notes", default=str(NOTES))
    args = parser.parse_args()
    snap = Path(args.snapshot)
    pins = json.loads((snap / "revisions.json").read_text())
    claw_date = subprocess.check_output(
        ["gh", "api", f"repos/CultureBotAI/{CLAW}/commits/{pins['claw']}", "--jq", ".commit.committer.date"],
        text=True).strip()
    audit = build(pins, json.loads(Path(args.notes).read_text()), (REPO / "_fleet/mechs_template.md").read_text(),
                  json.loads(STATS.read_text()), fetch_bytes, lambda mech, sha: git_show(snap / "mechs" / mech, sha),
                  claw_date, datetime.datetime.now(datetime.timezone.utc), args.notes)
    AUDIT.write_text(json.dumps(audit, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {AUDIT.relative_to(REPO)} ({len(audit['repositories'])} repositories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
