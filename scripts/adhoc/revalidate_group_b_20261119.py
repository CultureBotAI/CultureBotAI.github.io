#!/usr/bin/env python3
"""Revalidate the 24 published-site criteria for Group B, 2026-11-19.

Inputs: current site_features.json, live public Pages, exact deployment APIs.
Outputs: new group-b JSON/text evidence and screenshots only; no site changes.
Serves the authorized November 19 website-feature refresh (PR assigned by root).
Run one complete --mech DUFMech canary and inspect its saved files before others.
"""
import argparse
import base64
import datetime as dt
import email.utils
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from audit_browser_group_b_20261104 import (
    SNAPSHOT_JS, ACTION_JS, compact, summarize_json, PROFILES, SELECT_FACETS, EXTRAS, BULK,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '_fleet/reviews/site-features-20261119/group-b'
TEMP = ROOT / '.temp/site-feature-audit-20261119/group-b'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
GROUP = ('CultureMech', 'MediaIngredientMech', 'ProteinTraitsMech', 'DUFMech', 'NaturalProductMech', 'CMMMech')
BULK = dict(BULK, NaturalProductMech=['pages/index.json'])
EXTRAS = dict(EXTRAS, NaturalProductMech=['pages/map.html', 'pages/chemical-map.html', 'pages/sequence-map.html'])
EXTRA_JS = r'''() => {
 const all=s=>[...document.querySelectorAll(s)], txt=e=>(e.innerText||e.textContent||'').trim();
 const visible=e=>e.getClientRects().length>0;
 const interesting=/evidence|reference|curation|history|source|schema|licen[sc]e|review|related|cross.mech/i;
 return {sections:all('h2,h3,h4').filter(e=>interesting.test(txt(e))).map(e=>({heading:txt(e),text:txt(e.parentElement).slice(0,14000)})),
 relevant_links:all('a[href]').filter(e=>interesting.test(txt(e))||/github.com|doi.org|pubmed|identifiers.org|ebi.ac.uk|purl.obolibrary|\/mechs\//.test(e.href)).map(e=>({text:txt(e).slice(0,180),url:e.href})),
 load_messages:all('[role=status],[aria-live],.error,[id*=status],[id*=Status]').filter(visible).map(e=>txt(e).slice(0,1200)),
 graph:{plotly:all('.js-plotly-plot').map(e=>({traces:(e.data||[]).map(t=>({type:t.type,x:t.x?.length,y:t.y?.length,labels:t.labels?.length})),title:e.layout?.title})),
 svg_points:all('circle,.point,.node').length, canvases:all('canvas').map(e=>({width:e.width,height:e.height}))},
 overflow:all('body *').filter(e=>{let r=e.getBoundingClientRect();return visible(e)&&r.width>0&&(r.right>innerWidth+1||r.left < -1)&&!e.closest('svg');}).slice(0,35).map(e=>({tag:e.tagName,id:e.id,class:String(e.className),right:e.getBoundingClientRect().right,text:txt(e).slice(0,160)})),
 styles:{background:getComputedStyle(document.body).backgroundColor,color:getComputedStyle(document.body).color},
 theme_storage:Object.fromEntries(Object.entries(localStorage).filter(([k])=>/theme/i.test(k)))}; }'''

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))

def deployment(repo, url):
    d = api(f'repos/CultureBotAI/{repo}/deployments?environment=github-pages&per_page=1')[0]
    status = api(f'repos/CultureBotAI/{repo}/deployments/{d["id"]}/statuses?per_page=1')[0]
    headers = subprocess.check_output(['curl', '--silent', '--show-error', '--head', '--location', '--max-time', '30', url], text=True)
    modified = re.findall(r'^last-modified:\s*(.+)$', headers, re.M | re.I)
    codes = re.findall(r'^HTTP/\S+\s+(\d+)', headers, re.M)
    assert status['state'] == 'success', status
    assert codes and codes[-1] == '200', headers
    assert modified, 'No Last-Modified header: ' + url
    modified_at = email.utils.parsedate_to_datetime(modified[-1].strip())
    assert modified_at >= dt.datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')), headers
    return {k: d[k] for k in ('id', 'sha', 'created_at')} | {
        'state': status['state'], 'status_created_at': status['created_at'],
        'last_modified': modified[-1].strip(), 'http_status': int(codes[-1]),
        'url': url, 'log_url': status.get('log_url'), 'checked_at': now()}

def capture(page):
    return compact(page.evaluate(SNAPSHOT_JS)) | page.evaluate(EXTRA_JS)

def settle(page, mech):
    page.wait_for_timeout(900)
    if mech == 'ProteinTraitsMech':
        if '#record=' in page.url:
            page.wait_for_function("document.querySelector('#results .detail') && !document.querySelector('#results').innerText.match(/Loading record/i)", timeout=150000)
        else:
            page.wait_for_function("!document.querySelector('#results')?.innerText.match(/Loading .*shards|Loading records?/i)", timeout=150000)
    page.evaluate('() => document.fonts.ready')

