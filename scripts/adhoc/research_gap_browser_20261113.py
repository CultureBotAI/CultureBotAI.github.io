"""Research gap-browser adoption; 2026-11-13, development-plan PR.

Inputs: pinned CLAW manifest, public site corpus allowlist, GitHub read APIs,
and optional local Git objects. Outputs: public per-repository evidence JSON.
Reads committed files only; never executes Mech code or runs literature scans.
"""
import argparse
import base64
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from roots import ORDER, is_withheld


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE)


def api(endpoint):
    return json.loads(run("gh", "api", endpoint))


def collect(name, mech, local_root):
    repo = mech["github"]
    metadata = api(f"repos/{repo}")
    assert metadata["full_name"].lower() == repo.lower()
    assert not metadata["private"], "Only public repositories may enter this report"
    branch = metadata["default_branch"]
    sha = api(f"repos/{repo}/commits/{branch}")["sha"]
    local = local_root / name
    has_local = False
    if local.exists():
        origin = run("git", "-C", str(local), "remote", "get-url", "origin")
        assert repo.lower() in origin.lower(), "Local identity mismatch"
        try:
            run("git", "-C", str(local), "cat-file", "-e", sha)
            has_local = True
        except subprocess.CalledProcessError:
            pass
    tree_complete = True
    if has_local:
        paths = run("git", "-C", str(local), "ls-tree", "-r", "--name-only", sha).splitlines()
    else:
        tree = api(f"repos/{repo}/git/trees/{sha}?recursive=1")
        tree_complete = not tree.get("truncated")
        if tree_complete:
            paths = [p["path"] for p in tree["tree"] if p["type"] == "blob"]
        else:
            # A large corpus can truncate GitHub's recursive response. Inspect
            # only the complete configuration/code/browser subtrees instead,
            # and explicitly leave corpus presence unknown.
            paths = []
            root_tree = api(f"repos/{repo}/git/trees/{sha}")
            for entry in root_tree["tree"]:
                if entry["type"] == "tree" and entry["path"] in {"src", "conf", "app"}:
                    subtree = api(f"repos/{repo}/git/trees/{entry['sha']}?recursive=1")
                    assert not subtree.get("truncated"), "Incomplete source subtree"
                    paths.extend(entry["path"] + "/" + p["path"]
                                 for p in subtree["tree"] if p["type"] == "blob")

    def read(path):
        if has_local:
            return run("git", "-C", str(local), "show", f"{sha}:{path}")
        content = api(f"repos/{repo}/contents/{path}?ref={sha}")
        return base64.b64decode(content["content"]).decode()

    configs = {}
    for path in ("conf/discussions_config.yaml", "conf/kgscan_config.yaml"):
        if path in paths:
            configs[path] = yaml.safe_load(read(path))
    schema_paths = [p for p in paths if "/schema/" in p and p.endswith(".yaml")]
    schemas = {}
    for path in schema_paths:
        if path.endswith("mech_shared.yaml") or path in mech.get("schema_paths", []):
            body = read(path)
            schemas[path] = {"discussion_type": "  Discussion:" in body,
                             "discussion_slot": "discussions:" in body,
                             "sha256": hashlib.sha256(body.encode()).hexdigest()}
    samples = []
    # A bounded presence probe, not a census. Git grep includes every tracked
    # file at the pin regardless of ignore settings; record scope comes from CLAW.
    if has_local:
        probe = subprocess.run(["git", "-C", str(local), "grep", "-l", "-E",
                                "^[[:space:]]*discussions:", sha, "--", "*.yaml"],
                               capture_output=True, text=True)
        assert probe.returncode in (0, 1), probe.stderr
        for line in probe.stdout.splitlines():
            path = line.split(":", 1)[1]
            if not any(fnmatch.fnmatch(path, g) for g in mech.get("record_globs", [])):
                continue
            doc = yaml.safe_load(read(path))
            discussions = doc.get("discussions") if isinstance(doc, dict) else None
            if discussions:
                samples.append({"path": path, "discussions": discussions[:1]})
                if len(samples) == 3:
                    break
    return {"name": name, "repository": repo, "default_branch": branch,
            "revision": sha, "acquired_at": datetime.now(timezone.utc).isoformat(),
            "knowledge_gap_scan": mech["capabilities"]["knowledge_gap_scan"],
            "record_globs": mech.get("record_globs", []), "configs": configs,
            "schema_evidence": schemas, "committed_tree_complete": tree_complete,
            "discussion_assets": [p for p in paths if p.startswith("app/discussions/")],
            "sample_probe": "pinned tracked YAML" if has_local else "not performed",
            "discussion_samples": samples}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--local-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", choices=ORDER)
    args = parser.parse_args()
    manifest = yaml.safe_load(args.manifest.read_text())
    by_name = {m["display_name"]: m for m in manifest["mechs"].values()}
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ([args.repo] if args.repo else ORDER):
        assert not is_withheld(name)
        result = collect(name, by_name[name], args.local_root)
        # Keep evidence excerpts as public committed data only; no raw manifest.
        target = args.output / f"{name}.json"
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        assert target.stat().st_size > 0
        print(f"{name}: {result['revision'][:12]}, {len(result['discussion_samples'])} sample records", flush=True)


if __name__ == "__main__":
    main()
