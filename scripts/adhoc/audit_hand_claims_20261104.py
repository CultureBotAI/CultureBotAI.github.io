#!/usr/bin/env python3
"""Audit hand-curated X-Mech claim sources for the November 4 refresh PR.

Inputs: central fragment/template and isolated snapshot's immutable revisions.
Outputs: primary-source hashes, changed-file diffs, line anchors, schema/license
receipts and matching cross-reference pairs under _fleet/reviews/refresh-20261104.
No production source or shared checkout is modified. Date: 2026-11-04.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = '56ec3db204095e425e2ed7481d4f97b997906815'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True)


def blob(root, sha, path):
    result = subprocess.run(['git', '-C', str(root), 'show', f'{sha}:{path}'], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def objects(text, variable):
    body = text.split(f'var {variable} = ', 1)[1].split('\n  ];', 1)[0]
    result = []
    for line in body.splitlines():
        if '{ ' not in line:
            continue
        row = {}
        for key, value in re.findall(r'(\w+):\s*("(?:[^"\\]|\\.)*"|true|false|\d+)', line):
            row[key] = json.loads(value)
        if row:
            result.append(row)
    return result


def source_receipt(clone, before_sha, after_sha, path, anchor=None, terms=()):
    a, b = blob(clone, before_sha, path), blob(clone, after_sha, path)
    row = {'path': path, 'before_sha': before_sha, 'after_sha': after_sha,
           'exists_before': a is not None, 'exists_at_pin': b is not None,
           'unchanged': a is not None and a == b,
           'sha256': hashlib.sha256(b).hexdigest() if b is not None else None}
    if b is None:
        return row
    lines = b.decode('utf-8', 'replace').splitlines()
    if anchor:
        row['anchor'] = anchor
        row['anchor_excerpt'] = [{'line': i+1, 'text': lines[i]} for i in range(max(0,anchor-4), min(len(lines),anchor+4))]
    pattern = re.compile('|'.join(re.escape(term) for term in terms), re.I) if terms else None
    row['evidence_excerpts'] = [{'line': i+1, 'text': line} for i, line in enumerate(lines)
                                if pattern and pattern.search(line)][:50]
    if a is not None and a != b:
        changes = list(difflib.unified_diff(a.decode('utf-8', 'replace').splitlines(), lines,
                                           fromfile=before_sha + ':' + path, tofile=after_sha + ':' + path))
        row['diff_lines'] = len(changes)
        row['diff'] = '\n'.join(changes[:300])
        row['diff_truncated'] = len(changes) > 300
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--links', action='store_true')
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    old_stats = json.loads(git(ROOT, 'show', BASE + ':_fleet/data/mech_stats.json'))
    old = {row['mech']: row['source_revision'] for row in old_stats['mechs']}
    repo_to_mech = {row['repo'].lower(): name for name, row in pins.items()}
    fragment = (ROOT / '_fleet/fleet_fragment.html').read_text()
    template = (ROOT / '_fleet/mechs_template.md').read_text()
    refs = objects(fragment, 'XREFS')
    pairs = re.findall(r'<div class="pair"><b>([^<]+)</b><i>→</i><b class="to">([^<]+)</b>', template)
    receipts = {'xrefs': [], 'hub': objects(fragment, 'HUB'), 'schema_licenses': {},
                'pairs_match': sorted(tuple((r['from'], r['to'])) for r in refs) == sorted(pairs)}
    for index, row in enumerate(refs, 1):
        entry = {'number': index, 'locator': f"XREFS {row['from']} → {row['to']}", 'claim': row}
        match = re.fullmatch(r'https://github.com/CultureBotAI/([^/]+)/blob/([^/]+)/(.+?)(?:#L(\d+))?', row['url'])
        if not match:
            entry['unhandled_url'] = row['url']
            receipts['xrefs'].append(entry)
            continue
        repo, prior_ref, path, line = match.groups()
        name = repo_to_mech[repo.lower()]
        before = old[name] if prior_ref == 'main' else prior_ref
        pin = pins[name]['sha']
        clone = args.snapshot / 'mechs' / name
        entry['new_url'] = row['url'].replace('/blob/' + prior_ref + '/', '/blob/' + pin + '/')
        entry['primary_source'] = source_receipt(clone, before, pin, path, int(line) if line else None,
                                                [row['from'], row['to'], row['from'].lower(), row['to'].lower()])
        auxiliary = []
        for evidence_path, evidence_sha, evidence_line in re.findall(r'([A-Za-z0-9_./-]+)@([0-9a-f]{40})(?::(\d+))?', row['ev']):
            candidates = [(n, p) for n, p in pins.items() if old[n] == evidence_sha or p['sha'] == evidence_sha]
            if len(candidates) == 1:
                owner, owner_pin = candidates[0]
                auxiliary.append(source_receipt(args.snapshot / 'mechs' / owner, evidence_sha, owner_pin['sha'], evidence_path,
                                                 int(evidence_line) if evidence_line else None, [row['from'], row['to']]))
        entry['auxiliary_sources'] = auxiliary
        receipts['xrefs'].append(entry)
    for name, pin in pins.items():
        clone = args.snapshot / 'mechs' / name
        paths = git(clone, 'ls-tree', '-rz', '--name-only', pin['sha']).split('\0')
        schemas = [p for p in paths if re.fullmatch(r'src/[^/]+/schema/[^/]+\.yaml', p)]
        roots = {}
        for path in schemas:
            doc = yaml.safe_load(blob(clone, pin['sha'], path))
            roots[path] = [key for key, definition in (doc.get('classes') or {}).items()
                           if isinstance(definition, dict) and definition.get('tree_root')]
        licenses = [p for p in paths if '/' not in p and p.upper().startswith('LICENSE')]
        receipts['schema_licenses'][name] = {
            'pin': pin['sha'], 'tree_roots': roots,
            'licenses': [source_receipt(clone, old[name], pin['sha'], path, terms=['CC BY', 'BSD', 'AIO', 'data/curated', 'data/aio'])
                         for path in licenses]}
    receipts['explore_urls'] = sorted(set(re.findall(r'https://culturebotai\.github\.io/[^\s\"<>)]+', template)))
    if args.links:
        import urllib.request
        checked = []
        for url in receipts['explore_urls']:
            try:
                request = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'xmech-refresh-audit'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    checked.append({'url': url, 'status': response.status, 'final_url': response.url})
            except Exception as exc:
                checked.append({'url': url, 'error': str(exc)})
        receipts['explore_head_checks'] = checked
    destination = ROOT / '_fleet/reviews/refresh-20261104/hand-claims-sources.json'
    destination.write_text(json.dumps(receipts, indent=2) + '\n')
    print(f"{len(refs)} cross references; template pairs match={receipts['pairs_match']}; primary changed=" +
          str([r['number'] for r in receipts['xrefs'] if not r.get('primary_source', {}).get('unchanged')]))
    print(f'Verified receipt: {destination} ({destination.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
