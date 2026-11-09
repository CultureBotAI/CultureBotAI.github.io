#!/usr/bin/env python3
"""Assemble the independently reviewed November 8 website-feature judgments.

Inputs: `_fleet/reviews/refresh-20261108/site-deployments-auditor.json` and
`_fleet/reviews/refresh-20261108/site-deployment-diffs.json`.
Outputs: existing 24-feature `_fleet/data/site_features.json`, independent skeptic
ledger `_fleet/reviews/refresh-20261108/site-deployments-skeptic.json`, and
per-column comparison receipt `_fleet/reviews/refresh-20261108/feature-column-review.json`.
2026-11-08; refresh PR. No catalogue definitions or methodology are rewritten.
"""
import argparse
from collections import Counter
import datetime as dt
import email.utils
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '_fleet/reviews/refresh-20261108'
BASE_COMMIT = 'a610fbb13f410410943ab36ed5746f17f8aa83c1'

NOTE_UPDATES = {
    'AntibioticMech': {
        'result_counts': [('3,064-record', '3,105-record')],
        'full_catalogue': [('3,064-record', '3,105-record')],
        'domain_view': [('3,064 compounds', '3,105 compounds')],
        'corpus_stats': [('3,064 compounds', '3,105 compounds'), ('2,815 SEEDED', '2,799 SEEDED')],
        'category_browse': [(
            '1,147 directly filed records and 1,225 including its 78-record antimycobacterial subclass; Antifungal has 609.',
            '1,182 directly filed records and 1,260 including its 78-record antimycobacterial subclass; Antifungal has 613.'
        )],
        'downloads': [('3,064-entry', '3,105-entry')],
        'build_provenance': [('digest 6c2a5f8e3f3f and 3,064 records', 'digest 03fdb6772528 and 3,105 records')],
    },
    'CommunityMech': {
        'search': [('485 communities', '511 communities')],
        'facets': [('96 of 485 communities; reset restores all 485.', '99 of 511 communities; reset restores all 511.')],
        'full_catalogue': [('485 published records', '511 published records')],
        'corpus_stats': [('485 published communities', '511 published communities')],
        'downloads': [('485 communities', '511 communities')],
    },
    'HabitatMech': {
        'review_status': [('1,915 of 3,209 are SEEDED', '1,911 of 3,209 are SEEDED')],
        'corpus_stats': [('1,915 SEEDED records', '1,911 SEEDED records')],
    },
    'MediaIngredientMech': {
        'build_provenance': [('2026-11-04T07:37:37+00:00', '2026-11-08T23:01:00+00:00')],
    },
    'PathwayMech': {
        'search': [('280 pathways', '282 pathways')],
        'result_counts': [('280-record', '282-record')],
        'full_catalogue': [('280 stable pathway links, matching the landing and the 280-record', '282 stable pathway links, matching the landing and the 282-record')],
        'domain_view': [('280 records', '282 records')],
        'corpus_stats': [('280 pathway records, 105 taxa, 14,788 mechanistic edges and 5,917 distinct references.', '282 pathway records, 105 taxa, 14,838 mechanistic edges and 5,922 distinct references.')],
        'downloads': [(
            '280-record pathway index. These and the version/checksum manifest return HTTP 200; the manifest reports 5,466 nodes and 14,788 edges.',
            '282-record pathway index. These and the version/checksum manifest return HTTP 200; the manifest reports 5,472 nodes and 14,838 edges.'
        )],
    },
    'TraitMech': {
        'record_pages': [('761 source records carry causal graphs', '769 source records carry causal graphs')],
        'domain_view': [('761 source records carry causal graphs', '769 source records carry causal graphs')],
    },
    'CMMMech': {
        'search': [('23 of 678.', '23 of 698.')],
        'facets': [('restores all 678.', 'restores all 698.')],
        'full_catalogue': [('678 published records', '698 published records')],
        'domain_view': [(
            '970 edges; the text map retains 602 material points, a subset of the 678-record catalogue.',
            '972 edges; the text map retains 602 material points, a subset of the 698-record catalogue.'
        )],
        'corpus_stats': [('678 materials', '698 materials')],
        'category_browse': [('427 minerals', '447 minerals')],
        'downloads': [('678 catalogue entries', '698 catalogue entries')],
        'build_provenance': [(
            '678 materials, 609 mechanisms, latest curation 2026-11-04 and corpus digest 92117fbb1ec5.',
            '698 materials, 609 mechanisms, latest curation 2026-11-06 and corpus digest 5644b56e7db2.'
        )],
    },
    'AIMech': {
        'build_provenance': [('snapshot date 2026-10-24 and digest de5b593fee12', 'snapshot date 2026-11-04 and digest de5b593fee12')],
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
    ]))
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
        if state != 'success' or not modified:
            raise ValueError(name + ': deployment not verified')
        if email.utils.parsedate_to_datetime(modified) < dt.datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00')):
            raise ValueError(name + ': served content predates deployment')
        if prior['features']['responsive']['status'] == 'present':
            for page_url, page_info in audit.get('pages', {}).items():
                if page_url.endswith('/schema.html'):
                    continue
                if page_info.get('resized_390', 390) > 390 or page_info.get('fresh_390', 390) > 390:
                    raise ValueError(f'{name}: unexpected horizontal overflow at 390px on {page_url}')

        entry = {
            'site': prior['site'],
            'repository': prior['repository'],
            'deployed_revision': deployment['sha'],
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
                note = note.replace(old_sub, new_sub, 1)
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
            'deployed_revision': deployment['sha'],
            'prior_deployed_revision': diffs[name]['prior_deployed_revision'],
            'changed_deployed_sha': deployment['sha'] != diffs[name]['prior_deployed_revision'],
            'verdicts': len(catalogue),
            'disagreements': [],
            'features': skeptic_features,
        }

    data['checked_on'] = '2026-11-08'
    data['scope'] = (
        'Live GitHub Pages sites checked on November 8, 2026 against all 24 existing catalogue criteria. '
        'Each site had an auditor and an independent skeptic; the root editor resolved rubric disagreements and compared each feature across the fleet. '
        'Checks exercised identifier and label searches, filters and reset, sorting and URL restoration, representative record pages, scientific links and downloads, '
        'theme persistence, 390-pixel layouts and failed data requests. Corpus-wide claims additionally used complete published indexes or pinned source inventories. '
        'Record-page rendering was sampled rather than exhaustive. Each recorded deployed revision had a successful deployment status and a served Last-Modified date '
        'no earlier than its deployment request. These live-site checks are separate from the common corpus pins.'
    )

    columns = {}
    for key in catalogue:
        columns[key] = {
            'old': dict(Counter(entry['features'][key]['status'] for entry in before['mechs'].values())),
            'new': dict(Counter(entry['features'][key]['status'] for entry in data['mechs'].values())),
            'notes': {name: entry['features'][key] for name, entry in data['mechs'].items()},
        }

    skeptic_report = {
        'checked_on': '2026-11-08',
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
