#!/usr/bin/env python3
"""Verify the local gap browser for website #577; 2026-11-14.

Inputs: generated gap assets, summary and UI source (or a real Jekyll --site).
Outputs: durable QA JSON at --report; disposable preview/downloads/screenshots
under .temp/knowledge-gaps-20261114. The fallback renders Kramdown in the live
site shell and explicitly does not claim a full Jekyll or deployment check.
"""
import argparse
import csv
import datetime as dt
import functools
import hashlib
import http.server
import json
import platform
from pathlib import Path
import re
import shutil
import subprocess
import threading
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / '.temp/knowledge-gaps-20261114'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'culturebotai-gap-browser-local-qa'})
    with urllib.request.urlopen(request, timeout=30) as response:
        assert response.status == 200
        return response.read()


def prepare(args):
    if args.site:
        return args.site, {'method': 'Actual supplied Jekyll build, served locally', 'site': str(args.site.relative_to(ROOT))}
    preview = TEMP / ('preview-' + args.report.stem)
    (preview / 'knowledge-gaps').mkdir(parents=True, exist_ok=True)
    (preview / 'assets/gaps').mkdir(parents=True, exist_ok=True)
    cache = TEMP / 'shell-cache'
    cache.mkdir(parents=True, exist_ok=True)
    for filename, url in [('shell.html', 'https://culturebotai.github.io/mechs/'),
                          ('main.css', 'https://culturebotai.github.io/assets/main.css')]:
        target = cache / filename
        if not target.exists():
            target.write_bytes(fetch(url))
        assert target.stat().st_size
    markdown = (ROOT / 'knowledge-gaps.md').read_text()
    markdown = re.sub(r"\{\{\s*'([^']+)'\s*\|\s*relative_url\s*\}\}", lambda m: m[1], markdown)
    markdown = markdown.replace('{% include gaps-summary.html %}', args.summary.read_text())
    assert '{%' not in markdown and '{{' not in markdown
    source = preview / 'body.md'
    source.write_text(markdown)
    fragment = preview / 'body.html'
    subprocess.run(['ruby', str(ROOT / 'scripts/adhoc/render_hub_preview_20261112.rb'), str(source), str(fragment)], check=True)
    shell, count = re.subn(r'(<main\b[^>]*>).*?(</main>)',
                          lambda m: m[1] + '<div class="wrapper">' + fragment.read_text() + '</div>' + m[2],
                          (cache / 'shell.html').read_text(), count=1, flags=re.S)
    assert count == 1
    (preview / 'knowledge-gaps/index.html').write_text(shell)
    shutil.copy2(cache / 'main.css', preview / 'assets/main.css')
    shutil.copy2(ROOT / 'assets/custom.css', preview / 'assets/custom.css')
    shutil.copytree(args.assets, preview / 'assets/gaps', dirs_exist_ok=True)
    for name in ('browser.js', 'search-core.js', 'search-worker.js', 'browser.css'):
        shutil.copy2(ROOT / 'assets/gaps' / name, preview / 'assets/gaps' / name)
    return preview, {'method': 'Kramdown-rendered current body in retained live site shell, local CSS/JS/data; not a full Jekyll build or deployment',
                     'page_sha256': sha(ROOT / 'knowledge-gaps.md'), 'shell_sha256': sha(cache / 'shell.html'),
                     'ui_sha256': {name: sha(preview / 'assets/gaps' / name) for name in ('browser.js', 'search-core.js', 'search-worker.js', 'browser.css')},
                     'preview_sha256': sha(preview / 'knowledge-gaps/index.html')}


class Handler(http.server.SimpleHTTPRequestHandler):
    faults = {}

    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if self.faults.get(path, 0):
            self.faults[path] -= 1
            self.send_error(503, 'Injected QA failure')
        else:
            super().do_GET()


def settled(page):
    page.wait_for_function("""() => !document.querySelector('#gap-app').hidden &&
      !document.querySelector('#gap-result-status').textContent.startsWith('Searching') &&
      !document.querySelector('#gap-result-status').textContent.startsWith('Loading')""")


def submit(page, query):
    page.locator('#gap-query').fill(query)
    page.locator('#gap-query').press('Enter')
    settled(page)


