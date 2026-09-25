"""Compare each Mech card's headline figure against the site the card cites.

Run from the site root: `python3 scripts/fleet/check_cards.py`. Read-only, and
the only script here that needs the network.

The card numbers in _fleet/mechs_template.md are hand-curated from each Mech's
published browser (CultureMech's from its committed README; see SOURCES), so
nothing regenerates them and nothing noticed when they
went stale — two of six had drifted within two days of a refresh
(CultureBotAI.github.io#104). This reports that, and is meant to run on the
nightly schedule rather than on a pull request: the corpora move fast enough
that a blocking check would make an unrelated docs fix unmergeable because some
Mech published records overnight.

What fails and what only warns (#148, #115, #176, #217):

  ok       the site states the card's figure.
  grew     the site is ahead of the card, the refresh that pinned the card is
           at most GRACE_DAYS old, and the site is at most MAX_LEAD ahead. A
           warning: the page is a snapshot at the refresh's pins, and fast
           Mechs publish within hours of them.
  STALE    the site is ahead and the refresh is older than that, or the site
           leads the card by more than MAX_LEAD of the card (the card then
           understates it by over a third). Refresh the page.
  WRONG    the card differs from figure_at_pin, the figure the audit read from
           the source's own committed copy at the pin with figure() below. The
           card was never right, however the site has moved since (#217, #231).
  SHRANK   the site states fewer than the card. Records are not normally
           withdrawn in bulk, so either the card is wrong or the site regressed.
  GONE     the source answered a 4xx other than a throttle. The page the card
           cites has moved or been deleted, which is how #175 began.
  CHANGED  the source arrived but no figure could be read from it: the markup or
           the wording moved, and the card is no longer being checked at all.
  MARKUP   a card in the template does not carry exactly one headline figure.
  UNCARDED a card with no SOURCES entry, or an entry with no card.
  AUDIT    site_audit.json is missing or malformed, its pinned_at_utc is
           missing, cannot be read as a time, or is in the future, or a
           source's figure_at_pin is missing or not a whole number.
  unread   the fetch did not arrive: DNS, timeout, a dropped connection, a
           5xx, or a 408, 425 or 429 throttle. A warning, because the network is
           not the site's fault, unless more than half the sources are unread,
           when the run has verified too little to call itself a pass and fails
           as UNCHECKED.

The pin time and each source's figure at the pin come from
_fleet/data/site_audit.json, which the refresh writes (update-xmech-page, step 7).
ProteinTraitsMech's data file is built in CI rather than committed, so it has no
copy at the pin and no figure_at_pin; its card is checked only against the site.
"""
from __future__ import annotations

import datetime
import http.client
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from card_markup import card_figures, card_names, markup_problems

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "_fleet/mechs_template.md"
AUDIT = REPO / "_fleet/data/site_audit.json"
SITE = "https://culturebotai.github.io/"

# Where each card's headline actually comes from. Pinned here rather than
# guessed, because the ten sites do not agree on how they publish it:
#
#   html  the figure is in a stat tile, as <b>N</b><span>LABEL
#   text  the figure is in a sentence, as "N LABEL" — CultureMech and
#         NaturalProductMech state theirs in prose rather than a tile
#   json  the page computes it at runtime, so the markup carries a placeholder
#         and only the data file has the number (#86)
#
# Several repo roots are client-side meta-refresh shells that return 200, so
# these are the pages/ or app/ URLs, never the root. CultureMech's is its README.
SOURCES: dict[str, tuple[str, str, str]] = {
    "HabitatMech":         ("html", "HabitatMech/pages/index.html", "habitat records"),
    "CommunityMech":       ("html", "CommunityMech/", "communities"),
    "TaxonMech":           ("html", "TaxonMech/pages/index.html", "taxon records"),
    "TraitMech":           ("html", "TraitMech/pages/index.html", "trait records"),
    "CellStructureMech":   ("html", "CellStructureMech/pages/index.html", "structure records"),
    "AntibioticMech":      ("html", "AntibioticMech/pages/index.html", "compound records"),
    "NaturalProductMech":  ("text", "NaturalProductMech/pages/index.html", "natural product structures"),
    # No page CultureMech reliably serves states its canonical count. The app/
    # landing tile is a legacy hand-typed figure (#86). Its pages/ media index is
    # built and deployed by the generate-pages workflow, and the branch-based
    # Pages build replaces that deployment on other pushes to main, so the index
    # appears and disappears (#175, #180). The README on main is committed and
    # states the count in its generated corpus snapshot ("6,288 merged records").
    "CultureMech":         ("text", "https://raw.githubusercontent.com/CultureBotAI/CultureMech/main/README.md", "merged records"),
    "ProteinTraitsMech":   ("json", "proteintraitsmech/data/facets.json", "total"),
    "MediaIngredientMech": ("json", "MediaIngredientMech/data/ingredients.json", "ingredients"),
}