def dark(page):
    for selector in ('#theme-control', '#theme-selector'):
        if page.locator(selector).count() and page.locator(selector).first.evaluate('(e)=>e.tagName') == 'SELECT':
            page.locator(selector).first.select_option('dark'); return
    for selector in ('.theme-toggle', '#theme-toggle', '[data-theme-toggle]'):
        target = page.locator(selector)
        if target.count() and target.first.is_visible():
            target.first.click(); return
    button = page.get_by_role('button', name='Dark', exact=True)
    if button.count(): button.first.click()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mech', required=True, choices=GROUP)
    parser.add_argument('--followup', action='store_true', help='Use a separate followup receipt; retain the original run.')
    args = parser.parse_args()
    config = json.loads((ROOT / '_fleet/data/site_features.json').read_text())['mechs'][args.mech]
    OUT.mkdir(parents=True, exist_ok=True); TEMP.mkdir(parents=True, exist_ok=True)
    slug = args.mech.lower() + ('-followup' if args.followup else '')
    dest = OUT / (slug + '.json')
    if dest.exists(): raise SystemExit('Refusing to overwrite retained receipt: ' + str(dest))
    repo = config['repository'].rsplit('/', 1)[-1]
    base = f'https://culturebotai.github.io/{repo}/'
    report = {'mech': args.mech, 'started_at': now(), 'checked_on': '2026-11-19',
              'method': 'Live Chrome; actual controls, populated page captures, cold URL restoration, 390px resized and fresh loads, failed requests and recovery.',
              'deployment_before': deployment(repo, config['site']), 'pages': {}, 'actions': {}, 'failure_cases': {}, 'bulk': {}, 'licenses': {}}
    def save():
        temp = dest.with_suffix('.json.tmp'); temp.write_text(json.dumps(report, indent=2) + '\n'); temp.replace(dest)
    save()
    # Exact repository license texts are compared with rendered site statements.
    revision = report['deployment_before']['sha']
    for item in api(f'repos/CultureBotAI/{repo}/git/trees/{revision}')['tree']:
        if item['type'] == 'blob' and re.search(r'licen[sc]e|copying', item['path'], re.I):
            doc = api(f'repos/CultureBotAI/{repo}/contents/{item["path"]}?ref={revision}')
            report['licenses'][item['path']] = {'sha': doc['sha'], 'text': base64.b64decode(doc['content']).decode('utf-8')[:14000]}
    save()
    urls = list(dict.fromkeys([config['site'], config['features']['search']['url']] +
        [f['url'] for f in config['features'].values() if urlsplit(f['url']).netloc == 'culturebotai.github.io' and not urlsplit(f['url']).path.endswith(('.json', '.yaml', '.tsv', '.csv'))] +
        [base + path for path in EXTRAS[args.mech]]))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        report['browser_version'] = browser.version
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, color_scheme='light')
        page = ctx.new_page(); page.set_default_timeout(15000)
        requests, errors, failures = [], [], []
        page.on('request', lambda req: requests.append({'url': req.url, 'type': req.resource_type}))
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.on('requestfailed', lambda req: failures.append({'url': req.url, 'failure': req.failure}))
        for pos, url in enumerate(urls):
            requests.clear(); errors.clear(); failures.clear()
            rec = {'checked_at': now()}
            try:
                response = page.goto(url, wait_until='networkidle', timeout=90000); settle(page, args.mech)
                rec.update(capture(page), http_status=response.status if response else None,
                           requests=list(requests), errors=list(errors), request_failures=list(failures))
                if pos == 0:
                    screen = OUT / (slug + '-desktop.png'); page.screenshot(path=str(screen)); rec['desktop_screenshot'] = str(screen.relative_to(ROOT))
                    dark(page); settle(page, args.mech); rec['after_theme_toggle'] = capture(page)
                page.set_viewport_size({'width': 390, 'height': 844}); settle(page, args.mech)
                rec['resized_390'] = capture(page)
                page.reload(wait_until='networkidle', timeout=90000); settle(page, args.mech)
                rec['fresh_390'] = capture(page)
                if pos in (0, 2):
                    screen = OUT / (slug + f'-mobile-{pos}.png'); page.screenshot(path=str(screen)); rec['mobile_screenshot'] = str(screen.relative_to(ROOT))
                page.set_viewport_size({'width': 1280, 'height': 900})
            except Exception as error:
                rec.update(error=str(error), requests=list(requests), errors=list(errors), request_failures=list(failures))
                page.set_viewport_size({'width': 1280, 'height': 900})
            report['pages'][url] = rec; save()
        browse = config['features']['search']['url'].split('#')[0].split('?')[0]
        query, queries, sort, reset = PROFILES[args.mech]
        def action(name, operation):
            try:
                operation(); settle(page, args.mech)
                report['actions'][name] = page.evaluate(ACTION_JS) | {'checked_at': now(), 'detail': page.evaluate(EXTRA_JS)}
            except Exception as error: report['actions'][name] = {'error': str(error), 'checked_at': now()}
            save()
        page.goto(browse, wait_until='networkidle', timeout=90000); settle(page, args.mech)
        report['actions']['initial'] = page.evaluate(ACTION_JS); save()
        for value in queries + ['no-such-record-nov19-feature-audit']:
            action('query:' + value, lambda value=value: page.locator(query).fill(value))
        action('clear_query', lambda: page.locator(query).fill(''))
        if sort:
            options = page.locator(sort + ' option').evaluate_all('(es)=>es.map(e=>e.value)')
            for value in options:
                action('sort:' + value, lambda value=value: page.locator(sort).select_option(value))
        else:
            report['actions']['sorting_controls'] = {'selects': page.locator('select').evaluate_all('(es)=>es.map(e=>({id:e.id,text:e.innerText}))'),
                                                       'sort_buttons': page.get_by_role('button', name=re.compile('sort', re.I)).count()}
        if args.mech in SELECT_FACETS:
            for selector in SELECT_FACETS[args.mech]:
                options = page.locator(selector + ' option').evaluate_all('(es)=>es.filter(e=>!e.disabled).map(e=>e.value)')
                if len(options) > 1:
                    action('facet:' + selector, lambda selector=selector, value=options[1]: page.locator(selector).select_option(value))
            action('combined_query', lambda: page.locator(query).fill(queries[-1]))
        elif args.mech == 'CultureMech':
            action('facet:first', lambda: page.locator('input[type=checkbox]:visible').first.check())
            action('combined_query', lambda: page.locator(query).fill(queries[-1]))
        else:
            action('active_site', lambda: page.goto(browse + '#cat=STRUCT_ACTIVE_SITE&q=racemase', wait_until='networkidle', timeout=90000))
        cold_url = page.url
        action('reload_state', lambda: page.reload(wait_until='networkidle', timeout=90000))
        cold = ctx.new_page(); cold.set_default_timeout(15000)
        try:
            cold.goto(cold_url, wait_until='networkidle', timeout=90000); settle(cold, args.mech)
            report['actions']['cold_url'] = cold.evaluate(ACTION_JS)
        except Exception as error: report['actions']['cold_url'] = {'error': str(error)}
        cold.close(); save()
        if reset: action('reset', lambda: page.locator(reset).first.click())
        else: action('reset', lambda: page.goto(browse, wait_until='networkidle', timeout=90000))
        # Test observed data dependencies, then recover through an ordinary reload.
        candidates = {browse}
        for url, rec in report['pages'].items():
            if any(r['type'] in ('fetch', 'xhr') for r in rec.get('requests', [])) and re.search('map|graph|browse', url): candidates.add(url)
        for url in sorted(candidates):
            aborted = []
            def block(route):
                if route.request.resource_type in ('fetch', 'xhr') or route.request.url.endswith('/data.js'):
                    aborted.append(route.request.url); route.abort()
                else: route.continue_()
            test = ctx.new_page(); test.route('**/*', block)
            result = {'started_at': now()}
            try:
                test.goto(url, wait_until='networkidle', timeout=90000); settle(test, args.mech)
                result.update(aborted=aborted, failed=capture(test))
                test.unroute('**/*', block); test.reload(wait_until='networkidle', timeout=90000); settle(test, args.mech)
                result['recovered'] = capture(test)
            except Exception as error: result.update(error=str(error), aborted=aborted)
            report['failure_cases'][url] = result; test.close(); save()
        for path in BULK.get(args.mech, []):
            url = base + path
            try:
                response = ctx.request.get(url, timeout=120000); payload = response.body()
                result = {'http_status': response.status, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
                if response.ok:
                    data = response.json(); result['data'] = summarize_json(data)
                    if isinstance(data, dict):
                        result['list_examples'] = {k: {'first': v[:1], 'last': v[-1:]} for k,v in data.items() if isinstance(v,list) and len(json.dumps(v[:1]+v[-1:])) < 18000}
                report['bulk'][url] = result
            except Exception as error: report['bulk'][url] = {'error': str(error)}
            save()
        browser.close()
    report['deployment_after'] = deployment(repo, config['site'])
    assert report['deployment_after']['id'] == report['deployment_before']['id'], 'Deployment changed during review'
    assert report['deployment_after']['sha'] == revision, 'Deployment revision changed during review'
    report['finished_at'] = now(); report['complete'] = True; save()
    print(json.dumps({'mech': args.mech, 'output': str(dest.relative_to(ROOT)), 'pages': len(report['pages']),
                      'action_errors': [k for k,v in report['actions'].items() if 'error' in v], 'complete': True}))

if __name__ == '__main__':
    main()
