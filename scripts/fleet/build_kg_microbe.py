"""Count the released kg-microbe core KGX node records for the heatmap only.

python3 scripts/fleet/build_kg_microbe.py /path/to/kg-microbe-core.tar.gz

The source manifest pins the public release asset by SHA-256. Counts use the
suite's prefix registry over every node field, including xrefs and descriptions.
Edges, graph-local identifiers and unregistered namespaces are outside this
comparison. One KGX node is one matching record; this is not a Mech corpus.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
from urllib.parse import quote, urlsplit

from build_cells import encoded
from prefix_census import norm, rx

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '_fleet/kg_microbe_source.json'
SUMMARY = ROOT / '_fleet/data/kg_microbe_census.json'
ASSETS = ROOT / 'assets/fleet/comparison-cells'


def digest(stream):
    sha = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        sha.update(chunk)
    return sha.hexdigest()


def node_url(row, release):
    """A term's external page, or the release containing a graph-local node."""
    iri = row.get('iri', '')
    parsed = urlsplit(iri)
    if parsed.scheme in ('http', 'https') and parsed.netloc and not parsed.username:
        return 'https://' + iri.split('://', 1)[1]
    identifier = row['id']
    if rx.fullmatch(identifier):
        return 'https://bioregistry.io/' + quote(identifier, safe=':')
    return release


def scan(stream, source, cap=300):
    reader = csv.DictReader(stream, delimiter='\t')
    fields = reader.fieldnames or []
    if not {'id', 'name', 'xref', 'description'} <= set(fields) or len(fields) != len(set(fields)):
        raise ValueError('Expected a KGX node table with unique column names')
    seen = set()
    occurrences = collections.Counter()
    totals = collections.Counter()
    samples = collections.defaultdict(list)
    for row in reader:
        identifier = row.get('id')
        if None in row or any(value is None for value in row.values()) or not identifier or identifier in seen:
            raise ValueError('Malformed or duplicate KGX node record')
        seen.add(identifier)
        found = collections.Counter(norm.get(p, p) for p in rx.findall('\t'.join(row.values())))
        occurrences.update(found)
        totals.update(found.keys())
        for prefix in found:
            if len(samples[prefix]) < cap:
                label = (row['name'] + ' · ' if row['name'] else '') + identifier
                samples[prefix].append(['', label, node_url(row, source['release_url'])])
    if not seen or not occurrences:
        raise ValueError('Empty KGX node census')
    docs = {
        'kg-microbe|' + prefix: {
            'mech': 'kg-microbe', 'prefix': prefix, 'base': source['release_url'],
            'total': totals[prefix], 'occurrences': count, 'records': samples[prefix],
        } for prefix, count in sorted(occurrences.items())
    }
    return len(seen), dict(sorted(occurrences.items())), docs


def build(archive, source):
    with archive.open('rb') as handle:
        if digest(handle) != source['sha256']:
            raise ValueError('kg-microbe release asset SHA-256 does not match the source manifest')
    # Read only named members; never extract archive paths into the workspace.
    with tarfile.open(archive) as outer, tempfile.TemporaryFile() as inner:
        member = outer.getmember(source['archive_member'])
        if not member.isfile():
            raise ValueError('Expected a regular nested graph archive')
        with outer.extractfile(member) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                inner.write(chunk)
        inner.seek(0)
        with tarfile.open(fileobj=inner) as graph:
            node = graph.getmember(source['nodes_member'])
            if not node.isfile():
                raise ValueError('Expected a regular KGX node table')
            with graph.extractfile(node) as handle:
                node_hash = digest(handle)
            with graph.extractfile(node) as handle:
                records, prefixes, docs = scan(io.TextIOWrapper(handle, encoding='utf-8', newline=''), source)
    summary = {
        'name': 'kg-microbe', 'key': 'kgmicrobe', 'site': '/kg-microbe/',
        'source': dict(source, nodes_sha256=node_hash),
        'as_of': datetime.date.today().isoformat(), 'records': records,
        'method': 'Identifier occurrences in all KGX node fields, including xrefs and descriptions, '
                  'using the suite namespace registry. Edges, graph-local identifiers and '
                  'unregistered namespaces are excluded. One node is one matching record.',
        'prefixes': prefixes,
        'cells': {key: {'records': doc['total'], 'occurrences': doc['occurrences'],
                        'sha256': hashlib.sha256(encoded(doc)).hexdigest()}
                  for key, doc in docs.items()},
    }
    return summary, docs


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    summary, docs = build(args.archive, json.loads(SOURCE.read_text()))
    ASSETS.mkdir(parents=True, exist_ok=True)
    wanted = {key.replace('|', '--') + '.json' for key in docs}
    for key, doc in docs.items():
        (ASSETS / (key.replace('|', '--') + '.json')).write_bytes(encoded(doc))
    for path in ASSETS.glob('kg-microbe--*.json'):
        if path.name not in wanted:
            path.unlink()
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(f"kg-microbe: {summary['records']:,} nodes; {len(summary['prefixes'])} tracked vocabularies")


if __name__ == '__main__':
    main()
