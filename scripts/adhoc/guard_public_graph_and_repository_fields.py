"""Validate graph endpoint and feature repository identities before render.

Inputs: assembly source/fixtures; outputs: public-output guards, 2026-11-10.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'scripts/fleet/assemble_page.py';s=p.read_text()
s=s.replace('            raise ValueError(f"{name}: repository must be a GitHub repository URL")', '            raise ValueError(f"{name}: repository must be a GitHub repository URL")\n        if is_withheld(mech["repository"]):\n            raise ValueError(f"{name}: repository must be in canonical public membership")')
s=s.replace('    measured = set(data["order"])', '''    # Hand-maintained graph relations also have structured member identities.
    for variable, fields in (("XREFS", ("from", "to")), ("HUB", ("mech",))):
        block = fragment.split("var " + variable + " = [", 1)[1].split("\\n  ];", 1)[0]
        for field in fields:
            identities = re.findall(r"\\b" + field + r':\\s*"([^"\\n]+)"', block)
            if any(identity not in names for identity in identities):
                raise ValueError("Graph references must use public corpus members")
    measured = set(data["order"])''')
p.write_text(s)
p=root/'tests/test_fleet_page.py';s=p.read_text().replace("{'newmech', 'ghostmech'}", "{'newmech', 'ghostmech', 'culturebotai/newmech'}");p.write_text(s)
p=root/'tests/test_public_projection.py';s=p.read_text().replace('import roots\n', 'import roots\nfrom assemble_page import assemble\n')
a=s.index("\n\nif __name__")
s=s[:a]+'''
    def test_arbitrary_private_graph_endpoint_is_refused(self):
        inputs = [json.loads((ROOT / '_fleet/data' / name).read_text()) for name in
                  ('fleet_data.json', 'manifest.json', 'mech_stats.json', 'prefix_census.json', 'site_features.json', 'recent_terms.json')]
        fragment = (ROOT / '_fleet/fleet_fragment.html').read_text().replace('from: "TaxonMech"', 'from: "private_lab"', 1)
        with self.assertRaisesRegex(ValueError, 'Graph references'):
            assemble((ROOT / '_fleet/mechs_template.md').read_text(), fragment, *inputs)
''' + s[a:];p.write_text(s)
