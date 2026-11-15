"""Acquire immutable native gap records for website #577 (2026-11-14).

Inputs: reviewed public source config, verified Git repositories, CLAW exporter.
Output: validated public snapshot. Never writes to source Mechs or calls research
providers. All source records are parsed; unsupported roots remain explicit.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime
import fnmatch
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from roots import ORDER, contains_unlisted_mech, is_withheld


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def publication_allowed(source, root):
    """A root may narrow the reviewed source grant, never override a hold (#578)."""
    return (source.get("publication_allowed", False) is True
            and root.get("publication_allowed", True) is True)


def json_bytes(value):
    def default(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(type(obj).__name__)
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       default=default) + "\n").encode()


def write_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temp.write(data)
        temporary = Path(temp.name)
    temporary.replace(path)


def load_exporter(root):
    root = Path(root).resolve()
    origin = git(root, "remote", "get-url", "origin").decode().strip().removesuffix(".git")
    if origin not in {"https://github.com/CultureBotAI/culturebotai-claw",
                      "git@github.com:CultureBotAI/culturebotai-claw"}:
        raise ValueError("Unexpected CLAW repository identity")
    module = root / "src/kg_microbe_discussions/public_export.py"
    schema = module.with_name("public_export.schema.json")
    spec = importlib.util.spec_from_file_location("gap_public_export", module)
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    provenance = {"repository": "CultureBotAI/culturebotai-claw",
                  "revision": git(root, "rev-parse", "HEAD").decode().strip(),
                  "module_sha256": digest(module.read_bytes()),
                  "schema_sha256": digest(schema.read_bytes()),
                  "dirty": bool(git(root, "status", "--porcelain", "--",
                                    "src/kg_microbe_discussions/public_export.py",
                                    "src/kg_microbe_discussions/public_export.schema.json").strip())}
    return exporter, provenance


def matches(path, pattern):
    """POSIX path glob: ** matches zero or more components, * never crosses /."""
    parts, patterns = path.split("/"), pattern.split("/")
    def walk(i, j):
        if j == len(patterns):
            return i == len(parts)
        if patterns[j] == "**":
            return walk(i, j + 1) or (i < len(parts) and not parts[i].startswith(".")
                                       and walk(i + 1, j))
        return (i < len(parts) and (not parts[i].startswith(".") or patterns[j].startswith("."))
                and fnmatch.fnmatchcase(parts[i], patterns[j]) and walk(i + 1, j + 1))
    return walk(0, 0)


def records(repo, revision, config):
    # Listing Git objects is independent of dirty/untracked/ignored working files.
    prefixes = set()
    for pattern in config["globs"]:
        literal = re.split(r"[*?\[]", pattern, maxsplit=1)[0]
        prefixes.add(literal.rsplit("/", 1)[0] if literal != pattern else literal)
    # Every declared root participates; a root-level pattern requires the full
    # tree listing followed by component-aware matching below.
    scope = [] if "" in prefixes else sorted(prefixes)
    rows = git(repo, "ls-tree", "-r", "-z", revision, "--", *scope).split(b"\0")
    for row in rows:
        if not row:
            continue
        metadata, path_bytes = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        path = path_bytes.decode()
        if (any(matches(path, glob) for glob in config["globs"])
                and not any(matches(path, glob) for glob in config.get("exclude_globs", []))):
            if mode not in {"100644", "100755"} or kind != "blob":
                raise ValueError(f"Non-regular source record: {path}")
            yield path, oid


@contextmanager
def blobs(repo):
    process = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def read(oid):
        process.stdin.write((oid + "\n").encode())
        process.stdin.flush()
        header = process.stdout.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError(f"Cannot read pinned object {oid}")
        length = int(header[2])
        payload = process.stdout.read(length)
        if len(payload) != length or process.stdout.read(1) != b"\n":
            raise ValueError("Truncated Git object")
        return payload
    try:
        yield read
    finally:
        process.stdin.close()
        process.wait(timeout=30)
        process.stdout.close()
        process.stderr.close()


def verify_repo(repo, source):
    origin = git(repo, "remote", "get-url", "origin").decode().strip().removesuffix(".git")
    expected = source["repository"]
    if origin.lower() not in {f"https://github.com/{expected}".lower(),
                              f"git@github.com:{expected}".lower()}:
        raise ValueError(f"Wrong Git identity for {source['name']}")
    if not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
        raise ValueError("Source must use a full commit SHA")
    git(repo, "cat-file", "-e", source["revision"] + "^{commit}")
    if source.get("license_sha256"):
        license_path = source["license_url"].split(f"/blob/{source['revision']}/", 1)[1]
        if digest(git(repo, "show", f"{source['revision']}:{license_path}")) != source["license_sha256"]:
            raise ValueError("Source license bytes differ from reviewed configuration")


