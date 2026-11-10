"""Give synthetic site tests explicit public memberships, 2026-11-10.

Inputs: existing tests. Outputs: fixtures for canonical-public-membership PR.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'tests/test_fleet_page.py';s=p.read_text()
s=s.replace('import unittest\n','import unittest\nfrom unittest import mock\n')
s=s.replace('class FleetPageTests(unittest.TestCase):\n    def setUp(self):','''class FleetPageTests(unittest.TestCase):
    def setUp(self):
        public = roots.public_names() | {'newmech', 'ghostmech'}
        patcher = mock.patch.object(roots, 'public_names', return_value=public)
        patcher.start()
        self.addCleanup(patcher.stop)''')
s=s.replace('        self.check_cards = check_cards','''        public = roots.public_names() | {m.lower() for m in self.NAMES}
        patcher = mock.patch.object(roots, 'public_names', return_value=public)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.check_cards = check_cards''')
s=s.replace('        data.mkdir(parents=True)\n', '''        data.mkdir(parents=True)
        shutil.copyfile(ROOT / '_fleet/data/manifest.json', data / 'manifest.json')
''')
s=s.replace("'artifacts': [{}] * self.snapshot['artifact_count']", "'artifacts': [{'consumers': 'all'}] * self.snapshot['artifact_count']")
s=s.replace("            git('add', '.')", "            shutil.copyfile(ROOT / 'tests/fixtures/pinned_fleet_api.py', root / 'src/kg_microbe_fleet/__init__.py')\n            git('add', '.')",1)
p.write_text(s)
p=root/'tests/test_suite_updates.py';s=p.read_text().replace('    def setUp(self):','''    def setUp(self):
        public = roots.public_names() | {'amech', 'bmech'}
        patcher = mock.patch.object(roots, 'public_names', return_value=public)
        patcher.start()
        self.addCleanup(patcher.stop)''',1);p.write_text(s)
p=root/'tests/test_kg_microbe.py';s=p.read_text().replace("        with mock.patch.dict(check_cards.SOURCES, sources, clear=True):", "        with mock.patch.dict(check_cards.SOURCES, sources, clear=True), mock.patch.object(roots, 'public_names', return_value=frozenset({'amech', 'bmech'})):");p.write_text(s)
p=root/'tests/test_site_features.py';s=p.read_text().replace('"repository"', '"repository|withheld"') if False else p.read_text();p.write_text(s)
