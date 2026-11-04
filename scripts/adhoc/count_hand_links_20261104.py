#!/usr/bin/env python3
"""Recount numeric cross-reference claims at the Nov 4 X-Mech refresh pins.

Inputs: isolated snapshot record corpus and committed source blobs. Outputs:
hand-claims-counts.json with exact field-level counters and samples. 2026-11-04.
Serves the refresh PR; does not edit any page source or shared checkout.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import roots


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    roots.MECHS_ROOT = str(args.snapshot / 'mechs')
    result = {}
    for name in ['NaturalProductMech', 'AntibioticMech', 'CellStructureMech', 'TraitMech', 'HabitatMech', 'MediaIngredientMech', 'CommunityMech']:
        records = defaultdict(set)
        entries, relations, traits, identifiers = Counter(), Counter(), Counter(), Counter()
        targets = defaultdict(set)
        samples = defaultdict(list)
        import_ids = {}
        for path in roots.record_paths(name):
            raw = Path(path).read_text()
            doc = yaml.load(raw, Loader=yaml.CSafeLoader)
            relpath = str(Path(path).relative_to(args.snapshot / 'mechs' / name))
            for node in walk(doc):
                for link in node.get('related_records') or []:
                    if not isinstance(link, dict):
                        continue
                    corpus = link.get('corpus')
                    if corpus:
                        records[corpus].add(relpath)
                        entries[corpus] += 1
                        targets[corpus].add(link.get('identifier'))
                        relations[str(corpus) + ':' + str(link.get('relation'))] += 1
                        if len(samples[corpus]) < 3:
                            samples[corpus].append({'path': relpath, 'link': link})
                if node.get('node_type') == 'TRAIT':
                    traits['nodes'] += 1
                    for key in ['grounding', 'trait_term', 'identifier']:
                        if node.get(key):
                            traits['with_' + key] += 1
                if 'media_ingredient_mech_id' in node:
                    identifiers[str(node['media_ingredient_mech_id'])] += 1
                if node.get('source') == 'communitymech-unmapped':
                    records['communitymech-unmapped'].add(relpath)
                    entries['communitymech-unmapped'] += 1
                    if len(samples['communitymech-unmapped']) < 3:
                        samples['communitymech-unmapped'].append({'path': relpath, 'synonym': node})
            if relpath in records['communitymech-unmapped']:
                import_ids[relpath] = sorted(set(re.findall(r'source_id=(communitymech\.ingredient:[^\s;)]+)', raw)))
        result[name] = {'pin': pins[name]['sha'], 'related_record_counts': {k: len(v) for k,v in records.items()},
                        'related_entries': dict(entries), 'unique_targets': {k: len(v) for k,v in targets.items()},
                        'relations': dict(relations), 'trait_nodes': dict(traits),
                        'media_ingredient_mech_ids': dict(identifiers), 'samples': dict(samples),
                        'related_record_paths': {k: sorted(v) for k, v in records.items()},
                        'community_import_source_ids': import_ids}
        print(name, result[name]['related_record_counts'], result[name]['trait_nodes'], flush=True)
    for name in ['TraitMech', 'CellStructureMech', 'TaxonMech']:
        clone = args.snapshot / 'mechs' / name
        pin = pins[name]['sha']
        values = {}
        for label, pattern in [('curation_event', 'curation_event'), ('write_validated', 'write_validated')]:
            done = subprocess.run(['git', '-C', str(clone), 'grep', '-l', pattern, pin, '--', 'scripts/*.py', 'scripts/**/*.py'], text=True, capture_output=True)
            if done.returncode not in (0, 1):
                raise RuntimeError(done.stderr)
            values[label] = {line.split(':', 1)[1] for line in done.stdout.splitlines()}
        result.setdefault(name, {})['scripts_naming_both_helpers'] = sorted(values['curation_event'] & values['write_validated'])
        result[name]['scripts_naming_either_helper'] = sorted(values['curation_event'] | values['write_validated'])
    out = ROOT / '_fleet/reviews/refresh-20261104/hand-claims-counts.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Verified receipt {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
