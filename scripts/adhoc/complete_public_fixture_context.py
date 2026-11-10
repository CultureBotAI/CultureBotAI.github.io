"""Complete synthetic public allowlists and preserve import side-effect check.

Inputs: regression fixtures; outputs: corrected tests; fleet PR, 2026-11-10.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'tests/test_fleet_page.py';s=p.read_text().replace("public = roots.public_names() | {m.lower() for m in self.NAMES}", "public = roots.public_names() | {m.lower() for m in self.NAMES} | {'dmech'} | {f'm{i}mech' for i in range(20)}")
s=s.replace('            done = subprocess.run([sys.executable, "-c", "import prefix_census"],','            membership_before = (data / "manifest.json").read_bytes()\n            done = subprocess.run([sys.executable, "-c", "import prefix_census"],')
s=s.replace('written = sorted(path.name for path in data.iterdir())', 'written = sorted(path.name for path in data.iterdir() if path.name != "manifest.json")\n            self.assertEqual((data / "manifest.json").read_bytes(), membership_before)')
p.write_text(s)
p=root/'tests/test_suite_updates.py';s=p.read_text().replace("{'amech', 'bmech'}", "{'amech', 'bmech', 'cmech'}");p.write_text(s)
