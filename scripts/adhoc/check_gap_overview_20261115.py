#!/usr/bin/env python3
"""Check gap section navigation and snapshot statistics; 2026-11-15.

Serves section-navigation PR #598 and regressions #599–602. Inputs: published gap assets,
summary and optional actual Jekyll site. Outputs: --report and screenshots under
.temp/gap-overview-20261115. Counts are independently derived from the published
index. Run --canary before the expanded desktop/mobile/failure checks.
"""
import argparse
from collections import Counter
import datetime as dt
import functools
import http.server
import json
from pathlib import Path
import threading
import time
import urllib.parse

import check_gap_browser_20261114 as qa

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / '.temp/gap-overview-20261115'
TARGETS = ('gap-form', 'gap-terms-title', 'gap-pairs-title', 'gap-results-title',
           'gap-static-title', 'bibliography')


class Handler(qa.Handler):
    """Hold a localhost asset without blocking the browser's main document."""
    holds = {}
    faults = {}

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        held = self.holds.get(path)
        if held:
            held[0].set()
            if not held[1].wait(25):
                self.send_error(503, 'Overview QA hold expired')
                return
        super().do_GET()


def expected_counts(manifest, items):
    counts = Counter({source['name']: 0 for source in manifest['sources']})
    for item in items:
        if item['lane'] != 'candidate' and item['kind'] in ('KNOWLEDGE_GAP', 'HUMAN_MODEL_MISMATCH'):
            assert item['mech'] in counts
            counts[item['mech']] += 1
    return dict(counts)


def params(page):
    return urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query, keep_blank_values=True)


def terms_settled(page):
    page.wait_for_function("""() => /^(Entity occurrences loaded|No indexed entity mentions|Entity occurrences could not load)/
      .test(document.querySelector('#gap-terms-status').textContent)""")


def visible_target(page, target):
    """Require a settled, visible destination below the actual sticky header."""
    # Driver-side polling also runs when page JavaScript is disabled; Playwright's
    # default requestAnimationFrame poll never advances in that context.
    deadline, stable_since, stable_top = time.monotonic() + 30, None, None
    bounds = None
    while time.monotonic() < deadline:
        bounds = page.evaluate("""id => {
          const e=document.getElementById(id); if(!e || !e.getClientRects().length)return null;
          const r=e.getBoundingClientRect(),h=document.querySelector('.site-header')?.getBoundingClientRect();
          return {top:r.top,bottom:r.bottom,height:r.height,header_bottom:Math.max(0,h?.bottom || 0),viewport_height:innerHeight};
        }""", target)
        now = time.monotonic()
        if bounds is None:
            stable_since, stable_top = None, None
        else:
            if stable_top is None or abs(stable_top - bounds['top']) > .5:
                stable_top, stable_since = bounds['top'], now
            lower, height = bounds['header_bottom'], bounds['viewport_height']
            fits = bounds['height'] <= height - lower
            if (bounds['top'] >= lower - 1 and bounds['top'] < height - 20
                    and (not fits or bounds['bottom'] <= height + 1)
                    and now - stable_since >= .12):
                return bounds
        time.sleep(.05)
    raise AssertionError(f'Section target did not settle visibly below header: {target}: {bounds}')


def tile_snapshot(page):
    return page.locator('#gap-stats-grid button').evaluate_all("""nodes => nodes.map(e => ({
      mech:e.dataset.mech,count:e.dataset.count,coverage:e.dataset.coverage,action:e.dataset.action,
      text:e.innerText,number:e.querySelector('.gap-stat-count')?.textContent || ''}))""")