def adapt(doc, config):
    if config.get("adapter", "discussions") == "discussions":
        return doc, {}
    if config["adapter"] != "research_gaps":
        raise ValueError("Unknown native gap adapter")
    key = config["gap_key"]
    gaps = doc.get("research_gaps", [])
    if not isinstance(gaps, list):
        raise ValueError("research_gaps must be a list")
    mapped, locators, seen = [], {}, set()
    for gap in gaps:
        scope, reason = gap.get(key), gap.get("reason")
        if not isinstance(scope, str) or not scope or scope in seen:
            raise ValueError("Missing or duplicate native gap scope")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Missing native gap reason")
        seen.add(scope)
        identity = "research-gap:" + scope
        # These schemas describe curation/protocol coverage, not asserted
        # scientific unknowns. Do not inherit record citations or invent status.
        mapped.append({"discussion_id": identity, "prompt": reason, "kind": "CURATION_TODO"})
        locators[identity] = f"research_gaps[{key}={scope}]"
    return {**doc, "discussions": mapped}, locators


def acquire(config, repos_root, cache_root, exporter, provenance, selected=None):
    sources, items, identities = [], [], set()
    names = [s["name"] for s in config["sources"]]
    if set(names) != set(ORDER) or len(names) != len(ORDER):
        raise ValueError("Source config must account for every public corpus exactly once")
    for source in config["sources"]:
        name = source["name"]
        if selected and name != selected:
            continue
        if is_withheld(name) or is_withheld(source["repository"]):
            raise ValueError("Non-public source")
        repo = Path(repos_root) / name
        if not repo.is_dir():
            repo = Path(cache_root) / name
        verify_repo(repo, source)
        roots, source_items, touched = [], [], set()
        with blobs(repo) as read:
            for root in source["roots"]:
                if root.get("schema_sha256") and digest(git(repo, "show", f"{source['revision']}:{root['schema_path']}")) != root["schema_sha256"]:
                    raise ValueError("Source schema bytes differ from reviewed configuration")
                row = {"name": root["name"], "support": "supported" if root["supported"] else "unsupported",
                       "status": "unsupported", "eligible_records": None, "inspected_records": 0,
                       "discussion_count": None, "reason": root.get("unsupported_reason", ""),
                       "globs": root["globs"], "exclude_globs": root.get("exclude_globs", [])}
                if not publication_allowed(source, root):
                    row.update(status="unavailable", reason="Public redistribution not established for this source root")
                elif root["supported"]:
                    row.update(status="complete", eligible_records=0, discussion_count=0)
                    print(f"Reading {name}/{root['name']} at {source['revision'][:12]}", flush=True)
                    for path, oid in records(repo, source["revision"], root):
                        if path in touched:
                            raise ValueError(f"Overlapping source roots: {name}/{path}")
                        touched.add(path)
                        row["eligible_records"] += 1
                        raw = read(oid)
                        doc = yaml.load(raw, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
                        if not isinstance(doc, dict):
                            raise ValueError(f"Not a record mapping: {name}/{path}")
                        doc, locators = adapt(doc, root)
                        normalized = exporter.normalize_record(
                            doc, mech=name, repository=source["repository"], revision=source["revision"],
                            path=path, source_sha256=digest(raw), root_config=root,
                            license=source["data_license"], record_url="")
                        for item in normalized:
                            if item["discussion_id"] in locators:
                                item["source"]["locator"] = locators[item["discussion_id"]]
                            exporter.validate_item(item)
                            if item["id"] in identities:
                                raise ValueError(f"Duplicate item identity: {item['id']}")
                            identities.add(item["id"])
                        source_items.extend(normalized)
                        row["discussion_count"] += len(normalized)
                        row["inspected_records"] += 1
                        if row["inspected_records"] % 25000 == 0:
                            print(f"{name}/{root['name']}: parsed {row['inspected_records']} records", flush=True)
                    if row["eligible_records"] == 0:
                        raise ValueError(f"Declared supported root matched no records: {name}/{root['name']}")
                roots.append(row)
                print(f"{name}/{row['name']}: {row['status']}, {row['inspected_records']} records, {row['discussion_count']} items", flush=True)
        items.extend(source_items)
        statuses = {r["status"] for r in roots}
        coverage = next(iter(statuses)) if len(statuses) == 1 else "partial"
        sources.append({k: source[k] for k in ("name", "repository", "revision", "acquired_at", "data_license", "license_url")}
                       | {"coverage_status": coverage, "roots": roots,
                          "items": len(source_items), "source_url": f"https://github.com/{source['repository']}/tree/{source['revision']}"})
    snapshot = {"schema_version": 1, "source_config_sha256": digest(json_bytes(config)),
                "exporter": provenance, "sources": sources, "items": sorted(items, key=lambda i: i["id"])}
    if contains_unlisted_mech(json_bytes(snapshot).decode()):
        raise ValueError("Withheld identity in public snapshot metadata or items")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "_gaps/sources.json")
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, default=ROOT / ".temp/knowledge-gaps-20261114/repos")
    parser.add_argument("--source", choices=ORDER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    exporter, provenance = load_exporter(args.claw_root)
    if args.plan:
        for source in config["sources"]:
            if not args.source or source["name"] == args.source:
                print(source["name"], source["revision"], [(r["name"], r["supported"]) for r in source["roots"]])
        return
    snapshot = acquire(config, args.repos_root, args.cache_root, exporter, provenance, args.source)
    write_atomic(args.output, json_bytes(snapshot))
    if json.loads(args.output.read_text()) != json.loads(json_bytes(snapshot)):
        raise ValueError("Snapshot read-back mismatch")
    print(f"Persisted {len(snapshot['items'])} items from {len(snapshot['sources'])} Mechs: {args.output}")


if __name__ == "__main__":
    main()
