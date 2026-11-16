#!/usr/bin/env python3
"""Exercise the knowledge-gap embedding browser for issue #609; 2026-11-15.

Inputs: generated assets and optional actual Jekyll site. Outputs: a JSON receipt,
screenshots and verified exports in repository .temp. Run --canary and inspect
its persisted result before expanding. Failure injection runs only on localhost.
"""
import argparse
import csv
import datetime as dt
import functools
import http.server
import json
from pathlib import Path
import threading
import urllib.parse

import check_gap_browser_20261114 as qa
import check_gap_terms_20261115 as terms_qa

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / '.temp/gap-embedding-20261115'


def settled(page):
    terms_qa.settled(page)
    page.wait_for_function("() => document.querySelector('#gap-map-status').textContent === 'Embedding map loaded.' && !document.querySelector('#gap-map-content').hidden")


def points(page):
    return page.locator('#gap-map-plot circle').evaluate_all("""nodes => nodes.map(e => ({
      id:e.dataset.gapId,x:e.getAttribute('cx'),y:e.getAttribute('cy'),fill:e.getAttribute('fill')}))""")


def assert_scope(page, expected_ids):
    settled(page)
    actual = points(page)
    assert len(actual) == len(expected_ids) and {row['id'] for row in actual} == set(expected_ids)
    assert page.locator('#gap-map-point option').count() == len(expected_ids) + 1
    return {row['id']: row for row in actual}


def export_check(page, expected_ids, document, output, name, format_):
    with page.expect_download() as download:
        page.locator('#gap-map-export-' + format_).click()
    path = output / (name + '.' + format_)
    download.value.save_as(path)
    assert path.stat().st_size > 0
    if format_ == 'json':
        result = json.loads(path.read_text())
        assert result['build_id'] == document['build_id'] and result['terms_sha256'] == document['terms_sha256']
        assert result['inputs_sha256'] == document['inputs_sha256']
        assert result['model'] == document['model'] and result['projection'] == document['projection']
        actual = {point['id'] for point in result['points']}
        expected = {point['id']: point for point in document['points']}
        for point in result['points']:
            assert all(point[key] == value for key, value in expected[point['id']].items())
        assert {context['id'] for context in result['contexts']} == actual
        wanted_records = {key for context in result['contexts'] for key in context['record_ids']}
        assert {record['id'] for record in result['records']} == wanted_records
    else:
        with path.open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        actual = {row['id'] for row in rows}
        expected = {point['id']: point for point in document['points']}
        for row in rows:
            assert float(row['x']) == expected[row['id']]['x'] and float(row['y']) == expected[row['id']]['y']
    assert actual == set(expected_ids)
    return {'points': len(actual), 'bytes': path.stat().st_size, 'sha256': qa.sha(path)}


