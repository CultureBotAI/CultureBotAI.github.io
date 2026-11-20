#!/usr/bin/env python3
"""Package complete Group A evidence without modifying original receipts/screens.

Inputs: completed raw.json and supplemental JSON in the accepted attempts.
Outputs: deterministic gzip copies plus compact publication.json with original
and compressed SHA256 values and screenshot inventory. Website feature audit,
2026-11-19. --plan writes nothing; begin with HabitatMech before the other sites.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '_fleet/reviews/site-features-20261119/group-a'
ATTEMPTS = {'HabitatMech': 'audit-3', 'CommunityMech': 'audit-1', 'TaxonMech': 'audit-1', 'PathwayMech': 'audit-2', 'CellStructureMech': 'audit-2', 'AntibioticMech': 'audit-1'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mech', required=True, choices=ATTEMPTS)
    ap.add_argument('--plan', action='store_true')
    args = ap.parse_args()
    folder = BASE / args.mech / ATTEMPTS[args.mech]
    raw = json.loads((folder / 'raw.json').read_text())
    assert raw.get('finished_at') and raw.get('deployment_stable')
    sources = [folder / 'raw.json'] + sorted(folder.glob('followup-*.json'))
    target = folder / 'publication.json'
    if args.plan:
        print(json.dumps({'mech': args.mech, 'sources': [str(p.relative_to(ROOT)) for p in sources], 'output': str(target.relative_to(ROOT))}))
        return
    assert not target.exists(), target
    archives = []
    for source in sources:
        dest = source.with_suffix('.json.gz')
        assert not dest.exists(), dest
        body = source.read_bytes()
        compressed = gzip.compress(body, mtime=0)
        assert gzip.decompress(compressed) == body
        dest.write_bytes(compressed)
        assert dest.read_bytes() == compressed
        archives.append({'source': source.name, 'source_bytes': len(body), 'source_sha256': digest(body), 'archive': dest.name, 'archive_bytes': len(compressed), 'archive_sha256': digest(compressed)})
    summaries = {url: {'status': row.get('status'), 'error': row.get('error'), 'fresh_width': row.get('fresh_390', {}).get('scroll_width'), 'resized_width': row.get('resized_390', {}).get('scroll_width'), 'theme': row.get('desktop', {}).get('theme'), 'saved_theme': row.get('desktop', {}).get('saved_theme'), 'background': row.get('desktop', {}).get('background'), 'counts': row.get('desktop', {}).get('counts'), 'page_errors': row.get('page_errors'), 'screenshots': row.get('screenshots')} for url, row in raw['pages'].items()}
    screenshots = [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())} for p in sorted(folder.glob('*.png'))]
    summary = {'mech': args.mech, 'started_at': raw['started_at'], 'finished_at': raw['finished_at'], 'deployment_before': raw['deployment_before'], 'deployment_after': raw['deployment_after'], 'deployment_stable': raw['deployment_stable'], 'archives': archives, 'pages': summaries,
        'actions': {name: {'url': row.get('url'), 'counts': row.get('counts'), 'error': row.get('error')} for name, row in raw['actions'].items()},
        'downloads': {url: {'bytes': row['bytes'], 'sha256': row['sha256'], 'retained_body': row['retained_body']} for url, row in raw['downloads'].items()},
        'screenshots': screenshots, 'limits': 'Record rendering is sampled. Complete raw observations are losslessly archived; original raw JSON and screenshots remain retained locally and are not required to be committed. External 403/429 responses do not alone establish a broken citation or absent schema.'}
    target.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'mech': args.mech, 'archives': len(archives), 'bytes': sum(x['archive_bytes'] for x in archives), 'summary': str(target.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
