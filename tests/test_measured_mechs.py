"""Record links for the two newly measured corpora follow their actual publishers."""
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/fleet'))
import build_subsets
import prefix_census


class MeasuredMechTests(unittest.TestCase):
    def test_pathway_links_use_published_identifier_slugs(self):
        with mock.patch.dict(build_subsets.MECHS, {'PathwayMech': {'root': '/example/PathwayMech'}}):
            slug = build_subsets.slug_for('PathwayMech', '/example/PathwayMech/data/pathways/human-title.yaml',
                                          'gomodel:YeastPathways/GLYCOLYSIS')
        self.assertEqual(slug, 'gomodel_YeastPathways_GLYCOLYSIS.html')
        self.assertEqual(build_subsets.SITE_BASE['PathwayMech'],
                         'https://culturebotai.github.io/PathwayMech/pages/records/')

    def test_duf_links_identify_the_family_in_its_native_browser(self):
        with mock.patch.dict(build_subsets.MECHS, {'DUFMech': {'root': '/example/DUFMech'}}):
            for identifier, expected in [('Pfam:PF04149', 'PF04149.html'), ('InterPro:IPR001234', None)]:
                self.assertEqual(build_subsets.slug_for('DUFMech', '/example/DUFMech/data/worklists/source.json',
                                                        identifier), expected)
        self.assertEqual(build_subsets.SITE_BASE['DUFMech'], 'https://culturebotai.github.io/DUFMech/families/')

    def test_new_provider_namespaces_and_description_aliases_are_counted(self):
        text = 'gomodel:YeastPathways_GLYCOLYSIS SGD:S000001635 WikiPathways:WP5587 Rfam:RF01764 pfam:PF04149 Interpro:IPR001234'
        self.assertEqual([prefix_census.norm.get(p, p) for p in prefix_census.rx.findall(text)],
                         ['gomodel', 'SGD', 'WikiPathways', 'Rfam', 'Pfam', 'InterPro'])


if __name__ == '__main__':
    unittest.main()
