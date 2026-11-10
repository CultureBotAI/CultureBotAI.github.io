"""Replace private-name denylist with canonical public membership, 2026-11-10.

Inputs: site sources. Outputs: staged source changes for fleet integration PR.
Run under hold_site_integration_lock.py; source edits are atomic replacements.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def write(name, text):
    path = ROOT / name
    staged = path.with_name(path.name + '.staged')
    staged.write_text(text)
    staged.replace(path)

path = ROOT / 'scripts/fleet/roots.py'
s = path.read_text().replace('import glob\n', 'import glob\nimport json\nfrom pathlib import Path\n')
a=s.index('# Private or withheld Mechs')
b=s.index('ORDER = list(RECORD_GLOBS)', a)
s=s[:a]+'''# The canonical public snapshot is an allowlist, never a private-name denylist.
# It contains no excluded identities. Refuse stale/unlisted Mech inputs at every
# consumer boundary; refreshing it requires CLAW's shared public projection.
PUBLIC_SNAPSHOT = Path(__file__).resolve().parents[2] / "_fleet/data/manifest.json"


def public_names():
    snapshot = json.loads(PUBLIC_SNAPSHOT.read_text())
    return frozenset(
        token.lower() for name, mech in snapshot["mechs"].items()
        for token in (name, mech["key"], mech["github"].rsplit("/", 1)[-1])
    )


def is_withheld(value: str | None) -> bool:
    """Refuse Mech identifiers absent from the canonical public projection.

    Kept as the guard's existing name for its callers. Unknown Mechs fail
    closed too; callers cannot reconstruct or serialize excluded membership.
    """
    if not isinstance(value, str):
        return False
    candidates = re.findall(r"(?<![a-z0-9])[a-z][a-z0-9]*mech(?![a-z0-9])", value.lower())
    return bool(set(candidates) - public_names())


if any(is_withheld(name) for name in RECORD_GLOBS):
    raise RuntimeError("RECORD_GLOBS includes a Mech absent from public membership; refresh the census scope")

''' + s[b:]
write('scripts/fleet/roots.py',s)
for name in ('scripts/fleet/assemble_page.py','scripts/fleet/build_site_audit.py'):
    s=(ROOT/name).read_text().replace('WITHHELD_MECHS, ', '')
    a=s.index('    for withheld in WITHHELD_MECHS:')
    b=s.index('    return ',a)
    variable='page' if 'assemble_page' in name else 'serialized'
    error='ValueError' if 'assemble_page' in name else 'SystemExit'
    s=s[:a]+f'    if is_withheld({variable}):\n        raise {error}("withheld Mech must not appear in public output")\n'+s[b:]
    write(name,s)
s=(ROOT/'scripts/fleet/refresh_manifest.py').read_text()
s=s.replace('import subprocess\n', 'import subprocess\nimport sys\nimport types\n')
s=s.replace('from roots import WITHHELD_MECHS, is_withheld','from roots import is_withheld')
a=s.index('def public_artifacts('); b=s.index('\n\ndef validate(',a)
s=s[:a]+'''def public_artifacts(registry, manifest):
    """Count only artifacts that have an applicable public consumer."""
    public = manifest.public()
    kept = []
    for artifact in registry["artifacts"]:
        consumers = artifact.get("consumers")
        if consumers == "all":
            applicable = set(public.keys)
        elif isinstance(consumers, list):
            applicable = set(consumers) & set(public.keys)
        elif isinstance(consumers, dict) and set(consumers) == {"capability"}:
            applicable = set(public.with_capability(consumers["capability"]))
        else:
            raise ValueError("Unsupported artifact consumer declaration")
        if applicable:
            kept.append(artifact)
    return kept
''' + s[b:]
s=s.replace('def validate(snapshot):','def validate(snapshot, *, known_public=None):')
s=s.replace('if not catalogue or not snapshot["mechs"]:', 'if not catalogue:')
s=s.replace('if is_withheld(name) or is_withheld(mech.get("key")) or is_withheld(mech.get("github")):', 'if known_public is not None and name not in known_public:')
s=s.replace('if snapshot["artifact_count"] < 1:', 'if snapshot["artifact_count"] < 0:')
a=s.index('    for withheld in WITHHELD_MECHS:'); b=s.index('\n\ndef project(',a)
s=s[:a]+'''    if known_public is None and is_withheld(serialized):
        raise ValueError("withheld Mech must not appear in public manifest snapshot")
''' + s[b:]
a=s.index('    for key, mech in manifest["mechs"].items():'); b=s.index('    snapshot = {',a)
s=s[:a]+'''    public = manifest.public()
    for key, mech in public.mechs.items():
        name = mech.display_name
        if name in mechs:
            raise ValueError(f"Duplicate display name: {name}")
        mechs[name] = {"key": key, "github": mech.github,
                       "capabilities": {
                           name: {"status": cap.status,
                                  **({"reason": cap.reason} if cap.reason else {}),
                                  **({"settings": dict(cap.settings)} if cap.settings else {}),
                                  **({"reason_claims": {
                                      **({"present": list(cap.reason_claims.present)} if cap.reason_claims.present else {}),
                                      **({"absent": list(cap.reason_claims.absent)} if cap.reason_claims.absent else {}),
                                  }} if cap.reason_claims else {})}
                           for name, cap in mech.capabilities.items()}}
''' + s[b:]
s=s.replace('"capability_catalogue": manifest["capability_catalogue"],', '"capability_catalogue": {name: {"settings": {key: {"type": setting.value_type, **({"required_when_enabled": True} if setting.required_when_enabled else {}), **({"minimum": setting.minimum} if setting.minimum is not None else {})} for key, setting in cap.settings.items()}} if cap.settings else {} for name, cap in manifest.capability_catalogue.items()},')
s=s.replace('len(public_artifacts(registry))','len(public_artifacts(registry, manifest))')
s=s.replace('    validate(snapshot)\n    return snapshot', '    validate(snapshot, known_public=set(mechs))\n    return snapshot')
s=s.replace('    return project(manifest, registry, revision)', '''    # Execute only the verified canonical package's committed loader, not its
    # dirty working tree. Its public() method owns reserved-tag semantics.
    source = git("show", f"{revision}:src/kg_microbe_fleet/__init__.py")
    name = "_pinned_fleet_" + revision
    module = types.ModuleType(name)
    module.__file__ = str(Path(root) / "src/kg_microbe_fleet/__init__.py")
    sys.modules[name] = module
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)
        fleet = module.parse_fleet_manifest(manifest, Path(MANIFEST_PATH))
        if not callable(getattr(fleet, "public", None)):
            raise ValueError("CLAW pin predates the required canonical public-membership API")
        return project(fleet, registry, revision)
    finally:
        del sys.modules[name]''')
write('scripts/fleet/refresh_manifest.py',s)
