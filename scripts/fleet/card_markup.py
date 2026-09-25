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


def card_figures(template: str) -> dict[str, int]:
    """Each card's headline figure, keyed by Mech.

    Read inside the card's own <article>, so a card without a figure is absent
    rather than borrowing the next card's.
    """
    figures: dict[str, int] = {}
    for mech, body in ARTICLE.findall(template):
        hit = FIGURE.search(body)
        if hit:
            figures[mech] = int(hit.group(1).replace(",", ""))
    return figures
