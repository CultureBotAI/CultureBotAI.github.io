"""Acquire pinned record-owned terms for website #583 (2026-11-15).

Inputs: the retained gap snapshot, reviewed source config and immutable Mech Git
objects. Output: a compact vocabulary with complete acquisition coverage. Only
forms that can occur in gap prose are retained, including every colliding source
record. Scientific source files are never changed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from urllib.parse import quote

import yaml

from snapshot import (ROOT, ORDER, blobs, digest, git, is_withheld, json_bytes,
                      matches, publication_allowed, records, verify_repo, write_atomic)
from terms import make_surface_prefilter

POLICY = {
    "version": 1,
    "scope": "Record identifiers, preferred labels and declared exact or unqualified aliases only",
    "retention": "Keep every source record with a form occurring in snapshot prose; retain all collisions",
    "synonyms": "Explicit broad, narrow, related and other non-exact synonym scopes are excluded",
    "culture_label": "Prefer original_name to the machine-readable name",
    "cofactor_identity": "chemical_id is the explicit chemical identity; retain native record_id separately",
    "nested_entities": "Excluded: participants, ingredients, lineage, citations, arbitrary xrefs and curator notes",
}
SOURCE_FIELDS = ("name", "repository", "revision", "acquired_at", "data_license", "license_url")


def entity_id(repository, path, record_id):
    return "entity-" + digest(json_bytes([repository.lower(), path, record_id]))


def label_fields(source, root):
    fields = root.get("name_fields", [])
    return ["original_name", *fields] if source["name"] == "CultureMech" else fields


def root_policy(source, root):
    return {"name": root["name"], "globs": root["globs"],
            "exclude_globs": root.get("exclude_globs", []), "id_field": root["id_field"],
            "label_fields": label_fields(source, root),
            "alias_fields": root.get("alias_fields", []),
            "alias_value_fields": root.get("alias_value_fields", []),
            "canonical_id_field": "chemical_id" if source["name"] == "CofactorMech" else root["id_field"],
            "publication_allowed": publication_allowed(source, root)}


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected a nonempty string for {field}")
    return value.strip()


def aliases(doc, root):
    """Keep native aliases without turning broader/related concepts into names."""
    result = set()
    for field in root.get("alias_fields", []):
        values = doc.get(field, [])
        if values is None:
            continue
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            raise ValueError(f"Expected alias list or scalar for {field}")
        for value in values:
            if isinstance(value, str):
                if value.strip():
                    result.add(value.strip())
                continue
            if not isinstance(value, dict):
                raise ValueError(f"Malformed alias in {field}")
            scopes = [value[key] for key in ("synonym_type", "scope") if value.get(key) is not None]
            if any(not isinstance(scope, str) or scope.casefold() not in {"exact", "exact_synonym"}
                   for scope in scopes):
                continue
            for key in root.get("alias_value_fields", []):
                if value.get(key) is not None:
                    result.add(text(value[key], f"{field}.{key}"))
                    break
    return sorted(result)


def project_record(doc, source, root, path, raw, possible):
    record_id = text(doc.get(root["id_field"]), root["id_field"])
    label = next((doc[field] for field in label_fields(source, root)
                  if isinstance(doc.get(field), str) and doc[field].strip()), None)
    label = text(label, "preferred label")
    canonical_id = (text(doc.get("chemical_id"), "chemical_id")
                    if source["name"] == "CofactorMech" else record_id)
    selected = [value for value in aliases(doc, root) if possible(value)]
    if not selected and not any(possible(value) for value in (label, record_id, canonical_id)):
        return None
    repository, revision = source["repository"], source["revision"]
    return {"id": entity_id(repository, path, record_id), "mech": source["name"],
            "record_id": record_id, "canonical_id": canonical_id, "label": label,
            "aliases": selected,
            "source": {"repository": repository, "revision": revision, "path": path,
                       "sha256": digest(raw), "license": source["data_license"],
                       "url": f"https://github.com/{repository}/blob/{revision}/{quote(path, safe='/')}"}}


def acquire(config, snapshot, repos_root, cache_root, selected=None):
    names = [source["name"] for source in config["sources"]]
    if set(names) != set(ORDER) or len(names) != len(ORDER):
        raise ValueError("Vocabulary config must account for every public corpus exactly once")
    if snapshot["source_config_sha256"] != digest(json_bytes(config)):
        raise ValueError("Vocabulary and gap snapshot must use the same source configuration")
    possible = make_surface_prefilter(snapshot)
    sources, terms = [], []
    for source in config["sources"]:
        name = source["name"]
        if selected and name != selected:
            continue
        if is_withheld(name) or is_withheld(source["repository"]):
            raise ValueError("Withheld vocabulary source")
        repo = Path(repos_root) / name
        if not repo.is_dir():
            repo = Path(cache_root) / name
        verify_repo(repo, source)
        rows, touched = [], set()
        with blobs(repo) as read:
            for root in source["roots"]:
                row = root_policy(source, root) | {"status": "unavailable", "eligible_records": None,
                       "inspected_records": 0, "candidate_records": 0,
                       "reason": "Public redistribution not established for this source root"}
                if publication_allowed(source, root):
                    if not root.get("schema_path") or not root.get("schema_sha256"):
                        raise ValueError(f"Missing reviewed vocabulary schema: {name}/{root['name']}")
                    schema = git(repo, "show", f"{source['revision']}:{root['schema_path']}")
                    if digest(schema) != root["schema_sha256"]:
                        raise ValueError(f"Vocabulary schema digest mismatch: {name}/{root['name']}")
                    row.update(status="complete", eligible_records=0, reason=None)
                    print(f"Reading vocabulary {name}/{root['name']} at {source['revision'][:12]}", flush=True)
                    for path, oid in records(repo, source["revision"], root):
                        if path in touched:
                            raise ValueError(f"Overlapping vocabulary roots: {name}/{path}")
                        touched.add(path)
                        row["eligible_records"] += 1
                        raw = read(oid)
                        doc = yaml.load(raw, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
                        if not isinstance(doc, dict):
                            raise ValueError(f"Vocabulary record is not a mapping: {name}/{path}")
                        try:
                            term = project_record(doc, source, root, path, raw, possible)
                        except ValueError as error:
                            raise ValueError(f"{name}/{path}: {error}") from error
                        if term:
                            terms.append(term)
                            row["candidate_records"] += 1
                        row["inspected_records"] += 1
                        if row["inspected_records"] % 25000 == 0:
                            print(f"{name}/{root['name']}: {row['inspected_records']} inspected, "
                                  f"{row['candidate_records']} candidate records", flush=True)
                    if not row["eligible_records"]:
                        raise ValueError(f"Vocabulary root matched no records: {name}/{root['name']}")
                rows.append(row)
                print(f"{name}/{root['name']}: {row['status']}, {row['inspected_records']} records, "
                      f"{row['candidate_records']} candidates", flush=True)
        statuses = {row["status"] for row in rows}
        sources.append({key: source[key] for key in SOURCE_FIELDS} | {
            "coverage_status": next(iter(statuses)) if len(statuses) == 1 else "partial", "roots": rows})
    vocabulary = {"schema_version": 1, "snapshot_sha256": digest(json_bytes(snapshot)),
                  "source_config_sha256": digest(json_bytes(config)), "policy": POLICY,
                  "sources": sources, "terms": sorted(terms, key=lambda term: term["id"])}
    validate_vocabulary(vocabulary, snapshot, config, pilot=bool(selected))
    return vocabulary


def validate_vocabulary(vocabulary, snapshot, config, *, pilot=False):
    """Offline publication gate; source holds remain binding even for forged JSON."""
    if vocabulary.get("schema_version") != 1 or vocabulary.get("policy") != POLICY:
        raise ValueError("Unsupported vocabulary contract or extraction policy")
    if vocabulary.get("snapshot_sha256") != digest(json_bytes(snapshot)):
        raise ValueError("Vocabulary belongs to another gap snapshot")
    if vocabulary.get("source_config_sha256") != digest(json_bytes(config)):
        raise ValueError("Vocabulary source configuration mismatch")
    if snapshot["source_config_sha256"] != vocabulary["source_config_sha256"]:
        raise ValueError("Vocabulary and gap snapshot source pins differ")
    configs = {source["name"]: source for source in config["sources"]}
    names = [source["name"] for source in vocabulary["sources"]]
    if (len(names) != len(set(names)) or not set(names) <= set(configs)
            or (not pilot and set(names) != set(ORDER))):
        raise ValueError("Missing or duplicate vocabulary source coverage")
    sources = {source["name"]: source for source in vocabulary["sources"]}
    for source in vocabulary["sources"]:
        declared = configs[source["name"]]
        if any(source[key] != declared[key] for key in SOURCE_FIELDS):
            raise ValueError("Vocabulary source provenance mismatch")
        if [row["name"] for row in source["roots"]] != [root["name"] for root in declared["roots"]]:
            raise ValueError("Vocabulary roots differ from reviewed scope")
        for row, root in zip(source["roots"], declared["roots"]):
            if any(row.get(key) != value for key, value in root_policy(declared, root).items()):
                raise ValueError("Vocabulary root policy or publication hold mismatch")
            if not publication_allowed(declared, root):
                if (row["status"] != "unavailable" or row["eligible_records"] is not None
                        or row["inspected_records"] != 0 or row["candidate_records"] != 0 or not row["reason"]):
                    raise ValueError("Vocabulary publication hold requires unavailable unknown coverage")
            elif (row["status"] != "complete" or type(row["eligible_records"]) is not int
                  or row["eligible_records"] < 1 or row["inspected_records"] != row["eligible_records"]
                  or type(row["candidate_records"]) is not int
                  or not 0 <= row["candidate_records"] <= row["inspected_records"]):
                raise ValueError("Invalid complete vocabulary coverage")
        statuses = {row["status"] for row in source["roots"]}
        if source["coverage_status"] != (next(iter(statuses)) if len(statuses) == 1 else "partial"):
            raise ValueError("Vocabulary aggregate coverage mismatch")
    counts, identities, documents = Counter(), set(), defaultdict(set)
    possible = make_surface_prefilter(snapshot)
    for term in vocabulary["terms"]:
        if term["id"] in identities:
            raise ValueError("Duplicate vocabulary identity")
        identities.add(term["id"])
        if term["mech"] not in sources:
            raise ValueError("Uncovered vocabulary source")
        declared, provenance = configs[term["mech"]], term["source"]
        path = text(provenance["path"], "source path")
        if (path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/"))
                or re.search(r"[\x00-\x1f\x7f]", path)):
            raise ValueError("Invalid vocabulary source path")
        for key, expected in (("repository", declared["repository"]), ("revision", declared["revision"]),
                              ("license", declared["data_license"])):
            if provenance[key] != expected:
                raise ValueError("Term source provenance mismatch")
        expected_url = f"https://github.com/{declared['repository']}/blob/{declared['revision']}/{quote(path, safe='/')}"
        if provenance["url"] != expected_url or not re.fullmatch(r"[0-9a-f]{64}", provenance["sha256"]):
            raise ValueError("Invalid vocabulary source URL or digest")
        matched = [root for root, row in zip(declared["roots"], sources[term["mech"]]["roots"])
                   if publication_allowed(declared, root) and row["status"] == "complete"
                   and any(matches(path, pattern) for pattern in root["globs"])
                   and not any(matches(path, pattern) for pattern in root.get("exclude_globs", []))]
        if len(matched) != 1:
            raise ValueError("Term must belong to one publishable vocabulary root")
        record_id = text(term["record_id"], "record_id")
        if term["id"] != entity_id(declared["repository"], path, record_id):
            raise ValueError("Vocabulary identity does not match its record")
        canonical_id = text(term["canonical_id"], "canonical_id")
        if (term["mech"] != "CofactorMech" and canonical_id != record_id
                or term["mech"] == "CofactorMech" and not re.fullmatch(r"CHEBI:[0-9]+", canonical_id)):
            raise ValueError("Undeclared vocabulary canonical identity mapping")
        label = text(term["label"], "label")
        if not isinstance(term["aliases"], list):
            raise ValueError("Vocabulary aliases must be a list")
        term_aliases = [text(value, "alias") for value in term["aliases"]]
        if not any(possible(value) for value in (label, record_id, canonical_id, *term_aliases)):
            raise ValueError("Vocabulary term has no form in the gap snapshot")
        key = (term["mech"], matched[0]["name"])
        counts[key] += 1
        documents[key].add(path)
    for source in vocabulary["sources"]:
        for row in source["roots"]:
            key = (source["name"], row["name"])
            if counts[key] != row["candidate_records"] or len(documents[key]) != counts[key]:
                raise ValueError("Vocabulary root candidate/document counts mismatch")
    if is_withheld(json_bytes(vocabulary).decode()):
        raise ValueError("Withheld identity in public vocabulary")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "_gaps/sources.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "_gaps/snapshot.json")
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, default=ROOT / ".temp/knowledge-gaps-20261114/repos")
    parser.add_argument("--source", choices=ORDER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    config, snapshot = json.loads(args.config.read_text()), json.loads(args.snapshot.read_text())
    if args.plan:
        for source in config["sources"]:
            if not args.source or source["name"] == args.source:
                print(source["name"], source["revision"], [root_policy(source, root) for root in source["roots"]])
        return
    vocabulary = acquire(config, snapshot, args.repos_root, args.cache_root, args.source)
    write_atomic(args.output, json_bytes(vocabulary))
    if json.loads(args.output.read_text()) != vocabulary:
        raise ValueError("Vocabulary read-back mismatch")
    print(f"Persisted {len(vocabulary['terms'])} source term records from {len(vocabulary['sources'])} Mechs: {args.output}")


if __name__ == "__main__":
    main()
