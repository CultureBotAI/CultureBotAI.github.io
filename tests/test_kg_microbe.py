"""Release-backed graph comparisons stay distinct from Mech corpora."""
import copy
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import build_data
import build_kg_microbe as kg
import build_site_audit
import build_subsets
import check_cards
import prefix_census
import roots


class KGXTests(unittest.TestCase):
    source = {'release_url': 'https://github.com/Knowledge-Graph-Hub/kg-microbe/releases/tag/2025-03-07'}

    def table(self, rows):
        text = io.StringIO()
        writer = csv.writer(text, delimiter='\t', lineterminator='\n')
        writer.writerow(['id', 'name', 'xref', 'description', 'iri'])
        writer.writerows(rows)
        text.seek(0)
        return text

    def test_counts_mentions_and_matching_nodes_separately_without_graph_local_ids(self):
        stream = self.table([
            ['CHEBI:1', 'First', 'ChEBI:2|Chemspider:3|LINCS:LSM-1', 'PMID:7\nCHEBI:1', 'https://example.org/1'],
            ['strain:local', 'Second', 'CHEBI:1|biolink:Thing', 'Unregistered:1', ''],
            ['GO:1', 'Third', '', 'CHEBI:2', ''],
        ])
        total, prefixes, docs = kg.scan(stream, self.source, cap=1)
        self.assertEqual(total, 3)
        self.assertEqual(prefixes, {'CHEBI': 5, 'ChemSpider': 1, 'GO': 1, 'LINCS': 1, 'PMID': 1})
        doc = docs['kg-microbe|CHEBI']
        self.assertEqual((doc['occurrences'], doc['total'], len(doc['records'])), (5, 3, 1))
        self.assertEqual(doc['records'][0], ['', 'First · CHEBI:1', 'https://example.org/1'])
        self.assertEqual(kg.node_url({'id': 'strain:local'}, self.source['release_url']), self.source['release_url'])

    def test_refuses_duplicate_nodes_and_incomplete_rows(self):
        row = ['CHEBI:1', 'First', '', '', '']
        for stream in (self.table([row, row]), self.table([row[:-1]]), io.StringIO('id\tname\n1\tFirst\n')):
            with self.assertRaises(ValueError):
                kg.scan(stream, self.source)

    def test_new_registry_aliases_apply_to_mechs_too(self):
        text = 'CELEX:32024R1252 Chemspider:42 PDBeChem:ATP GlyGen:G123 Patent:EP123'
        self.assertEqual([prefix_census.norm.get(p, p) for p in prefix_census.rx.findall(text)],
                         ['CELEX', 'ChemSpider', 'PDB', 'GlyTouCan', 'patent'])
        self.assertIn('CELEX', roots.CITATION)
        self.assertEqual(build_subsets.terms_in('PDBeChem:ATP envo:1 pato:2 foodon:3'),
                         {'PDB-CCD:ATP', 'ENVO:1', 'PATO:2', 'FOODON:3'})

    def test_comparison_assets_match_the_release_census(self):
        summary = json.loads((ROOT / '_fleet/data/kg_microbe_census.json').read_text())
        source = json.loads(kg.SOURCE.read_text())
        self.assertEqual({k: v for k, v in summary['source'].items() if k != 'nodes_sha256'}, source)
        build_data.validate_comparison(summary)
        expected = {key.replace('|', '--') + '.json' for key in summary['cells']}
        self.assertEqual({p.name for p in kg.ASSETS.glob('*.json')}, expected)
        for key, row in summary['cells'].items():
            asset = kg.ASSETS / (key.replace('|', '--') + '.json')
            payload = asset.read_bytes()
            doc = json.loads(payload)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), row['sha256'])
            self.assertEqual((doc['total'], doc['occurrences']), (row['records'], row['occurrences']))
            self.assertEqual(len(doc['records']), min(300, row['records']))
            self.assertTrue(all(link[2].startswith('https://') for link in doc['records']))

    def test_comparison_only_affects_heatmap_not_fleet_or_graph(self):
        read = lambda name: json.loads((ROOT / '_fleet/data' / name).read_text())
        sub, cen, cells, comparison = map(read, ('subsets_summary.json', 'prefix_census.json', 'cells_summary.json', 'kg_microbe_census.json'))
        with mock.patch('builtins.print'):
            baseline = build_data.build(sub, cen, cells)
            result = build_data.build(sub, cen, cells, comparison)
        self.assertEqual(result['order'], baseline['order'])
        self.assertEqual(result['vocab_edges'], baseline['vocab_edges'])
        self.assertEqual(result['indexed_voc'], baseline['indexed_voc'])
        self.assertNotIn('kg-microbe', roots.ORDER)
        self.assertIn('kg-microbe', result['heat'])
        for key in ('records', 'occurrences', 'sha256'):
            broken = copy.deepcopy(comparison)
            row = next(iter(broken['cells'].values()))
            row[key] = 'bad'
            with self.assertRaises(ValueError):
                build_data.validate_comparison(broken)


