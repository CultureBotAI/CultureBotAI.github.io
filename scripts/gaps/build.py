"""Validate a public gap snapshot and build deterministic Pages assets (#577).

Inputs: retained snapshot/config and pinned CLAW contract. Outputs: hashed search
and detail JSON, manifest, and a static coverage include. --check never writes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import html
import json
from pathlib import Path
import tempfile

from snapshot import (ROOT, ORDER, contains_unlisted_mech, digest, json_bytes, load_exporter,
                      matches, publication_allowed, validate_public_sources, write_atomic)
from terms import build_term_document

INDEX_FIELDS = ("id", "mech", "record_id", "record_label", "aliases", "discussion_id",
                "prompt", "rationale", "kind", "status", "origin", "review_state", "lane",
                "evidence_refs", "attaches_to")
MAX_DETAIL_GZIP = 500 * 1024
MAX_TERMS_GZIP = 2 * 1024 * 1024


def load_vocabulary(path, snapshot, config, *, pilot=False):
    """Require the acquired vocabulary to obey this snapshot's source boundary."""
    from vocabulary import validate_vocabulary
    vocabulary = json.loads(path.read_text())
    validate_vocabulary(vocabulary, snapshot, config, pilot=pilot)
    return vocabulary


def validate(snapshot, config, exporter, provenance, *, pilot=False):
    validate_public_sources(config["sources"])
    validate_public_sources(snapshot["sources"])
    if snapshot["schema_version"] != 1:
        raise ValueError("Unsupported snapshot version")
    if snapshot["source_config_sha256"] != digest(json_bytes(config)):
        raise ValueError("Source configuration does not match the acquired snapshot")
    if snapshot["exporter"] != provenance:
        raise ValueError("Exporter revision, dirty state or bytes differ from snapshot")
    if not pilot and provenance["dirty"]:
        raise ValueError("A public bundle requires committed exporter code")
    source_names = [s["name"] for s in snapshot["sources"]]
    if len(source_names) != len(set(source_names)) or (not pilot and set(source_names) != set(ORDER)):
        raise ValueError("Missing or duplicate public source coverage")
    config_by_name = {s["name"]: s for s in config["sources"]}
    exporter.validate_items(snapshot["items"])
    by_source = Counter(i["mech"] for i in snapshot["items"])
    by_root = Counter()
    root_documents = defaultdict(set)
    document_hashes = {}
    source_rows = {source["name"]: source for source in snapshot["sources"]}
    for source in snapshot["sources"]:
        declared = config_by_name[source["name"]]
        for key in ("repository", "revision", "acquired_at", "data_license", "license_url"):
            if source[key] != declared[key]:
                raise ValueError(f"Source metadata mismatch: {source['name']}/{key}")
        repository_url = f"https://github.com/{source['repository']}"
        if source["source_url"] != f"{repository_url}/tree/{source['revision']}":
            raise ValueError("Coverage source URL must identify the pinned repository")
        if not source["license_url"].startswith(f"{repository_url}/blob/{source['revision']}/"):
            raise ValueError("License URL must identify the pinned source repository")
        if source["items"] != by_source[source["name"]]:
            raise ValueError("Source item count mismatch")
        if [r["name"] for r in source["roots"]] != [r["name"] for r in declared["roots"]]:
            raise ValueError("Source roots do not match config")
        statuses = {row["status"] for row in source["roots"]}
        expected_status = next(iter(statuses)) if len(statuses) == 1 else "partial"
        if source["coverage_status"] != expected_status:
            raise ValueError("Aggregate coverage does not match its roots")
        for row, root in zip(source["roots"], declared["roots"]):
            if row["status"] not in {"complete", "unsupported", "unavailable"}:
                raise ValueError("Invalid root coverage status")
            if row["support"] != ("supported" if root["supported"] else "unsupported"):
                raise ValueError("Root support does not match configuration")
            if row["globs"] != root["globs"] or row["exclude_globs"] != root.get("exclude_globs", []):
                raise ValueError("Source root scope drift")
            if not publication_allowed(declared, root) and row["status"] != "unavailable":
                raise ValueError("Root publication hold requires unavailable coverage")
            if row["status"] == "complete":
                if (not root["supported"] or
                        type(row["eligible_records"]) is not int or row["eligible_records"] < 1 or
                        row["inspected_records"] != row["eligible_records"]):
                    raise ValueError("Invalid complete coverage assertion")
            elif (row["discussion_count"] is not None or not row["reason"] or
                  row["eligible_records"] is not None or row["inspected_records"] != 0):
                raise ValueError("Unsupported coverage must be explicit, not zero")
        if sum(r["discussion_count"] or 0 for r in source["roots"]) != source["items"]:
            raise ValueError("Root and source item counts differ")
    for item in snapshot["items"]:
        if item["mech"] not in source_names:
            raise ValueError("Uncovered item source")
        declared = config_by_name[item["mech"]]
        if (item["source"]["repository"] != declared["repository"] or
                item["source"]["revision"] != declared["revision"] or
                item["source"]["license"] != declared["data_license"]):
            raise ValueError("Item source provenance mismatch")
        path = item["source"]["path"]
        matched = [root for root, row in zip(declared["roots"], source_rows[item["mech"]]["roots"])
                   if root["supported"] and row["status"] == "complete"
                   and any(matches(path, pattern) for pattern in root["globs"])
                   and not any(matches(path, pattern) for pattern in root.get("exclude_globs", []))]
        if len(matched) != 1:
            raise ValueError("Item must belong to exactly one complete, non-excluded source root")
        root_key = (item["mech"], matched[0]["name"])
        by_root[root_key] += 1
        # A pinned Git document has one byte digest, regardless of how many
        # discussions it contributes. Check snapshot consistency without reading
        # source repositories again during offline asset generation (#579).
        document = (item["source"]["repository"].lower(), item["source"]["revision"], path)
        sha256 = item["source"]["sha256"]
        if document in document_hashes and document_hashes[document] != sha256:
            raise ValueError("Conflicting source hashes for one pinned document")
        document_hashes[document] = sha256
        root_documents[root_key].add(document)
    for source in snapshot["sources"]:
        for row in source["roots"]:
            if by_root[(source["name"], row["name"])] != (row["discussion_count"] or 0):
                raise ValueError("Root item count does not match its actual items")
            if len(root_documents[(source["name"], row["name"])]) > row["inspected_records"]:
                raise ValueError("Item documents exceed inspected records for source root")
    if contains_unlisted_mech(json_bytes(snapshot).decode()):
        raise ValueError("Withheld identity in public snapshot")


