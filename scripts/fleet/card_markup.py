"""The one parser for the Mech cards in _fleet/mechs_template.md.

assemble_page.py, check_cards.py and the tests used to read the card markup with
three separate regexes, and check_cards.py paired each Mech with the *next*
figure in the file, so a card missing its figure silently took its neighbour's
(#114). Everything now reads the cards here, one <article> at a time.
"""
from __future__ import annotations

import re

ARTICLE = re.compile(r'<article\b[^>]*\bdata-mech="([^"]+)"[^>]*>(.*?)</article>', re.S)
FIGURE = re.compile(r'<div class="num"><b>([\d,]+)</b>')


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
        count = len(FIGURE.findall(body))
        if count == 0:
            problems.append((mech, "card has no readable headline figure"))
        elif count > 1:
            problems.append((mech, f"card has {count} headline figures; it must have exactly one"))
    outside = len(FIGURE.findall(ARTICLE.sub("", template)))
    if outside:
        problems.append(("-", f"{outside} headline figure(s) outside any card"))
    return problems


def card_figures(template: str) -> dict[str, int]:
    """Each card's headline figure, keyed by Mech.

    Read inside the card's own <article>, so a card without a figure is absent
    rather than borrowing the next card's. A card with more than one figure is
    absent too; markup_problems() says which cards those are.
    """
    figures: dict[str, int] = {}
    for mech, body in ARTICLE.findall(template):
        hits = FIGURE.findall(body)
        if len(hits) == 1:
            figures[mech] = int(hits[0].replace(",", ""))
    return figures
