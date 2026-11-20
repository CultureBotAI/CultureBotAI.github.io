#!/usr/bin/env python3
"""Inspect retained Group A receipts and prove complete downloaded index coverage.

Inputs: a completed Nov19 browser receipt plus its hash-bound .temp downloads.
Outputs: stdout summary; --write-proof writes a new coverage.json beside that
receipt. Serves the website-feature-only revalidation, 2026-11-19. No network.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '_fleet/reviews/site-features-20261119/group-a'


def arrays(data, path='$'):
    if isinstance(data, list):
        yield path, data
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                yield from arrays(value, path + '.' + key)


def coverage(rows):
    result = {'rows': len(rows)}
    if not rows:
        return result
    if all(isinstance(row, dict) for row in rows):
        result['fields'] = {}
        keys = set().union(*(row.keys() for row in rows))
        for key in sorted(keys):
            if key not in ('id', 'identifier', 'slug', 'url', 'path', 'href', 'page', 'source_path', 'name', 'label', 'file'):
                continue
            values = [str(row[key]) for row in rows if row.get(key) is not None and str(row[key])]
            result['fields'][key] = {'nonempty': len(values), 'unique': len(set(values)), 'sha256': hashlib.sha256('\n'.join(sorted(values)).encode()).hexdigest(), 'samples': values[:2] + values[-2:]}
    elif all(isinstance(row, list) for row in rows):
        result['row_lengths'] = sorted(set(map(len, rows)))
        result['columns'] = {}
        for col in range(min(5, min(map(len, rows)))):
            values = [str(row[col]) for row in rows]
            result['columns'][str(col)] = {'nonempty': sum(bool(x) for x in values), 'unique': len(set(values)), 'sha256': hashlib.sha256('\n'.join(sorted(values)).encode()).hexdigest(), 'samples': values[:2] + values[-2:]}
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mech', required=True)
    ap.add_argument('--attempt', default='audit-1')
    ap.add_argument('--write-proof', action='store_true')
    ap.add_argument('--page', help='Print the retained desktop state for a URL suffix, without writes')
    args = ap.parse_args()
    folder = BASE / args.mech / args.attempt
    source = folder / 'raw.json'
    raw = json.loads(source.read_text())
    if not raw.get('finished_at') or not raw.get('deployment_stable'):
        raise SystemExit('Receipt is unfinished or lacks a stable verified deployment')
    if args.page:
        for url, row in raw['pages'].items():
            if url.endswith(args.page):
                desktop = row.get('desktop', {})
                print(json.dumps({'url': url, 'body': desktop.get('body'), 'links': desktop.get('all_links'), 'counts': desktop.get('counts'), 'headings': desktop.get('headings')}, indent=2))
        return
    proof = {'mech': args.mech, 'receipt': str(source.relative_to(ROOT)), 'receipt_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'deployed_revision': raw['deployment_after']['sha'], 'downloads': {}}
    for url, item in raw['downloads'].items():
        path = ROOT / item['retained_body']
        body = path.read_bytes()
        assert hashlib.sha256(body).hexdigest() == item['sha256'], path
        if '.json' not in url:
            continue
        decoded = gzip.decompress(body) if body[:2] == b'\x1f\x8b' else body
        data = json.loads(decoded)
        proof['downloads'][url] = {'body_sha256': item['sha256'], 'arrays': {key: coverage(rows) for key, rows in arrays(data)}}
    if args.mech == 'HabitatMech':
        category_rows = []
        for url, item in raw['downloads'].items():
            if '/pages/category/' in url:
                category_rows.extend(json.loads((ROOT / item['retained_body']).read_bytes()))
        slugs = [row[1] for row in category_rows]
        proof['habitat_categories'] = {'records': len(slugs), 'unique_record_slugs': len(set(slugs)), 'slug_sha256': hashlib.sha256('\n'.join(sorted(slugs)).encode()).hexdigest(), 'route_pattern': 'pages/habitats/<slug>.html'}
    if args.mech == 'CommunityMech':
        item = raw['downloads']['https://culturebotai.github.io/CommunityMech/communities.json']
        records = json.loads((ROOT / item['retained_body']).read_bytes())
        links = ['https://culturebotai.github.io/CommunityMech/communities/' + row['id'] + '.html' for row in records]
        expected = hashlib.sha256('\n'.join(sorted(set(links))).encode()).hexdigest()
        actual = raw['pages']['https://culturebotai.github.io/CommunityMech/browser.html']['desktop']['record_links_sha256']
        proof['community_browser_binding'] = {'index_records': len(records), 'unique_routes': len(set(links)), 'expected_route_sha256': expected, 'browser_route_sha256': actual, 'exact_match': expected == actual}
    if args.write_proof:
        dest = folder / 'coverage.json'
        if dest.exists():
            raise SystemExit('Refusing to overwrite coverage proof')
        dest.write_text(json.dumps(proof, indent=2) + '\n')
    summary = {'mech': args.mech, 'finished_at': raw['finished_at'], 'deployment_stable': raw['deployment_stable'],
        'pages': {url: {'status': row.get('status'), 'error': row.get('error'), 'fresh_width': row.get('fresh_390', {}).get('scroll_width'), 'resized_width': row.get('resized_390', {}).get('scroll_width'), 'theme': row.get('desktop', {}).get('theme'), 'errors': row.get('page_errors'), 'screenshots': row.get('screenshots')} for url, row in raw['pages'].items()},
        'actions': {key: {'error': row.get('error'), 'url': row.get('url'), 'counts': row.get('counts'), 'first_rows': row.get('first_rows'), 'visible_rows': row.get('visible_rows')} for key, row in raw['actions'].items()},
        'failures': {url: {'blocked': row.get('blocked'), 'failure_counts': row.get('after_search', row.get('initial_failure', {})).get('counts'), 'failure_body': row.get('after_search', row.get('initial_failure', {})).get('body', '')[:1500], 'recovered_counts': row.get('recovered_on_reload', {}).get('counts'), 'error': row.get('error')} for url, row in raw['failures'].items()},
        'coverage': proof, 'licenses': list(raw['licenses']),
        'link_checks': {url: {'status': row.get('status'), 'error': row.get('error')} for url, row in raw['link_checks'].items()}}
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
