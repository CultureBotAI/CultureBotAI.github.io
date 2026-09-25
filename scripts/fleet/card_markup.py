"""The one parser for the Mech cards in _fleet/mechs_template.md.

assemble_page.py, check_cards.py and the tests used to read the card markup with
three separate regexes, and check_cards.py paired each Mech with the *next*
figure in the file, so a card missing its figure silently took its neighbour's
(#114). Everything now reads the cards here, one <article> at a time.
"""
from __future__ import annotations

import collections
import re

ARTICLE = re.compile(r'<article\b[^>]*\bdata-mech="([^"]+)"[^>]*>(.*?)</article>', re.S)
# A card's headline tile, counted whatever it holds, so a malformed second tile
# cannot slip past the one-per-card rule (#261).
TILE = re.compile(r'<div class="num">')
# The figure in a tile: digits with thousands commas, starting with a digit, so
# "<b>,</b>" is unreadable rather than int("") (#261).
FIGURE = re.compile(r'<div class="num"><b>(\d[\d,]*)</b>')


def card_names(template: str) -> list[str]:
    """Every card's Mech, in page order, duplicates kept."""
    return [mech for mech, _ in ARTICLE.findall(template)]


def markup_problems(template: str) -> list[tuple[str, str]]:
    """(Mech, what is wrong) for every card that does not state exactly one figure.

    A card with two figures used to be read as its first, and a figure outside
    every card was ignored, so a second stat tile changed the fleet total without
    failing anything (#218). "-" stands for a figure that belongs to no card.
    """
    problems = []
    for mech, body in ARTICLE.findall(template):
        tiles = len(TILE.findall(body))
        if tiles == 0:
            problems.append((mech, "card has no headline figure"))
        elif tiles > 1:
            problems.append((mech, f"card has {tiles} headline figures; it must have exactly one"))
        elif not FIGURE.search(body):
            problems.append((mech, "card's headline figure is unreadable"))
    for mech, count in collections.Counter(card_names(template)).items():
        if count > 1:
            # The nightly would check only one of them (#262).
            problems.append((mech, f"{count} cards for one Mech"))
    outside = len(TILE.findall(ARTICLE.sub("", template)))
    if outside:
        problems.append(("-", f"{outside} headline figure(s) outside any card"))
    return problems


def card_figures(template: str) -> dict[str, int]:
    """Each card's headline figure, keyed by Mech.

    Read inside the card's own <article>, so a card without a figure is absent
    rather than borrowing the next card's. A card with more than one headline
    tile, an unreadable one, or a second card for the same Mech is absent too;
    markup_problems() says which cards those are.
    """
    names = collections.Counter(card_names(template))
    figures: dict[str, int] = {}
    for mech, body in ARTICLE.findall(template):
        hits = FIGURE.findall(body)
        if names[mech] == 1 and len(TILE.findall(body)) == 1 and len(hits) == 1:
            figures[mech] = int(hits[0].replace(",", ""))
    return figures
