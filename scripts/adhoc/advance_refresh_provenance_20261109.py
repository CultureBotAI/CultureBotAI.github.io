#!/usr/bin/env python3
"""Advance verified source pins and refresh dates for the November 9 X-Mech PR.

Inputs: old site audit, new pins, independently reviewed XREF source receipt.
Outputs: maintained prose/URLs and _fleet/infrastructure.json only; the normal builder owns site_audit.json.
Every cited path must exist at its new pin; XREF hashes/anchors are reverified.
2026-11-09. Dry-run by default, --apply after inspecting the evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = '59ff865e401dba047acccd5c9334e7965e70aca0'
FILES = ['_fleet/mechs_template.md', '_fleet/fleet_fragment.html', '_fleet/README.md',
         'index.md', 'resources.md', 'research.md', 'microgrowagents.md', 'culturemech.md',
         'mediaingredientmech.md', 'communitymech.md', 'CLAUDE.md']
REVIEWED_CHANGED_SOURCES = set()
GIT_ENV = {
    **os.environ,
    'GIT_CONFIG_GLOBAL': '/dev/null',
    'GIT_CONFIG_NOSYSTEM': '1',
}


def blob(clone, sha, path):
    return subprocess.check_output(['git', '-C', str(clone), 'show', f'{sha}:{path}'], env=GIT_ENV)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--only-file', choices=FILES)
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    old = json.loads(subprocess.check_output([
        'git', '-C', str(ROOT), 'show',
        f'{BASE_COMMIT}:_fleet/data/site_audit.json'
    ], env=GIT_ENV))
    by_repo = {row['repo'].lower(): (name, row) for name, row in pins['mechs'].items()}
    old_by_repo = {row['repo'].lower(): row for row in old['repositories']}
    by_sha = {row['sha']: name for name, row in pins['mechs'].items()}
    reviewed = json.loads((ROOT / '_fleet/reviews/refresh-20261109/hand-claims-sources.json').read_text())
    url_updates = {}
    checked = set()
    for row in reviewed['xrefs']:
        url = row['new_url']
        match = re.match(r'https://github.com/CultureBotAI/([^/]+)/blob/([^/]+)/([^#]+)', url)
        name, pin = by_repo[match[1].lower()]
        source = row['primary_source']
        content = blob(args.snapshot / 'mechs' / name, pin['sha'], match[3])
        if hashlib.sha256(content).hexdigest() != source['sha256']:
            raise ValueError('reviewed XREF bytes differ: ' + row['locator'])
        lines = content.decode().splitlines()
        for excerpt in source.get('anchor_excerpt', []):
            if lines[excerpt['line'] - 1] != excerpt['text']:
                raise ValueError('reviewed anchor differs: ' + row['locator'])
        if not source['unchanged'] and (name, match[3]) not in REVIEWED_CHANGED_SOURCES:
            raise ValueError('changed evidence needs separate review: ' + row['locator'])
        if source['unchanged']:
            if blob(args.snapshot / 'mechs' / name, source['before_sha'], match[3]) != content:
                raise ValueError('incorrect unchanged-source assertion')
        url_updates[row['claim']['url']] = url
        for auxiliary in row['auxiliary_sources']:
            aux_name = by_sha[auxiliary['after_sha']]
            aux_content = blob(args.snapshot / 'mechs' / aux_name, auxiliary['after_sha'], auxiliary['path'])
            if hashlib.sha256(aux_content).hexdigest() != auxiliary['sha256']:
                raise ValueError('reviewed auxiliary source bytes differ')
            for excerpt in auxiliary.get('anchor_excerpt', []):
                if aux_content.decode().splitlines()[excerpt['line'] - 1] != excerpt['text']:
                    raise ValueError('reviewed auxiliary anchor differs')

    changes = []
    for file in FILES:
        if args.only_file and file != args.only_file:
            continue
        path = ROOT / file
        before = text = path.read_text()
        for old_url, new_url in url_updates.items():
            text = text.replace(old_url, new_url)
        for name, pin in pins['mechs'].items():
            previous = old_by_repo[pin['repo'].lower()]['sha']
            if previous == pin['sha'] or previous not in text:
                continue
            for match in re.finditer(r'https://github.com/CultureBotAI/([^/]+)/(blob|tree)/' + previous + r'/([^\s\"\)<>#]+)', text):
                if match[1].lower() != pin['repo'].lower():
                    raise ValueError('mismatched repository in pin link')
                relpath = match[3]
                subprocess.run(['git', '-C', str(args.snapshot / 'mechs' / name), 'cat-file', '-e', pin['sha'] + ':' + relpath], env=GIT_ENV, check=True)
                checked.add((name, relpath))
            text = text.replace(previous, pin['sha'])
        text = text.replace('November 8, 2026', 'November 9, 2026')
        text = text.replace('The November 8 refresh', 'The November 9 refresh')
        text = text.replace('The November 8\nrefresh', 'The November 9\nrefresh')
        text = text.replace('November 8 pins', 'November 9 pins')
        text = text.replace('2026-11-08 20:35 UTC', '2026-11-09 12:41 UTC')
        text = text.replace('0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34', 'e539df04bc92364727c2f22c46fe7ecbac3ce116')
        text = text.replace('snapshot at e36c6ae', 'snapshot at e539df0')
        text = text.replace(
            'The CLAW governance snapshot at e539df0 declares all fourteen members, 26\ngoverned artifacts and 28 capabilities, including record-review declarations.\nThe added evidence-reference validation contract is enabled for MediaIngredientMech,\nCellStructureMech and HabitatMech; the other eleven members record explicit reasons\nfor leaving it disabled.',
            'The CLAW governance snapshot at e539df0 declares 15 members (fourteen corpus\nMechs plus EdgeMech curation infrastructure), 26 governed artifacts and 28 capabilities,\nincluding record-review declarations. The added evidence-reference validation contract is\nenabled for MediaIngredientMech, CellStructureMech and HabitatMech; the other twelve\nmembers record explicit reasons for leaving it disabled.'
        )
        if text != before:
            changes.append(file)
            if args.apply:
                path.write_text(text)

    if not args.only_file:
        infra_path = ROOT / '_fleet/infrastructure.json'
        infra_before = infra_path.read_text()
        infra = json.loads(infra_before)
        infra['members']['EdgeMech']['checked_on'] = '2026-11-09'
        infra['members']['EdgeMech']['evidence_url'] = (
            'https://github.com/CultureBotAI/culturebotai-claw/blob/'
            f"{pins['claw']}/src/kg_microbe_fleet/fleet.yaml"
        )
        infra_after = json.dumps(infra, indent=2) + '\n'
        if infra_after != infra_before:
            changes.append('_fleet/infrastructure.json')
            if args.apply:
                infra_path.write_text(infra_after)

    receipt = {
        'xref_primary_hashes_and_anchors_verified': len(reviewed['xrefs']),
        'other_link_paths_verified': sorted([list(item) for item in checked]),
        'updated_files': changes,
    }
    if args.apply:
        (ROOT / '_fleet/reviews/refresh-20261109/provenance-edits.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
