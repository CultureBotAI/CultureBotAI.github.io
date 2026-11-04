#!/usr/bin/env python3
"""Acquire current public integration/release evidence for the Nov 4 refresh PR.

Inputs: pinned Mech snapshot, GitHub repository/release APIs, kg-microbe's
declared default branch. Outputs: hand-claims-hub.json. Does not change the
separate release comparison, page sources, or any Mech checkout. 2026-11-04.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def gh(path, raw=False):
    args = ['gh', 'api', path]
    if raw:
        args += ['-H', 'Accept: application/vnd.github.raw+json']
    value = subprocess.check_output(args, text=True)
    return value if raw else json.loads(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--only')
    parser.add_argument('--local-only', action='store_true', help='append pinned local source evidence to the saved network receipt')
    args = parser.parse_args()
    names = ['CultureMech', 'CommunityMech', 'AntibioticMech', 'ProteinTraitsMech', 'CellStructureMech', 'NaturalProductMech']
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    data = {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'releases': {}, 'kg_microbe': {}}
    if args.local_only:
        data = json.loads((ROOT / '_fleet/reviews/refresh-20261104/hand-claims-hub.json').read_text())
    for name in names:
        if args.local_only:
            break
        if args.only and name != args.only:
            continue
        releases = gh('repos/CultureBotAI/' + pins[name]['repo'] + '/releases?per_page=1')
        data['releases'][name] = [{'tag_name': row['tag_name'], 'published_at': row['published_at'],
                                   'url': row['html_url'], 'draft': row['draft'], 'prerelease': row['prerelease']}
                                  for row in releases]
        print(name, len(releases), flush=True)
    if not args.only and not args.local_only:
        repository = 'Knowledge-Graph-Hub/kg-microbe'
        repo = gh('repos/' + repository)
        pin = gh('repos/' + repository + '/commits/' + repo['default_branch'])
        data['kg_microbe'] = {'repository': repository, 'default_branch': repo['default_branch'],
                              'sha': pin['sha'], 'commit_date': pin['commit']['committer']['date'], 'sources': {}}
        for path in ['docs/INGREDIENT_ACCEPTANCE.md', 'docs/SEMANTIC_MODEL_DECISIONS_20260914.md',
                     'scripts/mim_conservative_refresh.py', 'kg_microbe/utils/ingredient_context.py',
                     'README.md', 'docs/runbooks/reviewed-release-inputs.md']:
            content = gh('repos/' + repository + '/contents/' + path + '?ref=' + pin['sha'], raw=True)
            lines = content.splitlines()
            selected = set()
            for i, line in enumerate(lines):
                if re.search(r'candidate|production|promot|MediaIngredientMech|MIM|ingredient.context|optional|stage', line, re.I):
                    selected.update(range(max(0,i-2), min(len(lines),i+3)))
            data['kg_microbe']['sources'][path] = {
                'url': f'https://github.com/{repository}/blob/{pin["sha"]}/{path}',
                'sha256': hashlib.sha256(content.encode()).hexdigest(),
                'excerpts': [{'line': i+1, 'text': lines[i]} for i in sorted(selected)]}
    if not args.only:
        paths = {
            'CultureMech': ['src/culturemech/schema/mech_shared.yaml', 'src/culturemech/match/kg_media_matcher.py'],
            'CommunityMech': ['src/communitymech/schema/mech_shared.yaml', 'scripts/gtdb_ground.py', 'src/communitymech/embedding/loader.py'],
            'TraitMech': ['src/traitmech/templates/graph.html', 'src/traitmech/templates/trait.html'],
            'TaxonMech': ['src/taxonmech/extract.py'],
            'HabitatMech': ['src/habitatmech/extract.py', 'src/habitatmech/seed.py'],
            'MediaIngredientMech': ['src/mediaingredientmech/validation/kg_microbe_dict.py'],
            'AntibioticMech': ['src/antibioticmech/schema/antibioticmech.yaml'],
            'NaturalProductMech': ['src/naturalproductmech/schema/naturalproductmech.yaml'],
            'ProteinTraitsMech': ['src/proteintraitsmech/schema/mech_shared.yaml'],
            'CellStructureMech': ['src/cellstructuremech/schema/mech_shared.yaml'],
        }
        data['pinned_mech_sources'] = {}
        for name, members in paths.items():
            data['pinned_mech_sources'][name] = {}
            for path in members:
                raw = subprocess.check_output(['git', '-C', str(args.snapshot / 'mechs' / name), 'show', pins[name]['sha'] + ':' + path])
                lines = raw.decode().splitlines()
                selected = set(range(min(42, len(lines))))
                for i, line in enumerate(lines):
                    if re.search(r'kg.microbe|DeepWalk|Madin|gtdb/|lpsn/|mediadive/|bactotraits/|PREGO|GOLD|BacDive|alternate|synonym', line, re.I):
                        selected.update(range(max(0,i-1), min(len(lines),i+2)))
                data['pinned_mech_sources'][name][path] = {
                    'url': f'https://github.com/CultureBotAI/{pins[name]["repo"]}/blob/{pins[name]["sha"]}/{path}',
                    'sha256': hashlib.sha256(raw).hexdigest(),
                    'excerpts': [{'line': i+1, 'text': lines[i]} for i in sorted(selected)[:160]]}
    suffix = '-' + args.only if args.only else ''
    out = ROOT / f'_fleet/reviews/refresh-20261104/hand-claims-hub{suffix}.json'
    out.write_text(json.dumps(data, indent=2) + '\n')
    assert out.stat().st_size > 100
    print(f'Verified receipt: {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
