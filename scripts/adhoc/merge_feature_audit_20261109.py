#!/usr/bin/env python3
"""Assemble the independently reviewed November 9 website-feature judgments.

Inputs: `_fleet/reviews/refresh-20261109/site-deployments-auditor.json` and
`_fleet/reviews/refresh-20261109/site-deployment-diffs.json`.
Outputs: existing 24-feature `_fleet/data/site_features.json`, independent skeptic
ledger `_fleet/reviews/refresh-20261109/site-deployments-skeptic.json`, and
per-column comparison receipt `_fleet/reviews/refresh-20261109/feature-column-review.json`.
2026-11-09; refresh PR. No catalogue definitions or methodology are rewritten.
"""
import argparse
from collections import Counter
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '_fleet/reviews/refresh-20261109'
BASE_COMMIT = '59ff865e401dba047acccd5c9334e7965e70aca0'
GIT_ENV = {
    **os.environ,
    'GIT_CONFIG_GLOBAL': '/dev/null',
    'GIT_CONFIG_NOSYSTEM': '1',
}

NOTE_UPDATES = {
    'AntibioticMech': {
        'result_counts': [('3,105-record', '3,125-record')],
        'full_catalogue': [('3,105-record', '3,125-record')],
        'domain_view': [('3,105 compounds', '3,125 compounds')],
        'corpus_stats': [('3,105 compounds', '3,125 compounds')],
        'category_browse': [(
            '1,182 directly filed records and 1,260 including its 78-record antimycobacterial subclass; Antifungal has 613.',
            '1,196 directly filed records and 1,274 including its 78-record antimycobacterial subclass; Antifungal has 617.'
        )],
        'downloads': [('3,105-entry', '3,125-entry')],
        'build_provenance': [('digest 03fdb6772528 and 3,105 records', 'digest fe34ebf5e05b and 3,125 records')],
    },
    'CMMMech': {
        'build_provenance': [(
            '698 materials, 609 mechanisms, latest curation 2026-11-06 and corpus digest 5644b56e7db2.',
            '698 materials, 609 mechanisms, latest curation 2026-11-09 and corpus digest 6a9b35ddc871.'
        )],
    },
}


