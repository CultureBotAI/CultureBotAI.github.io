#!/usr/bin/env python3
"""Verify the ThiS-family false-positive repair for issue #605; 2026-11-15.

Inputs: --baseline-ref Git assets, current --assets, and retained gap snapshot and
vocabulary. Output: --output JSON evidence with six removed source contexts,
independent counts, asset hashes, and assertions that other term data is intact.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.gaps.terms import iter_item_texts

BASELINE = 'cabf5b4b12e419774bc5f6a00c75a9882a25c100'
CANONICAL_ID = 'PFAM:PF02597'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def document_digest(value):
    return digest((json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n').encode())


def git_bytes(revision, path):
    return subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT)


def asset_path(url):
    path = PurePosixPath(url)
    assert not path.is_absolute() and '..' not in path.parts, url
    return path.as_posix()


def verified_assets(manifest, read):
    entries = {'index': manifest['index'], 'terms': manifest['terms'], **manifest['details']}
    checked = {}
    terms = None
    for name, entry in entries.items():
        raw = read(asset_path(entry['url']))
        checked[name] = digest(raw)
        assert checked[name] == entry['sha256'], f'Asset hash mismatch: {name}'
        if name == 'terms':
            terms = json.loads(raw)
    return terms, checked


def totals(document):
    result = {
        'recognized_terms': len(document['terms']),
        'accepted_occurrences': sum(p['count'] for term in document['terms'] for p in term['postings']),
        'discussions_with_terms': len({p['discussion_id'] for term in document['terms'] for p in term['postings']}),
    }
    assert all(document['summary'][key] == value for key, value in result.items())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', default=BASELINE)
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets/gaps')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ['git', 'rev-parse', '--verify', '--end-of-options', args.baseline_ref + '^{commit}'],
        cwd=ROOT, text=True).strip()
    report = {'complete': False, 'issue': 605, 'baseline_revision': revision,
              'canonical_id': CANONICAL_ID, 'verification': {}}
    try:
        before_raw = git_bytes(revision, 'assets/gaps/manifest.json')
        after_raw = (args.assets / 'manifest.json').read_bytes()
        before_manifest, after_manifest = json.loads(before_raw), json.loads(after_raw)
        before, before_hashes = verified_assets(
            before_manifest, lambda path: git_bytes(revision, 'assets/gaps/' + path))
        after, after_hashes = verified_assets(after_manifest, lambda path: (args.assets / path).read_bytes())
        report['hashes'] = {'baseline_manifest': digest(before_raw), 'current_manifest': digest(after_raw),
                            'baseline_assets': before_hashes, 'current_assets': after_hashes}
        report['verification']['asset_hashes_valid'] = True
        snapshot_raw = (ROOT / '_gaps/snapshot.json').read_bytes()
        vocabulary_raw = (ROOT / '_gaps/term-vocabulary.json').read_bytes()
        assert snapshot_raw == git_bytes(revision, '_gaps/snapshot.json')
        assert vocabulary_raw == git_bytes(revision, '_gaps/term-vocabulary.json')
        snapshot, vocabulary = json.loads(snapshot_raw), json.loads(vocabulary_raw)
        assert before['build_id'] == after['build_id'] == document_digest(snapshot)
        assert before['vocabulary_sha256'] == after['vocabulary_sha256'] == document_digest(vocabulary)
        assert before_manifest['build_id'] == after_manifest['build_id'] == before['build_id']
        report.update(snapshot_sha256=before['build_id'], vocabulary_sha256=before['vocabulary_sha256'])
        report['verification']['snapshot_and_vocabulary_unchanged'] = True
        manifests = [deepcopy(value) for value in (before_manifest, after_manifest)]
        for value in manifests:
            del value['terms']
            del value['sizes']['terms_bytes']
            del value['sizes']['terms_gzip_bytes']
        assert manifests[0] == manifests[1], 'Unexpected non-term manifest change'
        report['verification']['search_detail_and_other_manifest_data_unchanged'] = True
        removed = [term for term in before['terms'] if term['canonical_id'] == CANONICAL_ID]
        assert len(removed) == 1
        assert after['terms'] == [term for term in before['terms'] if term['canonical_id'] != CANONICAL_ID]
        assert before['ambiguities'] == after['ambiguities']
        assert before['vocabulary_sources'] == after['vocabulary_sources']
        report['verification']['all_other_terms_postings_and_ambiguities_unchanged'] = True
        items = {item['id']: item for item in snapshot['items']}
        contexts, counts = [], Counter()
        for posting in removed[0]['postings']:
            item = items[posting['discussion_id']]
            fields = dict(iter_item_texts(item))
            assert posting['count'] == len(posting['mentions'])
            for mention in posting['mentions']:
                context = fields[mention['field']]
                assert context[mention['start']:mention['end']] == mention['text'] == 'this family'
                counts[item['mech']] += 1
                contexts.append({'discussion_id': item['id'], 'mech': item['mech'],
                                 'record_id': item['record_id'], 'record_label': item['record_label'],
                                 'kind': item['kind'], 'source_url': item['source']['url'],
                                 **mention, 'context': context})
        assert len(contexts) == 6 and counts == {'DUFMech': 3, 'TraitMech': 3}
        report.update(removed_occurrences=contexts, removed_by_mech=dict(sorted(counts.items())),
                      before=totals(before), after=totals(after))
        assert report['before']['accepted_occurrences'] - report['after']['accepted_occurrences'] == 6
        assert report['before']['recognized_terms'] - report['after']['recognized_terms'] == 1
        expected_summary = dict(before['summary'])
        expected_summary.update(report['after'])
        expected_summary['case_rejected_occurrences'] += 6
        assert after['summary'] == expected_summary, 'Unexpected summary change'
        report['verification']['exactly_six_false_matches_removed'] = True
        report['complete'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        assert args.output.stat().st_size and json.loads(args.output.read_text()) == report
    print(json.dumps({'complete': True, 'output': str(args.output), 'removed_by_mech': report['removed_by_mech']}))


if __name__ == '__main__':
    main()