def layout(page):
    result = page.evaluate("""() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
      h1:document.querySelectorAll('main h1').length, main:document.querySelectorAll('main').length})""")
    assert result['scrollWidth'] <= result['width'] + 1, result
    assert result['h1'] == 1 and result['main'] == 1, result
    return result


def contrast(page):
    pairs = page.evaluate("""() => {
      const rgb=s=>(s.match(/[\\d.]+/g)||[]).map(Number);
      const luminance=c=>c.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4)
        .reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
      const selectors=['#gap-controls .gap-note','#gap-results .gap-record','#gap-results a','#gap-query','#gap-results .gap-badge'];
      return selectors.map(selector=>{const e=document.querySelector(selector);if(!e)return null;
        let ancestor=e,background;while(ancestor){const c=rgb(getComputedStyle(ancestor).backgroundColor);
          if(c.length===3||c[3]===1){background=c;break;}ancestor=ancestor.parentElement;}
        if(!background)background=[255,255,255];const foreground=rgb(getComputedStyle(e).color);
        const levels=[luminance(foreground),luminance(background)].sort((a,b)=>a-b);
        return {selector,ratio:(levels[1]+.05)/(levels[0]+.05),foreground,background};}).filter(Boolean);
    }""")
    assert pairs and all(p['ratio'] >= 4.5 for p in pairs), pairs
    return {'scope': 'Sampled control/note/card/link/badge text on nearest opaque backgrounds; not a full accessibility audit', 'pairs': pairs}


