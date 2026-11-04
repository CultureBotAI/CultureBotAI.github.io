#!/usr/bin/env python3
"""Propagate verified November 4 figures into maintained page sources.

Inputs: pinned source-excerpts/secondary receipts and live browser audit receipts.
Outputs: maintained prose and graph facts; generated products use normal builders.
Date 2026-11-04; refresh PR. Dry-run by default; canary --only TraitMech --apply.
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
    'TraitMech': [('748', '761')],
    'HabitatMech': [('1,286', '1,294'), ('2,151', '2,149')],
    'CommunityMech': [('480 community', '485 community'), ('480 communities', '485 communities'),
                      ('480 curated communities', '485 curated communities'), ('count 489', 'count 494')],
    'PathwayMech': [('275 pathway', '280 pathway'), ('275 pathways', '280 pathways'), ('275 records', '280 records'),
                    ('275 links', '280 links'), ('14,691', '14,788'), ('5,912', '5,917')],
    'CellStructureMech': [('1,001', '1,022'), ('852', '873')],
    'ProteinTraitsMech': [('429,394', '429,421'), ('118,327', '118,338'), ('147,137', '147,149'),
                         ('391 sequence-structure', '392 sequence-structure'), ('12 evolution', '15 evolution')],
    'NaturalProductMech': [('3,116', '3,136'), ('3,407', '3,441'), ('806', '840'), ('2,341', '2,351'),
                          ('185 records', '216 records'), ('297 graph', '317 graph'),
                          ('297 have causal graphs', '317 have causal graphs'), ('795 individual', '815 individual')],
    'AntibioticMech': [('3,012', '3,064'), ('2,702', '2,740'), ('310 minted', '324 minted'),
                       ('492 records', '506 records'), ('309 with molecular', '333 with molecular'),
                       ('64 with causal graphs', '75 with causal graphs')],
    'CMMMech': [('663 material', '678 material'), ('663 critical-material', '678 critical-material'),
                ('663\nrecords', '678\nrecords'), ('412 mineral', '427 mineral'), ('499', '500'),
                ('607 mechanisms', '609 mechanisms'), ('164 remain', '178 remain')],
    'MediaIngredientMech': [('2,953', '2,956'), ('260 UNMAPPED', '262 UNMAPPED'), ('81 REJECTED', '82 REJECTED')],
}
COUNTS = {'CommunityMech': (480,485), 'PathwayMech': (275,280), 'CellStructureMech': (1001,1022),
          'ProteinTraitsMech': (429394,429421), 'NaturalProductMech': (3116,3136),
          'AntibioticMech': (3012,3064), 'CMMMech': (663,678), 'MediaIngredientMech': (2953,2956)}


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
        destination = ROOT / '_fleet/reviews/refresh-20261104' / ('figure-edits-' + (args.only or 'fleet') + '.json')
        destination.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
