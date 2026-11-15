"""Acquire pinned record-owned terms for website #583 (2026-11-15).

Inputs: the retained gap snapshot, reviewed source config and immutable Mech Git
objects. Output: a compact vocabulary with complete acquisition coverage. Only
forms that can occur in gap prose are retained, including every colliding source
record. Scientific source files are never changed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

import yaml

from snapshot import (ROOT, ORDER, blobs, contains_unlisted_mech, digest, git, is_withheld, json_bytes,
                      matches, publication_allowed, records, verify_repo, write_atomic)
from terms import SEMANTIC_NAMESPACES, make_surface_prefilter

POLICY = {
    "version": 1,
    "scope": "Record identifiers, preferred labels and declared exact or unqualified aliases only",
    "retention": "Keep every source record with a form occurring in snapshot prose; retain all collisions",
    "synonyms": "Explicit broad, narrow, related and other non-exact synonym scopes are excluded",
    "culture_label": "Prefer original_name to the machine-readable name",
    "cofactor_identity": "chemical_id is the explicit chemical identity; retain native record_id separately",
    "nested_entities": "Excluded: participants, ingredients, lineage, citations, arbitrary xrefs and curator notes",
}
LEGACY_POLICY = deepcopy(POLICY)
POLICY.update(version=2, canonical_owners="Retain every permitted native owner of a retained canonical entity",
              canonical_namespaces=SEMANTIC_NAMESPACES)
SOURCE_FIELDS = ("name", "repository", "revision", "acquired_at", "data_license", "license_url")


def entity_id(repository, path, record_id):
    return "entity-" + digest(json_bytes([repository.lower(), path, record_id]))


def canonical_key(value):
    """Match the matcher's explicit namespace grouping, never arbitrary xrefs."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    prefix, separator, local = value.partition(":")
    if separator and local and not re.search(r"\s", value) and prefix.casefold() in SEMANTIC_NAMESPACES:
        return SEMANTIC_NAMESPACES[prefix.casefold()] + ":" + local
    return None


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


def project_record(doc, source, root, path, raw, possible, *, owner=False):
    record_id = text(doc.get(root["id_field"]), root["id_field"])
    label = next((doc[field] for field in label_fields(source, root)
                  if isinstance(doc.get(field), str) and doc[field].strip()), None)
    label = text(label, "preferred label")
    canonical_id = (text(doc.get("chemical_id"), "chemical_id")
                    if source["name"] == "CofactorMech" else record_id)
    selected = [value for value in aliases(doc, root) if possible(value)]
    lexical = bool(selected) or any(possible(value) for value in (label, record_id, canonical_id))
    if not lexical and not owner:
        return None
    repository, revision = source["repository"], source["revision"]
    return {"id": entity_id(repository, path, record_id), "mech": source["name"],
            "record_id": record_id, "canonical_id": canonical_id, "label": label,
            "retention": "lexical_match" if lexical else "canonical_owner",
            "aliases": selected,
            "source": {"repository": repository, "revision": revision, "path": path,
                       "sha256": digest(raw), "license": source["data_license"],
                       "url": f"https://github.com/{repository}/blob/{revision}/{quote(path, safe='/')}"}}


def finalize_ownership(sources, terms, selected=None):
    """Refresh retained/owner counts without changing native inspection totals."""
    counts, owners = Counter(), Counter()
    source_rows = {source["name"]: source for source in sources}
    for term in terms:
        path = term["source"]["path"]
        roots = [row for row in source_rows[term["mech"]]["roots"]
                 if row["publication_allowed"] and any(matches(path, glob) for glob in row["globs"])
                 and not any(matches(path, glob) for glob in row["exclude_globs"])]
        if len(roots) != 1:
            raise ValueError("Canonical owner must belong to exactly one permitted root")
        key = (term["mech"], roots[0]["name"])
        counts[key] += 1
        owners[key] += term["retention"] == "canonical_owner"
    for source in sources:
        for row in source["roots"]:
            key = (source["name"], row["name"])
            row["candidate_records"], row["owner_records"] = counts[key], owners[key]
            if not row["publication_allowed"]:
                row["owner_closure"] = "unavailable"
            elif not selected or source["name"] == selected:
                row["owner_closure"] = "complete"
            else:
                row.setdefault("owner_closure", "pending")


