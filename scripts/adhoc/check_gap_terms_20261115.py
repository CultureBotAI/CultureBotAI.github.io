#!/usr/bin/env python3
"""Browser acceptance evidence for the Mech term explorer, issue #583, 2026-11-15.

Inputs: generated gap assets and optional actual Jekyll site. Outputs: JSON
receipt, screenshots and verified filtered downloads. Run --canary first.
No source mutations, research-provider calls or deployment operations.
"""
import argparse
import csv
import datetime as dt
import functools
import http.server
import itertools
import json
from pathlib import Path
import threading
import unicodedata
import urllib.parse

import check_gap_browser_20261114 as qa

ROOT = Path(__file__).resolve().parents[2]
TEMP = ROOT / '.temp/gap-terms-20261115'


def folded(value):
    return unicodedata.normalize('NFKC', value).lower()


def scope(items, mech='', all_discussions=False):
    return [item for item in items if (not mech or item['mech'] == mech) and
            (all_discussions or (item['lane'] != 'candidate' and
             item['kind'] in ('KNOWLEDGE_GAP', 'HUMAN_MODEL_MISMATCH') and
             item['status'] in ('OPEN', 'UNDER_DISCUSSION')))]


def expected(terms, items, vocab=''):
    """Independent count arithmetic over published postings, without browser code."""
    ids = {item['id'] for item in items}
    ranked, memberships = [], {}
    for term in terms:
        if vocab and not any(ref['mech'] == vocab for ref in term['entity_refs']):
            continue
        selected = [p for p in term['postings'] if p['discussion_id'] in ids]
        if not selected:
            continue
        memberships[term['id']] = {p['discussion_id'] for p in selected}
        ranked.append({'id': term['id'], 'label': term['label'],
                       'occurrences': sum(p['count'] for p in selected),
                       'discussions': len(selected)})
    ranked.sort(key=lambda row: (-row['occurrences'], folded(row['label']), row['id']))
    pairs = []
    for a, b in itertools.combinations(ranked[:20], 2):
        both = memberships[a['id']] & memberships[b['id']]
        if both:
            pairs.append({'a': a['id'], 'b': b['id'], 'discussions': len(both)})
    ranks = {term['id']: i for i, term in enumerate(ranked)}
    pairs.sort(key=lambda pair: (-pair['discussions'], ranks[pair['a']], ranks[pair['b']]))
    return ranked, pairs, memberships


def settled(page):
    page.wait_for_function("""() => !document.querySelector('#gap-app').hidden &&
      !/^(Searching|Loading)/.test(document.querySelector('#gap-result-status').textContent) &&
      /^(Entity occurrences loaded|No indexed entity mentions)/.test(document.querySelector('#gap-terms-status').textContent)""")


def assert_count(page, count):
    status = page.locator('#gap-result-status').inner_text()
    assert status.startswith(f'{count:,} matching discussions' if count else 'No discussions match'), status


def assert_charts(page, terms, items, vocab=''):
    ranked, pairs, memberships = expected(terms, items, vocab)
    cloud = page.locator('#gap-term-cloud button').evaluate_all("""nodes => nodes.map(e => ({
      id:e.dataset.term, count:Number(e.querySelector('.gap-term-count').textContent.replaceAll(',',''))}))""")
    assert cloud == [{'id': row['id'], 'count': row['occurrences']} for row in ranked[:50]], cloud
    actual_pairs = page.locator('#gap-term-pairs tr').evaluate_all("""rows => rows.map(row => ({
      a:row.querySelector('button').dataset.term,b:row.querySelector('button').dataset.term2,
      discussions:Number(row.lastElementChild.textContent.replaceAll(',',''))}))""")
    assert actual_pairs == pairs, actual_pairs[:5]
    return ranked, pairs, memberships


def download_check(page, expected_ids, output, name, format_, recognition, terms):
    with page.expect_download() as download:
        page.locator('#gap-export-' + format_).click()
    path = output / (name + '.' + format_)
    download.value.save_as(path)
    assert path.stat().st_size > 0
    if format_ == 'json':
        document = json.loads(path.read_text())
        actual = {item['id'] for item in document['items']}
        assert document['filters']['term']
        assert document['term_recognition'] == recognition
        selected_ids = {document['filters'][key] for key in ('term', 'term2') if document['filters'][key]}
        assert {term['id'] for term in document['selected_entities']} == selected_ids
        by_id = {term['id']: term for term in terms}
        for entity in document['selected_entities']:
            for key in ('label', 'canonical_id', 'entity_refs'):
                assert entity[key] == by_id[entity['id']][key], (entity['id'], key)
    else:
        with path.open(newline='') as handle:
            actual = {row['id'] for row in csv.DictReader(handle)}
    assert actual == expected_ids, (len(actual), len(expected_ids))
    return {'items': len(actual), 'bytes': path.stat().st_size, 'sha256': qa.sha(path)}


