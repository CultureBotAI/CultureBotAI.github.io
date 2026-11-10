"""Preserve comparison and malformed-input semantics under exact public guards.

Inputs: site validators and fixtures. Outputs: integration fixes, 2026-11-10.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'scripts/fleet/assemble_page.py';s=p.read_text()
s=s.replace('if is_withheld(name) or is_withheld(mech.get("repository")):', 'if is_withheld(name):')
s=s.replace('if any(is_withheld(n) for n in (', 'if any(is_withheld(n) for n in (')
s=s.replace('+ list(data.get("heat", ())) + [k for k in census', '+ [k for k in data.get("heat", ()) if k != "kg-microbe"] + [k for k in census')
p.write_text(s)
p=root/'scripts/fleet/check_updates.py';s=p.read_text().replace('if is_withheld(mech) or (isinstance(entry, dict) and is_withheld(entry.get("repository"))):','if is_withheld(mech):')
s=s.replace('            repo = repository.removeprefix', '            if is_withheld(repository):\n                raise ValueError("withheld repository must not be queried")\n            repo = repository.removeprefix');p.write_text(s)
p=root/'tests/test_fleet_page.py';s=p.read_text().replace('{"repo": "T", "sha": "a" * 40}', '{"repo": "TraitMech", "sha": "a" * 40}');p.write_text(s)
p=root/'tests/test_suite_updates.py';s=p.read_text().replace("public = roots.public_names() | {'amech', 'bmech', 'cmech', 'dmech', 'emech'}", "public = roots.public_names() | {name for letter in 'abcde' for name in (letter + 'mech', 'culturebotai/' + letter + 'mech')}");p.write_text(s)
