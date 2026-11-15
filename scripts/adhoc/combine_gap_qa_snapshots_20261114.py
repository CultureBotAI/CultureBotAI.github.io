#!/usr/bin/env python3
"""Combine real pinned pilot snapshots for numbered-shard QA (#581), 2026-11-14.

Inputs: disjoint snapshots with the same configuration and exporter envelope.
Output: a QA-only combined snapshot at a caller-specified repository .temp path.
Source coverage and scientific items are preserved; no production asset writes.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.temp'):
        raise ValueError('QA snapshot output must remain inside repository .temp')
    docs = [json.loads(path.read_text()) for path in args.inputs]
    if len(docs) < 2:
        raise ValueError('Supply at least two snapshots')
    for doc in docs:
        for key in ('schema_version', 'source_config_sha256', 'exporter'):
            if doc[key] != docs[0][key]:
                raise ValueError(f'Snapshot {key} mismatch')
    sources, items = [], []
    names, identities = set(), set()
    for doc in docs:
        for source in doc['sources']:
            if source['name'] in names:
                raise ValueError('Duplicate source: ' + source['name'])
            names.add(source['name'])
            sources.append(source)
        for item in doc['items']:
            if item['id'] in identities:
                raise ValueError('Duplicate item identity: ' + item['id'])
            identities.add(item['id'])
            items.append(item)
    if any(item['mech'] not in names for item in items):
        raise ValueError('Item without source coverage')
    combined = {key: docs[0][key] for key in ('schema_version', 'source_config_sha256', 'exporter')}
    combined.update(sources=sources, items=sorted(items, key=lambda item: item['id']))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(combined, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n')
    if not output.stat().st_size or json.loads(output.read_text()) != combined:
        raise ValueError('QA snapshot did not persist correctly')
    print(json.dumps({'sources': sorted(names), 'items': len(items), 'output': str(output.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