def view_checks(browser, url, terms, items, width, output, recognition):
    context = browser.new_context(viewport={'width': width, 'height': 900}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        assert page.goto(url, wait_until='networkidle').status == 200
        settled(page)
        assert page.locator('#gap-mech option').count() == 17
        assert page.locator('#gap-vocab option').count() == 17
        selected = scope(items)
        ranked, pairs, memberships = assert_charts(page, terms, selected)
        assert ranked and pairs
        result = {'width': width, 'initial_discussions': len(selected),
                  'recognized_terms': len(ranked), 'occurrences': sum(r['occurrences'] for r in ranked),
                  'nonzero_top20_pairs': len(pairs), 'layout': qa.layout(page)}
        page.locator('.gap-term-explorer').screenshot(path=str(output / f'{width}-term-cloud-light.png'))
        first = ranked[0]['id']
        initial_history = page.evaluate('history.length')
        button = page.locator('#gap-term-cloud button').filter(has=page.locator('.gap-term-count')).first
        assert button.get_attribute('data-term') == first
        button.focus(); button.press('Enter'); settled(page)
        assert_count(page, len(memberships[first]))
        assert page.evaluate('history.length') == initial_history + 1
        assert_charts(page, terms, selected)
        result['term_json'] = download_check(page, memberships[first], output, f'{width}-term', 'json', recognition, terms)
        pair = pairs[0]
        page.locator('#gap-term-pairs button').first.click(); settled(page)
        pair_ids = memberships[pair['a']] & memberships[pair['b']]
        assert_count(page, len(pair_ids))
        pair_url = page.url
        result['pair_json'] = download_check(page, pair_ids, output, f'{width}-pair', 'json', recognition, terms)
        result['pair_csv'] = download_check(page, pair_ids, output, f'{width}-pair', 'csv', recognition, terms)
        page.go_back(); settled(page)
        assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)['term'] == [first]
        assert_count(page, len(memberships[first]))
        page.go_forward(); settled(page); assert_count(page, len(pair_ids))
        page.reload(wait_until='networkidle'); settled(page); assert_count(page, len(pair_ids))
        assert page.url == pair_url
        result['keyboard_history_cold_pair'] = True
        page.locator('#gap-terms-clear').click(); settled(page); assert_count(page, len(selected))
        page.locator('#gap-mech').select_option('TraitMech'); settled(page)
        trait = scope(items, 'TraitMech')
        assert_charts(page, terms, trait); assert_count(page, len(trait))
        result['individual_mech_discussions'] = len(trait)
        page.locator('.gap-term-explorer').screenshot(path=str(output / f'{width}-trait-cloud.png'))
        page.locator('#gap-mech').select_option('CellStructureMech'); settled(page)
        other_source = scope(items, 'CellStructureMech')
        page.locator('#gap-vocab').select_option('TraitMech'); settled(page)
        assert_count(page, len(other_source))
        owner_ranked, _, owner_memberships = assert_charts(page, terms, other_source, 'TraitMech')
        assert owner_ranked
        owner_term = owner_ranked[0]['id']
        page.locator('#gap-term-cloud button').first.click(); settled(page)
        assert_count(page, len(owner_memberships[owner_term]))
        result['vocabulary_json'] = download_check(page, owner_memberships[owner_term], output, f'{width}-vocabulary', 'json', recognition, terms)
        page.locator('#gap-vocab').select_option('CofactorMech'); settled(page)
        assert_count(page, len(other_source))
        assert not urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query).get('term')
        assert_charts(page, terms, other_source, 'CofactorMech')
        result['independent_source_and_vocabulary'] = True
        page.locator('#gap-vocab').select_option(''); settled(page)
        page.locator('#gap-mech').select_option('PathwayMech'); settled(page)
        assert_count(page, 0)
        assert page.locator('#gap-terms-content').is_hidden()
        page.locator('.gap-coverage > summary').click()
        assert 'unsupported' in page.locator('#gap-coverage').inner_text()
        page.locator('.gap-coverage > summary').click()
        result['unsupported_source_empty_scope'] = True
        page.locator('#gap-reset').click(); settled(page)
        page.locator('#gap-view').select_option('all'); settled(page)
        assert_charts(page, terms, items); assert_count(page, len(items))
        result['all_discussions_scope'] = len(items)
        # #605: exercise the reported source-Mech scope and the independent
        # vocabulary selector against the regenerated occurrence postings.
        page.locator('#gap-mech').select_option('DUFMech'); settled(page)
        duf = [item for item in items if item['mech'] == 'DUFMech']
        duf_ranked, _, _ = assert_charts(page, terms, duf); assert_count(page, len(duf))
        result['duf_source_scope'] = {'discussions': len(duf), 'recognized_terms': len(duf_ranked)}
        page.locator('.gap-term-explorer').screenshot(path=str(output / f'{width}-duf-cloud.png'))
        page.locator('#gap-mech').select_option(''); settled(page)
        page.locator('#gap-vocab').select_option('DUFMech'); settled(page)
        duf_vocabulary, _, _ = assert_charts(page, terms, items, 'DUFMech')
        assert_count(page, len(items))
        result['duf_vocabulary_scope'] = {'recognized_terms': len(duf_vocabulary)}
        page.locator('#gap-vocab').select_option(''); settled(page)
        page.locator('#gap-view').select_option('candidates'); settled(page)
        candidates = [item for item in items if item['lane'] == 'candidate']
        assert_charts(page, terms, candidates); assert_count(page, len(candidates))
        result['candidate_scope'] = len(candidates)
        page.locator('#gap-reset').click(); settled(page)
        page.locator('#gap-query').fill('<script>nonexistent & literal</script>')
        page.locator('#gap-query').press('Enter'); settled(page)
        assert_count(page, 0); assert page.locator('#gap-terms-content').is_hidden()
        result['literal_empty_query'] = True
        page.goto(url + '?term=unavailable-term-id', wait_until='networkidle'); settled(page)
        assert_count(page, 0); assert page.locator('#gap-export-json').is_disabled()
        assert 'not in this entity index' in page.locator('#gap-term-selection-label').inner_text()
        page.goto(url + '?vocab=unavailable-vocabulary&term=' + urllib.parse.quote(first), wait_until='networkidle'); settled(page)
        assert_count(page, 0)
        assert page.locator('#gap-terms-content').is_hidden()
        page.locator('#gap-reset').click(); settled(page)
        page.evaluate("document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('culturebot-theme','dark')")
        page.locator('.gap-term-explorer').screenshot(path=str(output / f'{width}-term-cloud-dark.png'))
        result['dark_layout'] = qa.layout(page)
        result['page_errors'] = errors
        assert not errors, errors
        return result
    finally:
        context.close()