# Where inside a source the figure must be read, when the source states the same
# label elsewhere too. CultureMech's README says "merged records" in its prose;
# only the block its generator writes, and its CI keeps in sync with the data,
# is the figure (#176). Markers missing is a shape change, not a pass.
REGIONS: dict[str, tuple[str, str]] = {
    "CultureMech": ("<!-- BEGIN GENERATED CORPUS STATS -->", "<!-- END GENERATED CORPUS STATS -->"),
}

# How long a card may trail a growing site before the page counts as stale, and
# how far it may trail within that time. A fixed percentage alone did not hold:
# CellStructureMech adds about two records an hour, 9% a day on a card of 542,
# so a 10% allowance went red a day after every refresh (#217). The time limit
# asks for a refresh a fortnight after the pins while any Mech grows; the lead
# limit asks sooner once a site is more than half as large again as its card
# (the card then understates it by over a third), which CellStructureMech
# reaches in under a week.
GRACE_DAYS = 14
MAX_LEAD = 0.5

# Sources with no committed copy at the pin, so no figure_at_pin: the served
# file is built in CI. Every other source must have one, or WRONG is off (#260).
NO_PIN_COPY = ("ProteinTraitsMech",)

# 4xx answers that mean "not now" rather than "not here" (#219).
THROTTLES = (408, 425, 429)


def source_url(path: str) -> str:
    """A SOURCES path relative to the Pages host, or an absolute https URL."""
    return path if path.startswith("https://") else SITE + path


def fetch(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "culturebotai-card-check"})
    return urllib.request.urlopen(request, timeout=timeout).read().decode("utf-8", "replace")


def region(body: str, markers: tuple[str, str]) -> str | None:
    """The text between two markers, or None when either is missing."""
    start, end = markers
    _, found, rest = body.partition(start)
    if not found:
        return None
    inside, found, _ = rest.partition(end)
    return inside if found else None


def published(kind: str, body: str, selector: str) -> int | None:
    """The figure the site publishes, or None when the shape has changed."""
    if kind == "json":
        document = json.loads(body)
        # ingredients.json has shipped as a bare list in some releases. Test the
        # shape before reaching into it: a list has no .get, and the error that
        # raises is not a parse error, so it used to escape as a traceback
        # instead of an "unread" line (#110).
        if isinstance(document, list):
            return len(document)
        if not isinstance(document, dict):
            return None
        value = document.get(selector)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return None
    if kind == "text":
        # The figure sits in a sentence. Strip tags first so markup between the
        # number and the words it belongs to cannot hide the pairing.
        # Markdown emphasis goes too: a README may bold the number alone.
        prose = re.sub(r"[*_]", "", re.sub(r"<[^>]+>", " ", body))
        # Whitespace runs collapse, so a line wrapped inside the label still
        # matches (#207).
        prose = re.sub(r"\s+", " ", prose)
        label = re.escape(" ".join(selector.split())).replace(r"\ ", " ")
        hit = re.search(r"([\d,]+) " + label, prose)
        return int(hit.group(1).replace(",", "")) if hit else None
    hit = re.search(r"<b>([\d,]+)</b>\s*<span>\s*" + re.escape(selector), body)
    return int(hit.group(1).replace(",", "")) if hit else None


def figure(mech: str, kind: str, body: str, selector: str) -> int | None:
    """The figure a source's body states, read the way the nightly reads it.

    Applies the Mech's REGIONS first, so the refresh can read the committed copy
    at the pin with exactly the rules used on the live site (#221). None when no
    figure can be read; a body of the wrong type raises, as published() does.
    """
    if mech in REGIONS:
        body = region(body, REGIONS[mech])
        if body is None:
            return None
    return published(kind, body, selector)


