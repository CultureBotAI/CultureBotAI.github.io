#!/usr/bin/env python3
"""Retain bounded follow-up evidence for Nov19 Group A website judgments.

Inputs: completed audit and live Pages; outputs a fresh followup-N.json beside
the raw receipt. Checks pagination, known source/sibling links and positive
Community search restoration. Read-only upstream; website-feature refresh,
2026-11-19. Existing receipts are never overwritten.
"""
import argparse
import base64
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
from revalidate_group_a_20261119 import CHROME, ROOT, OUT, deployment, gh, now, state


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mech', required=True)
    ap.add_argument('--attempt', default='audit-1')
    ap.add_argument('--name', default='followup-1')
    ap.add_argument('--plan', action='store_true')
    args = ap.parse_args()
    if not re.fullmatch(r'[A-Za-z]+Mech', args.mech) or not re.fullmatch(r'[a-z0-9-]+', args.name):
        ap.error('literal mech/name required')
    source = OUT / args.mech / args.attempt / 'raw.json'
    dest = source.with_name(args.name + '.json')
    raw = json.loads(source.read_text())
    assert raw.get('finished_at') and raw.get('deployment_stable')
    if args.plan:
        print(json.dumps({'mech': args.mech, 'receipt': str(source), 'output': str(dest), 'exists': dest.exists()}))
        return
    assert not dest.exists(), dest
    cfg = json.loads((ROOT / '_fleet/data/site_features.json').read_text())['mechs'][args.mech]
    report = {'mech': args.mech, 'started_at': now(), 'source_receipt': str(source.relative_to(ROOT)), 'link_checks': {}, 'actions': {}}
    def save():
        dest.write_text(json.dumps(report, indent=2) + '\n')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        report['deployment_before'] = deployment(ctx, args.mech, cfg['site'])
        page = ctx.new_page()
        if args.mech == 'CommunityMech':
            page.goto('https://culturebotai.github.io/CommunityMech/browser.html', wait_until='networkidle')
            page.locator('#search').fill('ANME-SRB Marine Methane Seep Consortium')
            page.wait_for_timeout(700)
            report['actions']['positive_query_before_reload'] = state(page)
            page.reload(wait_until='networkidle')
            page.wait_for_timeout(700)
            report['actions']['positive_query_after_reload'] = state(page)
            url = 'https://culturebotai.github.io/CultureMech/pages/normalized/003277.html'
            r = ctx.request.get(url)
            report['link_checks'][url] = {'status': r.status, 'resolved_url': r.url}
        category = {'HabitatMech': 'pages/category/host-associated.html', 'AntibioticMech': 'pages/class/antibacterial.html'}.get(args.mech)
        if category:
            page.goto(f'https://culturebotai.github.io/{args.mech}/' + category, wait_until='networkidle')
            report['actions']['category_first'] = state(page)
            next_link = page.get_by_role('link', name=re.compile(r'^Next', re.I)).first
            if not next_link.count():
                next_link = page.locator('a[rel=next]').first
            if not next_link.count():
                next_link = page.get_by_role('link', name='2', exact=True).first
            if next_link.count():
                next_link.click()
                page.wait_for_timeout(700)
                report['actions']['category_next'] = state(page)
            else:
                report['actions']['category_next'] = {'not_found': True}
            page.set_viewport_size({'width': 390, 'height': 844})
            report['actions']['category_resized_390'] = state(page)
            page.reload(wait_until='networkidle')
            report['actions']['category_fresh_390'] = state(page)
        # Resolve the precise linked schema and source blobs at the deployed SHA,
        # avoiding web-UI rate limits without treating them as missing files.
        repo = args.mech
        sha = raw['deployment_after']['sha']
        urls = sorted({a['url'] for row in raw['pages'].values() for a in row.get('desktop', {}).get('all_links', []) if f'github.com/CultureBotAI/{repo}/blob/' in a['url'] and re.search(r'\.(yaml|yml)(#.*)?$', a['url'])})
        report['pinned_source_checks'] = {}
        for url in urls[:12]:
            path = url.split('/blob/', 1)[1].split('/', 1)[1].split('#')[0]
            try:
                item = gh(f'repos/CultureBotAI/{repo}/contents/{path}?ref={sha}')
                body = base64.b64decode(item['content'])
                report['pinned_source_checks'][url] = {'revision': sha, 'path': path, 'git_blob_sha': item['sha'], 'bytes': len(body), 'excerpt': body[:700].decode(errors='replace')}
            except Exception as exc:
                report['pinned_source_checks'][url] = {'error': str(exc)}
            save()
        report['deployment_after'] = deployment(ctx, repo, cfg['site'])
        report['deployment_stable'] = report['deployment_before']['verified'] and report['deployment_after']['verified'] and report['deployment_after']['id'] == report['deployment_before']['id'] and report['deployment_after']['sha'] == sha
        report['finished_at'] = now()
        save()
        browser.close()
    print(dest)


if __name__ == '__main__':
    main()