def assert_tiles(page, manifest, counts):
    tiles = tile_snapshot(page)
    names = {source['name'] for source in manifest['sources']}
    assert len(tiles) == len(names) + 1
    by_mech = {tile['mech']: tile for tile in tiles}
    assert set(by_mech) == names | {''}
    assert int(by_mech['']['count']) == sum(counts.values())
    assert by_mech['']['action'] == 'filter'
    for source in manifest['sources']:
        name, coverage = source['name'], source['coverage_status']
        tile = by_mech[name]
        assert tile['coverage'] == coverage, (name, tile)
        assert int(tile['count']) == counts[name], (name, tile, counts[name])
        if coverage == 'complete':
            assert tile['action'] == 'filter'
            assert tile['number'].replace(',', '').strip() == str(counts[name])
        elif coverage == 'partial' and counts[name] > 0:
            assert tile['action'] == 'filter'
            assert tile['number'].replace(',', '').strip() == str(counts[name]) + '+'
            assert 'partial' in tile['text'].lower()
        else:
            assert tile['action'] == 'coverage'
            assert tile['number'].strip() == '—'
            assert coverage in tile['text'].lower()
    assert sum(int(by_mech[name]['count']) for name in names) == int(by_mech['']['count'])
    return tiles


def visual_style(page):
    # Theme colors transition for 150 ms. Measure the final rendered state,
    # including loaded fonts, rather than sampling two colors mid-transition.
    page.evaluate('() => document.fonts.ready.then(() => true)')
    page.wait_for_function("""() => {
      if(document.getAnimations().some(a => (a.pending || a.playState==='running') &&
          a.effect?.getComputedTiming().iterations!==Infinity))return false;
      const nodes=[...document.querySelectorAll('.gap-section-nav a,.gap-stat-name,.gap-stat-count,.gap-stat-coverage,#gap-query')];
      const state=JSON.stringify(nodes.map(e=>{const rows=[];for(let p=e;p;p=p.parentElement){
        const s=getComputedStyle(p);rows.push([s.color,s.backgroundColor,s.fontFamily,s.fontSize,s.fontWeight]);}
        return rows;}));
      const now=performance.now(),old=window.__overviewStyle;
      if(!old || old.state!==state)window.__overviewStyle={state,since:now};
      return now-window.__overviewStyle.since>=200;
    }""")
    result = page.evaluate("""() => {
      const rgb=s=>(s.match(/[\\d.]+/g)||[]).map(Number);
      const magenta=c=>c[0]>c[1]+10 && c[2]>c[1]+5 && c[0]>c[2]-30;
      const lum=c=>c.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4)
        .reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
      const background=e=>{for(let p=e;p;p=p.parentElement){const c=rgb(getComputedStyle(p).backgroundColor);
        if(c.length===3||c[3]===1)return c;}return [255,255,255];};
      const checks=[...document.querySelectorAll('.gap-section-nav a,.gap-stat-name,.gap-stat-count,.gap-stat-coverage')]
        .filter(e=>e.getClientRects().length).map(e=>{const s=getComputedStyle(e), fg=rgb(s.color),bg=background(e);
          const levels=[lum(fg),lum(bg)].sort((a,b)=>a-b), size=parseFloat(s.fontSize),weight=Number(s.fontWeight);
          return {selector:e.className || e.tagName,text:e.textContent,ratio:(levels[1]+.05)/(levels[0]+.05),
            foreground_rgb:fg,background_rgb:bg,font_size_px:size,font_weight:weight,
            required:size>=24 || (size>=18.66 && weight>=700)?3:4.5};});
      const icons=[...document.querySelectorAll('.gap-section-nav svg')].map(e=>rgb(getComputedStyle(e).stroke));
      const numbers=[...document.querySelectorAll('.gap-stat-count')].map(e=>rgb(getComputedStyle(e).color));
      const control=getComputedStyle(document.querySelector('#gap-query'));
      return {checks,nav_icons_magenta:icons.every(magenta),stat_numbers_magenta:numbers.every(magenta),
        ordinary_control_uses_other_palette:![control.color,control.backgroundColor,control.borderColor].map(rgb).some(magenta)};
    }""")
    assert result['nav_icons_magenta'] and result['stat_numbers_magenta']
    assert result['ordinary_control_uses_other_palette']
    assert result['checks'] and all(row['ratio'] >= row['required'] for row in result['checks']), result
    return result