def read_source(mech: str, kind: str, path: str, selector: str, fetcher=None) -> tuple[str, int | str]:
    """The figure a source publishes, or why there is none.

    Returns ("value", N), or a status and the reason: "GONE" for a 4xx other
    than a throttle, "unread" for a fetch that did not arrive, "CHANGED" for a
    body with no figure in it.
    """
    fetcher = fetcher or fetch
    try:
        body = fetcher(source_url(path))
    except urllib.error.HTTPError as error:
        # HTTPError is a URLError, so it is caught first. A 4xx is the source
        # telling us it is not there, unless it is asking us to come back later.
        gone = 400 <= error.code < 500 and error.code not in THROTTLES
        return ("GONE" if gone else "unread"), f"fetch failed: {error}"
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as error:
        # HTTPException covers a body cut short (IncompleteRead) and a garbled
        # status line, which used to end the run with a traceback (#220).
        return "unread", f"fetch failed: {error}"
    try:
        value = figure(mech, kind, body, selector)
    except (ValueError, TypeError, AttributeError) as error:
        # json.JSONDecodeError is a ValueError. The other two are what a
        # body of an unexpected type raises when it is walked.
        return "CHANGED", f"unparseable: {error}"
    if value is None:
        # #247: this used to say the missing block was "found".
        where = ("the generated block is missing or states no figure" if mech in REGIONS
                 else f"no {selector!r} found")
        return "CHANGED", f"{kind} shape changed; {where}"
    return "value", value


def pin_time(audit: dict) -> datetime.datetime:
    """The audit's pin time as an aware datetime; a time with no offset is UTC.

    Raises ValueError when the field is missing or is not an ISO time (#232).
    """
    value = audit.get("pinned_at_utc")
    if not isinstance(value, str):
        raise ValueError(f"pinned_at_utc is {value!r}")
    moment = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=datetime.timezone.utc)


def classify(card: int, site: int, age: datetime.timedelta | None) -> str:
    """How a published figure relates to the card that states it."""
    if site == card:
        return "ok"
    if site < card:
        return "SHRANK"
    if age is None or age > datetime.timedelta(days=GRACE_DAYS):
        return "STALE"
    return "grew" if site - card <= card * MAX_LEAD else "STALE"


