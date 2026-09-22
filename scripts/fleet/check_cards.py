"""Compare each Mech card's headline figure against the site the card cites.

Run from the site root: `python3 scripts/fleet/check_cards.py`. Read-only, and
the only script here that needs the network.

The card numbers in _fleet/mechs_template.md are hand-curated from each Mech's
published browser, so nothing regenerates them and nothing noticed when they
went stale — two of six had drifted within two days of a refresh
(CultureBotAI.github.io#104). This reports that, and is meant to run on the
nightly schedule rather than on a pull request: the corpora move fast enough
that a blocking check would make an unrelated docs fix unmergeable because some
Mech published records overnight.

Two failure kinds, kept apart on purpose. A fetch that does not arrive is a
warning, because the network is not the site's fault. A fetch that arrives and
does not match is a failure, because either the number moved or the markup did,
and both need a person.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

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
# these are the pages/ or app/ URLs, never the root.
SOURCES: dict[str, tuple[str, str, str]] = {
    "HabitatMech":         ("html", "HabitatMech/pages/index.html", "habitat records"),
    "CommunityMech":       ("html", "CommunityMech/", "communities"),
    "TaxonMech":           ("html", "TaxonMech/pages/index.html", "taxon records"),
    "TraitMech":           ("html", "TraitMech/pages/index.html", "trait records"),
    "CellStructureMech":   ("html", "CellStructureMech/pages/index.html", "structure records"),
    "AntibioticMech":      ("html", "AntibioticMech/pages/index.html", "compound records"),
    "NaturalProductMech":  ("text", "NaturalProductMech/pages/index.html", "natural product structures"),
    # Not the app/ landing tile, which is a legacy hand-typed figure matching no
    # data layer; pages/ is the merged canonical count the card states (#86).
    "CultureMech":         ("text", "CultureMech/pages/", "media records"),
    "ProteinTraitsMech":   ("json", "proteintraitsmech/data/facets.json", "total"),
    "MediaIngredientMech": ("json", "MediaIngredientMech/data/ingredients.json", "ingredients"),
}

CARD = re.compile(r'data-mech="([A-Za-z]+)".*?<div class="num"><b>([\d,]+)</b>', re.S)


def cards(template: str) -> dict[str, int]:
    """The headline figure each card states, keyed by Mech."""
    return {m.group(1): int(m.group(2).replace(",", "")) for m in CARD.finditer(template)}


def fetch(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "culturebotai-card-check"})
    return urllib.request.urlopen(request, timeout=timeout).read().decode("utf-8", "replace")


def published(kind: str, body: str, selector: str) -> int | None:
    """The figure the site publishes, or None when the shape has changed."""
    if kind == "json":
        document = json.loads(body)
        value = document.get(selector)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, int):
            return value
        # ingredients.json is a bare list under its key in some releases
        return len(document) if isinstance(document, list) else None
    if kind == "text":
        # The figure sits in a sentence. Strip tags first so markup between the
        # number and the words it belongs to cannot hide the pairing.
        prose = re.sub(r"<[^>]+>", " ", body)
        hit = re.search(r"([\d,]+)\s+" + re.escape(selector), prose)
        return int(hit.group(1).replace(",", "")) if hit else None
    hit = re.search(r"<b>([\d,]+)</b>\s*<span>\s*" + re.escape(selector), body)
    return int(hit.group(1).replace(",", "")) if hit else None


def main() -> int:
    stated = cards(TEMPLATE.read_text())
    missing = sorted(set(stated) - set(SOURCES))
    drifted, unreadable, matched = [], [], []

    for mech, (kind, path, selector) in sorted(SOURCES.items()):
        if mech not in stated:
            unreadable.append((mech, "no card in the template"))
            continue
        try:
            body = fetch(SITE + path)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            unreadable.append((mech, f"fetch failed: {error}"))
            continue
        try:
            value = published(kind, body, selector)
        except (ValueError, json.JSONDecodeError) as error:
            unreadable.append((mech, f"unparseable: {error}"))
            continue
        if value is None:
            unreadable.append((mech, f"{kind} shape changed; no {selector!r} found"))
        elif value != stated[mech]:
            drifted.append((mech, stated[mech], value))
        else:
            matched.append(mech)

    for mech in matched:
        print(f"  ok       {mech:<20} {stated[mech]:>9,}")
    for mech, card, site in drifted:
        print(f"  DRIFTED  {mech:<20} card {card:,}, site {site:,}")
    for mech, why in unreadable:
        print(f"  unread   {mech:<20} {why}")
    if missing:
        print(f"  MISSING  cards with no entry in SOURCES: {', '.join(missing)}")

    print(f"\n{len(matched)} match, {len(drifted)} drifted, {len(unreadable)} unreadable.")
    if drifted or missing:
        print("Refresh the card figures in _fleet/mechs_template.md and the MECHS block "
              "in _fleet/fleet_fragment.html, then rerun assemble_page.py.")
        return 1
    if unreadable:
        # A site that cannot be reached is not the same as a wrong number, and a
        # nightly red for someone else's outage teaches people to ignore it.
        print("Nothing drifted, but some sites could not be read; see above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
