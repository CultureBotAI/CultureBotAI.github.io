#!/usr/bin/env python3
"""Browser QA for knowledge-gap cross-Mech analyses, visualizations and 17-Mech coverage.

Purpose: Verify the 8-item section navigation, full 17-member public fleet accounting
(16 corpus Mechs + EdgeMech infrastructure), interactive cross-Mech breakdown bars,
16x16 Source x Vocabulary matrix, posed/resolved timeline, reference silos, synthesis
sidecar (bridges, experiments, blind-spots, cohesion + isolated failure/retry),
co-occurrence SVG network + Jaccard/NPMI metrics, embedding-map lenses/bridge arcs,
light/dark WCAG contrast, and responsive layout without horizontal overflow.
Inputs: generated gap assets (assets/gaps), _includes/gaps-summary.html, and optional
Jekyll --site build (falls back to Kramdown in retained site shell).
Outputs: JSON receipt at --report and screenshots under .temp/gap-visualizations-qa.
Serves: feat/gap-visualizations-analyses-20261115 PR. Date: 2026-11-16.
Run --canary first before the full desktop + mobile + failure suite.
"""
import argparse
import datetime as dt
import functools
import http.server
import json
from pathlib import Path
import threading
import urllib.parse

import check_gap_browser_20261114 as qa
import check_gap_overview_20261115 as overview_qa
import check_gap_terms_20261115 as terms_qa
import check_gap_embedding_20261115 as map_qa

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / '.temp/gap-visualizations-qa'
TARGETS = (
    'gap-form',
    'gap-analyses-title',
    'gap-terms-title',
    'gap-pairs-title',
    'gap-map-title',
    'gap-results-title',
    'gap-static-title',
    'bibliography',
)


def full_settled(page):
    terms_qa.settled(page)
    page.wait_for_function("""() => {
      const s = document.querySelector('#gap-analytics-status');
      const c = document.querySelector('#gap-analytics-content');
      return (c && !c.hidden) || (s && s.textContent.startsWith('Synthesis sidecar could not load'));
    }""")