def view_checks(browser, url, manifest, index, width, output):
    context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme='light', accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    assert page.goto(url, wait_until='networkidle').status == 200
    settled(page)
    report = {'width': width, 'initial_status': page.locator('#gap-result-status').inner_text(), 'layout': layout(page)}
    report['light_text_contrast'] = contrast(page)
    assert page.locator('#gap-results > li').count() <= 50
    assert page.locator('#gap-coverage').locator('article').count() == len(manifest['sources'])
    page.locator('h1').scroll_into_view_if_needed()
    page.screenshot(path=str(output / f'{width}-light.png'))
    target = next(i for i in index['items'] if i['record_label'].lower() == 'animal pathogen')
    before_search_history = page.evaluate('history.length')
    submit(page, target['record_id'])
    after_search_history = page.evaluate('history.length')
    assert after_search_history == before_search_history + 1, {'before': before_search_history, 'after': after_search_history, 'trigger': 'one Enter search'}
    page.go_back(wait_until='networkidle'); settled(page)
    assert page.locator('#gap-query').input_value() == ''
    page.go_forward(wait_until='networkidle'); settled(page)
    assert page.locator('#gap-query').input_value() == target['record_id']
    report['enter_creates_one_history_entry'] = True
    button = page.locator('#gap-results button').filter(has_text=target['prompt'])
    assert button.count() == 1
    button.focus()
    button.press('Enter')
    page.wait_for_function("() => document.querySelector('#gap-detail-title').textContent !== 'Loading discussion…'")
    assert page.locator('#gap-detail-title').inner_text() == target['prompt']
    assert page.locator('#gap-detail-body').get_by_text('Proposed experiments', exact=True).count() == 1
    assert page.locator('#gap-detail-body').get_by_text('Pinned source record', exact=True).get_attribute('href').startswith('https://github.com/')
    report['detail_layout'] = layout(page)
    page.screenshot(path=str(output / f'{width}-detail.png'))
    cold_url = page.url
    cold = context.new_page()
    cold.goto(cold_url, wait_until='networkidle')
    settled(cold)
    cold.wait_for_function("() => !document.querySelector('#gap-detail').hidden && document.querySelector('#gap-detail-title').textContent !== 'Loading discussion…'")
    assert cold.locator('#gap-query').input_value() == target['record_id']
    assert cold.locator('#gap-detail-title').inner_text() == target['prompt']
    cold.close()
    report['cold_query_and_gap_url'] = True
    split_items = [i for i in index['items'] if i.get('detail_shard') and i['detail_shard'] != i['mech']]
    if split_items:
        last_key = sorted({i['detail_shard'] for i in split_items})[-1]
        split_item = next(i for i in split_items if i['detail_shard'] == last_key)
        split_page = context.new_page()
        split_page.goto(url + '?' + urllib.parse.urlencode({'view': 'all', 'status': '', 'gap': split_item['id']}), wait_until='networkidle')
        settled(split_page)
        split_page.wait_for_function("() => !document.querySelector('#gap-detail').hidden && document.querySelector('#gap-detail-title').textContent !== 'Loading discussion…'")
        assert split_page.locator('#gap-detail-title').inner_text() == split_item['prompt']
        assert split_page.locator('#gap-detail-body').get_by_text('Pinned source record', exact=True).count() == 1
        report['split_detail_shard'] = {'key': last_key, 'item': split_item['id'], 'loaded': True}
        split_page.close()
    page.locator('#gap-close-detail').click()
    assert page.evaluate("document.activeElement.classList.contains('gap-open')")
    submit(page, '<img src=x onerror="window.GAP_INJECTED=true">')
    assert page.locator('#gap-result-status').inner_text().startswith('No discussions')
    assert not page.evaluate('Boolean(window.GAP_INJECTED)')
    assert page.locator('#gap-results img').count() == 0
    report['literal_query_and_empty_state'] = True
    page.locator('#gap-reset').click()
    settled(page)
    page.locator('#gap-view').select_option('candidates')
    settled(page)
    expected = sum(i['lane'] == 'candidate' for i in index['items'])
    assert page.locator('#gap-results > li').count() == min(50, expected)
    report['candidate_count'] = expected
    page.locator('#gap-view').select_option('all')
    settled(page)
    assert page.locator('#gap-status').input_value() == ''
    if len(index['items']) > 50:
        page.locator('#gap-next').click()
        settled(page)
        assert 'Page 2 ' in page.locator('#gap-page-label').inner_text()
        restore_url = page.url
        page.reload(wait_until='networkidle'); settled(page)
        assert 'Page 2 ' in page.locator('#gap-page-label').inner_text()
        report['page_url_restored'] = urllib.parse.urlsplit(restore_url).query
    for kind in ('json', 'csv'):
        with page.expect_download() as download:
            page.locator('#gap-export-' + kind).click()
        target_file = output / f'export-{width}.{kind}'
        download.value.save_as(target_file)
        assert target_file.stat().st_size > 0
        if kind == 'json':
            data = json.loads(target_file.read_text())
            assert data['build_id'] == manifest['build_id']
            ids = [i['id'] for i in data['items']]
        else:
            with target_file.open(newline='') as handle:
                ids = [r['id'] for r in csv.DictReader(handle)]
        assert set(ids) == {i['id'] for i in index['items']} and len(ids) == len(index['items'])
        report['export_' + kind] = {'items': len(ids), 'bytes': target_file.stat().st_size}
    page.locator('#gap-mech').select_option('TraitMech'); settled(page)
    page.go_back(wait_until='networkidle'); settled(page)
    assert page.locator('#gap-mech').input_value() == ''
    report['back_restores_filters'] = True
    page.get_by_role('button', name='Switch to dark theme', exact=True).click()
    page.reload(wait_until='networkidle'); settled(page)
    assert page.locator('html').get_attribute('data-theme') == 'dark'
    report['theme_persists'] = True
    report['dark_layout'] = layout(page)
    report['dark_text_contrast'] = contrast(page)
    page.locator('h1').scroll_into_view_if_needed()
    page.screenshot(path=str(output / f'{width}-dark.png'))
    assert not errors, errors
    report['page_errors'] = errors
    context.close()
    return report