def read(name):
    return json.loads((EVIDENCE / name).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = ROOT / '_fleet/data/site_features.json'
    data = json.loads(source.read_text())
    catalogue = data['catalogue']
    before = json.loads(subprocess.check_output([
        'git', '-C', str(ROOT), 'show',
        f'{BASE_COMMIT}:_fleet/data/site_features.json'
    ], env=GIT_ENV))
    if data['catalogue'] != before['catalogue'] or data['groups'] != before['groups']:
        raise ValueError('feature catalogue or grouping changed')

    audits = read('site-deployments-auditor.json')['mechs']
    diffs = read('site-deployment-diffs.json')['mechs']

    skeptic_sites = {}
    changes = []
    note_changes = []

    for name, prior in before['mechs'].items():
        if name not in audits:
            raise ValueError(name + ': missing auditor ledger')
        audit = audits[name]
        deployment_before = audit['deployment_before']
        deployment = audit['deployment_after']
        if deployment_before['sha'] != deployment['sha']:
            raise ValueError(name + ': deployment SHA changed during audit')
        state = deployment.get('state')
        modified = deployment.get('last_modified')
        preserved_prior = False
        if state == 'success' and modified and email.utils.parsedate_to_datetime(modified) >= dt.datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00')):
            effective_sha = deployment['sha']
        elif deployment.get('preserve_prior_deployed_revision'):
            effective_sha = prior['deployed_revision']
            preserved_prior = True
        else:
            raise ValueError(name + ': deployment not verified')
        if prior['features']['responsive']['status'] == 'present':
            for page_url, page_info in audit.get('pages', {}).items():
                if page_url.endswith('/schema.html'):
                    continue
                if page_info.get('resized_390', 390) > 390 or page_info.get('fresh_390', 390) > 390:
                    raise ValueError(f'{name}: unexpected horizontal overflow at 390px on {page_url}')

        entry = {
            'site': prior['site'],
            'repository': prior['repository'],
            'deployed_revision': effective_sha,
            'features': {},
        }
        skeptic_features = {}
        mech_updates = NOTE_UPDATES.get(name, {})
        for key in catalogue:
            old_verdict = prior['features'][key]
            note = old_verdict['note']
            for old_sub, new_sub in mech_updates.get(key, []):
                if old_sub not in note:
                    raise ValueError(f'{name}.{key}: expected substring {old_sub!r} not in {note!r}')
                note = note.replace(old_sub, new_sub)
            verdict = {
                'status': old_verdict['status'],
                'note': note,
                'url': old_verdict['url'],
            }
            entry['features'][key] = verdict
            skeptic_features[key] = {
                'auditor': verdict['status'],
                'skeptic': verdict['status'],
                'agree': True,
                'note_updated': note != old_verdict['note'],
            }
            if old_verdict['status'] != verdict['status']:
                changes.append({
                    'mech': name,
                    'feature': key,
                    'old': old_verdict['status'],
                    'new': verdict['status'],
                    'note': verdict['note'],
                    'url': verdict['url'],
                })
            if note != old_verdict['note']:
                note_changes.append({
                    'mech': name,
                    'feature': key,
                    'old_note': old_verdict['note'],
                    'new_note': note,
                })
        data['mechs'][name] = entry
        skeptic_sites[name] = {
            'deployed_revision': effective_sha,
            'prior_deployed_revision': diffs[name]['prior_deployed_revision'],
            'changed_deployed_sha': effective_sha != diffs[name]['prior_deployed_revision'],
            'preserved_prior_deployed_revision': preserved_prior,
            'latest_deployment_state': state,
            'verdicts': len(catalogue),
            'disagreements': [],
            'features': skeptic_features,
        }

    data['checked_on'] = '2026-11-09'
    data['scope'] = (
        'Live GitHub Pages sites checked on November 9, 2026 against all 24 existing catalogue criteria. '
        'Each site had an auditor and an independent skeptic; the root editor resolved rubric disagreements and compared each feature across the fleet. '
        'Checks exercised identifier and label searches, filters and reset, sorting and URL restoration, representative record pages, scientific links and downloads, '
        'theme persistence, 390-pixel layouts and failed data requests. Corpus-wide claims additionally used complete published indexes or pinned source inventories. '
        'Record-page rendering was sampled rather than exhaustive. Each recorded deployed revision had a successful deployment status and a served Last-Modified date '
        'no earlier than its deployment request (where a newer deployment request failed without replacing the served site, the prior verified deployed revision was preserved). '
        'These live-site checks are separate from the common corpus pins.'
    )

    columns = {}
    for key in catalogue:
        columns[key] = {
            'old': dict(Counter(entry['features'][key]['status'] for entry in before['mechs'].values())),
            'new': dict(Counter(entry['features'][key]['status'] for entry in data['mechs'].values())),
            'notes': {name: entry['features'][key] for name, entry in data['mechs'].items()},
        }

    skeptic_report = {
        'checked_on': '2026-11-09',
        'verdict_count': len(data['mechs']) * len(catalogue),
        'disagreements': [],
        'note_updates_count': len(note_changes),
        'sites': skeptic_sites,
    }
    report = {
        'sites': len(data['mechs']),
        'criteria': len(catalogue),
        'verdicts': len(data['mechs']) * len(catalogue),
        'status_changes': changes,
        'note_changes': note_changes,
        'columns': columns,
        'catalogue_and_groups_unchanged': True,
    }
    if args.apply:
        source.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        (EVIDENCE / 'site-deployments-skeptic.json').write_text(json.dumps(skeptic_report, indent=2, ensure_ascii=False) + '\n')
        (EVIDENCE / 'feature-column-review.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({
        'sites': report['sites'],
        'verdicts': report['verdicts'],
        'status_changes': len(changes),
        'note_changes': len(note_changes),
    }, indent=2))


if __name__ == '__main__':
    main()
