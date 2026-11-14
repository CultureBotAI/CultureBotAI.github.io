"""Inspect source pins, schemas and licenses for the gap-browser implementation.

Date: 2026-11-14. Inputs: prior public survey, current GitHub main, local Git
objects. Outputs: per-source metadata under .temp/knowledge-gaps-20261114.
Serves the knowledge-gaps implementation PR; never extracts a whole corpus.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "_fleet/reviews/gap-browser-20261113/evidence"
OUT = ROOT / ".temp/knowledge-gaps-20261114/source-inspection"
LOCAL = Path("/Users/marcin/Documents/VIMSS/ontology/Mechs")


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE)


def api(path):
    return json.loads(run("gh", "api", path))


def inspect(name):
    old = json.loads((EVIDENCE / (name + ".json")).read_text())
    repo = old["repository"]
    meta = api("repos/" + repo)
    if meta["private"] or meta["full_name"].lower() != repo.lower():
        raise ValueError("Unexpected repository identity")
    sha = api(f"repos/{repo}/commits/{meta['default_branch']}")["sha"]
    local = LOCAL / name
    has_local = False
    if local.is_dir():
        origin = run("git", "-C", str(local), "remote", "get-url", "origin").strip()
        if origin.removesuffix(".git").lower() != ("https://github.com/" + repo).lower():
            raise ValueError("Unexpected local identity")
        has_local = subprocess.run(["git", "-C", str(local), "cat-file", "-e", sha],
                                   capture_output=True).returncode == 0
    def read(path):
        if has_local:
            return run("git", "-C", str(local), "show", f"{sha}:{path}")
        item = api(f"repos/{repo}/contents/{path}?ref={sha}")
        return base64.b64decode(item["content"]).decode()
    root = api(f"repos/{repo}/git/trees/{sha}")
    licenses = {p["path"]: read(p["path"]) for p in root["tree"]
                if p["type"] == "blob" and p["path"].lower().startswith(("license", "licence", "copying", "notice"))}
    if has_local:
        paths = run("git", "-C", str(local), "ls-tree", "-r", "--name-only", sha, "src").splitlines()
    else:
        src = next(p for p in root["tree"] if p["path"] == "src")
        tree = api(f"repos/{repo}/git/trees/{src['sha']}?recursive=1")
        if tree.get("truncated"):
            raise ValueError("Truncated src tree")
        paths = ["src/" + p["path"] for p in tree["tree"] if p["type"] == "blob"]
    schemas = {p: read(p) for p in paths if "/schema/" in p and p.endswith(".yaml")
               and not p.endswith(("mech_shared.yaml", "history.yaml"))}
    result = {"name": name, "repository": repo, "default_branch": meta["default_branch"],
              "revision": sha, "acquired_at": datetime.now(timezone.utc).isoformat(),
              "local_git_object_available": has_local, "licenses": licenses,
              "schemas": schemas, "root_paths": [p["path"] for p in root["tree"]]}
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (name + ".json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    check = json.loads(target.read_text())
    if check["revision"] != sha or not check["schemas"]:
        raise ValueError("Persisted inspection failed")
    print(name, sha, "licenses", list(licenses), "schemas", list(schemas), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="+", choices=sorted(p.stem for p in EVIDENCE.glob("*.json")))
    args = parser.parse_args()
    for name in args.names:
        inspect(name)
