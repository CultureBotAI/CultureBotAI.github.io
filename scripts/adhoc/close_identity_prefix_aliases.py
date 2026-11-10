"""Close identity-prefix and owner aliases in public guards, 2026-11-10.

Inputs: public roots guard/tests; outputs: exact membership boundary for PR.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'scripts/fleet/roots.py';s=p.read_text();a=s.index('    # URLs and owner/repository');b=s.index('\n\nif any(is_withheld',a)
s=s[:a]+'''    from urllib.parse import urlsplit
    if "://" in lowered:
        url = urlsplit(lowered)
        parts = url.path.strip("/").split("/")
        if url.hostname in {"github.com", "raw.githubusercontent.com"}:
            return "/".join(parts[:2]) not in allowed
        if url.hostname == "api.github.com" and parts[:1] == ["repos"]:
            return "/".join(parts[1:3]) not in allowed
        if url.hostname == "culturebotai.github.io":
            return parts[0] not in allowed
        return True
    parts = lowered.split("/")
    if len(parts) > 1:
        # Source paths are rooted at the exact public display name; repository
        # locators additionally require their exact owner/repository identity.
        return parts[0] not in allowed and "/".join(parts[:2]) not in allowed
    return True
''' + s[b:];p.write_text(s)
p=root/'tests/test_public_projection.py';s=p.read_text().replace("self.assertTrue(roots.is_withheld('private_lab'))", "self.assertTrue(roots.is_withheld('private_lab'))\n            self.assertTrue(roots.is_withheld('OpenMech_secret'))\n            self.assertTrue(roots.is_withheld('DifferentOwner/OpenMech'))\n            self.assertTrue(roots.is_withheld('https://github.com/DifferentOwner/OpenMech'))");p.write_text(s)