def summary_html(sources, counts):
    esc = html.escape
    lines = [f'<p>{counts["items"]:,} recorded discussion items across '
             f'{len(sources)} public Mechs; {counts["candidates"]:,} are candidates. '
             'Counts describe indexed records, not the extent of scientific knowledge. '
             'Unsupported roots are not empty results.</p>',
             '<ul class="gap-static-coverage">']
    for source in sources:
        lines.append(f'<li><a href="{esc(source["source_url"], quote=True)}">'
                     f'{esc(source["name"])}</a>: {esc(source["coverage_status"])}; '
                     f'{source["items"]:,} indexed items. '
                     f'<a href="{esc(source["license_url"], quote=True)}">'
                     f'{esc(source["data_license"])}</a>. Observed {esc(source["acquired_at"][:10])}.<ul>')
        for row in source["roots"]:
            detail = (f'{row["inspected_records"]:,} records inspected; {row["discussion_count"]:,} items'
                      if row["status"] == "complete" else row["reason"])
            lines.append(f'<li>{esc(row["name"])}: {esc(row["status"])} — {esc(detail)}</li>')
        lines.append('</ul></li>')
    lines.append('</ul><p>Selected structured fields are normalized for browsing; third-party '
                 'quotation snippets are omitted. Credit each linked Mech and its contributors. '
                 'Original records and cited sources remain authoritative.</p>')
    return "\n".join(lines) + "\n"


def detail_parts(items, build_id):
    """Split deterministically until every lazy download meets the budget (#581)."""
    content = json_bytes({"schema_version": 1, "build_id": build_id,
                          "items": {item["id"]: item for item in items}})
    compressed = len(gzip.compress(content, mtime=0))
    if compressed <= MAX_DETAIL_GZIP:
        return [(items, content, compressed)]
    if len(items) <= 1:
        raise ValueError("One discussion exceeds the compressed detail budget")
    midpoint = len(items) // 2
    return detail_parts(items[:midpoint], build_id) + detail_parts(items[midpoint:], build_id)


def artifacts(snapshot, vocabulary=None):
    build_id = digest(json_bytes(snapshot))
    sources, items = snapshot["sources"], snapshot["items"]
    counts = {"items": len(items), "candidates": sum(i["lane"] == "candidate" for i in items),
              "records_with_discussions": len({(i["mech"], i["source"]["path"]) for i in items})}
    files, details, item_shards = {}, {}, {}
    sizes = {}
    for source in sources:
        name = source["name"]
        selected = sorted((item for item in items if item["mech"] == name), key=lambda item: item["id"])
        if not selected:
            continue
        parts = detail_parts(selected, build_id)
        for position, (part, content, compressed) in enumerate(parts, 1):
            key = name if len(parts) == 1 else f"{name}-{position:04d}"
            sha = digest(content)
            path = f"data/{key}.{sha[:16]}.json"
            files[path] = content
            details[key] = {"url": path, "sha256": sha}
            sizes[key] = {"bytes": len(content), "gzip_bytes": compressed}
            if len(parts) > 1:
                item_shards.update({item["id"]: {"detail_shard": key} for item in part})
    index_items = [{**{key: item[key] for key in INDEX_FIELDS}, **item_shards.get(item["id"], {}),
                    "source_url": item["source"]["url"]}
                   for item in items]
    index = json_bytes({"schema_version": 1, "build_id": build_id, "items": index_items})
    if len(gzip.compress(index, mtime=0)) > 2 * 1024 * 1024:
        raise ValueError("Search projection exceeds 2 MiB compressed budget")
    sha = digest(index)
    index_path = f"data/search.{sha[:16]}.json"
    files[index_path] = index
    manifest = {"schema_version": 1, "build_id": build_id, "sources": sources,
                "counts": counts, "index": {"url": index_path, "sha256": sha}, "details": details,
                "exporter": snapshot["exporter"], "source_config_sha256": snapshot["source_config_sha256"],
                "sizes": {"index_bytes": len(index), "index_gzip_bytes": len(gzip.compress(index, mtime=0)),
                          "details": sizes}}
    if vocabulary is not None:
        term_document = build_term_document(snapshot, vocabulary)
        if term_document.get("schema_version") != 1 or term_document.get("build_id") != build_id:
            raise ValueError("Term recognition must identify the same gap snapshot")
        term_bytes = json_bytes(term_document)
        compressed = len(gzip.compress(term_bytes, mtime=0))
        if compressed > MAX_TERMS_GZIP:
            raise ValueError("Term projection exceeds 2 MiB compressed budget")
        term_sha = digest(term_bytes)
        term_path = f"data/terms.{term_sha[:16]}.json"
        files[term_path] = term_bytes
        manifest["terms"] = {"url": term_path, "sha256": term_sha}
        manifest["sizes"].update(terms_bytes=len(term_bytes), terms_gzip_bytes=compressed)
    files["manifest.json"] = json_bytes(manifest)
    return files, summary_html(sources, counts), manifest


