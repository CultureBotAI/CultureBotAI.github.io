#!/usr/bin/env python3
"""Account for the Nov 9 refresh diff for its PR and independent review.

Inputs: base Git commit and current fleet products. Outputs: reproducible JSON
and Markdown receipts. No production files or shared checkouts are changed.
2026-11-09; refresh PR number is assigned after validation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
from card_markup import card_figures

GIT_ENV = {
    **os.environ,
    'GIT_CONFIG_GLOBAL': '/dev/null',
    'GIT_CONFIG_NOSYSTEM': '1',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='59ff865e401dba047acccd5c9334e7965e70aca0')
    args = parser.parse_args()
    def before(path):
        return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{args.base}:{path}'], env=GIT_ENV)
    def data(name, old=False):
        path = '_fleet/data/' + name + '.json'
        return json.loads(before(path) if old else (ROOT / path).read_bytes())
    old, new = data('mech_stats', True), data('mech_stats')
    old_rows = {row['mech']: row for row in old['mechs']}
    old_cards = card_figures(before('_fleet/mechs_template.md').decode())
    new_cards = card_figures((ROOT / '_fleet/mechs_template.md').read_text())
    result = {'base': args.base, 'totals': {}, 'mechs': [], 'methodology': {}, 'cells': {}, 'edges': {}}
    for name, a, b in [
        ('merged_prs', old['merged_prs_total'], new['merged_prs_total']),
        ('mech_merged_prs', sum(r['merged_prs'] for r in old['mechs']), sum(r['merged_prs'] for r in new['mechs']),),
        ('repository_records', sum(r['records'] for r in old['mechs']), sum(r['records'] for r in new['mechs'])),
        ('card_records', sum(old_cards.values()), sum(new_cards.values())),
        ('vocabularies', len(data('fleet_data', True)['voc']), len(data('fleet_data')['voc']))]:
        result['totals'][name] = {'old': a, 'new': b, 'delta': b - a}
    old_additional = {row['repo']: row for row in old['additional_repositories']}
    result['additional_repositories'] = [
        {'repo': row['repo'], 'merged_prs_old': old_additional[row['repo']]['merged_prs'],
         'merged_prs_new': row['merged_prs']}
        for row in new['additional_repositories']]
    for row in new['mechs']:
        previous = old_rows[row['mech']]
        result['mechs'].append({
            'mech': row['mech'], 'pin': row['source_revision'],
            'records_old': previous['records'], 'records_new': row['records'],
            'card_old': old_cards[row['mech']], 'card_new': new_cards[row['mech']],
            'merged_prs_old': previous['merged_prs'], 'merged_prs_new': row['merged_prs'],
            'reviewed_old': previous.get('reviewed'), 'reviewed_new': row.get('reviewed')})
    for name in ('cells', 'edges'):
        stem = 'cells_summary' if name == 'cells' else 'subsets_summary'
        a, b = data(stem, True)[name], data(stem)[name]
        result[name] = {'old_count': len(a), 'new_count': len(b),
                        'added': sorted(b.keys() - a.keys()), 'removed': sorted(a.keys() - b.keys()),
                        'changed': sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}
    for path in ['scripts/fleet/prefix_census.py', 'scripts/fleet/roots.py',
                 'scripts/fleet/build_subsets.py', 'scripts/fleet/build_cells.py',
                 'scripts/fleet/build_data.py', 'scripts/fleet/mech_stats.py',
                 '_fleet/kg_microbe_source.json', '_fleet/data/kg_microbe_census.json']:
        current = (ROOT / path).read_bytes()
        result['methodology'][path] = {'unchanged': before(path) == current,
                                       'sha256': hashlib.sha256(current).hexdigest()}
        if not result['methodology'][path]['unchanged']:
            raise ValueError(f'methodology changed: {path}')
    lines = ['# Refresh comparison — November 9, 2026', '', f'Base: `{args.base}`.', '',
             '| Measure | Previous | Refreshed | Delta |', '| --- | ---: | ---: | ---: |']
    for name, row in result['totals'].items():
        lines.append(f"| {name} | {row['old']:,} | {row['new']:,} | {row['delta']:+,} |")
    lines += ['', '| Mech | Old records | New records | Old merged PRs | New merged PRs | Pin |',
              '| --- | ---: | ---: | ---: | ---: | --- |']
    for row in result['mechs']:
        lines.append(f"| {row['mech']} | {row['records_old']:,} | {row['records_new']:,} | {row['merged_prs_old']:,} | {row['merged_prs_new']:,} | `{row['pin']}` |")
    lines += ['', '| Supporting repository | Old merged PRs | New merged PRs |', '| --- | ---: | ---: |']
    for row in result['additional_repositories']:
        lines.append(f"| {row['repo']} | {row['merged_prs_old']:,} | {row['merged_prs_new']:,} |")
    lines += ['', 'Counting code, record globs, prefix normalization, graph extraction and the kg-microbe release comparison are byte-identical to the base.', '']
    for name in ('cells', 'edges'):
        row = result[name]
        lines.append(f"{name}: {row['old_count']} → {row['new_count']}; {len(row['changed'])} metadata entries changed, {len(row['added'])} added, {len(row['removed'])} removed.")
    out = ROOT / '_fleet/reviews/refresh-20261109'
    (out / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / 'comparison.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(result['totals'], indent=2))


if __name__ == '__main__':
    main()