def activate_anchor(page, target, keyboard=False):
    link = page.locator('.gap-section-nav a[href="#' + target + '"]')
    if keyboard:
        link.focus()
        link.press('Enter')
    else:
        link.click()
    page.wait_for_function('hash => location.hash === hash', arg='#' + target)
    return visible_target(page, target)


def overview_spacing(page):
    """Keep the heading, navigation and counts in order without a hidden h2 gap (#602)."""
    result = page.evaluate("""() => {
      const title=document.querySelector('.gap-intro h1'),nav=document.querySelector('.gap-section-nav'),
        stats=document.querySelector('#gap-stats'),grid=document.querySelector('#gap-stats-grid'),
        hidden=getComputedStyle(document.querySelector('#gap-stats-title'));
      const a=title.getBoundingClientRect(),b=nav.getBoundingClientRect(),c=grid.getBoundingClientRect();
      return {dom_order:Boolean(title.compareDocumentPosition(nav)&Node.DOCUMENT_POSITION_FOLLOWING) &&
          Boolean(nav.compareDocumentPosition(stats)&Node.DOCUMENT_POSITION_FOLLOWING),
        title_to_nav_px:b.top-a.bottom,nav_to_counts_px:c.top-b.bottom,
        hidden_heading_position:hidden.position,
        hidden_heading_margins:[hidden.marginTop,hidden.marginRight,hidden.marginBottom,hidden.marginLeft].map(parseFloat)};
    }""")
    assert result['dom_order'], result
    assert 0 <= result['title_to_nav_px'] <= 32 and 0 <= result['nav_to_counts_px'] <= 32, result
    assert result['hidden_heading_position'] == 'absolute', result
    assert result['hidden_heading_margins'] == [0, 0, 0, 0], result
    return result


def discussion_links_after_static_navigation(context, page, url):
    """A discussion permalink must not carry an unrelated section destination (#599)."""
    result = []
    for target in ('gap-static-title', 'bibliography'):
        page.goto(url + '?view=gaps&status=', wait_until='networkidle')
        qa.settled(page); terms_settled(page)
        activate_anchor(page, target)
        button = page.locator('#gap-results .gap-open').first
        gap_id, prompt = button.get_attribute('data-gap-id'), button.inner_text()
        button.click()
        page.wait_for_function('text => document.querySelector("#gap-detail-title").textContent === text', arg=prompt)
        href = page.locator('#gap-detail-body').get_by_role('link', name='Link to this discussion', exact=True).get_attribute('href')
        parsed = urllib.parse.urlsplit(href)
        assert not parsed.fragment, (target, href)
        assert urllib.parse.parse_qs(parsed.query).get('gap') == [gap_id], (target, href, gap_id)
        cold = context.new_page()
        try:
            cold.goto(urllib.parse.urljoin(page.url, href), wait_until='networkidle')
            qa.settled(cold)
            cold.wait_for_function('text => !document.querySelector("#gap-detail").hidden && document.querySelector("#gap-detail-title").textContent === text', arg=prompt)
            assert cold.locator('#gap-detail').is_visible()
            assert cold.locator('#gap-detail-body').get_by_role('link', name='Pinned source record', exact=True).count() == 1
            assert params(cold).get('gap') == [gap_id]
            result.append({'after_section': target, 'gap_id': gap_id, 'fragment': parsed.fragment,
                           'cold_detail_populated_and_visible': True})
        finally:
            cold.close()
    return result


