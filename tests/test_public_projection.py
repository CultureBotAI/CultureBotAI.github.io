"""Canonical public projection must precede serialization and aggregation."""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import roots
from assemble_page import assemble
import build_data
from refresh_manifest import project


class Projection:
    """Protocol fixture: the canonical API owns how public members are selected."""
    def __init__(self, public=False):
        cap = SimpleNamespace(status='enabled', reason=None, settings={}, reason_claims=None)
        self.mechs = {
            'publicmech': SimpleNamespace(display_name='PublicMech', github='Owner/PublicMech', capabilities={'test': cap}),
        }
        if not public:
            self.mechs['secretmech'] = SimpleNamespace(display_name='SecretMech', github='Owner/SecretMech', capabilities={'test': cap})
        self.capability_catalogue = {'test': SimpleNamespace(settings={})}
    @property
    def keys(self):
        return tuple(self.mechs)
    def public(self):
        return Projection(public=True)
    def with_capability(self, name):
        return self.keys


class PublicProjectionTests(unittest.TestCase):
    def test_shared_projection_removes_identity_and_distinct_artifact_contributions(self):
        manifest = Projection()
        registry = {
            'canonical_repository': 'CultureBotAI/culturebotai-claw',
            'artifacts': [
                {'consumers': 'all'},
                {'consumers': ['publicmech']},
                {'consumers': ['secretmech']},
                {'consumers': ['secretmech']},
                {'consumers': ['secretmech']},
            ],
        }
        result = project(manifest, registry, 'a' * 40)
        self.assertEqual(result['artifact_count'], 2)
        self.assertEqual(set(result['mechs']), {'PublicMech'})
        self.assertNotIn('secret', json.dumps(result).lower())
        self.assertEqual(len(manifest.keys), 2)
        self.assertEqual(len(registry['artifacts']), 5)

    def test_guard_uses_public_allowlist_instead_of_a_named_private_repository(self):
        with patch.object(roots, 'public_names', return_value=frozenset({'openmech', 'owner/openmech'})):
            self.assertFalse(roots.is_withheld('Owner/OpenMech'))
            self.assertTrue(roots.is_withheld('Owner/UnexpectedMech'))
            self.assertTrue(roots.is_withheld('UnexpectedMech--CHEBI'))
            self.assertTrue(roots.is_withheld('private_lab'))
            self.assertTrue(roots.is_withheld('OpenMech_secret'))
            self.assertTrue(roots.is_withheld('DifferentOwner/OpenMech'))
            self.assertTrue(roots.is_withheld('https://github.com/DifferentOwner/OpenMech'))
            self.assertTrue(roots.is_withheld('CultureBotAI/private_lab'))

    def test_unprojected_nonzero_census_is_refused_before_aggregation(self):
        # Distinct nonzero contributions: an accidental inclusion changes both
        # vocabulary membership and totals. Refusal precedes all other parsing.
        census = {'CultureMech': {'files': 2, 'prefixes': {'CHEBI': 3}},
                  'private_lab': {'files': 11, 'prefixes': {'PRIVATE': 29}}}
        with self.assertRaisesRegex(ValueError, 'public aggregates'):
            build_data.build({}, census, {})

    def test_arbitrary_private_graph_endpoint_is_refused(self):
        inputs = [json.loads((ROOT / '_fleet/data' / name).read_text()) for name in
                  ('fleet_data.json', 'manifest.json', 'mech_stats.json', 'prefix_census.json', 'site_features.json', 'recent_terms.json')]
        fragment = (ROOT / '_fleet/fleet_fragment.html').read_text().replace('from: "TaxonMech"', 'from: "private_lab"', 1)
        with self.assertRaisesRegex(ValueError, 'Graph references'):
            assemble((ROOT / '_fleet/mechs_template.md').read_text(), fragment, *inputs)


if __name__ == '__main__':
    unittest.main()

class SnapshotPinTests(unittest.TestCase):
    def test_pin_is_immutable_and_cannot_inject_workflow_output(self):
        from print_manifest_pin import pin
        self.assertEqual(pin({'source': {'repository': 'CultureBotAI/culturebotai-claw', 'revision': 'a' * 40}}), 'a' * 40)
        for revision in ('main', 'a' * 40 + '\nother=value', None):
            with self.assertRaises(ValueError):
                pin({'source': {'repository': 'CultureBotAI/culturebotai-claw', 'revision': revision}})
