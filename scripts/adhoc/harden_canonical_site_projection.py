"""Harden canonical loader identity and cross-reference exclusion, 2026-11-10.

Inputs: site projection source/tests. Outputs: guarded PR sources.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'scripts/fleet/refresh_manifest.py';s=p.read_text()
s=s.replace('    validate(snapshot, known_public=set(mechs))', '''    serialized = json.dumps(snapshot).lower()
    for key, mech in manifest.mechs.items():
        if key in public.mechs:
            continue
        for token in (key, mech.display_name, mech.github):
            if re.search(r"(?<![a-z0-9])" + re.escape(token.lower()) + r"(?![a-z0-9])", serialized):
                raise ValueError("Excluded member metadata in a public capability declaration")
    validate(snapshot, known_public=set(mechs))''')
s=s.replace('    revision = git("rev-parse", "HEAD").strip()', '''    if Path(git("rev-parse", "--show-toplevel").strip()).resolve() != Path(root).resolve():
        raise ValueError("CLAW source must be its exact Git worktree root")
    allowed = {f"https://github.com/{AUTHORITY}.git", f"https://github.com/{AUTHORITY}",
               f"git@github.com:{AUTHORITY}.git"}
    for direction in ((), ("--push",)):
        urls = git("remote", "get-url", *direction, "--all", "origin").splitlines()
        if not urls or any(url not in allowed for url in urls):
            raise ValueError("CLAW origin must match the canonical authority")
    revision = git("rev-parse", "HEAD").strip()''')
p.write_text(s)
p=root/'tests/test_fleet_page.py';s=p.read_text().replace("            git('init', '-q')\n            manifest", "            git('init', '-q')\n            git('remote', 'add', 'origin', 'https://github.com/CultureBotAI/culturebotai-claw.git')\n            manifest");p.write_text(s)
p=root/'scripts/fleet/assemble_page.py';s=p.read_text().replace('withheld Mech must not appear in site features', 'withheld Mech repository must not appear in site features');p.write_text(s)
