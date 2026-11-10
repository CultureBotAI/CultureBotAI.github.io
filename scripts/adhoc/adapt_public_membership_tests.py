"""Adapt site regression fixtures to public projection API, 2026-11-10.

Input: existing tests. Output: retained mixed-membership fixture tests for PR.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'tests/test_infrastructure_membership.py'
s=p.read_text().replace('"CultureMech", "CofactorMech", "AssayMech", "EdgeMech", None, ""','"CultureMech", "EdgeMech", None, ""')
a=s.index('    def test_manifest_projection_strips_scaleupmech');b=s.index('    def test_manifest_validation_rejects_withheld_mech',a)
s=s[:a]+s[b:]
s=s.replace('"Withheld Mech ScaleupMech"','"withheld Mech"')
p.write_text(s)
p=root/'scripts/fleet/build_data.py'
s=p.read_text().replace('from roots import CITATION, ORDER', 'from roots import CITATION, ORDER, is_withheld')
s=s.replace('    pins=cen.get("_revisions", {})', '''    # Refuse unprojected or stale inputs before any vocabulary, edge, count or
    # downloadable cell metadata is aggregated or serialized.
    if any(is_withheld(json.dumps(value)) for value in (sub, cen, cell_summary)):
        raise ValueError("withheld Mech must not contribute to public aggregates")
    pins=cen.get("_revisions", {})''')
p.write_text(s)
p=root/'.claude/skills/update-xmech-page/SKILL.md';s=p.read_text();a=s.index('- **Withheld Mechs');b=s.index('- **The three numbers',a)
s=s[:a]+'''- **Public membership.** CLAW's reserved `exclude-from-public` fleet tag is
  enforced by its shared `FleetManifest.public()` projection when refreshing
  the snapshot. Only that public allowlist is retained here; no excluded-name
  registry or metadata is emitted. Every producer refuses unlisted Mech inputs
  before statistics or serialization. A stale corpus scope requires a reviewed
  refresh, not a fallback to the full fleet.
''' + s[b:];p.write_text(s)
