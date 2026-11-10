"""Enforce exact public identities independently of Mech suffixes, 2026-11-10.

Inputs: public guards. Outputs: exact producer checks for fleet integration PR.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'scripts/fleet/roots.py';s=p.read_text();a=s.index('def is_withheld(');b=s.index('\n\nif any(is_withheld',a)
s=s[:a]+'''def contains_unlisted_mech(value: str) -> bool:
    """Additional prose check; structured identities use the exact guard below."""
    candidates = re.findall(r"(?<![a-z0-9])[a-z][a-z0-9]*mech(?![a-z0-9])", value.lower())
    return bool(set(candidates) - public_names())


def is_withheld(value: str | None) -> bool:
    """Refuse any identity or repository locator outside public membership.

    Arbitrary keys and display names are supported; a Mech suffix is not the
    authority. The two support repositories do not contribute scientific data.
    """
    if value is None or value == "":
        return False
    if not isinstance(value, str):
        return True
    allowed = public_names() | {"culturebotai-claw", "culturebotai.github.io"}
    lowered = value.strip().lower()
    if lowered in allowed:
        return False
    # URLs and owner/repository locators have a repository path component.
    from urllib.parse import urlsplit
    parts = urlsplit(lowered).path.strip("/").split("/") if "://" in lowered else lowered.split("/")
    if "culturebotai" in parts:
        index = parts.index("culturebotai") + 1
        return index >= len(parts) or parts[index].removesuffix(".git") not in allowed
    if len(parts) > 1:
        return parts[0] not in allowed
    # Composite asset keys use public display names followed by a delimiter.
    return not any(lowered.startswith(name + sep) for name in allowed for sep in ("--", "|", "_"))
''' + s[b:];p.write_text(s)
for name, var in [('scripts/fleet/assemble_page.py','page'),('scripts/fleet/build_site_audit.py','serialized'),('scripts/fleet/refresh_manifest.py','serialized')]:
    p=root/name;s=p.read_text().replace('from roots import ', 'from roots import contains_unlisted_mech, ',1)
    s=s.replace(f'is_withheld({var})',f'contains_unlisted_mech({var})')
    if 'refresh_manifest' in name:
        s=s.replace('if known_public is not None and name not in known_public:', 'if ((known_public is not None and name not in known_public) or\n                (known_public is None and any(is_withheld(value) for value in (name, mech.get("key"), mech.get("github"))))):')
    p.write_text(s)
p=root/'scripts/fleet/build_data.py';s=p.read_text().replace('from roots import CITATION, ORDER, is_withheld','from roots import CITATION, ORDER, contains_unlisted_mech')
s=s.replace('is_withheld(json.dumps(value))','contains_unlisted_mech(json.dumps(value))')
s=s.replace('    pins=cen.get("_revisions", {})','''    if any(not name.startswith("_") and name not in ORDER for name in cen):
        raise ValueError("withheld member must not contribute to public aggregates")
    if any(any(name not in ORDER for name in key.split("|")) for key in sub.get("edges", {})):
        raise ValueError("Edge endpoints must belong to public corpus membership")
    pins=cen.get("_revisions", {})''');p.write_text(s)
p=root/'tests/test_public_projection.py';s=p.read_text().replace("self.assertTrue(roots.is_withheld('UnexpectedMech--CHEBI'))", "self.assertTrue(roots.is_withheld('UnexpectedMech--CHEBI'))\n            self.assertTrue(roots.is_withheld('private_lab'))\n            self.assertTrue(roots.is_withheld('CultureBotAI/private_lab'))")
s=s.replace("'SecretMech': {'files': 11", "'private_lab': {'files': 11");p.write_text(s)
p=root/'scripts/adhoc/refresh_public_fleet_artifacts.py';s=p.read_text().replace("'_fleet/data/site_audit.json': encoded(audit)", "'_fleet/data/site_audit.json': json.dumps(audit, indent=1, ensure_ascii=False) + '\\n'");p.write_text(s)