def view_checks(browser, url, manifest, counts, width, output, canary):
    context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme='light')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        page.goto(url, wait_until='networkidle'); qa.settled(page); terms_settled(page)
        links = page.locator('.gap-section-nav a')
        assert links.evaluate_all('nodes => nodes.map(e=>e.getAttribute("href"))') == ['#' + key for key in TARGETS]
        assert all(links.nth(i).is_visible() for i in range(6))
        tiles = assert_tiles(page, manifest, counts)
        report = {'width': width, 'snapshot_counts': tiles, 'layout': qa.layout(page), 'light_style': visual_style(page)}
        report['overview_spacing'] = overview_spacing(page)
        page.locator('.gap-intro').screenshot(path=str(output / f'{width}-overview-light.png'))
        page.goto(url + '?view=all&status=&q=iron&mech=TraitMech#gap-form', wait_until='networkidle')
        qa.settled(page); terms_settled(page)
        query = params(page)
        destinations = {}
        for i, target in enumerate(TARGETS):
            destinations[target] = activate_anchor(page, target, keyboard=bool(i % 2))
            assert params(page) == query, (target, page.url)
        activate_anchor(page, 'gap-form')
        activate_anchor(page, 'gap-terms-title', keyboard=True)
        page.go_back(); qa.settled(page)
        assert urllib.parse.urlsplit(page.url).fragment == 'gap-form'
        visible_target(page, 'gap-form')
        page.go_forward(); qa.settled(page)
        assert urllib.parse.urlsplit(page.url).fragment == 'gap-terms-title'
        visible_target(page, 'gap-terms-title')
        qa.submit(page, 'oxygen'); terms_settled(page)
        assert urllib.parse.urlsplit(page.url).fragment == 'gap-terms-title'
        assert params(page)['q'] == ['oxygen']
        assert tile_snapshot(page) == tiles, 'Snapshot statistics changed under a query'
        for target in ('gap-pairs-title', 'gap-results-title'):
            page.goto(url + '?view=all&status=&q=iron#' + target, wait_until='networkidle')
            qa.settled(page); terms_settled(page)
            visible_target(page, target)
            assert params(page) == {'view': ['all'], 'status': [''], 'q': ['iron']}
        report['discussion_links_after_static_navigation'] = discussion_links_after_static_navigation(context, page, url)
        choices = [tile['mech'] for tile in tiles]
        if canary or width != 1280:
            choices = list(dict.fromkeys(['', next(t['mech'] for t in tiles if t['mech'] and t['action']=='filter' and int(t['count'])>0),
                next(t['mech'] for t in tiles if t['mech'] and t['action']=='filter' and int(t['count'])==0),
                next(t['mech'] for t in tiles if t['action']=='coverage')]))
        by_mech = {tile['mech']: tile for tile in tiles}
        exercised = []
        for name in choices:
            dirty = '?view=all&status=RESOLVED&q=overview-no-match&kind=CURATION_TODO&review=unknown&sort=mech&vocab=TraitMech&term=missing'
            page.goto(url + dirty, wait_until='networkidle'); qa.settled(page); terms_settled(page)
            page.locator('#gap-stats-grid button[data-mech="' + name + '"]').click()
            if by_mech[name]['action'] == 'coverage':
                visible_target(page, 'gap-static-title')
                assert page.locator('.gap-static').evaluate('e=>e.open')
            else:
                qa.settled(page); terms_settled(page)
                state = params(page)
                assert state.get('view', ['gaps']) == ['gaps'] and state.get('status') == ['']
                assert state.get('mech', ['']) == [name]
                for key in ('q', 'kind', 'review', 'term', 'term2', 'vocab', 'gap'):
                    assert state.get(key, ['']) == [''], (name, key, state)
                expected = counts[name] if name else sum(counts.values())
                text = page.locator('#gap-result-status').inner_text()
                assert text.startswith(f'{expected:,} matching discussions' if expected else 'No discussions match'), (name, text, expected)
                assert urllib.parse.urlsplit(page.url).fragment == 'gap-results-title'
                visible_target(page, 'gap-results-title')
            assert tile_snapshot(page) == tiles
            exercised.append(name)
        page.locator('#gap-reset').click(); qa.settled(page); terms_settled(page)
        page.evaluate("document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('culturebot-theme','dark')")
        report.update(destinations=destinations,query_hash_history_preserved=True,cold_section_urls=True,
            statistics_stable_under_search=True,clicked_tiles=exercised,dark_layout=qa.layout(page),dark_style=visual_style(page))
        page.locator('.gap-intro').screenshot(path=str(output / f'{width}-overview-dark.png'))
        assert not errors, errors
        report['page_errors'] = errors
        return report
    finally:
        context.close()