def view_checks(browser, url, manifest, index, document, term_document, width, output):
    context = browser.new_context(viewport={'width': width, 'height': 900}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    items = index['items']
    by_id = {item['id']: item for item in items}
    contexts = {row['id']: row for row in document['contexts']}
    records = {row['id']: row for row in document['records']}
    try:
        page.goto(url, wait_until='networkidle'); terms_qa.settled(page)
        assert page.locator('#gap-map-content').is_hidden()
        page.locator('#gap-map-load').click(); settled(page)
        active = terms_qa.scope(items)
        initial = assert_scope(page, [item['id'] for item in active])
        assert len(initial) > 50, 'Canary must exercise matching discussions beyond the first result page'
        report = {'width': width, 'initial_mapped': len(initial), 'layout': qa.layout(page)}
        page.locator('#gap-map-plot').screenshot(path=str(output / f'{width}-map-light.png'))
        first_box = page.locator('#gap-map-plot svg').get_attribute('viewBox')
        page.locator('#gap-map-zoom-in').click()
        assert page.locator('#gap-map-plot svg').get_attribute('viewBox') != first_box
        page.locator('#gap-map-reset').click()
        assert page.locator('#gap-map-plot svg').get_attribute('viewBox') == first_box
        page.locator('#gap-map-plot svg').focus(); page.keyboard.press('ArrowRight')
        assert page.locator('#gap-map-plot svg').get_attribute('viewBox') != first_box
        page.keyboard.press('0')
        assert page.locator('#gap-map-plot svg').get_attribute('viewBox') == first_box
        page.locator('#gap-map-color').select_option('kind')
        assert set(assert_scope(page, initial)) == set(initial)
        page.locator('#gap-map-color').select_option('mech')
        page.locator('#gap-next').click(); settled(page)
        assert assert_scope(page, initial) == initial
        report['pagination_does_not_change_map'] = True

        # Choose an off-page discussion with an actual retained native definition.
        shown = set(page.locator('#gap-results .gap-open').evaluate_all('nodes => nodes.map(e=>e.dataset.gapId)'))
        selected = next(key for key in initial if key not in shown and any(
            records[record_id]['description_status'] == 'present' for record_id in contexts[key]['record_ids']))
        page.locator('#gap-map-point').select_option(selected)
        page.wait_for_function('prompt => document.querySelector("#gap-detail-title").textContent === prompt', arg=by_id[selected]['prompt'])
        assert page.locator('#gap-detail-body').get_by_role('link', name='Pinned source record', exact=True).count() == 1
        assert page.locator('#gap-detail-body .gap-map-detail-context > details').count() == 1
        assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query).get('gap') == [selected]
        selection = page.locator('#gap-map-selection')
        assert selection.is_visible()
        assert selection.locator('details').count() == len(contexts[selected]['record_ids'])
        for position, record_id in enumerate(contexts[selected]['record_ids']):
            record = records[record_id]
            if record['description_status'] == 'present':
                assert selection.locator('details').nth(position).locator('.gap-map-description').text_content() == record['description']
        cold_url = page.url
        page.go_back(); settled(page)
        assert 'gap' not in urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)
        page.go_forward(); settled(page)
        page.wait_for_function('prompt => document.querySelector("#gap-detail-title").textContent === prompt', arg=by_id[selected]['prompt'])
        page.goto(cold_url + '#gap-map-title', wait_until='networkidle'); settled(page)
        assert page.locator('#gap-map-point').input_value() == selected
        page.locator('#gap-close-detail').click()
        circle = page.locator('#gap-map-plot circle[data-gap-id="' + selected + '"]')
        circle.focus(); circle.press('Enter')
        page.wait_for_function('prompt => document.querySelector("#gap-detail-title").textContent === prompt', arg=by_id[selected]['prompt'])
        report['off_page_point_populated_context_and_history'] = True
        report['keyboard_point_opens_discussion'] = True

        page.locator('#gap-mech').select_option('TraitMech'); settled(page)
        trait = terms_qa.scope(items, 'TraitMech')
        trait_ids = {item['id'] for item in trait}
        subset = assert_scope(page, trait_ids)
        assert all(row == initial[key] for key, row in subset.items())
        report['fixed_coordinates_and_colors_under_filtering'] = True
        ranked, pairs, membership = terms_qa.expected(term_document['terms'], trait)
        chosen_term = ranked[0]['id']
        page.locator('#gap-term-cloud button').first.click(); settled(page)
        assert_scope(page, membership[chosen_term])
        pair = pairs[0]
        page.locator('#gap-term-pairs button').first.click(); settled(page)
        pair_ids = membership[pair['a']] & membership[pair['b']]
        assert_scope(page, pair_ids)
        report['pair_export'] = export_check(page, pair_ids, document, output, f'{width}-map-pair', 'json')
        report['pair_csv'] = export_check(page, pair_ids, document, output, f'{width}-map-pair', 'csv')
        page.locator('#gap-reset').click(); settled(page)
        page.locator('#gap-view').select_option('all'); settled(page)
        all_ids = set(by_id)
        assert_scope(page, all_ids)
        report['all_export'] = export_check(page, all_ids, document, output, f'{width}-map-all', 'json')
        page.locator('#gap-mech').select_option('DUFMech'); settled(page)
        duf_ids = {item['id'] for item in items if item['mech'] == 'DUFMech'}
        assert_scope(page, duf_ids)
        page.locator('#gap-mech').select_option('PathwayMech'); settled(page)
        assert_scope(page, set())
        assert page.locator('#gap-map-empty').is_visible() and page.locator('#gap-map-export-json').is_disabled()
        page.locator('#gap-reset').click(); settled(page)
        page.locator('#gap-query').fill('<script>map-no-match & literal</script>'); page.locator('#gap-query').press('Enter'); settled(page)
        assert_scope(page, set())
        page.locator('#gap-reset').click(); settled(page)
        page.evaluate("document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('culturebot-theme','dark')")
        page.locator('#gap-map-plot').screenshot(path=str(output / f'{width}-map-dark.png'))
        report.update(dark_layout=qa.layout(page), point_scope_filters_and_empty_states=True,
                      page_errors=errors)
        assert not errors, errors
        return report
    finally:
        context.close()