def failure_checks(browser, url, manifest, index):
    context = browser.new_context()
    page = context.new_page()
    index_path = '/assets/gaps/' + manifest['index']['url']
    Handler.faults[index_path] = 1
    page.goto(url, wait_until='networkidle')
    page.wait_for_selector('#gap-retry:visible')
    assert 'could not load' in page.locator('#gap-load-status').inner_text()
    assert page.locator('#gap-results > li').count() == 0
    page.locator('#gap-retry').click(); settled(page)
    target = next(i for i in index['items'] if i['record_label'].lower() == 'animal pathogen')
    Handler.faults['/assets/gaps/' + manifest['details'][target.get('detail_shard') or target['mech']]['url']] = 1
    submit(page, target['record_id'])
    page.locator('#gap-results button').filter(has_text=target['prompt']).click()
    page.get_by_role('button', name='Retry this discussion').wait_for()
    assert page.locator('#gap-detail-title').inner_text() == 'Discussion could not load'
    assert page.locator('#gap-detail-body').get_by_text('Proposed experiments', exact=True).count() == 0
    page.get_by_role('button', name='Retry this discussion').click()
    page.wait_for_function("() => document.querySelector('#gap-detail-title').textContent !== 'Loading discussion…'")
    assert page.locator('#gap-detail-title').inner_text() == target['prompt']
    context.close()
    return {'index_failure_then_retry': True, 'detail_failure_clears_content_then_retry': True}


def warm_queries(browser, url, manifest):
    context = browser.new_context()
    page = context.new_page(); page.goto(url, wait_until='networkidle'); settled(page)
    result = page.evaluate("""async manifest => {
      const worker = new Worker('/assets/gaps/search-worker.js'); let seq=0;
      const call = data => new Promise((resolve,reject) => { const request=++seq;
        const listener=e=>{if(e.data.request===request){worker.removeEventListener('message',listener);
          e.data.type==='error'?reject(new Error(e.data.message)):resolve(e.data);}};
        worker.addEventListener('message',listener);worker.postMessage({...data,request});});
      await call({type:'init',url:new URL(manifest.index.url,location.origin+'/assets/gaps/manifest.json').href,
        sha256:manifest.index.sha256,build_id:manifest.build_id});
      const samples=[]; const qs=['iron','METPO:1004002','uptake','PMID','mechanism'];
      for(let n=0;n<35;n++){const start=performance.now();await call({type:'query',state:{q:qs[n%qs.length],view:'all',status:''}});
        if(n>=5)samples.push(performance.now()-start);}
      worker.terminate(); samples.sort((a,b)=>a-b);
      return {samples:30,p95_ms:samples[Math.ceil(samples.length*.95)-1],max_ms:samples.at(-1),
        measurement:'worker query round-trip after 5 warmups; all indexed items',user_agent:navigator.userAgent};
    }""", manifest)
    context.close()
    assert result['p95_ms'] < 150, result
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--site', type=Path)
    parser.add_argument('--canary', action='store_true')
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    args.assets, args.summary, args.report = args.assets.resolve(), args.summary.resolve(), args.report.resolve()
    if args.site:
        args.site = args.site.resolve()
    preview, provenance = prepare(args)
    manifest = json.loads((args.assets / 'manifest.json').read_text())
    index = json.loads((args.assets / manifest['index']['url']).read_text())
    output = TEMP / 'browser-artifacts' / args.report.stem
    output.mkdir(parents=True, exist_ok=True)
    report = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'provenance': provenance,
              'build_id': manifest['build_id'], 'manifest_sha256': sha(args.assets / 'manifest.json'),
              'reference_platform': platform.platform(), 'screenshots': str(output.relative_to(ROOT)),
              'complete': False, 'views': []}
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(preview)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    url = f'http://127.0.0.1:{server.server_port}/knowledge-gaps/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(args.browser_executable) if args.browser_executable else None)
            report['browser_version'] = browser.version
            for width in ([1280] if args.canary else [1280, 390]):
                report['views'].append(view_checks(browser, url, manifest, index, width, output))
                print(f'Validated {width}px view and complete exports', flush=True)
            if not args.canary:
                report['failures'] = failure_checks(browser, url, manifest, index)
                report['warm_query'] = warm_queries(browser, url, manifest)
                context = browser.new_context(java_script_enabled=False)
                page = context.new_page(); page.goto(url, wait_until='networkidle')
                page.locator('.gap-static summary').click()
                assert page.locator('.gap-static').inner_text().count('TraitMech') >= 1
                assert page.locator('noscript').is_visible()
                report['no_js_sources_and_summary'] = True
                context.close()
            browser.close()
        report['complete'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        assert json.loads(args.report.read_text()) == report
    print(json.dumps({'complete': report['complete'], 'views': len(report['views']), 'report': str(args.report)}, indent=2))


if __name__ == '__main__':
    main()
