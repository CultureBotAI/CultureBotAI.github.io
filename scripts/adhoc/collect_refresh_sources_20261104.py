#!/usr/bin/env python3
"""Capture pinned card figures and cited source excerpts for the Nov 4 refresh PR.

Inputs: isolated snapshot and unchanged card-source definitions. Outputs: JSON
evidence under _fleet/reviews/refresh-20261104; no shared checkout writes.
Date: 2026-11-04. Invoke --only TraitMech as the acquisition canary first.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import build_site_audit
import check_cards


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--only')
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    evidence = {}
    for name, pin in pins['mechs'].items():
        if args.only and name != args.only:
            continue
        clone = args.snapshot / 'mechs' / name
        show = build_site_audit.git_show(clone, pin['sha'])
        kind, source, selector = check_cards.SOURCES[name]
        source_path, body = build_site_audit.committed_copy(show, source)
        if kind == 'git-tree':
            source_path = check_cards.INVENTORY_DIRS[name] + ' inventory'
            body = check_cards.record_inventory(show('__git_tree__').decode(), selector)
        at_pin = None if name in check_cards.NO_PIN_COPY else build_site_audit.read_figure(name, kind, body, selector, source_path)
        row = {'sha': pin['sha'], 'card_source': source_path, 'card_at_pin': at_pin,
               'source_sha256': hashlib.sha256(body).hexdigest() if body else None, 'documents': {}}
        paths = subprocess.check_output(['git', '-C', str(clone), 'ls-tree', '-rz', '--name-only', pin['sha']], text=True).split('\0')
        selected = [p for p in paths if p in ('README.md', 'LICENSE', 'LICENSE-DATA', 'LICENSE-CODE')
                    or re.fullmatch(r'src/[^/]+/schema/[^/]+\.yaml', p)]
        for path in selected:
            content = show(path)
            text = content.decode('utf-8')
            lines = text.splitlines()
            if path.startswith('LICENSE'):
                excerpts = [{'line': i+1, 'text': line} for i, line in enumerate(lines)
                            if re.search(r'BSD|CC BY|Creative Commons|data/aio|data/curated|license|licence|code|source', line, re.I)]
            elif path == 'README.md':
                excerpts = [{'line': i+1, 'text': line} for i, line in enumerate(lines)
                            if re.search(r'\d|ground|status|categories|causal|corpus|mechanism|concept|source', line, re.I)]
            else:
                excerpts = [{'line': i+1, 'text': '\n'.join(lines[max(0,i-3):i+3])}
                            for i, line in enumerate(lines) if 'tree_root:' in line]
            row['documents'][path] = {'url': f"https://github.com/CultureBotAI/{pin['repo']}/blob/{pin['sha']}/{path}",
                                       'sha256': hashlib.sha256(content).hexdigest(), 'excerpts': excerpts}
        evidence[name] = row
        print(f"{name}: pinned card {at_pin}; {len(selected)} source documents", flush=True)
    out = ROOT / '_fleet/reviews/refresh-20261104' / ('source-excerpts-' + (args.only or 'fleet') + '.json')
    out.write_text(json.dumps(evidence, indent=2) + '\n')
    assert out.stat().st_size > 100
    print(f'VERIFIED {out}: {out.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