def span(age: datetime.timedelta) -> str:
    """A pin's age in the unit a reader wants: hours on the first day, then days."""
    if age.days >= 1:
        return f"{age.days} day{'s' if age.days != 1 else ''}"
    hours = int(age.total_seconds() // 3600)
    return f"{hours} hour{'s' if hours != 1 else ''}"


FAILURES = ("STALE", "WRONG", "SHRANK", "GONE", "CHANGED", "MARKUP", "UNCARDED", "AUDIT", "UNCHECKED")


def audit_entries(audit) -> tuple[dict, str | None]:
    """The audit's repositories keyed by lower-cased name, or why they cannot be read."""
    if not isinstance(audit, dict):
        return {}, f"site_audit.json holds a {type(audit).__name__}, not an object"
    if "repositories" not in audit:
        return {}, "site_audit.json has no repositories list"  # #257
    repositories = audit["repositories"]
    if not isinstance(repositories, list) or not all(
            isinstance(row, dict) and isinstance(row.get("repo"), str) for row in repositories):
        return {}, "site_audit.json: repositories must be a list of objects, each with a repo name"
    return {row["repo"].lower(): row for row in repositories}, None


def check(template: str, fetcher=None, audit=None, now: datetime.datetime | None = None,
          audit_error: str | None = None) -> list[tuple[str, str, str]]:
    """One (status, mech, detail) row per card problem and per source, plus the run-level verdicts.

    A malformed audit is an AUDIT row, not an exception, so the other rows still
    print (#250); audit_error carries a problem found while reading the file.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    rows = [("MARKUP", mech, why) for mech, why in markup_problems(template)]
    if audit_error:
        rows.append(("AUDIT", "-", audit_error))
    entries, problem = audit_entries(audit) if audit is not None else ({}, None)
    if problem:
        rows.append(("AUDIT", "-", problem))
        audit = None
    age = None
    if audit is not None:  # {} too, so a missing pin time is reported (#257)
        try:
            age = now - pin_time(audit)
        except ValueError as error:
            # Growth then counts as STALE, which fails anyway; say why.
            rows.append(("AUDIT", "-", f"site_audit.json: {error}"))
        else:
            if age < datetime.timedelta(0):
                # A pin in the future would hold off the grace limit until the
                # clock caught up with it (#242).
                rows.append(("AUDIT", "-", f"site_audit.json: pinned_at_utc {audit['pinned_at_utc']} is in the future"))
                age = None
    stated = card_figures(template)
    names = set(card_names(template))
    for mech in sorted(names - set(SOURCES)):
        rows.append(("UNCARDED", mech, "card with no entry in SOURCES"))
    for mech, (kind, path, selector) in sorted(SOURCES.items()):
        if mech not in names:
            rows.append(("UNCARDED", mech, "SOURCES entry with no card in the template"))
            continue
        if mech not in stated:
            continue  # its card's markup is already reported above
        card = stated[mech]
        entry = entries.get(mech.lower())
        at_pin = entry.get("figure_at_pin") if entry else None
        whole = isinstance(at_pin, int) and not isinstance(at_pin, bool)
        if audit is not None:
            # A missing or mistyped figure_at_pin would switch WRONG off without
            # a word (#260).
            if entry is None:
                rows.append(("AUDIT", mech, "no entry in site_audit.json"))
            elif at_pin is None and mech not in NO_PIN_COPY:
                rows.append(("AUDIT", mech, "site_audit.json has no figure_at_pin for it"))
            elif at_pin is not None and not whole:
                rows.append(("AUDIT", mech, f"figure_at_pin is {at_pin!r}, not a whole number"))
        if whole and at_pin != card:
            rows.append(("WRONG", mech, f"card {card:,}, but the source stated {at_pin:,} at the pin"))
            continue
        status, result = read_source(mech, kind, path, selector, fetcher)
        if status != "value":
            rows.append((status, mech, result))
            continue
        verdict = classify(card, result, age)
        detail = f"{card:>9,}" if verdict == "ok" else f"card {card:,}, site {result:,}"
        if verdict in ("grew", "STALE") and age is not None:
            detail += f" (+{result - card:,} in the {span(age)} since the pins)"
        rows.append((verdict, mech, detail))
    unread = sum(1 for status, _, _ in rows if status == "unread")
    if unread * 2 > len(SOURCES):
        # One site down is someone else's outage. Most of them down is this run
        # having checked nothing, which must not read as a pass (#115).
        rows.append(("UNCHECKED", "-", f"{unread} of {len(SOURCES)} sources could not be read"))
    return rows


def main() -> int:
    audit, audit_error = None, None
    try:
        audit = json.loads(AUDIT.read_text())
        if not isinstance(audit, dict):
            # check() reads None as "no audit supplied", so a null file would
            # otherwise pass silently (#257).
            audit_error = f"site_audit.json holds {type(audit).__name__}, not an object"
            audit = None
    except FileNotFoundError:
        audit_error = "site_audit.json is missing"
    except (OSError, ValueError) as error:
        audit_error = f"site_audit.json cannot be read: {error}"
    rows = check(TEMPLATE.read_text(), audit=audit, audit_error=audit_error)
    for status, mech, detail in rows:
        print(f"  {status:<9} {mech:<20} {detail}")
    tally: dict[str, int] = {}
    for status, _, _ in rows:
        tally[status] = tally.get(status, 0) + 1
    print("\n" + ", ".join(f"{count} {status.lower()}" for status, count in sorted(tally.items())) + ".")
    if any(status in FAILURES for status, _, _ in rows):
        print("Failing. STALE or SHRANK: refresh the card figures in _fleet/mechs_template.md "
              "and the MECHS block in _fleet/fleet_fragment.html (update-xmech-page), then rerun "
              "assemble_page.py. WRONG: correct the card and every other occurrence of its "
              "figure, found by grepping the tree for it as update-xmech-page step 6 does (the MECHS "
              "records: and extra: text in _fleet/fleet_fragment.html, cross-references, the pages "
              "that repeat it, and card_records in site_audit.json, the one audit field a WRONG fix "
              "edits, to match the corrected card), then rerun assemble_page.py; no re-pin. "
              "If figure_at_pin itself is wrong, re-derive it with build_site_audit.py against a "
              "snapshot at the audit's pins (update-xmech-page step 11); never edit it by hand. GONE or CHANGED: repoint that Mech's SOURCES entry. MARKUP or "
              "UNCARDED: fix the card or its SOURCES entry. AUDIT: never edit site_audit.json by hand, apart from card_records under WRONG. "
              "A missing or non-integer figure_at_pin: regenerate it with build_site_audit.py "
              "against a snapshot at its pins (update-xmech-page steps 7 and 11). A bad pin time, "
              "or a missing or malformed audit: take the pins and pin time from the last audit the "
              "builder wrote (git log -p -- _fleet/data/site_audit.json), then regenerate. A Mech "
              "with no entry: a full refresh with new pins. "
              "UNCHECKED: the run could not reach most sites; rerun before changing anything.")
        return 1
    if any(status in ("grew", "unread") for status, _, _ in rows):
        # A site a little ahead of a recently pinned card, or one that could not
        # be reached, is not a wrong number, and a nightly red for either
        # teaches people to ignore it.
        print("Passing with warnings; see above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
