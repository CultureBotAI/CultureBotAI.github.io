#!/usr/bin/env python3
"""Propagate verified November 8 figures into maintained page sources.

Inputs: pinned source-excerpts/secondary receipts and live browser audit receipts.
Outputs: maintained prose and graph facts; generated products use normal builders.
Date 2026-11-08; refresh PR. Dry-run by default; canary --only TraitMech --apply.
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
    'TraitMech': [('761', '769')],
    'HabitatMech': [('1,294', '1,295'), ('1,915 SEEDED', '1,914 SEEDED'), ('342 populated cells', '346 populated cells')],
    'CommunityMech': [
        ('485 community', '515 community'),
        ('485 communities', '510 communities'),
        ('485 curated communities', '510 curated communities'),
        ('lists 510 communities online and keeps nine additional isolate records in its repository.',
         'lists 510 communities online; its repository has 515 community records and nine additional isolate records.'),
        ('its repository\nadditionally includes nine isolates, so the census and statistics count 494.',
         'its repository\nhas 515 community files and nine isolates, so the census and statistics count 524.'),
    ],
    'PathwayMech': [
        ('280 pathway', '282 pathway'),
        ('280 pathways', '282 pathways'),
        ('280 records', '282 records'),
        ('280 links', '282 links'),
        ('14,788', '14,838'),
        ('5,917', '5,922'),
    ],
    'AntibioticMech': [
        ('3,064', '3,105'),
        ('2,740', '2,767'),
        ('324 minted', '338 minted'),
        ('506 records', '539 records'),
        ('333 with molecular', '361 with molecular'),
        ('333 a molecular', '361 a molecular'),
        ('75 with causal graphs', '91 with causal graphs'),
    ],
    'CMMMech': [
        ('678 material', '698 material'),
        ('678 critical-material', '698 critical-material'),
        ('678\nrecords', '698\nrecords'),
        ('427 mineral', '447 mineral'),
        ('178 remain', '198 remain'),
    ],
}
COUNTS = {
    'CommunityMech': (485, 510),
    'PathwayMech': (280, 282),
    'AntibioticMech': (3064, 3105),
    'CMMMech': (678, 698),
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
        destination = ROOT / '_fleet/reviews/refresh-20261108' / ('figure-edits-' + (args.only or 'fleet') + '.json')
        destination.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
