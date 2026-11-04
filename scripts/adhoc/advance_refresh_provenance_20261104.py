#!/usr/bin/env python3
"""Advance verified source pins and refresh dates for the November 4 X-Mech PR.

Inputs: old site audit, new pins, independently reviewed XREF source receipt.
Outputs: maintained prose/URLs only; the normal builder owns site_audit.json.
Every cited path must exist at its new pin; XREF hashes/anchors are reverified.
2026-11-04. Dry-run by default, --apply after inspecting the evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = ['_fleet/mechs_template.md', '_fleet/fleet_fragment.html', '_fleet/README.md',
         'index.md', 'resources.md', 'research.md', 'microgrowagents.md', 'culturemech.md',
         'mediaingredientmech.md', 'communitymech.md', 'CLAUDE.md']


def blob(clone, sha, path):
    return subprocess.check_output(['git', '-C', str(clone), 'show', f'{sha}:{path}'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--only-file', choices=FILES)
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    old = json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show',
                      '56ec3db204095e425e2ed7481d4f97b997906815:_fleet/data/site_audit.json']))
    by_repo = {row['repo'].lower(): (name, row) for name, row in pins['mechs'].items()}
    old_by_repo = {row['repo'].lower(): row for row in old['repositories']}
    by_sha = {row['sha']: name for name, row in pins['mechs'].items()}
    reviewed = json.loads((ROOT / '_fleet/reviews/refresh-20261104/hand-claims-sources.json').read_text())
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
            if lines[excerpt['line']-1] != excerpt['text']:
                raise ValueError('reviewed anchor differs: ' + row['locator'])
        if not source['unchanged'] and (name, match[3]) != ('TaxonMech', 'docs/CURATION.md'):
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
                if aux_content.decode().splitlines()[excerpt['line']-1] != excerpt['text']:
                    raise ValueError('reviewed auxiliary anchor differs')
    # The changed Taxon curation document's scope row was independently read;
    # its new overlay implementation section does not alter the three scope arrows.
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
                subprocess.run(['git', '-C', str(args.snapshot / 'mechs' / name), 'cat-file', '-e', pin['sha'] + ':' + relpath], check=True)
                checked.add((name, relpath))
            text = text.replace(previous, pin['sha'])
        text = text.replace('October 29, 2026', 'November 4, 2026')
        text = text.replace('The October 29 refresh', 'The November 4 refresh')
        text = text.replace('October 29 pins', 'November 4 pins')
        text = text.replace('2026-10-30 04:50 UTC', '2026-11-04 11:34 UTC')
        text = text.replace('snapshot at 1877438', 'snapshot at 09b39ca')
        text = text.replace('governed artifacts and 27 capabilities', 'governed artifacts and 28 capabilities')
        if text != before:
            changes.append(file)
            if args.apply:
                path.write_text(text)
    receipt = {'xref_primary_hashes_and_anchors_verified': len(reviewed['xrefs']),
               'other_link_paths_verified': sorted([list(item) for item in checked]), 'updated_files': changes}
    if args.apply:
        (ROOT / '_fleet/reviews/refresh-20261104/provenance-edits.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