def failure_checks(browser, url, manifest, output):
    context = browser.new_context(viewport={'width': 390, 'height': 900})
    path = '/assets/gaps/' + manifest['embedding']['url']
    qa.Handler.faults[path] = 1
    try:
        page = context.new_page(); page.goto(url + '#gap-map-title', wait_until='networkidle'); terms_qa.settled(page)
        page.wait_for_function("() => document.querySelector('#gap-map-status').textContent.startsWith('Embedding map could not load:')")
        assert page.locator('#gap-results .gap-open').count() > 0
        assert page.locator('#gap-map-content').is_hidden()
        page.screenshot(path=str(output / '390-map-load-failure.png'))
        page.locator('#gap-map-retry').click(); settled(page)
        assert page.locator('#gap-map-plot circle').count() > 50
        return {'map_failure_preserves_search_and_retries': True}
    finally:
        qa.Handler.faults.pop(path, None); context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path)
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets/gaps')
    parser.add_argument('--summary', type=Path, default=ROOT / '_includes/gaps-summary.html')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--browser-executable', type=Path)
    parser.add_argument('--canary', action='store_true')
    args = parser.parse_args()
    for name in ('site', 'assets', 'summary', 'report'):
        if getattr(args, name) is not None:
            setattr(args, name, getattr(args, name).resolve())
    output = TEMP / (args.report.stem + '-artifacts'); output.mkdir(parents=True, exist_ok=True)
    report = {'complete': False, 'canary': args.canary, 'views': [],
              'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'artifacts': str(output.relative_to(ROOT))}
    qa.TEMP = TEMP
    try:
        site, report['provenance'] = qa.prepare(args)
        assets = site / 'assets/gaps'
        manifest = json.loads((assets / 'manifest.json').read_text())
        documents = {}
        for key in ('index', 'terms', 'embedding'):
            file = assets / manifest[key]['url']
            assert qa.sha(file) == manifest[key]['sha256']
            documents[key] = json.loads(file.read_text())
            assert documents[key]['build_id'] == manifest['build_id']
        assert documents['embedding']['terms_sha256'] == manifest['terms']['sha256']
        report.update(build_id=manifest['build_id'], embedding_sha256=manifest['embedding']['sha256'])
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(qa.Handler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with qa.sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=str(args.browser_executable) if args.browser_executable else None)
                try:
                    report['browser_version'] = browser.version
                    url = f'http://127.0.0.1:{server.server_port}/knowledge-gaps/'
                    for width in ([1280] if args.canary else [1280, 390]):
                        report['views'].append(view_checks(browser, url, manifest, documents['index'], documents['embedding'], documents['terms'], width, output))
                        print(f'{width}px embedding membership, fixed coordinates, context, history and exports passed', flush=True)
                    if not args.canary:
                        report['failures'] = failure_checks(browser, url, manifest, output)
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