def identity_candidates(repo, revision, root, eligible, keys, retained):
    """Read cheap pinned top-level identity lines, parsing only candidate owners.

    Ordinary block YAML has a column-zero identity field. Other serializations
    (including JSON-in-YAML, indented mappings, aliases and multiline scalars)
    fall back to full parsing when no definite identity can be established.
    Thus an unrecognized serialization is never silently omitted by the grep.
    """
    field = root["canonical_id_field"]
    escaped = re.escape(field)
    pattern = f"^({escaped}|\"{escaped}\"|'{escaped}')[[:space:]]*:"
    prefixes = set()
    for glob in root["globs"]:
        literal = re.split(r"[*?\[]", glob, maxsplit=1)[0]
        prefixes.add(literal.rsplit("/", 1)[0] if literal != glob else literal)
    scope = [] if "" in prefixes else sorted(prefixes)
    command = ["git", "-C", str(repo), "grep", "--no-color", "--no-textconv", "-I", "-z", "-n",
               "-E", pattern, revision, "--", *scope]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    seen, candidates = set(), set()
    try:
        for raw in process.stdout:
            header, _line_number, line = raw.decode().split("\0", 2)
            path = header.removeprefix(revision + ":")
            if path not in eligible or path in retained:
                continue
            value = line.split(":", 1)[1].strip()
            # The normal million-record case needs no YAML deserialization.
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*:[^\s,\]}]+", value):
                native = value
            else:
                try:
                    decoded = yaml.load(line, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
                    native = decoded.get(field) if isinstance(decoded, dict) else None
                except yaml.YAMLError:
                    native = None
            seen.add(path)
            if not isinstance(native, str) or not native.strip() or canonical_key(native) in keys:
                candidates.add(path)
        error = process.stderr.read()
        if process.wait() not in (0, 1):
            raise ValueError("Pinned identity scan failed: " + error.decode())
    finally:
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=30)
    candidates.update(set(eligible) - seen - retained)
    return sorted((path, eligible[path]) for path in candidates)


