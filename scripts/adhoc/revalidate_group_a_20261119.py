#!/usr/bin/env python3
"""Revalidate six live Mech browsers against the existing 24-feature rubric.

Inputs: site_features.json, public Pages, exact deployment statuses and licenses.
Outputs: fresh per-attempt JSON/screenshots under the Nov19 group-a review folder;
download bodies stay in .temp/site-feature-audit-20261119/group-a.
Purpose: website-feature-only refresh, 2026-11-19; never changes upstream sites,
corpus pins or earlier receipts. --plan is write-free; run HabitatMech first.
"""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urljoin

from playwright.sync_api import sync_playwright
from audit_browser_group_b_20261104 import PROFILES, SELECT_FACETS, SNAPSHOT_JS, compact

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '_fleet/reviews/site-features-20261119/group-a'
CACHE = ROOT / '.temp/site-feature-audit-20261119/group-a'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
GROUP = ['HabitatMech', 'CommunityMech', 'TaxonMech', 'PathwayMech', 'CellStructureMech', 'AntibioticMech']
EXTRAS = {
    'HabitatMech': ['pages/text-map/', 'pages/text-map-source/index.html', 'pages/category/host-associated.html'],
    'CommunityMech': ['text_map.html', 'sequence_map.html', 'community_graph.html', 'schema.html'],
    'TaxonMech': ['pages/map.html', 'pages/type-strains.html', 'pages/domain/archaea.html'],
    'PathwayMech': ['pages/map.html', 'pages/sequence-map.html', 'pages/records/MIBiG_BGC0000194.html'],
    'CellStructureMech': ['pages/embedding-map.html', 'pages/sequence-map.html', 'pages/grounded.html', 'pages/category/microcompartment.html'],
    'AntibioticMech': ['pages/map.html', 'pages/sequence-map.html', 'pages/chemical-map.html', 'pages/antibacterial/index.html'],
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def gh(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def name(url):
    return re.sub(r'[^a-zA-Z0-9]+', '_', urlparse(url).path + urlparse(url).query).strip('_')[-150:]


def state(page):
    result = compact(page.evaluate(SNAPSHOT_JS))
    result.update(page.evaluate('''() => ({
      all_links:[...document.querySelectorAll('a[href]')].filter(x=>!x.closest('tbody')).map(x=>({text:(x.innerText||x.textContent||'').slice(0,250),url:typeof x.href==='string'?x.href:x.href.baseVal})),
      visible_result_links:[...document.querySelectorAll('tbody tr:not([hidden]) a[href],li[data-search]:not([hidden]) a[href],.community-card a[href]')].filter(x=>x.getClientRects().length).slice(0,8).map(x=>({text:x.innerText,url:x.href})),
      background:getComputedStyle(document.body).backgroundColor,
      diagram_shapes:document.querySelectorAll('svg circle,svg path,svg line,svg polygon').length,
      canvas_sizes:[...document.querySelectorAll('canvas')].map(x=>({width:x.width,height:x.height,displayWidth:x.getBoundingClientRect().width})),
      overflow:[...document.querySelectorAll('main *')].filter(x=>x.getBoundingClientRect().right>innerWidth+2).slice(0,12).map(x=>({tag:x.tagName,id:x.id,cls:x.className,right:x.getBoundingClientRect().right}))
    })'''))
    return result


def deployment(context, repo, site):
    d = gh(f'repos/CultureBotAI/{repo}/deployments?environment=github-pages&per_page=1')[0]
    s = gh(f'repos/CultureBotAI/{repo}/deployments/{d["id"]}/statuses?per_page=1')[0]
    r = context.request.head(site, timeout=45000)
    lm = r.headers.get('last-modified')
    ok = s['state'] == 'success' and r.status == 200 and bool(lm) and parsedate_to_datetime(lm) >= dt.datetime.fromisoformat(d['created_at'].replace('Z', '+00:00'))
    return {k: d[k] for k in ('id', 'sha', 'created_at')} | {
        'state': s['state'], 'status_created_at': s['created_at'], 'log_url': s.get('log_url'),
        'site': site, 'http_status': r.status, 'last_modified': lm, 'verified': ok,
    }


def json_summary(data):
    if isinstance(data, list):
        return {'kind': 'list', 'count': len(data), 'first': data[:1], 'last': data[-1:]}
    if not isinstance(data, dict):
        return {'kind': type(data).__name__}
    out = {'kind': 'dict', 'keys': list(data)[:50], 'arrays': {}}
    for key, value in data.items():
        if isinstance(value, list):
            out['arrays'][key] = {'count': len(value), 'first': value[:1], 'last': value[-1:]}
        elif isinstance(value, (str, int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, dict):
            out[key] = value if len(json.dumps(value)) < 10000 else {'keys': list(value)[:30], 'count': len(value)}
    return out


def run(mech, attempt):
    baseline = json.loads((ROOT / '_fleet/data/site_features.json').read_text())
    cfg = baseline['mechs'][mech]
    repo = cfg['repository'].rsplit('/', 1)[1]
    base = f'https://culturebotai.github.io/{repo}/'
    dest = OUT / mech / attempt
    if dest.exists():
        raise SystemExit(f'Refusing to overwrite existing evidence: {dest}')
    dest.mkdir(parents=True)
    cache = CACHE / mech / attempt
    cache.mkdir(parents=True)
    raw = {'mech': mech, 'started_at': now(), 'method': 'Actual Chrome/Playwright interactions; fresh and resized 390px; exact deployment bracket; sampled detail pages, complete published index proofs separately.',
           'catalogue_sha256': hashlib.sha256(json.dumps(baseline['catalogue'], sort_keys=True).encode()).hexdigest(),
           'pages': {}, 'actions': {}, 'failures': {}, 'downloads': {}, 'link_checks': {}, 'licenses': {}, 'errors': []}
    def save():
        path = dest / 'raw.json'
        tmp = path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(raw, indent=2) + '\n')
        tmp.replace(path)
    save()
    urls = [cfg['site'], cfg['features']['search']['url'].split('#')[0].split('?')[0]]
    urls += [v['url'].split('#')[0] for v in cfg['features'].values() if not urlparse(v['url']).path.endswith(('.json', '.gz', '.tsv', '.csv', '.yaml', '.yml'))]
    urls += [base + p for p in EXTRAS[mech]]
    urls = list(dict.fromkeys(urls))
    query, queries, sort, reset = PROFILES[mech]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, color_scheme='light')
        raw['deployment_before'] = deployment(ctx, repo, cfg['site'])
        save()
        if not raw['deployment_before']['verified']:
            raise RuntimeError('Deployment/Last-Modified bracket is not verified')
        page = ctx.new_page()
        page.set_default_timeout(10000)
        for url in urls:
            events, errors = [], []
            page.close()
            page = ctx.new_page()
            page.set_default_timeout(10000)
            page.on('response', lambda r, es=events: es.append({'url': r.url, 'status': r.status, 'kind': r.request.resource_type}))
            page.on('pageerror', lambda e, es=errors: es.append(str(e)))
            try:
                r = page.goto(url, wait_until='networkidle', timeout=90000)
                page.wait_for_timeout(700)
                if url == cfg['site']:
                    toggle = page.locator('.theme-toggle,#theme-toggle')
                    if toggle.count():
                        for _ in range(3):
                            if page.evaluate('document.documentElement.dataset.theme') == 'dark':
                                break
                            toggle.first.click()
                            page.wait_for_timeout(200)
                    elif page.locator('#theme-control').count():
                        page.locator('#theme-control').select_option('dark')
                row = {'status': r.status if r else None, 'desktop': state(page), 'requests': events, 'page_errors': errors}
                raw['pages'][url] = row
                if 'map' in url or 'graph' in url:
                    point = page.locator('svg circle').first
                    canvas = page.locator('canvas').first
                    try:
                        if point.count() and point.is_visible():
                            point.click(timeout=3000, force=True)
                        elif canvas.count() and canvas.is_visible():
                            canvas.click(timeout=3000)
                        page.wait_for_timeout(300)
                        row['map_after_pointer'] = state(page)
                    except Exception as exc:
                        row['map_pointer_error'] = str(exc)
                stem = name(url)
                page.screenshot(path=str(dest / (stem + '-desktop.png')))
                page.set_viewport_size({'width': 390, 'height': 844})
                page.wait_for_timeout(400)
                row['resized_390'] = state(page)
                fresh = browser.new_context(viewport={'width': 390, 'height': 844}, color_scheme='light')
                fp = fresh.new_page()
                fp.goto(url, wait_until='networkidle', timeout=90000)
                fp.wait_for_timeout(500)
                row['fresh_390'] = state(fp)
                fp.screenshot(path=str(dest / (stem + '-mobile.png')))
                fresh.close()
                page.set_viewport_size({'width': 1280, 'height': 900})
                row['screenshots'] = [stem + '-desktop.png', stem + '-mobile.png']
            except Exception as exc:
                raw['pages'].setdefault(url, {})['error'] = str(exc)
            save()
            print(mech, 'PAGE', url, flush=True)
        browse = urls[1]
        page.goto(browse, wait_until='networkidle', timeout=90000)
        page.wait_for_timeout(600)
        def action(label, fn):
            try:
                fn()
                page.wait_for_timeout(1000)
                raw['actions'][label] = state(page)
            except Exception as exc:
                raw['actions'][label] = {'error': str(exc)}
            save()
        action('initial', lambda: None)
        for q in queries + ['no-such-record-nov19-audit']:
            action('search:' + q, lambda q=q: page.locator(query).fill(q))
        action('query_before_reload', lambda: page.locator(query).fill(queries[0]))
        action('query_after_reload', lambda: page.reload(wait_until='networkidle'))
        action('query_clear', lambda: page.locator(query).fill(''))
        if mech == 'HabitatMech':
            action('sort_query', lambda: page.locator(query).fill('water'))
        if sort:
            options = page.locator(sort + ' option').evaluate_all('(xs)=>xs.map(x=>x.value)')
            for option in options:
                action('sort:' + option, lambda option=option: page.locator(sort).select_option(option))
        if mech in SELECT_FACETS:
            for selector in SELECT_FACETS[mech]:
                options = page.locator(selector + ' option').evaluate_all('(xs)=>xs.filter(x=>!x.disabled).map(x=>x.value)')
                if len(options) > 1:
                    action('facet:' + selector, lambda selector=selector, option=options[1]: page.locator(selector).select_option(option))
        else:
            action('facet:first_checkbox', lambda: page.locator('input[type=checkbox]:visible').first.check())
        action('facets_before_reload', lambda: None)
        action('facets_after_reload', lambda: page.reload(wait_until='networkidle'))
        if reset:
            action('keyboard_reset', lambda: (page.locator(reset).first.focus(), page.keyboard.press('Enter')))
        next_button = page.get_by_role('link', name=re.compile(r'^Next', re.I))
        if not next_button.count():
            next_button = page.get_by_role('button', name=re.compile(r'^Next', re.I))
        if next_button.count() and next_button.first.is_enabled():
            action('next_page', lambda: next_button.first.click())
        page.close()
        # Fail data requests in fresh contexts, then remove the fault and reload.
        failure_urls = {browse}
        for url, row in raw['pages'].items():
            if any(r['kind'] in ('fetch', 'xhr') for r in row.get('requests', [])):
                failure_urls.add(url)
        for url in sorted(failure_urls):
            fc = browser.new_context(viewport={'width': 1280, 'height': 900})
            blocked = []
            def block(route):
                if route.request.resource_type in ('fetch', 'xhr'):
                    blocked.append(route.request.url)
                    route.abort()
                else:
                    route.continue_()
            fc.route('**/*', block)
            fp = fc.new_page()
            try:
                fp.goto(url, wait_until='networkidle', timeout=90000)
                fp.wait_for_timeout(600)
                row = {'blocked': blocked, 'initial_failure': state(fp)}
                raw['failures'][url] = row
                search = fp.locator('input[type=search],input[name=q]')
                if search.count():
                    search.first.fill(queries[0])
                    fp.wait_for_timeout(1000)
                    row['after_search'] = state(fp)
                fc.unroute('**/*', block)
                fp.reload(wait_until='networkidle', timeout=90000)
                fp.wait_for_timeout(800)
                row['recovered_on_reload'] = state(fp)
            except Exception as exc:
                raw['failures'].setdefault(url, {'blocked': blocked})['error'] = str(exc)
            fc.close()
            save()
        # Follow machine-readable downloads and scientific/schema/source/sibling links.
        links = [a | {'from': u} for u, row in raw['pages'].items() for a in row.get('desktop', {}).get('all_links', [])]
        seen = set()
        for link in links:
            url = link['url']
            if url in seen or not url.startswith('https://'):
                continue
            download = url.startswith(base) and re.search(r'\.(json|gz|tsv|csv)(\?|$)', url)
            check = bool(re.search(r'schema|source YAML|source record|license', link['text'], re.I) or ('culturebotai.github.io/' in url and not url.startswith(base)) or re.search(r'pubmed.ncbi.nlm.nih.gov|doi.org/', url))
            if not download and not check:
                continue
            seen.add(url)
            # Bound repeated citation requests, retaining all DOM evidence separately.
            if check and not download and len(raw['link_checks']) >= 35:
                continue
            try:
                response = ctx.request.get(url, timeout=20000)
                item = link | {'status': response.status, 'resolved_url': response.url}
                if download and response.status == 200:
                    body = response.body()
                    item.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
                    filename = hashlib.sha256(url.encode()).hexdigest()[:16] + '-' + urlparse(url).path.rsplit('/', 1)[-1]
                    (cache / filename).write_bytes(body)
                    item['retained_body'] = str((cache / filename).relative_to(ROOT))
                    parsed = gzip.decompress(body) if body[:2] == b'\x1f\x8b' else body
                    if '.json' in url:
                        item['data'] = json_summary(json.loads(parsed))
                    else:
                        item['header'] = parsed[:500].decode(errors='replace')
                        item['lines'] = parsed.count(b'\n')
                    raw['downloads'][url] = item
                else:
                    raw['link_checks'][url] = item
            except Exception as exc:
                raw['link_checks'][url] = link | {'error': str(exc)}
            save()
        sha = raw['deployment_before']['sha']
        listing = gh(f'repos/CultureBotAI/{repo}/contents?ref={sha}')
        for item in listing:
            if item['name'].startswith('LICENSE') and item['type'] == 'file':
                content = gh(f'repos/CultureBotAI/{repo}/contents/{item["name"]}?ref={sha}')
                body = base64.b64decode(content['content'])
                raw['licenses'][item['name']] = {'url': item['html_url'], 'sha': item['sha'], 'text': body.decode()}
        raw['deployment_after'] = deployment(ctx, repo, cfg['site'])
        raw['deployment_stable'] = raw['deployment_after']['verified'] and raw['deployment_after']['id'] == raw['deployment_before']['id'] and raw['deployment_after']['sha'] == sha
        raw['finished_at'] = now()
        save()
        browser.close()
    print(json.dumps({'mech': mech, 'output': str(dest / 'raw.json'), 'pages': len(raw['pages']), 'actions': len(raw['actions']), 'downloads': len(raw['downloads']), 'deployment_stable': raw['deployment_stable']}), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mech', choices=GROUP, required=True)
    ap.add_argument('--attempt', default='audit-1')
    ap.add_argument('--plan', action='store_true')
    args = ap.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.attempt):
        ap.error('attempt must be a simple lowercase name')
    if args.plan:
        cfg = json.loads((ROOT / '_fleet/data/site_features.json').read_text())
        print(json.dumps({'mech': args.mech, 'criteria': list(cfg['catalogue']), 'criterion_count': len(cfg['catalogue']), 'site': cfg['mechs'][args.mech]['site'], 'chrome': CHROME, 'output': str(OUT / args.mech / args.attempt), 'cache': str(CACHE / args.mech / args.attempt), 'existing_output': (OUT / args.mech / args.attempt).exists()}, indent=2))
    else:
        run(args.mech, args.attempt)


if __name__ == '__main__':
    main()
