#!/usr/bin/env python3
"""Propagate verified November 9 figures into maintained page sources.

Inputs: pinned source-excerpts/secondary receipts and live browser audit receipts.
Outputs: maintained prose and graph facts; generated products use normal builders.
Date 2026-11-09; refresh PR. Dry-run by default; canary --only HabitatMech --apply.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FILES = ['_fleet/mechs_template.md', '_fleet/fleet_fragment.html', '_fleet/README.md',
         'index.md', 'resources.md', 'research.md', 'microgrowagents.md',
         'culturemech.md', 'mediaingredientmech.md', 'communitymech.md', 'CLAUDE.md']
CHANGES = {
    'HabitatMech': [
        ('1,295 reviewed', '1,298 reviewed'),
        ('1,295 records with REVIEWED status; 2,149 ontology-grounded;', '1,298 records with REVIEWED status; 2,147 ontology-grounded;'),
    ],
    'CommunityMech': [
        ('lists 510 communities online; its repository has 515 community records and nine additional isolate records.',
         'lists 511 communities online and keeps eighteen additional isolate records in its repository.'),
        ('lists 510 communities online; its repository has 511 community records and eighteen additional isolate records.',
         'lists 511 communities online and keeps eighteen additional isolate records in its repository.'),
        ('**515 community records** and **nine additional isolate records**',
         '**511 community records** and **eighteen additional isolate records**'),
        ('515 community records and nine additional isolate records', '511 community records and eighteen additional isolate records'),
        ('510 communities across 16 categories', '511 communities across 16 categories'),
        ('510 curated communities', '511 curated communities'),
        ('510 communities,', '511 communities,'),
        ('CommunityMech\'s nine `data/isolates` records have no published page.',
         'CommunityMech\'s eighteen `data/isolates` records have no published page.'),
        ('CommunityMech\'s browser lists 510 communities; its repository\nhas 515 community files and nine isolates, so the census and statistics count 524.',
         'CommunityMech\'s browser lists 511 communities; its repository\nadditionally includes eighteen isolates, so the census and statistics count 529.'),
    ],
    'AntibioticMech': [
        ('3,105', '3,125'),
        ('2,767', '2,782'),
        ('338 minted', '343 minted'),
        ('539 records', '557 records'),
        ('361 with molecular', '374 with molecular'),
        ('361 a molecular', '374 a molecular'),
        ('91 with causal graphs', '97 with causal graphs'),
    ],
}
COUNTS = {
    'CommunityMech': (510, 511),
    'AntibioticMech': (3105, 3125),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=CHANGES)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    names = [args.only] if args.only else list(CHANGES)
    receipt = []
    for file in FILES:
        path = ROOT / file
        before = text = path.read_text()
        for name in names:
            for old, new in CHANGES[name]:
                # Whole lexical tokens: never rewrite SHA fragments, issue ids or CSS colors.
                pattern = r'(?<![\w#])' + re.escape(old) + r'(?!\w)'
                text, n = re.subn(pattern, lambda _: new, text)
                if n:
                    receipt.append({'path': file, 'mech': name, 'old': old, 'new': new, 'occurrences': n})
            if name in COUNTS:
                old, new = COUNTS[name]
                if file == '_fleet/mechs_template.md':
                    pattern = rf'(<article class="mech-card" data-mech="{name}".*?<div class="num"><b>){old:,}(</b>)'
                    text = re.sub(pattern, lambda m: m[1] + f'{new:,}' + m[2], text, flags=re.S)
                elif file == '_fleet/fleet_fragment.html':
                    pattern = rf'(    {name}: \{{[^\n]*?records: ){old}(,)'
                    text = re.sub(pattern, lambda m: m[1] + str(new) + m[2], text)
        if args.apply and text != before:
            path.write_text(text)
    if args.apply:
        destination = ROOT / '_fleet/reviews/refresh-20261109' / ('figure-edits-' + (args.only or 'fleet') + '.json')
        destination.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