def failure_checks(browser, url, term_path, terms, items):
    results = {}
    active = scope(items)
    ranked, _pairs, memberships = expected(terms, active)
    for selected in (False, True):
        context = browser.new_context()
        try:
            qa.Handler.faults[term_path] = 1
            page = context.new_page()
            page.goto(url + ('?term=' + urllib.parse.quote(ranked[0]['id']) if selected else ''), wait_until='networkidle')
            page.wait_for_function("() => document.querySelector('#gap-terms-status').textContent.startsWith('Entity occurrences could not load')")
            if selected:
                assert page.locator('#gap-results > li').count() == 0
                assert page.locator('#gap-export-json').is_disabled()
                assert 'No broader results' in page.locator('#gap-result-status').inner_text()
            else:
                assert_count(page, len(active))
            page.locator('#gap-terms-retry').click(); settled(page)
            assert_count(page, len(memberships[ranked[0]['id']]) if selected else len(active))
            results['selected_url' if selected else 'ordinary_search'] = 'failed visibly, preserved scope, retried successfully'
        finally:
            context.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path)
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets/gaps')
    parser.add_argument('--summary', type=Path, default=ROOT / '_includes/gaps-summary.html')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--browser-executable', type=Path)
    parser.add_argument('--canary', action='store_true')
    args = parser.parse_args()
    report = {'complete': False, 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'canary': args.canary}
    output = TEMP / (args.report.stem + '-artifacts')
    output.mkdir(parents=True, exist_ok=True)
    try:
        site, provenance = qa.prepare(args)
        report['provenance'] = provenance
        assets = site / 'assets/gaps'
        manifest = json.loads((assets / 'manifest.json').read_text())
        items = json.loads((assets / manifest['index']['url']).read_text())['items']
        term_file = assets / manifest['terms']['url']
        assert qa.sha(term_file) == manifest['terms']['sha256']
        term_doc = json.loads(term_file.read_text())
        assert term_doc['build_id'] == manifest['build_id']
        recognition = {'asset': manifest['terms'], **{key: term_doc[key] for key in
                       ('term_build_id', 'vocabulary_sha256', 'policy')}}
        report.update(build_id=manifest['build_id'], term_sha256=qa.sha(term_file), artifacts=str(output.relative_to(ROOT)))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(qa.Handler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        url = f'http://127.0.0.1:{server.server_port}/knowledge-gaps/'
        try:
            with qa.sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=str(args.browser_executable) if args.browser_executable else None)
                try:
                    report['browser_version'] = browser.version
                    report['views'] = []
                    for width in ([1280] if args.canary else [1280, 390]):
                        report['views'].append(view_checks(browser, url, term_doc['terms'], items, width, output, recognition))
                        print(f'{width}px entity counts, exact term/pair exports, scope and URL checks passed', flush=True)
                    if not args.canary:
                        report['term_load_failures'] = failure_checks(browser, url, '/assets/gaps/' + manifest['terms']['url'], term_doc['terms'], items)
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
        assert json.loads(args.report.read_text()) == report and args.report.stat().st_size
    print(json.dumps({'complete': True, 'report': str(args.report)}))


if __name__ == '__main__':
    main()
