#!/usr/bin/env python3
"""Propagate Nov 4 recent-terms output to the three dedicated Mech pages.

Inputs: _fleet/data/recent_terms.json. Outputs: bounded Recent Additions sections.
Serves the refresh PR's recent-additions propagation issue; 2026-11-04.
No history, sort, counting or pin methodology changes. Dry-run by default.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = {
    'CommunityMech': ('communitymech.md', 'community and isolate records'),
    'MediaIngredientMech': ('mediaingredientmech.md', 'ingredient records'),
    'CultureMech': ('culturemech.md', 'merged canonical media'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=PAGES)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / '_fleet/data/recent_terms.json').read_text())
    rows = {item['mech']: item for item in data['mechs']}
    for name, (filename, entity) in PAGES.items():
        if args.only and args.only != name:
            continue
        row = rows[name]
        assert len(row['records']) == 5
        sha = row['source_revision']
        section = f"\n\nFive most recently added {entity} in the pinned repository snapshot ([`{sha[:7]}`](https://github.com/CultureBotAI/{row['repo']}/tree/{sha})):\n\n"
        for number, record in enumerate(row['records'], 1):
            label = record['label'].replace('[', '\\[').replace(']', '\\]')
            section += f"{number}. **[{label}]({record['url']})** (`{record['id']}`, added {record['added_date']})\n"
        section += '\nSee all fourteen Mechs\' recent additions on the [X-Mech Suite overview](/mechs/#recent-additions).\n\n'
        path = ROOT / filename
        text = path.read_text()
        prefix, remainder = text.split('## Recent Additions', 1)
        _, suffix = remainder.split('\n## ', 1)
        result = prefix + '## Recent Additions' + section + '## ' + suffix
        print(filename + (': update' if result != text else ': unchanged'))
        if args.apply:
            path.write_text(result)
            assert section in path.read_text()


if __name__ == '__main__':
    main()