class CMMMechTests(unittest.TestCase):
    def tree(self, rows, truncated=False):
        return json.dumps({'truncated': truncated, 'tree': [
            {'path': p, 'type': 'blob', 'mode': '100644', 'sha': 'a' * 40} for p in rows]})

    def test_inventory_counts_only_canonical_recursive_yaml_records(self):
        kind, _, selector = check_cards.SOURCES['CMMMech']
        body = self.tree(['data/records/cobalt.yaml', 'data/records/pilots/metal.yml',
                          'tests/fixtures/example.yaml', 'reviews/cobalt.yaml', 'data/records/README.md'])
        self.assertEqual(check_cards.published(kind, body, selector), 2)
        for bad in (self.tree(['data/records/a.yaml'], True),
                    self.tree(['data/records/a.yaml', 'data/records/a.yaml']), '{}'):
            with self.assertRaises(ValueError):
                check_cards.published(kind, bad, selector)
        symlink = json.loads(self.tree(['data/records/a.yaml']))
        symlink['tree'][0]['mode'] = '120000'
        with self.assertRaises(ValueError):
            check_cards.published(kind, json.dumps(symlink), selector)

    def test_card_audit_compares_inventory_at_pin_without_inventing_a_website(self):
        body = self.tree(['data/records/cobalt.yaml']).encode()
        row = build_site_audit.build_entry(
            'CMMMech', check_cards.SOURCES['CMMMech'],
            {'sha': 'a' * 40, 'commit_date': '2026-10-08T00:00:00Z'},
            {'source_revision': 'a' * 40, 'repo': 'CMMMech', 'merged_prs': 2},
            1, 'Counted records.', lambda _: body, lambda _: body)
        self.assertEqual(row['figure_at_pin'], 1)
        self.assertEqual(row['data_sha256'], row['data_sha256_at_pin'])
        self.assertIn('/tree/' + 'a' * 40 + '/data/records', row['site'])
        self.assertNotIn('site_html_sha256', row)
        self.assertNotIn('built in CI', row['notes'])

    def test_record_links_preserve_subdirectories_and_yaml_extension(self):
        with mock.patch.dict(build_subsets.MECHS, {'CMMMech': {'root': '/tmp/CMMMech'}}):
            self.assertEqual(build_subsets.slug_for('CMMMech', '/tmp/CMMMech/data/records/pilots/a.yml', 'cmmmech:a'),
                             'pilots/a.yml')
        self.assertEqual(roots.RECORD_GLOBS['CMMMech'], ['data/records/**/*.yaml', 'data/records/**/*.yml'])

    def test_an_addition_gets_its_own_growth_allowance_without_redating_older_mechs(self):
        sources = {m: ('html', m + '/', 'records') for m in ('AMech', 'BMech')}
        template = ''.join(f'<article data-mech="{m}"><div class="num"><b>100</b></div></article>' for m in sources)
        audit = {'pinned_at_utc': '2026-09-01T00:00:00Z', 'repositories': [
            {'repo': 'AMech', 'figure_at_pin': 100, 'pinned_at_utc': '2026-09-29T00:00:00Z'},
            {'repo': 'BMech', 'figure_at_pin': 100},
        ]}
        now = datetime.datetime(2026, 9, 30, tzinfo=datetime.timezone.utc)
        with mock.patch.dict(check_cards.SOURCES, sources, clear=True):
            rows = check_cards.check(template, lambda _: '<b>101</b><span>records</span>', audit, now)
            self.assertEqual({m: status for status, m, _ in rows}, {'AMech': 'grew', 'BMech': 'STALE'})
            audit['repositories'][0]['pinned_at_utc'] = '2026-10-02T00:00:00Z'
            rows = check_cards.check(template, lambda _: '<b>101</b><span>records</span>', audit, now)
            self.assertTrue(any(status == 'AUDIT' and m == 'AMech' for status, m, _ in rows))


if __name__ == '__main__':
    unittest.main()
