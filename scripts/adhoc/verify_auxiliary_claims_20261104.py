#!/usr/bin/env python3
"""Verify retained auxiliary inventory claims for the Nov 4 X-Mech refresh PR.

Inputs: immutable ProteinTraitsMech/DUF/NP/Taxon object stores and owner records.
Outputs: hand-claims-auxiliary.json; these auxiliary products do not join the
fleet's unchanged record census. No checkout writes. Date: 2026-11-04.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import roots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    roots.MECHS_ROOT = str(args.snapshot / 'mechs')
    result = {}
    def blob(name, path, sha=None):
        return subprocess.check_output(['git', '-C', str(args.snapshot / 'mechs' / name), 'show', (sha or pins[name]['sha']) + ':' + path])

    name = 'ProteinTraitsMech'
    inventory = blob(name, 'data/cross_mech/protein_inventory.jsonl')
    coverage = json.loads(blob(name, 'data/cross_mech/coverage.json'))
    statuses = dict(Counter(json.loads(line)['status'] for line in inventory.splitlines()))
    assert statuses == coverage['counts']['proteins_by_status']
    assert hashlib.sha256(inventory).hexdigest() == coverage['artifact_sha256']['protein_inventory.jsonl']
    mentions = blob(name, 'data/cross_mech/protein_mentions.jsonl')
    assert hashlib.sha256(mentions).hexdigest() == coverage['mentions_sha256']
    mention_rows = [json.loads(line) for line in mentions.splitlines()]
    result[name] = {'pin': pins[name]['sha'], 'proteins_by_status': statuses,
                    'inventory_sha256_matches_coverage': True, 'protein_mentions': len(mention_rows),
                    'mentions_sha256': hashlib.sha256(mentions).hexdigest(),
                    'mention_roles': dict(Counter(str(row.get('role')) for row in mention_rows))}
    print(name, statuses, len(mention_rows), flush=True)

    name = 'DUFMech'
    family_manifest = json.loads(blob(name, 'data/families/manifest.json'))
    counts, characterized = Counter(), Counter()
    found = set()
    command = ['git', '-C', str(args.snapshot / 'mechs' / name), 'archive', pins[name]['sha'], 'data/families']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout, mode='r|') as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith('.yaml'):
                continue
            raw = archive.extractfile(member).read()
            key = Path(member.name).name
            assert hashlib.sha256(raw).hexdigest() == family_manifest[key]
            found.add(key)
            row = yaml.load(raw, Loader=yaml.CSafeLoader)
            counts[row.get('curation_status')] += 1
            characterized[row.get('characterization_status')] += 1
    assert process.wait() == 0
    assert found == family_manifest.keys()
    cross = json.loads(blob(name, 'data/cross_mech/cross-mech-duf-examples-2026-10-10.manifest.json'))
    cross_raw = blob(name, 'data/cross_mech/' + cross['files']['json']['path'])
    assert hashlib.sha256(cross_raw).hexdigest() == cross['files']['json']['sha256']
    cross_rows = json.loads(cross_raw)
    assert len(cross_rows) == cross['rows']['total']
    cov = cross['snapshot']['derivation']['coverage']
    result[name] = {'pin': pins[name]['sha'], 'native_families': len(found),
                    'native_curation_status': dict(counts), 'native_characterization_status': dict(characterized),
                    'all_native_hashes_match_manifest': True, 'cross_mech_rows': len(cross_rows),
                    'cross_mech_hash_matches_manifest': True, 'scanned_families': cov['scanned_families'],
                    'unscanned_families': len(cov['unscanned_pfam_ids'])}
    print(name, result[name], flush=True)

    name = 'NaturalProductMech'
    owners, references, checked = 0, 0, []
    for path in roots.record_paths(name):
        doc = yaml.load(Path(path).read_bytes(), Loader=yaml.CSafeLoader)
        refs = doc.get('causal_graph_refs') or []
        if refs:
            owners += 1
        for graph_id in refs:
            ikey = doc['chemical_structure']['standard_inchi_key']
            component_path = f'data/causal_graphs/{ikey}/{graph_id}.yaml'
            raw = blob(name, component_path)
            component = yaml.load(raw, Loader=yaml.CSafeLoader)
            assert component['record_id'] == doc['identifier']
            assert component['standard_inchi_key'] == ikey
            assert component['graph']['graph_id'] == graph_id
            references += 1
            checked.append({'owner': str(Path(path).relative_to(args.snapshot / 'mechs' / name)),
                            'record_id': doc['identifier'], 'inchikey': ikey, 'component': component_path,
                            'sha256': hashlib.sha256(raw).hexdigest()})
    result[name] = {'pin': pins[name]['sha'], 'referencing_owners': owners, 'referenced_components': references,
                    'owner_id_inchikey_and_graph_id_match': True, 'components': checked}
    print(name, owners, references, flush=True)

    name = 'TaxonMech'
    prior = '830eb576c1381e73aba1ed284c1ae005c7a5337e'
    command = ['git', '-C', str(args.snapshot / 'mechs' / name), 'grep', '-lz', '^causal_graphs:', pins[name]['sha'], '--', 'data/taxa']
    matches = subprocess.check_output(command).decode().split('\0')
    graph_paths = [item.split(':', 1)[1] for item in matches if item]
    node_types, trait_groundings = Counter(), Counter()
    trait_owners = set()
    for path in graph_paths:
        doc = yaml.load(blob(name, path), Loader=yaml.CSafeLoader)
        for graph in doc.get('causal_graphs') or []:
            for node in graph.get('nodes') or []:
                node_types[node.get('node_type')] += 1
                if node.get('node_type') == 'TRAIT':
                    trait_owners.add(path)
                    trait_groundings[str(node.get('grounding'))] += 1
    paths = subprocess.check_output(['git', '-C', str(args.snapshot / 'mechs' / name), 'diff', '--name-only', '-z', prior, pins[name]['sha'], '--', 'data/taxa'], text=True).split('\0')
    comparisons = []
    for path in filter(None, paths):
        before, after = yaml.load(blob(name, path, prior), Loader=yaml.CSafeLoader), yaml.load(blob(name, path), Loader=yaml.CSafeLoader)
        for doc in (before, after):
            doc.pop('curation_history', None)
            doc.pop('causal_graphs', None)
        same = before == after
        assert same, path
        comparisons.append({'path': path, 'equal_outside_history_and_graphs': same})
    notes = []
    for source, value in [('pages/index.html', '100745'), ('pages/index.html', '20648'), ('README.md', '21,071')]:
        page = blob(name, source).decode()
        match = re.search('.{0,80}' + re.escape(value) + '.{0,160}', page)
        assert match, value
        notes.append({'source': source, 'value': value, 'source_excerpt': match.group(0)})
    result[name] = {'pin': pins[name]['sha'], 'previous_pin': prior,
                    'graph_records': len(graph_paths), 'graph_node_types': dict(node_types),
                    'trait_node_records': sorted(trait_owners), 'trait_groundings': dict(trait_groundings),
                    'changed_record_count': len(comparisons), 'all_other_record_blobs_unchanged': True,
                    'changed_records_unchanged_outside_history_and_graphs': comparisons, 'pinned_source_figures': notes}
    print(name, len(comparisons), 'changed records preserve strain/type-strain/genome metadata', flush=True)
    out = ROOT / '_fleet/reviews/refresh-20261104/hand-claims-auxiliary.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Verified receipt: {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
