#!/usr/bin/env python3
"""Assemble the independently reviewed November 4 website-feature judgments.

Inputs: 14 auditor ledgers, independent skeptic ledgers, and root arbitration.
Outputs: existing 24-feature data file plus a per-column comparison receipt.
2026-11-04; refresh PR. No catalogue definitions or methodology are rewritten.
"""
import argparse
from collections import Counter
import datetime as dt
import email.utils
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '_fleet/reviews/refresh-20261104'
GROUP_A = ['CellStructureMech', 'AntibioticMech', 'NaturalProductMech', 'HabitatMech', 'TaxonMech', 'PathwayMech']


def read(name):
    return json.loads((EVIDENCE / name).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = ROOT / '_fleet/data/site_features.json'
    data = json.loads(source.read_text())
    catalogue = data['catalogue']
    before = json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show',
                        '56ec3db204095e425e2ed7481d4f97b997906815:_fleet/data/site_features.json']))
    if data['catalogue'] != before['catalogue'] or data['groups'] != before['groups']:
        raise ValueError('feature catalogue or grouping changed')
    a_review = read('group-a-skeptic-b.json')
    b_review = read('group-b-independent-review.json')
    trait_review = read('trait-skeptic.json')
    b_rows = read('group-b-proposed-rows.json')
    if a_review['disagreements'] or b_review['disagreements']:
        raise ValueError('unresolved independent review disagreement')
    if a_review['verdict_count'] != 144:
        raise ValueError('incomplete group A review')
    changes = []
    for name, prior in data['mechs'].items():
        if name == 'TraitMech':
            audit = read('trait-auditor.json')
        elif name in GROUP_A:
            audit = read(name.lower() + '-auditor-a.json')
        else:
            audit = read(name.lower() + '-auditor-b.json')
        features = audit['features']
        if set(features) != set(catalogue):
            raise ValueError(name + ': incomplete feature audit')
        deployment = audit['deployment_after']
        if name in a_review.get('redeployment_addenda', {}):
            addition = a_review['redeployment_addenda'][name]
            assert addition['verdicts'] == len(catalogue) and not addition['disagreements']
            followup = audit['redeployment_followup']
            assert followup['public_tree_hashes_unchanged'] and followup['status_changes'] == 0
            deployment = followup['deployment_after']
            assert deployment['sha'] == addition['deployed_revision']
        state = deployment.get('state', deployment.get('latest_status', {}).get('state'))
        modified = deployment.get('last_modified', deployment.get('headers', {}).get('Last-Modified'))
        if state != 'success' or not modified:
            raise ValueError(name + ': deployment not verified')
        if email.utils.parsedate_to_datetime(modified) < dt.datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00')):
            raise ValueError(name + ': served content predates deployment')
        entry = {'site': b_rows.get(name, prior)['site'], 'repository': prior['repository'],
                 'deployed_revision': deployment['sha'], 'features': {}}
        for key in catalogue:
            verdict = {field: features[key][field] for field in ('status', 'note', 'url')}
            if name in GROUP_A:
                assert a_review['sites'][name]['statuses'][key] == verdict['status']
            elif name != 'TraitMech':
                reviewed = b_review['features'][name][key]
                assert reviewed['agree'] and reviewed['skeptic'] == verdict['status']
                assert b_rows[name]['features'][key] == verdict
            else:
                # The original Trait schema-source disagreement is resolved by
                # the independent skeptic and the root arbitration, both partial.
                assert trait_review['features'][key]['status'] == verdict['status']
            entry['features'][key] = verdict
            if before['mechs'][name]['features'][key]['status'] != verdict['status']:
                changes.append({'mech': name, 'feature': key, 'old': before['mechs'][name]['features'][key]['status'],
                                'new': verdict['status'], 'note': verdict['note'], 'url': verdict['url']})
        data['mechs'][name] = entry
    data['checked_on'] = '2026-11-04'
    data['scope'] = (
        'Live GitHub Pages sites checked on November 4, 2026 against all 24 existing catalogue criteria. '
        'Each site had an auditor and an independent skeptic; the root editor resolved rubric disagreements and compared each feature across the fleet. '
        'Checks exercised identifier and label searches, filters and reset, sorting and URL restoration, representative record pages, scientific links and downloads, '
        'theme persistence, 390-pixel layouts and failed data requests. Corpus-wide claims additionally used complete published indexes or pinned source inventories. '
        'Record-page rendering was sampled rather than exhaustive. Each recorded deployed revision had a successful deployment status and a served Last-Modified date '
        'no earlier than its deployment request. These live-site checks are separate from the common corpus pins.')
    columns = {}
    for key in catalogue:
        columns[key] = {'old': dict(Counter(entry['features'][key]['status'] for entry in before['mechs'].values())),
                        'new': dict(Counter(entry['features'][key]['status'] for entry in data['mechs'].values())),
                        'notes': {name: entry['features'][key] for name, entry in data['mechs'].items()}}
    report = {'sites': len(data['mechs']), 'criteria': len(catalogue), 'verdicts': len(data['mechs']) * len(catalogue),
              'status_changes': changes, 'columns': columns, 'catalogue_and_groups_unchanged': True}
    if args.apply:
        source.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        (EVIDENCE / 'feature-column-review.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'sites': report['sites'], 'verdicts': report['verdicts'], 'status_changes': changes}, indent=2))


if __name__ == '__main__':
    main()