def view_checks(browser, url, manifest, counts, width, output, canary):
    context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme='light')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    try:
        assert page.goto(url, wait_until='networkidle').status == 200
        full_settled(page)

        # 1. Section navigation (all 8 links visible) and 17 corpus/total buttons + EdgeMech infrastructure tile.
        links = page.locator('.gap-section-nav a')
        assert links.evaluate_all('nodes => nodes.map(e => e.getAttribute("href"))') == ['#' + k for k in TARGETS]
        assert all(links.nth(i).is_visible() for i in range(len(TARGETS)))

        tiles = overview_qa.assert_tiles(page, manifest, counts)
        infra_tiles = page.locator('#gap-stats-grid a.gap-stat-infrastructure').evaluate_all(
            'nodes => nodes.map(e => ({name: e.dataset.infrastructure, text: e.innerText}))'
        )
        expected_infra = [m['name'] for m in manifest.get('infrastructure', [])]
        assert [t['name'] for t in infra_tiles] == expected_infra == ['EdgeMech'], infra_tiles
        assert 'EdgeMech' in page.locator('#gap-snapshot').inner_text()

        light_layout = qa.layout(page)
        light_style = overview_qa.visual_style(page)
        spacing = overview_qa.overview_spacing(page)
        page.locator('.gap-intro').screenshot(path=str(output / f'{width}-overview-light.png'))

        # 2. Cross-Mech breakdown across all 16 corpus Mechs + EdgeMech (17 rows total).
        breakdown_rows = page.locator('#gap-breakdown-rows .gap-breakdown-row')
        assert breakdown_rows.count() == len(manifest['sources']) + len(expected_infra) == 17
        assert 'EdgeMech' in page.locator('#gap-breakdown-rows').inner_text()
        for lens in ('status', 'stance', 'layer', 'kind'):
            page.locator('#gap-breakdown-lens').select_option(lens)
            assert page.locator('#gap-breakdown-legend li').count() >= 1
        page.locator('#gap-analyses').screenshot(path=str(output / f'{width}-analyses-light.png'))

        # 3. 16 x 16 Source x Vocabulary cross-pollination matrix.
        assert page.locator('#gap-matrix-wrap').is_visible()
        assert page.locator('.gap-matrix-table tbody tr').count() == 16
        assert page.locator('.gap-matrix-table thead th').count() == 17
        for mode in ('occurrences', 'cross', 'discussions'):
            page.locator('#gap-matrix-mode').select_option(mode)
        first_cell = page.locator('.gap-matrix-table button.gap-matrix-btn').first
        assert first_cell.count() == 1
        first_cell.click()
        full_settled(page)
        q_params = overview_qa.params(page)
        assert q_params.get('mech') and q_params.get('vocab'), q_params
        assert page.locator('#gap-active-filters .gap-filter-chip').count() >= 2
        page.locator('#gap-reset').click()
        full_settled(page)
        assert page.locator('#gap-active-filters').is_hidden()

        # 4. Timeline & Reference concentration / cross-Mech citation silos.
        page.locator('#gap-view').select_option('all')
        full_settled(page)
        bars = page.locator('#gap-timeline-chart rect[role="button"]')
        assert bars.count() >= 1
        bars.first.click()
        full_settled(page)
        assert overview_qa.params(page).get('month'), page.url
        page.locator('#gap-active-filters .gap-filter-chip').filter(has_text='Month:').click()
        full_settled(page)
        assert not overview_qa.params(page).get('month')

        page.locator('#gap-refs-mode').select_option('cross')
        assert page.locator('#gap-refs-list .gap-compact-row').count() >= 1
        page.locator('#gap-refs-list .gap-mini-btn').first.click()
        full_settled(page)
        assert overview_qa.params(page).get('ref'), page.url
        page.locator('#gap-reset').click()
        full_settled(page)

        # 5. Synthesis sidecar panels: bridges, proposed experiments, blind-spots, cohesion.
        assert page.locator('#gap-analytics-content').is_visible()
        assert '7,510' in page.locator('#gap-bridges-summary').inner_text()
        assert '17 snapshot discussions' in page.locator('#gap-experiments-summary').inner_text()
        assert '101 of 1,220' in page.locator('#gap-blindspot-summary').inner_text()
        page.locator('#gap-blindspot-scope').select_option('all')
        assert '614 of 3,830' in page.locator('#gap-blindspot-summary').inner_text()
        page.locator('#gap-blindspot-scope').select_option('gaps')
        phrase_btn = page.locator('#gap-blindspot-phrases .gap-phrase-chip').first
        assert phrase_btn.count() == 1
        phrase_btn.click()
        full_settled(page)
        assert overview_qa.params(page).get('q'), page.url
        page.locator('#gap-reset').click()
        full_settled(page)

        # 6. Co-occurrence SVG network + NPMI / Jaccard / Discussions table.
        assert page.locator('#gap-pairs-network svg').is_visible()
        assert page.locator('#gap-pairs-network .gap-net-node').count() >= 2
        assert page.locator('#gap-pairs-network .gap-net-edge').count() >= 1
        headers = page.locator('#gap-pairs-table thead th').all_inner_texts()
        assert headers == ['Entity pair', 'Jaccard', 'NPMI', 'Discussions'], headers
        for metric in ('npmi', 'jaccard', 'discussions'):
            page.locator('#gap-pairs-metric').select_option(metric)
            assert page.locator('#gap-term-pairs tr').count() >= 1
        page.locator('.gap-term-explorer').screenshot(path=str(output / f'{width}-cooccurrence-light.png'))

        # 7. Embedding map new color lenses, cross-Mech neighbor arcs, and unshown fleet Mechs note.
        if not canary or width == 1280:
            page.locator('#gap-map-load').click()
            map_qa.settled(page)
            assert page.locator('#gap-map-unshown').is_visible()
            assert 'EdgeMech (infrastructure, no corpus)' in page.locator('#gap-map-unshown').inner_text()
            page.locator('#gap-map-bridges').check()
            assert page.locator('#gap-map-plot line.gap-map-arc').count() >= 1
            for color_mode in ('stance', 'layer', 'experiments', 'bridge', 'mech'):
                page.locator('#gap-map-color').select_option(color_mode)
                assert page.locator('#gap-map-legend li').count() >= 1
            page.locator('#gap-embedding').screenshot(path=str(output / f'{width}-embedding-bridges-light.png'))

        # 8. Coverage & static summary include EdgeMech without breaking 16 corpus <article> count.
        assert page.locator('#gap-coverage article').count() == len(manifest['sources']) == 16
        assert page.locator('#gap-coverage .gap-coverage-infra').count() == 1
        page.locator('#gap-stats-grid a.gap-stat-infrastructure').click()
        overview_qa.visible_target(page, 'gap-static-title')
        assert page.locator('.gap-static').evaluate('e => e.open')
        assert 'EdgeMech' in page.locator('.gap-static').inner_text()

        # 9. Dark mode layout and WCAG contrast check.
        page.evaluate(
            "document.documentElement.setAttribute('data-theme','dark');"
            "localStorage.setItem('culturebot-theme','dark')"
        )
        dark_layout = qa.layout(page)
        dark_style = overview_qa.visual_style(page)
        page.locator('#gap-analyses').screenshot(path=str(output / f'{width}-analyses-dark.png'))

        assert not errors, errors
        return {
            'width': width,
            'corpus_buttons': len(tiles),
            'infrastructure_tiles': infra_tiles,
            'breakdown_rows': 17,
            'light_layout': light_layout,
            'dark_layout': dark_layout,
            'light_contrast_checked': len(light_style['checks']),
            'dark_contrast_checked': len(dark_style['checks']),
            'overview_spacing': spacing,
            'page_errors': errors,
        }
    finally:
        context.close()


