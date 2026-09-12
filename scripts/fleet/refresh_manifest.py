"""Refresh the site's governance snapshot from committed CLAW sources."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import yaml

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "_fleet/data/manifest.json"
AUTHORITY = "CultureBotAI/culturebotai-claw"
MANIFEST_PATH = "src/kg_microbe_fleet/fleet.yaml"
ARTIFACT_PATH = "src/kg_microbe_governance/vendored_artifacts.json"
STATUSES = {"enabled", "disabled", "not_applicable"}


def validate(snapshot):
    """Fail closed when membership or capability declarations are incomplete."""
    source = snapshot["source"]
    revision = source["revision"]
    expected_url = f"https://github.com/{AUTHORITY}/blob/{revision}/{MANIFEST_PATH}"
    if (source["repository"] != AUTHORITY or not re.fullmatch(r"[0-9a-f]{40}", revision)
            or source["url"] != expected_url):
        raise ValueError("Invalid canonical manifest provenance")
    catalogue = snapshot["capability_catalogue"]
    if not catalogue or not snapshot["mechs"]:
        raise ValueError("Empty capability catalogue or fleet")
    keys = set()
    repositories = set()
    for name, mech in snapshot["mechs"].items():
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
    if snapshot["artifact_count"] < 1:
        raise ValueError("Empty artifact registry")


def project(manifest, registry, revision):
    if registry["canonical_repository"] != AUTHORITY:
        raise ValueError("Unexpected governance authority")
    mechs = {}
    for key, mech in manifest["mechs"].items():
        name = mech["display_name"]
        if name in mechs:
            raise ValueError(f"Duplicate display name: {name}")
        mechs[name] = {"key": key, "github": mech["github"],
                       "capabilities": mech["capabilities"]}
    snapshot = {
        "version": 1,
        "source": {"repository": AUTHORITY, "revision": revision,
                   "url": f"https://github.com/{AUTHORITY}/blob/{revision}/{MANIFEST_PATH}"},
        "capability_catalogue": manifest["capability_catalogue"],
        "mechs": mechs,
        "artifact_count": len(registry["artifacts"]),
    }
    validate(snapshot)
    return snapshot


def read_canonical(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True)
    revision = git("rev-parse", "HEAD").strip()
    # Read the same immutable commit for both inputs, never dirty checkout files.
    manifest = yaml.safe_load(git("show", f"{revision}:{MANIFEST_PATH}"))
    registry = json.loads(git("show", f"{revision}:{ARTIFACT_PATH}"))
    return project(manifest, registry, revision)


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