def publish(staging, output, summary_path, toolchain_path=None):
    """Install the validated bundle with rollback; preserve replaced assets."""
    operations = [(staging / "data", output / "data"),
                  (staging / "manifest.json", output / "manifest.json"),
                  (staging / "summary.html", summary_path)]
    if toolchain_path is not None:
        operations.append((staging / "toolchain.json", toolchain_path))
    destinations = [target.resolve() for _, target in operations]
    if len(set(destinations)) != len(destinations) or any(
            a in b.parents or b in a.parents for i, a in enumerate(destinations)
            for b in destinations[i + 1:]):
        raise ValueError("Generated artifact destinations must not overlap")
    backup_root = staging / "previous"
    backup_root.mkdir()
    completed = []
    try:
        for i, (prepared, target) in enumerate(operations):
            target.parent.mkdir(parents=True, exist_ok=True)
            backup = backup_root / str(i)
            existed = target.exists()
            if existed:
                target.replace(backup)
            try:
                prepared.replace(target)
            except BaseException:
                if existed:
                    backup.replace(target)
                raise
            completed.append((prepared, target, backup, existed))
    except BaseException:
        for prepared, target, backup, existed in reversed(completed):
            target.replace(prepared)
            if existed:
                backup.replace(target)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "_gaps/snapshot.json")
    parser.add_argument("--config", type=Path, default=ROOT / "_gaps/sources.json")
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/gaps")
    parser.add_argument("--summary", type=Path, default=ROOT / "_includes/gaps-summary.html")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--toolchain", type=Path, default=ROOT / "_gaps/toolchain.json")
    parser.add_argument("--vocabulary", type=Path, default=ROOT / "_gaps/term-vocabulary.json")
    args = parser.parse_args()
    snapshot, config = json.loads(args.snapshot.read_text()), json.loads(args.config.read_text())
    exporter, provenance = load_exporter(args.claw_root)
    validate(snapshot, config, exporter, provenance, pilot=args.pilot)
    vocabulary = load_vocabulary(args.vocabulary, snapshot, config, pilot=args.pilot)
    files, summary, manifest = artifacts(snapshot, vocabulary)
    if args.check:
        for path, content in files.items():
            if not (args.output / path).is_file() or (args.output / path).read_bytes() != content:
                raise ValueError(f"Generated gap asset differs: {path}")
        expected = {p for p in files if p.startswith("data/")}
        actual = {p.relative_to(args.output).as_posix() for p in (args.output / "data").rglob("*") if p.is_file()}
        if actual != expected or args.summary.read_text() != summary:
            raise ValueError("Generated gap file set or static summary differs")
        if not args.pilot and json.loads(args.toolchain.read_text()) != provenance:
            raise ValueError("Published exporter pin differs from snapshot")
    else:
        # Prepare and validate everything before replacing the owned data directory.
        staging_parent = ROOT / ".temp"
        staging_parent.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="gap-bundle-", dir=staging_parent))
        (staging / "data").mkdir()
        for path, content in files.items():
            write_atomic(staging / path, content)
        write_atomic(staging / "summary.html", summary.encode())
        if not args.pilot:
            write_atomic(staging / "toolchain.json", json_bytes(provenance))
        publish(staging, args.output, args.summary, None if args.pilot else args.toolchain)
        for path, content in files.items():
            if (args.output / path).read_bytes() != content:
                raise ValueError(f"Written asset does not match: {path}")
    print(json.dumps({"build_id": manifest["build_id"], "counts": manifest["counts"], "sizes": manifest["sizes"]}, indent=2))


if __name__ == "__main__":
    main()
