#!/usr/bin/env python3
"""Integrate independently reviewed November 19 feature judgments.

Inputs: three auditor proposals and root's completed review record.
Outputs: site_features.json and change ledger; assemble_page.py renders the page.
This feature-only update deliberately leaves corpus pins and artifacts unchanged.
2026-11-19, browser-feature revalidation PR.
"""
import copy
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / '_fleet/reviews/site-features-20261119'
BASELINE = 'bc50236b513043e907481c4a71b40d5251fcf744'


def main():
    completed = json.loads((REVIEW / 'review-complete.json').read_text())
    assert completed['all_384_verdicts_reviewed'] is True
    assert completed['cross_column_review_complete'] is True
    for path in completed['review_records']:
        assert (ROOT / path).is_file(), path
    old = json.loads(subprocess.check_output(['git', 'show', f'{BASELINE}:_fleet/data/site_features.json'], cwd=ROOT, text=True))
    merged = copy.deepcopy(old)
    proposals = {}
    for group in ('root', 'group-a', 'group-b'):
        rows = json.loads((REVIEW / group / 'proposals.json').read_text())
        assert not set(rows) & set(proposals), group
        proposals.update(rows)
    assert set(proposals) == set(old['mechs']) and len(proposals) == 16
    # Apply recorded arbiter decisions while preserving the original auditor rows.
    for decision in json.loads((REVIEW / 'arbitration.json').read_text())['overrides']:
        value = proposals[decision['mech']]['features'][decision['feature']]
        assert value['status'] == decision['auditor_status']
        value['status'] = decision['final_status']
        value['note'] = decision['final_note']
    changes = []
    for name, proposal in proposals.items():
        assert set(proposal['features']) == set(old['catalogue'])
        assert proposal['checked_on'] == '2026-11-19'
        row = {key: proposal[key] for key in ('site', 'repository', 'deployed_revision')}
        assert row['site'] == old['mechs'][name]['site']
        row['features'] = {}
        for feature in old['catalogue']:
            value = {key: proposal['features'][feature][key] for key in ('status', 'note', 'url')}
            row['features'][feature] = value
            prior = old['mechs'][name]['features'][feature]
            if value != prior:
                changes.append({'mech': name, 'feature': feature, 'previous': prior, 'current': value,
                                'rating_changed': value['status'] != prior['status']})
        merged['mechs'][name] = row
    merged['checked_on'] = '2026-11-19'
    merged['scope'] = ('All sixteen published corpus Mech sites were rechecked against the existing 24 criteria on November 19, 2026 (America/Los_Angeles; evidence timestamps are UTC). Every verdict had an auditor and an independent skeptic, followed by a cross-site comparison of each criterion. Live Chrome/Playwright checks exercised identifier and label search, filters/reset, sorting and URL restoration where offered, populated record views, scientific links and downloads, persisted themes, fresh and resized 390-pixel layouts, and failed data requests with recovery. Complete published indexes, manifests or deployed source inventories support catalogue coverage; record rendering was sampled except for all CofactorMech and AssayMech records. Successful deployment statuses and served Last-Modified dates were verified before and after each pass. Redeployment alone did not change a rating. These observations are separate from the retained corpus census and its pins. EdgeMech remains separately listed infrastructure; its proposed sample browser is not a published-site audit.')
    target = ROOT / '_fleet/data/site_features.json'
    target.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + '\n')
    (REVIEW / 'changes.json').write_text(json.dumps({'baseline': BASELINE, 'checked_on': merged['checked_on'],
        'verdicts': 384, 'rating_changes': sum(x['rating_changed'] for x in changes), 'changes': changes}, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'sites': 16, 'verdicts': 384, 'rating_changes': sum(x['rating_changed'] for x in changes)}))


if __name__ == '__main__':
    main()