def static_checks(browser, url, width, output):
    context = browser.new_context(viewport={'width': width, 'height': 900}, java_script_enabled=False)
    page = None
    try:
        page = context.new_page(); page.goto(url + '?q=iron', wait_until='networkidle')
        for target in TARGETS[:4]:
            assert not page.locator('.gap-section-nav a[href="#' + target + '"]').is_visible()
        coverage_bounds = activate_anchor(page, 'gap-static-title', keyboard=True)
        assert params(page) == {'q': ['iron']}
        if not page.locator('.gap-static').evaluate('e=>e.open'):
            page.locator('#gap-static-title').press('Enter')
        assert page.locator('.gap-static').evaluate('e=>e.open')
        assert 'TraitMech' in page.locator('.gap-static').inner_text()
        page.screenshot(path=str(output / f'{width}-no-js-coverage.png'))
        reference_bounds = activate_anchor(page, 'bibliography')
        assert params(page) == {'q': ['iron']}
        page.screenshot(path=str(output / f'{width}-no-js-references.png'))
        return {'width': width, 'static_links_and_summary_work': True, 'interactive_links_hidden': True,
                'coverage_bounds': coverage_bounds, 'reference_bounds': reference_bounds, 'layout': qa.layout(page)}
    except Exception as error:
        if page is not None:
            diagnostic = page.evaluate("""() => {
              const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();
                return {top:r.top,bottom:r.bottom,height:r.height,visible:Boolean(e.getClientRects().length)};};
              return {url:location.href,viewport:{width:innerWidth,height:innerHeight},scroll_y:scrollY,
                header:rect(document.querySelector('.site-header')),
                coverage:rect(document.getElementById('gap-static-title')),
                references:rect(document.getElementById('bibliography')),
                coverage_open:document.querySelector('.gap-static')?.open,active_element:document.activeElement?.id};
            }""")
            diagnostic['error'] = str(error)
            path = output / f'{width}-no-js-failure.json'
            path.write_text(json.dumps(diagnostic, indent=2) + '\n')
            page.screenshot(path=str(output / f'{width}-no-js-failure.png'))
            raise AssertionError(f'No-JavaScript check failed; diagnostic: {path}: {error}') from error
        raise
    finally:
        context.close()


