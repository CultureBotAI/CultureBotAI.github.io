"""Regression coverage for fleet admission, capability drift and generated output."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import assemble, capability_rows, script_json
from refresh_manifest import ARTIFACT_PATH, MANIFEST_PATH, read_canonical, semantic, validate


class FleetPageTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.data = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())

    def render(self):
        return assemble(self.template, self.fragment, self.data, self.snapshot)

    def test_published_page_contains_both_new_members_with_distinct_capabilities(self):
        page = self.render()
        self.assertEqual(page, (ROOT / "mechs.md").read_text())
        self.assertEqual(page.count('<span class="badge">in fleet manifest</span>'), 10)
        self.assertIn('Relationship graph of the 10 Mech knowledge bases', page)
        self.assertNotIn('not yet in fleet manifest', page)
        self.assertNotIn('one revision behind', page)
        caps = self.snapshot['mechs']
        self.assertEqual(caps['NaturalProductMech']['capabilities']['source_queue']['status'], 'enabled')
        self.assertEqual(caps['NaturalProductMech']['capabilities']['curation_history']['status'], 'disabled')
        self.assertEqual(caps['TaxonMech']['capabilities']['source_queue']['status'], 'disabled')
        self.assertEqual(caps['TaxonMech']['capabilities']['curation_history']['status'], 'enabled')
        self.assertIn('<tr><td>NaturalProductMech</td>', capability_rows(self.snapshot))
        self.assertIn('<tr><td>TaxonMech</td>', capability_rows(self.snapshot))

    def test_new_admission_cannot_silently_omit_card_or_graph_node(self):
        self.snapshot['mechs']['NewMech'] = deepcopy(self.snapshot['mechs']['TaxonMech'])
        self.snapshot['mechs']['NewMech'].update(key='newmech', github='CultureBotAI/NewMech')
        with self.assertRaisesRegex(ValueError, 'cards'):
            self.render()
        self.template += '\n<!--FLEET_BADGE:NewMech-->'
        self.template += '\n<article class="mech-card" data-mech="NewMech"></article>'
        with self.assertRaisesRegex(ValueError, 'Graph metadata'):
            self.render()

    def test_duplicate_actual_card_cannot_hide_behind_valid_badges(self):
        self.template = self.template.replace('data-mech="TaxonMech"', 'data-mech="TraitMech"')
        with self.assertRaisesRegex(ValueError, 'Actual Mech cards'):
            self.render()

    def test_census_cannot_reference_unknown_or_unmeasured_members(self):
        self.data['order'].append('GhostMech')
        with self.assertRaisesRegex(ValueError, 'Census order'):
            self.render()
        self.data['order'].pop()
        self.data['vocab_edges'][0]['a'] = 'TaxonMech'
        with self.assertRaisesRegex(ValueError, 'Census edges'):
            self.render()

    def test_missing_heat_row_cannot_publish_as_zero(self):
        self.data['heat'].pop('NaturalProductMech')
        with self.assertRaisesRegex(ValueError, 'Census heat rows'):
            self.render()

    def test_invalid_provenance_is_rejected(self):
        self.snapshot['source']['url'] = 'https://example.org/wrong'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.render()

    def test_incomplete_or_unknown_capability_fails_closed(self):
        caps = self.snapshot['mechs']['NaturalProductMech']['capabilities']
        original = caps.pop('curation_history')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.snapshot)
        caps['curation_history'] = {'status': 'unknown'}
        with self.assertRaisesRegex(ValueError, 'unknown status'):
            validate(self.snapshot)
        caps['curation_history'] = {'status': 'disabled'}
        with self.assertRaisesRegex(ValueError, 'missing reason'):
            validate(self.snapshot)
        caps['curation_history'] = original
        validate(self.snapshot)

    def test_semantic_drift_includes_capability_reason_and_membership(self):
        original = semantic(self.snapshot)
        self.snapshot['source']['revision'] = 'unrelated-commit'
        self.assertEqual(original, semantic(self.snapshot))
        changed = deepcopy(self.snapshot)
        changed['mechs']['NaturalProductMech']['capabilities']['source_queue']['status'] = 'disabled'
        self.assertNotEqual(original, semantic(changed))
        changed = deepcopy(self.snapshot)
        changed['mechs'].pop('NaturalProductMech')
        self.assertNotEqual(original, semantic(changed))
        changed = deepcopy(self.snapshot)
        changed['mechs']['NaturalProductMech']['capabilities']['curation_history']['reason'] = 'Changed evidence'
        self.assertNotEqual(original, semantic(changed))

    def test_script_data_and_tooltips_escape_markup(self):
        reason = '</script><script>alert("x")</script> & evidence'
        self.snapshot['mechs']['NaturalProductMech']['capabilities']['curation_history']['reason'] = reason
        self.assertNotIn('</script>', script_json(self.snapshot))
        self.assertIn('&lt;/script&gt;', capability_rows(self.snapshot))
        self.assertEqual(json.loads(script_json(self.snapshot)), self.snapshot)

    def test_unresolved_template_token_fails(self):
        self.template += '\n<!--FLEET_UNKNOWN-->'
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            self.render()

    def test_snapshot_reads_committed_sources_despite_dirty_checkout(self):
        # Model a CLAW checkout with a valid committed fleet and a dirty removal.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL)
            git('init', '-q')
            manifest = {'capability_catalogue': self.snapshot['capability_catalogue'], 'mechs': {}}
            for name, entry in self.snapshot['mechs'].items():
                manifest['mechs'][entry['key']] = dict(entry, display_name=name)
            registry = {'canonical_repository': 'CultureBotAI/culturebotai-claw',
                        'artifacts': [{}] * self.snapshot['artifact_count']}
            for path, data in [(MANIFEST_PATH, manifest), (ARTIFACT_PATH, registry)]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data))
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.org',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
            (root / MANIFEST_PATH).write_text('mechs: {}')
            result = read_canonical(root)
            self.assertEqual(semantic(result), semantic(self.snapshot))
            self.assertEqual(result['source']['revision'], git('rev-parse', 'HEAD').strip())


if __name__ == '__main__':
    unittest.main()
