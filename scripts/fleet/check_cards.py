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

What fails and what only warns (#148, #115, #176):

  ok       the site states the card's figure.
  grew     the site is ahead of the card by at most GROWTH_TOLERANCE. A warning:
           the page is a snapshot at a refresh's pins and fast Mechs publish
           within hours of them, so a small lead is the expected state, not a
           wrong card. site_audit.json records the lead the refresh saw.
  STALE    the site is further ahead than that. The card no longer describes the
           Mech; refresh it.
  SHRANK   the site states fewer than the card. Records are not normally
           withdrawn in bulk, so either the card is wrong or the site regressed.
  GONE     the source answered 4xx. The page the card cites has moved or been
           deleted, which is how #175 began; an outage does not look like this.
  CHANGED  the source arrived but no figure could be read from it: the markup or
           the wording moved, and the card is no longer being checked at all.
  unread   the fetch did not arrive (DNS, timeout, 5xx). A warning, because the
           network is not the site's fault, unless more than half the sources
           are unread, when the run has verified too little to call itself a
           pass and fails as UNCHECKED.

A card with no SOURCES entry, or an entry with no card, also fails.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from card_markup import card_figures

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "_fleet/mechs_template.md"
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

# How far a site may be ahead of its card before the card counts as stale. At
# the 2026-09-24 refresh the two fastest Mechs were 0.7% and 6.5% ahead of their
# pins when its audit was written; a mistyped or misattributed card is rarely
# that close (#148).
GROWTH_TOLERANCE = 0.10


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


def classify(card: int, site: int) -> str:
    """How a published figure relates to the card that states it."""
    if site == card:
        return "ok"
    if site < card:
        return "SHRANK"
    return "grew" if site - card <= card * GROWTH_TOLERANCE else "STALE"


def read_source(mech: str, kind: str, path: str, selector: str, fetcher=None) -> tuple[str, int | str]:
    """The figure a source publishes, or why there is none.

    Returns ("value", N), or a status and the reason: "GONE" for a 4xx, "unread"
    for a fetch that did not arrive, "CHANGED" for a body with no figure in it.
    """
    fetcher = fetcher or fetch
    try:
        body = fetcher(source_url(path))
    except urllib.error.HTTPError as error:
        # HTTPError is a URLError, so it is caught first. A 4xx is the source
        # telling us it is not there; a 5xx is the host having a bad night.
        status = "GONE" if 400 <= error.code < 500 else "unread"
        return status, f"fetch failed: {error}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return "unread", f"fetch failed: {error}"
    if mech in REGIONS:
        body = region(body, REGIONS[mech])
        if body is None:
            return "CHANGED", "the generated block that states the figure is gone"
    try:
        value = published(kind, body, selector)
    except (ValueError, TypeError, AttributeError) as error:
        # json.JSONDecodeError is a ValueError. The other two are what a
        # body of an unexpected type raises when it is walked.
        return "CHANGED", f"unparseable: {error}"
    if value is None:
        return "CHANGED", f"{kind} shape changed; no {selector!r} found"
    return "value", value


FAILURES = ("STALE", "SHRANK", "GONE", "CHANGED", "UNCARDED", "UNCHECKED")


def check(stated: dict[str, int], fetcher=None) -> list[tuple[str, str, str]]:
    """One (status, mech, detail) row per source, plus the run-level verdicts."""
    rows = []
    for mech in sorted(set(stated) - set(SOURCES)):
        rows.append(("UNCARDED", mech, "card with no entry in SOURCES"))
    for mech, (kind, path, selector) in sorted(SOURCES.items()):
        if mech not in stated:
            rows.append(("UNCARDED", mech, "SOURCES entry with no card in the template"))
            continue
        status, result = read_source(mech, kind, path, selector, fetcher)
        if status != "value":
            rows.append((status, mech, result))
            continue
        card = stated[mech]
        verdict = classify(card, result)
        detail = f"{card:>9,}" if verdict == "ok" else f"card {card:,}, site {result:,}"
        if verdict == "grew":
            detail += f" (+{(result - card) / card:.1%}, within {GROWTH_TOLERANCE:.0%})"
        rows.append((verdict, mech, detail))
    unread = sum(1 for status, _, _ in rows if status == "unread")
    if unread * 2 > len(SOURCES):
        # One site down is someone else's outage. Most of them down is this run
        # having checked nothing, which must not read as a pass (#115).
        rows.append(("UNCHECKED", "-", f"{unread} of {len(SOURCES)} sources could not be read"))
    return rows


def main() -> int:
    rows = check(card_figures(TEMPLATE.read_text()))
    for status, mech, detail in rows:
        print(f"  {status:<9} {mech:<20} {detail}")
    tally: dict[str, int] = {}
    for status, _, _ in rows:
        tally[status] = tally.get(status, 0) + 1
    print("\n" + ", ".join(f"{count} {status.lower()}" for status, count in sorted(tally.items())) + ".")
    failed = [status for status, _, _ in rows if status in FAILURES]
    if failed:
        print("Failing. STALE or SHRANK: refresh the card figures in _fleet/mechs_template.md "
              "and the MECHS block in _fleet/fleet_fragment.html, then rerun assemble_page.py. "
              "GONE or CHANGED: repoint that Mech's SOURCES entry. UNCARDED: add the missing "
              "card or SOURCES entry. UNCHECKED: the run could not reach most sites.")
        return 1
    if any(status in ("grew", "unread") for status, _, _ in rows):
        # A site a little ahead of its pinned card, or one that could not be
        # reached, is not a wrong number, and a nightly red for either teaches
        # people to ignore it.
        print("Passing with warnings; see above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