def load_checks(browser, url, manifest, output):
    result = {}
    for mode in ('index-held', 'terms-held', 'terms-failed'):
        context = browser.new_context(viewport={'width': 390, 'height': 900})
        asset = manifest['index' if mode == 'index-held' else 'terms']['url']
        path = '/assets/gaps/' + asset
        requested, release = threading.Event(), threading.Event()
        if mode.endswith('held'):
            Handler.holds[path] = (requested, release)
        else:
            Handler.faults[path] = 1
        try:
            page = context.new_page(); page.goto(url + '?q=iron#gap-pairs-title', wait_until='domcontentloaded')
            if mode == 'index-held':
                assert requested.wait(10), 'Index hold was not exercised'
                assert all(not page.locator('.gap-section-nav a[href="#' + key + '"]').is_visible() for key in TARGETS[:4])
                assert not page.locator('#gap-stats-grid').is_visible()
                release.set(); qa.settled(page); terms_settled(page)
            elif mode == 'terms-held':
                assert requested.wait(10), 'Term hold was not exercised'
                qa.settled(page); visible_target(page, 'gap-pairs-title')
                assert 'Loading' in page.locator('#gap-terms-status').inner_text()
                page.screenshot(path=str(output / '390-cooccurrence-loading.png'))
                # Static destinations must respond while the unrelated entity
                # request remains held, including disclosure and keyboard focus.
                for target in ('gap-static-title', 'bibliography'):
                    activate_anchor(page, target, keyboard=True)
                    assert page.evaluate('document.activeElement.id') == target
                    assert not release.is_set() and 'Loading' in page.locator('#gap-terms-status').inner_text()
                    if target == 'gap-static-title':
                        assert page.locator('.gap-static').evaluate('e=>e.open')
                    assert params(page).get('q') == ['iron']
                result['static_links_during_term_load'] = 'Coverage opens, focuses and scrolls; References focuses and scrolls before term release'
                # Restore the delayed section request, then check its final
                # position after the cloud changes the document's height.
                page.locator('.gap-section-nav a[href="#gap-pairs-title"]').click()
                assert urllib.parse.urlsplit(page.url).fragment == 'gap-pairs-title'
                release.set(); terms_settled(page); qa.settled(page)
            else:
                qa.settled(page)
                page.wait_for_function("() => document.querySelector('#gap-terms-status').textContent.startsWith('Entity occurrences could not load')")
            visible_target(page, 'gap-pairs-title')
            assert params(page).get('q') == ['iron']
            assert urllib.parse.urlsplit(page.url).fragment == 'gap-pairs-title'
            if mode == 'terms-failed':
                assert page.locator('#gap-pairs-status').is_visible()
            page.screenshot(path=str(output / ('390-' + mode + '.png')))
            result[mode] = 'Preserved cold section URL and visible target; loading gates respected'
        finally:
            release.set(); Handler.holds.pop(path, None); Handler.faults.pop(path, None); context.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--site', type=Path)
    parser.add_argument('--canary', action='store_true')
    parser.add_argument('--static-only', action='store_true', help='Isolate no-JavaScript section links; combine with --canary for one desktop case')
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    for key in ('assets', 'summary', 'report', 'site'):
        if getattr(args, key) is not None:
            setattr(args, key, getattr(args, key).resolve())
    output = TEMP / (args.report.stem + '-artifacts'); output.mkdir(parents=True, exist_ok=True)
    report = {'complete': False, 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'canary': args.canary, 'static_only': args.static_only,
              'artifacts': str(output.relative_to(ROOT)), 'views': []}
    # Keep this helper's previews and screenshots together; reuse the established renderer.
    qa.TEMP = TEMP
    try:
        site, provenance = qa.prepare(args)
        if args.site and (site / 'body.md').is_file() and (site / 'body.html').is_file():
            provenance['method'] = 'Retained Kramdown preview served locally; not a full Jekyll build or deployment'
        report['provenance'] = provenance
        assets = site / 'assets/gaps'
        manifest = json.loads((assets / 'manifest.json').read_text())
        index_path = assets / manifest['index']['url']
        assert qa.sha(index_path) == manifest['index']['sha256']
        index = json.loads(index_path.read_text()); assert index['build_id'] == manifest['build_id']
        counts = expected_counts(manifest, index['items'])
        report.update(build_id=manifest['build_id'],manifest_sha256=qa.sha(assets / 'manifest.json'),expected_gap_counts=counts)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with qa.sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=str(args.browser_executable) if args.browser_executable else None)
                try:
                    report['browser_version'] = browser.version
                    url = f'http://127.0.0.1:{server.server_port}/knowledge-gaps/'
                    widths = [1280] if args.canary else [1280, 620, 390]
                    if not args.static_only:
                        for width in widths:
                            report['views'].append(view_checks(browser, url, manifest, counts, width, output, args.canary))
                            print(f'Validated {width}px section navigation and snapshot statistics', flush=True)
                    static_widths = [1280] if args.canary else [1280, 620, 601, 390]
                    report['no_js'] = [static_checks(browser, url, width, output) for width in static_widths]
                    if not args.canary and not args.static_only:
                        report['loading_and_failures'] = load_checks(browser, url, manifest, output)
                finally:
                    browser.close()
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=5)
        report['complete'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        assert args.report.stat().st_size and json.loads(args.report.read_text()) == report
    print(json.dumps({'complete': True, 'report': str(args.report)}))


if __name__ == '__main__':
    main()
