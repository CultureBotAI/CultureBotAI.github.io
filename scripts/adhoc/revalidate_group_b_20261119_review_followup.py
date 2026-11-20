#!/usr/bin/env python3
"""Resolve two Group B reviewer questions, 2026-11-19 feature-refresh PR.

Inputs: public CultureMech map/navigation and DUFMech full index plus deployment
APIs. Outputs: new bounded review-followup JSON, deterministic gzip, hash receipt
under group-b. Existing receipts and proposed verdicts remain unchanged.
Run CultureMech as the first real unit and inspect persisted outputs before DUF.
"""
import argparse
import gzip
import hashlib
import json

from playwright.sync_api import sync_playwright
from revalidate_group_b_20261119 import CHROME, OUT, ROOT, deployment, now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mech', required=True, choices=['CultureMech', 'DUFMech'])
    args = parser.parse_args()
    config = json.loads((ROOT / '_fleet/data/site_features.json').read_text())['mechs'][args.mech]
    dest = OUT / (args.mech.lower() + '-review-followup.json')
    archive = dest.with_suffix('.json.gz')
    hashfile = dest.with_suffix('.publication.json')
    if any(p.exists() for p in [dest, archive, hashfile]):
        raise SystemExit('Refusing to overwrite review-followup artifacts')
    result = {'mech': args.mech, 'started_at': now(),
              'deployment_before': deployment(args.mech, config['site'])}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={'width':1280, 'height':900})
        base = f'https://culturebotai.github.io/{args.mech}/'
        if args.mech == 'CultureMech':
            page = context.new_page()
            blocked = []
            def block(route):
                blocked.append(route.request.url)
                route.abort()
            page.route('**/map-record-links.json', block)
            response = page.goto(base + 'app/umap.html', wait_until='networkidle')
            circles = page.locator('circle[role=link]')
            circles.first.wait_for()
            before = {'http_status': response.status, 'url':page.url,
                      'point_count':circles.count(),
                      'status_count':page.locator('#map-record-status').count()}
            point = circles.first.evaluate('(e)=>({label:e.getAttribute("aria-label"),id:e.__data__.id,category:e.__data__.category})')
            circles.first.press('Enter')
            status = page.locator('#map-record-status')
            status.wait_for(state='visible')
            result['blocked_point_activation'] = {
                'aborted':blocked, 'before_activation':before, 'point':point,
                'activation':'Keyboard Enter on the actual SVG point with role=link',
                'after_activation':{'url':page.url, 'text':status.inner_text(),
                    'role':status.get_attribute('role'), 'visible':status.is_visible(),
                    'links':status.locator('a').evaluate_all('(a)=>a.map(e=>({text:e.innerText,url:e.href}))'),
                    'point_count':circles.count()}}
            assert blocked and status.is_visible()
            assert 'Record links could not be loaded. Reload to retry' in status.inner_text()
            assert status.get_attribute('role') == 'status'
            page.unroute('**/map-record-links.json', block)
            page.reload(wait_until='networkidle')
            links_response = context.request.get(base + 'app/map-record-links.json')
            links = links_response.json()['links']
            index = circles.evaluate_all('(els,links)=>els.findIndex(e=>{const d=e.__data__;return /^\.\.\/pages\/normalized\/\d{6}\.html$/.test(links[d.category+"/"+d.id]||links["*/"+d.id]||"");})', links)
            assert index >= 0, 'No mapped historical point found for recovery check'
            recovered_point = circles.nth(index).evaluate('(e)=>({label:e.getAttribute("aria-label"),id:e.__data__.id,category:e.__data__.category})')
            circles.nth(index).press('Enter')
            page.wait_for_url('**/pages/normalized/*.html')
            page.wait_for_load_state('networkidle')
            result['recovery'] = {'action':'Reload with requests restored, then Enter on a verified mapped point',
                'links_http_status':links_response.status, 'point':recovered_point,
                'url':page.url, 'title':page.title(), 'heading':page.locator('h1').inner_text(),
                'body_characters':len(page.locator('body').inner_text())}
            assert result['recovery']['body_characters'] > 500
        else:
            response = context.request.get(base + 'index.json', timeout=120000)
            assert response.status == 200
            body = response.body()
            obj = json.loads(body)
            metadata = obj['metadata']
            sample = metadata['PF04149']
            record = sample['record']
            graphs = record['causal_graphs']
            result['full_export'] = {'url':response.url, 'http_status':response.status,
                'bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest(),
                'top_level_keys':sorted(obj), 'family_count':len(obj['families']),
                'metadata_count':len(metadata),
                'metadata_with_record_count':sum(isinstance(v.get('record'), dict) for v in metadata.values()),
                'metadata_with_history_field_count':sum('history' in v for v in metadata.values()),
                'metadata_with_reviews_field_count':sum('reviews' in v for v in metadata.values()),
                'sample_pointer':'/metadata/PF04149',
                'sample':{'keys':sorted(sample), 'record_keys':sorted(record),
                    'record_id':record.get('id'), 'record_name':record.get('name'),
                    'description':record.get('description'), 'causal_graph_count':len(graphs),
                    'history_count':len(sample['history']), 'review_count':len(sample['reviews']),
                    'graph_inventories':[{'keys':sorted(g), 'node_count':len(g.get('nodes',[])),
                        'edge_count':len(g.get('edges',[])),
                        'first_edge':g.get('edges',[None])[0] if g.get('edges') else None} for g in graphs],
                    'first_history':sample['history'][0], 'first_review':sample['reviews'][0]}}
            assert len(metadata) == len(obj['families']) == 8296
            assert graphs and sample['history'] and sample['reviews']
        browser.close()
    result['deployment_after'] = deployment(args.mech, config['site'])
    for key in ['id','sha']:
        assert result['deployment_before'][key] == result['deployment_after'][key]
    result['complete'] = True
    result['finished_at'] = now()
    raw = (json.dumps(result, indent=2) + '\n').encode()
    dest.write_bytes(raw)
    archive.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    assert gzip.decompress(archive.read_bytes()) == raw
    publication = {'raw':str(dest.relative_to(ROOT)), 'archive':str(archive.relative_to(ROOT)),
        'raw_bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest(),
        'gzip_bytes':archive.stat().st_size, 'gzip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    hashfile.write_text(json.dumps(publication, indent=2) + '\n')
    print(json.dumps(publication))


if __name__ == '__main__':
    main()