def analytics_failure_check(browser, url, manifest, output):
    context = browser.new_context(viewport={'width': 390, 'height': 900})
    path = '/assets/gaps/' + manifest['analytics']['url']
    overview_qa.Handler.faults[path] = 1
    try:
        page = context.new_page()
        page.goto(url + '#gap-analyses-title', wait_until='networkidle')
        terms_qa.settled(page)
        page.wait_for_function(
            "() => document.querySelector('#gap-analytics-status').textContent.startsWith('Synthesis sidecar could not load:')"
        )
        assert page.locator('#gap-analytics-retry').is_visible()
        assert page.locator('#gap-results .gap-open').count() > 0
        assert page.locator('#gap-breakdown-rows .gap-breakdown-row').count() == 17
        page.screenshot(path=str(output / '390-analytics-failure.png'))
        page.locator('#gap-analytics-retry').click()
        full_settled(page)
        assert page.locator('#gap-analytics-content').is_visible()
        return {'isolated_analytics_failure_and_retry': True}
    finally:
        overview_qa.Handler.faults.pop(path, None)
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path)
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets/gaps')
    parser.add_argument('--summary', type=Path, default=ROOT / '_includes/gaps-summary.html')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--canary', action='store_true')
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    for name in ('site', 'assets', 'summary', 'report'):
        if getattr(args, name) is not None:
            setattr(args, name, getattr(args, name).resolve())

    output = TEMP / (args.report.stem + '-artifacts')
    output.mkdir(parents=True, exist_ok=True)
    qa.TEMP = TEMP
    report = {
        'complete': False,
        'canary': args.canary,
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'artifacts': str(output.relative_to(ROOT)),
        'views': [],
    }
    try:
        site, provenance = qa.prepare(args)
        report['provenance'] = provenance
        assets = site / 'assets/gaps'
        manifest = json.loads((assets / 'manifest.json').read_text())
        for key in ('index', 'terms', 'embedding', 'analytics'):
            target = assets / manifest[key]['url']
            assert qa.sha(target) == manifest[key]['sha256'], key
        index = json.loads((assets / manifest['index']['url']).read_text())
        counts = overview_qa.expected_counts(manifest, index['items'])
        report.update(
            build_id=manifest['build_id'],
            manifest_sha256=qa.sha(assets / 'manifest.json'),
            analytics_sha256=manifest['analytics']['sha256'],
        )
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(overview_qa.Handler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with qa.sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=str(args.browser_executable) if args.browser_executable else None
                )
                try:
                    report['browser_version'] = browser.version
                    url = f'http://127.0.0.1:{server.server_port}/knowledge-gaps/'
                    widths = [1280] if args.canary else [1280, 620, 390]
                    for width in widths:
                        report['views'].append(view_checks(browser, url, manifest, counts, width, output, args.canary))
                        print(f'Validated {width}px gap visualizations, analyses, and 17-Mech coverage', flush=True)
                    if not args.canary:
                        report['analytics_failure'] = analytics_failure_check(browser, url, manifest, output)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
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