def close_owners(existing, config, snapshot, repos_root, cache_root, selected=None, receipt=None):
    """Repair a retained vocabulary through pinned identity-field closure (#595)."""
    if {source["name"] for source in existing["sources"]} != set(ORDER):
        raise ValueError("Owner repair requires complete original fleet coverage")
    validate_vocabulary(existing, snapshot, config, pilot=True, allow_legacy=True)
    result = deepcopy(existing)
    result["policy"] = deepcopy(POLICY)
    for term in result["terms"]:
        term.setdefault("retention", "lexical_match")
    for source in result["sources"]:
        for row in source["roots"]:
            row.setdefault("owner_closure", "pending" if row["publication_allowed"] else "unavailable")
    keys = {canonical_key(term["canonical_id"]) for term in result["terms"]} - {None}
    possible = make_surface_prefilter(snapshot)
    source_rows = {source["name"]: source for source in result["sources"]}
    measurements = {}
    for source in config["sources"]:
        name = source["name"]
        if selected and name != selected:
            continue
        repo = Path(repos_root) / name
        if not repo.is_dir():
            repo = Path(cache_root) / name
        verify_repo(repo, source)
        retained = {term["source"]["path"] for term in result["terms"] if term["mech"] == name}
        with blobs(repo) as read:
            for root, row in zip(source["roots"], source_rows[name]["roots"]):
                if not publication_allowed(source, root):
                    continue
                if digest(git(repo, "show", f"{source['revision']}:{root['schema_path']}")) != root["schema_sha256"]:
                    raise ValueError("Owner closure schema digest mismatch")
                eligible = dict(records(repo, source["revision"], root))
                if len(eligible) != row["eligible_records"]:
                    raise ValueError("Owner closure native count differs from original acquisition")
                print(f"Closing owners {name}/{root['name']}: {len(eligible)} pinned identities", flush=True)
                candidates = identity_candidates(repo, source["revision"], root_policy(source, root), eligible, keys, retained)
                added = 0
                for path, oid in candidates:
                    raw = read(oid)
                    doc = yaml.load(raw, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
                    if not isinstance(doc, dict):
                        raise ValueError("Owner candidate is not a mapping")
                    field = "chemical_id" if name == "CofactorMech" else root["id_field"]
                    if canonical_key(doc.get(field)) not in keys:
                        continue
                    result["terms"].append(project_record(doc, source, root, path, raw, possible, owner=True))
                    retained.add(path)
                    added += 1
                row["owner_closure"] = "complete"
                measurements[(name, root["name"])] = {"candidate_documents_parsed": len(candidates), "owners_added": added}
                print(f"{name}/{root['name']}: parsed {len(candidates)} candidate documents, added {added} owners", flush=True)
    finalize_ownership(result["sources"], result["terms"], selected)
    result["canonical_owners_complete"] = all(row["owner_closure"] != "pending"
        for source in result["sources"] for row in source["roots"])
    result["terms"].sort(key=lambda term: term["id"])
    validate_vocabulary(result, snapshot, config, pilot=bool(selected))
    if receipt is not None:
        before = {(source["name"], row["name"]): row for source in existing["sources"] for row in source["roots"]}
        rows = []
        for source in result["sources"]:
            for row in source["roots"]:
                key = (source["name"], row["name"])
                original = before[key]
                if any(original[field] != row[field] for field in ("eligible_records", "inspected_records", "publication_allowed")):
                    raise ValueError("Owner repair changed original acquisition totals or holds")
                rows.append({"source": source["name"], "root": row["name"], "repository": source["repository"],
                    "revision": source["revision"], "publication_allowed": row["publication_allowed"],
                    "eligible_records": row["eligible_records"], "inspected_records": row["inspected_records"],
                    "retained_before": original["candidate_records"], "retained_after": row["candidate_records"],
                    "owner_closure": row["owner_closure"],
                    **measurements.get(key, {"candidate_documents_parsed": 0, "owners_added": 0})})
        receipt.update(schema_version=1, issue=595, method="Pinned identity-field scan with uncertain-serialization fallback",
            selected_source=selected, input_vocabulary_sha256=digest(json_bytes(existing)),
            output_vocabulary_sha256=digest(json_bytes(result)), snapshot_sha256=result["snapshot_sha256"],
            source_config_sha256=result["source_config_sha256"], source_pins_unchanged=True,
            native_inspection_totals_and_holds_unchanged=True, retained_before=len(existing["terms"]),
            retained_after=len(result["terms"]), canonical_owners_complete=result["canonical_owners_complete"], roots=rows)
    return result


def acquire(config, snapshot, repos_root, cache_root, selected=None):
    names = [source["name"] for source in config["sources"]]
    if set(names) != set(ORDER) or len(names) != len(ORDER):
        raise ValueError("Vocabulary config must account for every public corpus exactly once")
    if snapshot["source_config_sha256"] != digest(json_bytes(config)):
        raise ValueError("Vocabulary and gap snapshot must use the same source configuration")
    possible = make_surface_prefilter(snapshot)
    sources, terms, locators = [], [], defaultdict(list)
    repositories = {}
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
        repositories[name] = repo
        rows, touched = [], set()
        with blobs(repo) as read:
            for root in source["roots"]:
                row = root_policy(source, root) | {"status": "unavailable", "eligible_records": None,
                       "inspected_records": 0, "candidate_records": 0,
                       "owner_records": 0, "owner_closure": "unavailable",
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
                        key = canonical_key(doc.get("chemical_id" if name == "CofactorMech" else root["id_field"]))
                        if key:
                            locators[key].append((name, root["name"], path, oid))
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
    retained = {(term["mech"], term["source"]["path"]) for term in terms}
    additions = defaultdict(list)
    for key in {canonical_key(term["canonical_id"]) for term in terms} - {None}:
        for name, root_name, path, oid in locators[key]:
            if (name, path) not in retained:
                additions[name].append((root_name, path, oid))
    declared = {source["name"]: source for source in config["sources"]}
    for name, candidates in additions.items():
        source = declared[name]
        roots = {root["name"]: root for root in source["roots"]}
        with blobs(repositories[name]) as read:
            for root_name, path, oid in sorted(candidates):
                raw = read(oid)
                doc = yaml.load(raw, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
                terms.append(project_record(doc, source, roots[root_name], path, raw, possible, owner=True))
    finalize_ownership(sources, terms)
    vocabulary = {"schema_version": 1, "snapshot_sha256": digest(json_bytes(snapshot)),
                  "source_config_sha256": digest(json_bytes(config)), "policy": POLICY,
                  "canonical_owners_complete": True,
                  "sources": sources, "terms": sorted(terms, key=lambda term: term["id"])}
    validate_vocabulary(vocabulary, snapshot, config, pilot=bool(selected))
    return vocabulary


def validate_vocabulary(vocabulary, snapshot, config, *, pilot=False, allow_legacy=False):
    """Offline publication gate; source holds remain binding even for forged JSON."""
    legacy = allow_legacy and vocabulary.get("policy") == LEGACY_POLICY
    if vocabulary.get("schema_version") != 1 or (not legacy and vocabulary.get("policy") != POLICY):
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
            if not legacy:
                allowed_closure = {"complete", "pending"} if pilot else {"complete"}
                if (publication_allowed(declared, root) and row.get("owner_closure") not in allowed_closure
                        or not publication_allowed(declared, root) and row.get("owner_closure") != "unavailable"):
                    raise ValueError("Canonical owner closure is incomplete or violates a publication hold")
        statuses = {row["status"] for row in source["roots"]}
        if source["coverage_status"] != (next(iter(statuses)) if len(statuses) == 1 else "partial"):
            raise ValueError("Vocabulary aggregate coverage mismatch")
    if not legacy:
        complete = all(row.get("owner_closure") != "pending" for source in vocabulary["sources"] for row in source["roots"])
        if vocabulary.get("canonical_owners_complete") is not complete:
            raise ValueError("Canonical owner closure summary mismatch")
    counts, owner_counts, identities, documents = Counter(), Counter(), set(), defaultdict(set)
    lexical_keys = set()
    owner_keys = set()
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
        lexical = any(possible(value) for value in (label, record_id, canonical_id, *term_aliases))
        retention = "lexical_match" if legacy else term.get("retention")
        if lexical:
            if retention != "lexical_match":
                raise ValueError("Corpus-present vocabulary term must declare lexical retention")
            lexical_keys.add(canonical_key(canonical_id))
        elif retention != "canonical_owner" or canonical_key(canonical_id) is None:
            raise ValueError("Vocabulary term has no form in the gap snapshot or retained canonical owner")
        else:
            owner_keys.add(canonical_key(canonical_id))
        key = (term["mech"], matched[0]["name"])
        counts[key] += 1
        owner_counts[key] += retention == "canonical_owner"
        documents[key].add(path)
    for source in vocabulary["sources"]:
        for row in source["roots"]:
            key = (source["name"], row["name"])
            if counts[key] != row["candidate_records"] or len(documents[key]) != counts[key]:
                raise ValueError("Vocabulary root candidate/document counts mismatch")
            if not legacy and row.get("owner_records") != owner_counts[key]:
                raise ValueError("Vocabulary canonical owner count mismatch")
    if not owner_keys <= lexical_keys:
        raise ValueError("Owner-only record has no corpus-present canonical sibling")
    if contains_unlisted_mech(json_bytes(vocabulary).decode()):
        raise ValueError("Withheld identity in public vocabulary")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "_gaps/sources.json")
    parser.add_argument("--snapshot", type=Path, default=ROOT / "_gaps/snapshot.json")
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, default=ROOT / ".temp/knowledge-gaps-20261114/repos")
    parser.add_argument("--source", choices=ORDER)
    parser.add_argument("--close-owners", type=Path, help="Close canonical ownership over an existing vocabulary without reparsing the fleet")
    parser.add_argument("--receipt", type=Path, help="Persist a deterministic owner-closure audit receipt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    if args.receipt and not args.close_owners:
        parser.error("--receipt requires --close-owners")
    config, snapshot = json.loads(args.config.read_text()), json.loads(args.snapshot.read_text())
    if args.plan:
        for source in config["sources"]:
            if not args.source or source["name"] == args.source:
                print(source["name"], source["revision"], [root_policy(source, root) for root in source["roots"]])
        return
    if args.close_owners:
        receipt = {}
        vocabulary = close_owners(json.loads(args.close_owners.read_text()), config, snapshot,
                                  args.repos_root, args.cache_root, args.source, receipt)
    else:
        vocabulary = acquire(config, snapshot, args.repos_root, args.cache_root, args.source)
    write_atomic(args.output, json_bytes(vocabulary))
    if json.loads(args.output.read_text()) != vocabulary:
        raise ValueError("Vocabulary read-back mismatch")
    if args.receipt:
        receipt["output_vocabulary_path"] = args.output.as_posix() if not args.output.is_absolute() else args.output.name
        receipt["output_bytes"] = args.output.stat().st_size
        write_atomic(args.receipt, json_bytes(receipt))
        if json.loads(args.receipt.read_text()) != receipt:
            raise ValueError("Owner receipt read-back mismatch")
    print(f"Persisted {len(vocabulary['terms'])} source term records from {len(vocabulary['sources'])} Mechs: {args.output}")


if __name__ == "__main__":
    main()
