#!/usr/bin/env python3
"""Read-only post-merge gap-browser verification for website PR #582, 2026-11-14.

Inputs: expected website merge SHA; committed assets; live Pages GET responses.
Outputs: report, response bodies/headers, downloads and screenshots under the
repository's .temp directory. Reuses the local QA interactions without fault
injection. Never builds, deploys, sends messages, edits Git or modifies a site.
Run --canary first, inspect its persisted receipt, then run the same command
without --canary for both viewport sizes and warm search/no-JavaScript checks.
"""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import re
import subprocess
import urllib.parse
import urllib.request

import check_gap_browser_20261114 as qa
import check_gap_terms_20261115 as term_qa
import check_gap_embedding_20261115 as embedding_qa

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'CultureBotAI/CultureBotAI.github.io'
ORIGIN = 'https://culturebotai.github.io'
PAGE = ORIGIN + '/knowledge-gaps/'
MANIFEST_PATH = 'assets/gaps/manifest.json'
UI_PATHS = ['assets/gaps/' + name for name in
            ('browser.js', 'search-core.js', 'search-worker.js', 'embedding-map.js', 'browser.css')]
UI_PATHS.append('assets/custom.css')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def persist(path, data):
    if not data:
        raise ValueError(f'Refusing empty evidence: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if path.read_bytes() != data or not path.stat().st_size:
        raise ValueError(f'Evidence read-back failed: {path.name}')


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def get(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'culturebotai-gap-browser-release-verification',
        'Cache-Control': 'no-cache',
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        if response.status != 200 or not data:
            raise ValueError(f'Nonempty HTTP 200 response required: {url}')
        return data, {'url': url, 'final_url': response.url, 'status': response.status,
                      'headers': dict(response.headers), 'bytes': len(data), 'sha256': digest(data)}


def pages_build(expected):
    raw = subprocess.check_output(['gh', 'api', f'repos/{REPOSITORY}/pages/builds/latest'],
                                  stderr=subprocess.PIPE)
    build = json.loads(raw)
    receipt = {key: build.get(key) for key in ('status', 'commit', 'url', 'created_at', 'updated_at', 'duration')}
    receipt['checked_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    if receipt['status'] != 'built' or receipt['commit'] != expected:
        raise ValueError('Latest Pages build does not match the expected release: ' + json.dumps(receipt))
    return receipt


def committed_bytes(revision, path, local_commit):
    if local_commit:
        return subprocess.check_output(['git', '--no-optional-locks', '-C', str(ROOT),
                                        'show', f'{revision}:{path}'], stderr=subprocess.PIPE)
    # Public immutable source bytes are a read-only fallback if the local clone
    # has not acquired the squash merge commit yet. No token or email is sent.
    url = f'https://raw.githubusercontent.com/{REPOSITORY}/{revision}/' + urllib.parse.quote(path, safe='/')
    return get(url)[0]


def descriptor_path(descriptor):
    if not isinstance(descriptor, dict) or not re.fullmatch(r'[0-9a-f]{64}', descriptor.get('sha256', '')):
        raise ValueError('Invalid asset descriptor')
    relative = descriptor.get('url', '')
    # Build output uses plain relative hashed JSON names; reject traversal,
    # cross-origin URLs and query strings before reading local or remote files.
    if not re.fullmatch(r'data/[A-Za-z0-9_.-]+\.json', relative):
        raise ValueError('Unexpected asset URL: ' + str(relative))
    return 'assets/gaps/' + relative


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(value for key, value in attrs if key == 'href' and value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-website-sha', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--canary', action='store_true')
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    expected = args.expected_website_sha
    if not re.fullmatch(r'[0-9a-f]{40}', expected):
        parser.error('--expected-website-sha must be a full lowercase Git commit SHA')
    report_path = args.report.resolve()
    if not report_path.is_relative_to(ROOT / '.temp'):
        parser.error('--report must be inside this repository\'s .temp directory')
    output = report_path.parent / (report_path.stem + '-artifacts')
    output.mkdir(parents=True, exist_ok=True)
    report = {'complete': False, 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'expected_website_sha': expected, 'url': PAGE, 'canary': args.canary,
              'scope': 'Live production Pages checks only: pinned assets, populated browser interactions, exports and navigation. No fault injection, builds, deployment or Git mutations.',
              'reference_platform': platform.platform(), 'views': [], 'navigation': [],
              'responses': {}, 'assets': {}, 'artifacts': str(output.relative_to(ROOT))}
    local_commit = subprocess.run(['git', '--no-optional-locks', '-C', str(ROOT),
                                   'cat-file', '-e', expected + '^{commit}'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    report['committed_asset_source'] = 'local immutable Git objects' if local_commit else 'public raw GitHub URLs at expected SHA'
    try:
        report['pages_before'] = pages_build(expected)
        for label, path in [('page', '/knowledge-gaps/'), ('hub', '/mechs/')]:
            body, response = get(ORIGIN + path)
            report['responses'][label] = response
            persist(output / (label + '.html'), body)
            if label == 'page' and b'id="gap-browser"' not in body:
                raise ValueError('The live HTML is not the gap-browser surface')
            if label == 'hub':
                links = Anchors(); links.feed(body.decode())
                if not any(urllib.parse.urljoin(ORIGIN + path, href) == PAGE for href in links.links):
                    raise ValueError('The live Mech directory does not link to the gap browser')
                report['hub_links_to_browser'] = True
        committed_manifest = committed_bytes(expected, MANIFEST_PATH, local_commit)
        live_manifest, response = get(ORIGIN + '/' + MANIFEST_PATH)
        if live_manifest != committed_manifest:
            raise ValueError('Live manifest differs from committed release bytes')
        persist(output / MANIFEST_PATH, live_manifest)
        report['responses'][MANIFEST_PATH] = response
        report['assets'][MANIFEST_PATH] = {'sha256': digest(live_manifest), 'matches_commit': True, 'bytes': len(live_manifest)}
        manifest = json.loads(live_manifest)
        if manifest.get('schema_version') != 1:
            raise ValueError('Unsupported manifest schema')
        report['build_id'], report['counts'] = manifest['build_id'], manifest['counts']
        descriptors = [('index', manifest['index'])] + [('detail:' + key, value) for key, value in sorted(manifest['details'].items())]
        if 'terms' in manifest:
            descriptors.append(('terms', manifest['terms']))
        if 'embedding' in manifest:
            descriptors.append(('embedding', manifest['embedding']))
        if 'analytics' in manifest:
            descriptors.append(('analytics', manifest['analytics']))
        paths = {}
        for label, descriptor in descriptors:
            path = descriptor_path(descriptor)
            if path in paths:
                raise ValueError('Duplicate generated asset path')
            paths[path] = (label, descriptor['sha256'])
        paths.update({path: ('ui', None) for path in UI_PATHS})
        index, term_document, embedding_document, analytics_document = None, None, None, None
        for path, (label, declared_hash) in paths.items():
            committed = committed_bytes(expected, path, local_commit)
            if declared_hash and digest(committed) != declared_hash:
                raise ValueError('Committed manifest hash mismatch: ' + path)
            live, response = get(ORIGIN + '/' + path)
            if live != committed:
                raise ValueError('Live asset differs from committed release: ' + path)
            if label != 'ui':
                document = json.loads(live)
                if document.get('schema_version') != 1 or document.get('build_id') != manifest['build_id']:
                    raise ValueError('Asset build ID mismatch: ' + path)
                if label == 'index':
                    index = document
                elif label == 'terms':
                    term_document = document
                elif label == 'embedding':
                    embedding_document = document
                elif label == 'analytics':
                    analytics_document = document
            persist(output / path, live)
            report['responses'][path] = response
            report['assets'][path] = {'kind': label, 'sha256': digest(live), 'matches_commit': True, 'bytes': len(live)}
        if index is None or len(index['items']) != manifest['counts']['items']:
            raise ValueError('Index count does not match live manifest')
        if embedding_document is not None and (
                term_document is None or embedding_document['terms_sha256'] != manifest['terms']['sha256']):
            raise ValueError('Embedding map is not bound to the live term matches')
        if analytics_document is not None:
            if term_document is not None and analytics_document.get('terms_sha256') != manifest['terms']['sha256']:
                raise ValueError('Analytics sidecar is not bound to the live term matches')
            if embedding_document is not None and analytics_document.get('embedding_inputs_sha256') != embedding_document.get('inputs_sha256'):
                raise ValueError('Analytics sidecar is not bound to the live embedding inputs')
        report['detail_shards_verified'] = len(manifest['details'])
        persist(output / 'http-responses.json', json_bytes(report['responses']))
        print(f'Live manifest, index, {len(manifest["details"])} detail shards and UI match {expected}', flush=True)
        with qa.sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=str(args.browser_executable) if args.browser_executable else None)
            try:
                report['browser_version'] = browser.version
                for width in ([1280] if args.canary else [1280, 390]):
                    report['views'].append(qa.view_checks(browser, PAGE, manifest, index, width, output))
                    if term_document is not None:
                        recognition = {'asset': manifest['terms'], **{key: term_document[key] for key in
                                       ('term_build_id', 'vocabulary_sha256', 'policy')}}
                        report.setdefault('term_views', []).append(term_qa.view_checks(
                            browser, PAGE, term_document['terms'], index['items'], width, output, recognition))
                    if embedding_document is not None:
                        report.setdefault('embedding_views', []).append(embedding_qa.view_checks(
                            browser, PAGE, manifest, index, embedding_document, term_document, width, output))
                    navigation = qa.navigation_check(browser, PAGE, index, width, output)
                    navigation['scope'] = 'Live production header route, mobile menu and populated detail; the live hub backlink was separately checked by HTTP.'
                    report['navigation'].append(navigation)
                    print(f'Live {width}px search, full exports, details and navigation passed', flush=True)
                if not args.canary:
                    report['warm_query'] = qa.warm_queries(browser, PAGE, manifest)
                    context = browser.new_context(java_script_enabled=False)
                    try:
                        page = context.new_page(); page.goto(PAGE, wait_until='networkidle')
                        page.locator('.gap-static summary').click()
                        summary = page.locator('.gap-static').inner_text()
                        if (not page.locator('noscript').is_visible()
                                or not all(source['name'] in summary for source in manifest['sources'])
                                or not all(member['name'] in summary for member in manifest.get('infrastructure', []))):
                            raise ValueError('Live no-JavaScript summary lacks a source or explanation')
                        report['no_js_all_sources'] = True
                    finally:
                        context.close()
            finally:
                browser.close()
        report['pages_after'] = pages_build(expected)
        after_manifest, response = get(ORIGIN + '/' + MANIFEST_PATH)
        report['responses']['manifest_after'] = response
        if after_manifest != committed_manifest:
            raise ValueError('Live manifest changed during verification')
        persist(output / 'manifest-after.json', after_manifest)
        persist(output / 'http-responses.json', json_bytes(report['responses']))
        report['complete'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        persist(report_path, json_bytes(report))
        if json.loads(report_path.read_text()) != report:
            raise ValueError('Final live receipt read-back failed')
    print(json.dumps({'complete': report['complete'], 'report': str(report_path.relative_to(ROOT)), 'build_id': report['build_id']}))


if __name__ == '__main__':
    main()
