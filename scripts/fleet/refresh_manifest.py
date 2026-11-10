"""Refresh the site's governance snapshot from committed CLAW sources."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import types

import yaml

from roots import contains_unlisted_mech, is_withheld

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "_fleet/data/manifest.json"
AUTHORITY = "CultureBotAI/culturebotai-claw"
MANIFEST_PATH = "src/kg_microbe_fleet/fleet.yaml"
ARTIFACT_PATH = "src/kg_microbe_governance/vendored_artifacts.json"
STATUSES = {"enabled", "disabled", "not_applicable"}


def public_artifacts(registry, manifest):
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


def validate(snapshot, *, known_public=None):
    """Fail closed when membership or capability declarations are incomplete."""
    source = snapshot["source"]
    revision = source["revision"]
    expected_url = f"https://github.com/{AUTHORITY}/blob/{revision}/{MANIFEST_PATH}"
    if (source["repository"] != AUTHORITY or not re.fullmatch(r"[0-9a-f]{40}", revision)
            or source["url"] != expected_url):
        raise ValueError("Invalid canonical manifest provenance")
    catalogue = snapshot["capability_catalogue"]
    if not catalogue:
        raise ValueError("Empty capability catalogue or fleet")
    keys = set()
    repositories = set()
    for name, mech in snapshot["mechs"].items():
        if ((known_public is not None and name not in known_public) or
                (known_public is None and any(is_withheld(value) for value in (name, mech.get("key"), mech.get("github"))))):
            raise ValueError(f"{name}: withheld Mech must not appear in public manifest snapshot")
        if not name or mech["key"] in keys or mech["github"] in repositories:
            raise ValueError("Duplicate or empty Mech identity")
        keys.add(mech["key"])
        repositories.add(mech["github"])
        if set(mech["capabilities"]) != set(catalogue):
            raise ValueError(f"{name}: incomplete capability declarations")
        for key, declaration in mech["capabilities"].items():
            status = declaration["status"]
            if status not in STATUSES:
                raise ValueError(f"{name}.{key}: unknown status {status}")
            if status != "enabled" and not declaration.get("reason", "").strip():
                raise ValueError(f"{name}.{key}: missing reason")
    if snapshot["artifact_count"] < 0:
        raise ValueError("Empty artifact registry")
    serialized = json.dumps(snapshot)
    if known_public is None and contains_unlisted_mech(serialized):
        raise ValueError("withheld Mech must not appear in public manifest snapshot")


def project(manifest, registry, revision):
    if registry["canonical_repository"] != AUTHORITY:
        raise ValueError("Unexpected governance authority")
    mechs = {}
    public = manifest.public()
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
    snapshot = {
        "version": 1,
        "source": {"repository": AUTHORITY, "revision": revision,
                   "url": f"https://github.com/{AUTHORITY}/blob/{revision}/{MANIFEST_PATH}"},
        "capability_catalogue": {name: {"settings": {key: {"type": setting.value_type, **({"required_when_enabled": True} if setting.required_when_enabled else {}), **({"minimum": setting.minimum} if setting.minimum is not None else {})} for key, setting in cap.settings.items()}} if cap.settings else {} for name, cap in manifest.capability_catalogue.items()},
        "mechs": mechs,
        "artifact_count": len(public_artifacts(registry, manifest)),
    }
    serialized = json.dumps(snapshot).lower()
    for key, mech in manifest.mechs.items():
        if key in public.mechs:
            continue
        for token in (key, mech.display_name, mech.github):
            if re.search(r"(?<![a-z0-9])" + re.escape(token.lower()) + r"(?![a-z0-9])", serialized):
                raise ValueError("Excluded member metadata in a public capability declaration")
    validate(snapshot, known_public=set(mechs))
    return json.loads(json.dumps(snapshot))


def read_canonical(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True)
    if Path(git("rev-parse", "--show-toplevel").strip()).resolve() != Path(root).resolve():
        raise ValueError("CLAW source must be its exact Git worktree root")
    allowed = {f"https://github.com/{AUTHORITY}.git", f"https://github.com/{AUTHORITY}",
               f"git@github.com:{AUTHORITY}.git"}
    for direction in ((), ("--push",)):
        urls = git("remote", "get-url", *direction, "--all", "origin").splitlines()
        if not urls or any(url not in allowed for url in urls):
            raise ValueError("CLAW origin must match the canonical authority")
    revision = git("rev-parse", "HEAD").strip()
    # Read the same immutable commit for both inputs, never dirty checkout files.
    manifest = yaml.safe_load(git("show", f"{revision}:{MANIFEST_PATH}"))
    registry = json.loads(git("show", f"{revision}:{ARTIFACT_PATH}"))
    # Execute only the verified canonical package's committed loader, not its
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
        del sys.modules[name]


def semantic(snapshot):
    # Unrelated CLAW commits do not change the site's governance claims.
    return {key: value for key, value in snapshot.items() if key != "source"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    snapshot = read_canonical(args.claw_root)
    if args.check:
        current = json.loads(SNAPSHOT.read_text())
        validate(current)
        if semantic(current) != semantic(snapshot):
            raise SystemExit("Fleet snapshot is stale; refresh_manifest.py --claw-root PATH, then assemble_page.py")
        print(f"Fleet snapshot matches CLAW: {len(snapshot['mechs'])} members")
    else:
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {SNAPSHOT.relative_to(REPO)} from {snapshot['source']['revision']}")


if __name__ == "__main__":
    main()
