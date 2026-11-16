"""Acquire exact matched-record descriptions and compose embedding inputs (#609).

2026-11-15. Inputs: retained gap/term/vocabulary artifacts and pinned local Git
objects. Outputs: a per-record acquisition cache and embedding-inputs.json. No
model or network calls; no native repository writes. --plan is read-only and
--canary acquires exactly one record through the full cache/persistence path.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import yaml

from snapshot import (ROOT, blobs, contains_unlisted_mech, digest, git, json_bytes,
                      matches, publication_allowed, validate_public_sources,
                      verify_repo, write_atomic)
from terms import _concept_key, iter_item_texts, normalize_surface
import vocabulary as vocabulary_module
from vocabulary import canonical_key, label_fields


DESCRIPTION_FIELDS = {
    "HabitatMech": "definition", "CommunityMech": "description", "TraitMech": "definition",
    "PathwayMech": "description", "CellStructureMech": "definition",
    "ProteinTraitsMech": "definition", "DUFMech": "description",
    "NaturalProductMech": "definition", "AntibioticMech": "definition",
    "CMMMech": "description", "MediaIngredientMech": None, "CultureMech": "description",
    "TaxonMech": "definition", "AIMech": "definition", "CofactorMech": "description",
    "AssayMech": "description",
}
POLICY = {
    "version": 1, "composition": "combined_text",
    "gap_fields": "Nonempty fields in terms.iter_item_texts order; original text retained",
    "description_fields": DESCRIPTION_FIELDS,
    "record_scope": "Every native owner of an accepted matched term; no recursive recognition",
    "record_order": "Canonical identity, native label, then native description",
    "duplicate_blocks": "Deduplicate canonical identity/label/description text, retaining every native record reference",
    "missing_descriptions": "Retain native label and identifier; no synthetic definition or curation-note fallback",
    "text_budget": "Complete text; encoder must chunk rather than silently truncate",
}
RECORD_KEYS = {"id", "mech", "record_id", "canonical_id", "label", "description",
               "description_field", "description_status", "definition_sources", "source"}


def record_key(record):
    source = record["source"]
    return record["mech"], source["repository"], source["revision"], source["path"], record["record_id"]


def root_for(record, source):
    path = record["source"]["path"]
    eligible = [root for root in source["roots"] if publication_allowed(source, root)
                and any(matches(path, pattern) for pattern in root["globs"])
                and not any(matches(path, pattern) for pattern in root.get("exclude_globs", []))]
    if len(eligible) != 1:
        raise ValueError("Embedding record must belong to exactly one permitted source root")
    return eligible[0]


def matched_records(snapshot, term_document, config, vocabulary):
    """Resolve only accepted owners, preserving the existing vocabulary identity."""
    validate_public_sources(config["sources"])
    validate_public_sources(snapshot.get("sources", []))
    vocabulary_module.validate_vocabulary(vocabulary, snapshot, config)
    if (term_document.get("build_id") != digest(json_bytes(snapshot))
            or term_document.get("vocabulary_sha256") != digest(json_bytes(vocabulary))):
        raise ValueError("Embedding term data has stale snapshot/vocabulary bindings")
    binding = {"build_id": term_document["build_id"],
               "vocabulary_sha256": term_document["vocabulary_sha256"], "policy": term_document["policy"]}
    if term_document.get("term_build_id") != digest(json_bytes(binding)):
        raise ValueError("Embedding term policy binding differs")
    by_key = {record_key(record): record for record in vocabulary["terms"]}
    if len(by_key) != len(vocabulary["terms"]):
        raise ValueError("Duplicate native vocabulary record")
    sources = {source["name"]: source for source in config["sources"]}
    accepted, seen_terms = {}, set()
    for term in term_document["terms"]:
        if term["id"] in seen_terms or not term["entity_refs"] or not term["postings"]:
            raise ValueError("Duplicate, ownerless or unposted matched term")
        seen_terms.add(term["id"])
        seen_refs = set()
        for ref in term["entity_refs"]:
            key = record_key(ref)
            record = by_key.get(key)
            if record is None or key in seen_refs:
                raise ValueError("Matched owner missing or duplicated in retained vocabulary")
            seen_refs.add(key)
            if ref["source"] != record["source"] or ref["label"] != record["label"]:
                raise ValueError("Matched record provenance/label differs from vocabulary")
            concept, canonical = _concept_key(record)
            expected_id = "term-" + hashlib.sha256(concept.encode()).hexdigest()
            if term["id"] != expected_id or term["canonical_id"] != canonical:
                raise ValueError("Matched term identity differs from its native owner")
            root_for(record, sources[record["mech"]])
            accepted[record["id"]] = record
    return [deepcopy(accepted[key]) for key in sorted(accepted)]


def project_record(raw, record, source, root):
    """Project approved top-level text only, after validating the exact Git blob."""
    if digest(raw) != record["source"]["sha256"]:
        raise ValueError("Native embedding record bytes differ from retained vocabulary")
    document = yaml.load(raw, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
    if not isinstance(document, dict):
        raise ValueError("Embedding source record must be a mapping")
    native_id = document.get(root["id_field"])
    label = next((document[field].strip() for field in label_fields(source, root)
                  if isinstance(document.get(field), str) and document[field].strip()), None)
    native_canonical = document.get("chemical_id") if source["name"] == "CofactorMech" else native_id
    if (not isinstance(native_id, str) or native_id.strip() != record["record_id"]
            or label != record["label"] or not isinstance(native_canonical, str)
            or native_canonical.strip() != record["canonical_id"]):
        raise ValueError("Embedding source identity or label differs from vocabulary")
    field = DESCRIPTION_FIELDS[source["name"]]
    value = document.get(field) if field else None
    if value is not None and not isinstance(value, str):
        raise ValueError("Native description must be a string or absent")
    description = value.strip() if isinstance(value, str) else ""
    status = "present" if description else "missing_native_field" if field else "unsupported_field"
    citations = set()
    for name in ("definition_source", "definition_sources"):
        values = document.get(name)
        if values is None:
            continue
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError("Definition attribution must be text or a list of text")
        citations.update(value.strip() for value in values if value.strip())
    return {key: deepcopy(record[key]) for key in ("id", "mech", "record_id", "canonical_id", "label", "source")} | {
        "description": description, "description_field": field, "description_status": status,
        "definition_sources": sorted(citations)}


def input_text(gap_fields, records):
    sections = ["Knowledge gap text", *[field["field"] + ": " + field["text"] for field in gap_fields]]
    blocks = {}
    for record in records:
        identity = canonical_key(record["canonical_id"]) or "source:" + record["id"]
        key = identity, record["label"], record["description"]
        identifier = canonical_key(record["canonical_id"]) or record["record_id"]
        blocks[key] = "Identifier: " + identifier + "\nName: " + record["label"] + (
            "\nDescription: " + record["description"] if record["description"] else "")
    if blocks:
        sections += ["Matched Mech records", *[blocks[key] for key in sorted(blocks)]]
    return "\n\n".join(sections)


def build_inputs(snapshot, term_document, records):
    """Compose all discussion inputs deterministically without modifying inputs."""
    if term_document["build_id"] != digest(json_bytes(snapshot)):
        raise ValueError("Embedding terms belong to a different discussion snapshot")
    by_record = {record["id"]: record for record in records}
    by_key = {record_key(record): record for record in records}
    if len(by_record) != len(records) or len(by_key) != len(records):
        raise ValueError("Duplicate embedding record")
    by_item = {item["id"]: item for item in snapshot["items"]}
    if len(by_item) != len(snapshot["items"]):
        raise ValueError("Duplicate embedding discussion")
    fields = {key: dict(iter_item_texts(item)) for key, item in by_item.items()}
    item_terms, used_records, seen_terms = defaultdict(list), set(), set()
    for term in term_document["terms"]:
        if term["id"] in seen_terms:
            raise ValueError("Duplicate matched term")
        if not term["postings"]:
            raise ValueError("Accepted matched term has no discussion postings")
        seen_terms.add(term["id"])
        record_ids = []
        for ref in term["entity_refs"]:
            record = by_key.get(record_key(ref))
            if record is None or record["source"] != ref["source"] or record["label"] != ref["label"]:
                raise ValueError("Embedding records do not cover every exact matched owner")
            record_ids.append(record["id"])
        if not record_ids or len(set(record_ids)) != len(record_ids):
            raise ValueError("Matched owner list is empty or duplicated")
        record_ids.sort()
        used_records.update(record_ids)
        seen_postings = set()
        for posting in term["postings"]:
            key = posting["discussion_id"]
            if key not in by_item or key in seen_postings:
                raise ValueError("Unknown or duplicate term discussion")
            seen_postings.add(key)
            if type(posting["count"]) is not int or posting["count"] < 1 or posting["count"] != len(posting["mentions"]):
                raise ValueError("Term occurrence count differs from mentions")
            for mention in posting["mentions"]:
                text = fields[key].get(mention["field"])
                start, end = mention["start"], mention["end"]
                if (text is None or type(start) is not int or type(end) is not int
                        or not 0 <= start < end <= len(text) or text[start:end] != mention["text"]
                        or normalize_surface(text[start:end]) != mention["matched_as"]):
                    raise ValueError("Matched term does not address original gap text")
            item_terms[key].append({"term_id": term["id"], "record_ids": record_ids,
                                    "occurrence_count": posting["count"]})
    if used_records != set(by_record):
        raise ValueError("Embedding records include unmatched native records")
    items = []
    for key in sorted(by_item):
        gap_fields = [{"field": field, "text": text} for field, text in iter_item_texts(by_item[key]) if text.strip()]
        if not gap_fields:
            raise ValueError("Cannot embed a discussion without gap text")
        terms = sorted(item_terms[key], key=lambda row: row["term_id"])
        ids = sorted({record_id for term in terms for record_id in term["record_ids"]})
        text = input_text(gap_fields, [by_record[record_id] for record_id in ids])
        items.append({"discussion_id": key, "gap_fields": gap_fields, "matched_terms": terms,
                      "record_ids": ids, "input_text": text, "input_sha256": digest(text.encode("utf-8"))})
    per_mech = {}
    for name in sorted({source["name"] for source in snapshot.get("sources", [])} | {r["mech"] for r in records}):
        chosen = [record for record in records if record["mech"] == name]
        counts = Counter(record["description_status"] for record in chosen)
        per_mech[name] = {"matched_records": len(chosen), "descriptions_present": counts["present"],
                          "missing_native_field": counts["missing_native_field"], "unsupported_field": counts["unsupported_field"]}
    matched = sum(bool(item["matched_terms"]) for item in items)
    described = sum(any(by_record[key]["description_status"] == "present" for key in item["record_ids"]) for item in items)
    coverage = {"discussions": len(items), "discussions_with_matches": matched,
                "gap_text_only_discussions": len(items) - matched, "discussions_with_descriptions": described,
                "label_only_matched_discussions": matched - described, "matched_terms": len(seen_terms),
                "matched_records": len(records), "records_with_descriptions": sum(bool(r["description"]) for r in records),
                "records_missing_descriptions": sum(not r["description"] for r in records), "per_mech": per_mech}
    return {"schema_version": 1, "build_id": term_document["build_id"],
            "terms_sha256": digest(json_bytes(term_document)), "term_build_id": term_document["term_build_id"],
            "vocabulary_sha256": term_document["vocabulary_sha256"],
            "source_config_sha256": snapshot["source_config_sha256"], "policy": deepcopy(POLICY),
            "coverage": coverage, "records": [deepcopy(by_record[key]) for key in sorted(by_record)], "items": items}


def validate_inputs(inputs, snapshot, term_document, config, vocabulary):
    """Offline publication gate; native field fidelity is checked during acquisition."""
    expected = {record["id"]: record for record in matched_records(snapshot, term_document, config, vocabulary)}
    records = inputs.get("records")
    if not isinstance(records, list) or len(records) != len(expected):
        raise ValueError("Embedding native-record coverage differs from accepted owners")
    for record in records:
        if not isinstance(record, dict) or set(record) != RECORD_KEYS or record.get("id") not in expected:
            raise ValueError("Malformed or unexpected embedding record")
        original = expected[record["id"]]
        if any(record[key] != original[key] for key in ("id", "mech", "record_id", "canonical_id", "label", "source")):
            raise ValueError("Embedding record identity/provenance differs from retained vocabulary")
        field = DESCRIPTION_FIELDS[record["mech"]]
        description = record["description"]
        if not isinstance(description, str) or description != description.strip():
            raise ValueError("Embedding description is not trimmed native text")
        status = "present" if description else "missing_native_field" if field else "unsupported_field"
        if (record["description_field"] != field or record["description_status"] != status
                or field is None and description):
            raise ValueError("Embedding description field/status is outside the extraction policy")
        citations = record["definition_sources"]
        if (not isinstance(citations, list) or any(not isinstance(value, str) or not value.strip() or value != value.strip() for value in citations)
                or citations != sorted(set(citations))):
            raise ValueError("Malformed embedding definition attribution")
    if inputs != build_inputs(snapshot, term_document, records):
        raise ValueError("Embedding input text, coverage, ordering or bindings differ from their sources")
    if contains_unlisted_mech(json_bytes(inputs).decode()):
        raise ValueError("Unlisted Mech identity in embedding inputs")


def acquire_records(selected, config, repos_root, cache_root, record_cache, *, canary=False):
    """Acquire one canary or all selected records using the same persisted path."""
    validate_public_sources(config["sources"])
    sources = {source["name"]: source for source in config["sources"]}
    selected = sorted(selected, key=lambda record: record["id"])
    if canary:
        if not selected:
            raise ValueError("No matched native record is available for the acquisition canary")
        selected = selected[:1]
    grouped = defaultdict(list)
    for record in selected:
        grouped[record["mech"]].append(record)
    result, paths = [], []
    for name in sorted(grouped):
        source = sources[name]
        repo = Path(repos_root) / name
        if not repo.is_dir():
            repo = Path(cache_root) / name
        verify_repo(repo, source)
        checked_roots = set()
        with blobs(repo) as read:
            for record in grouped[name]:
                root = root_for(record, source)
                if root["name"] not in checked_roots:
                    raw_schema = read(source["revision"] + ":" + root["schema_path"])
                    if digest(raw_schema) != root["schema_sha256"]:
                        raise ValueError("Embedding source schema differs from reviewed pin")
                    checked_roots.add(root["name"])
                raw = read(source["revision"] + ":" + record["source"]["path"])
                projected = project_record(raw, record, source, root)
                cache = Path(record_cache) / (record["id"] + ".json")
                payload = {"policy_sha256": digest(json_bytes(POLICY)), "record": projected}
                serialized = json_bytes(payload)
                if not cache.is_file() or cache.read_bytes() != serialized:
                    write_atomic(cache, serialized)
                if cache.stat().st_size == 0 or json.loads(cache.read_bytes()) != payload:
                    raise ValueError("Embedding acquisition cache was not persisted intact")
                result.append(projected)
                paths.append(str(cache))
        print(f"Verified {len(grouped[name])} pinned {name} description records", flush=True)
    return sorted(result, key=lambda record: record["id"]), paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "_gaps/snapshot.json")
    parser.add_argument("--vocabulary", type=Path, default=ROOT / "_gaps/term-vocabulary.json")
    parser.add_argument("--config", type=Path, default=ROOT / "_gaps/sources.json")
    parser.add_argument("--assets", type=Path, default=ROOT / "assets/gaps")
    parser.add_argument("--repos-root", type=Path, default=Path("/Users/marcin/Documents/VIMSS/ontology/Mechs"))
    parser.add_argument("--cache-root", type=Path, default=ROOT / ".temp/knowledge-gaps-20261114/repos")
    parser.add_argument("--record-cache", type=Path, default=ROOT / ".temp/gap-embedding-20261115/records")
    parser.add_argument("--output", type=Path, default=ROOT / "_gaps/embedding-inputs.json")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--canary", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    snapshot, vocabulary, config = [json.loads(path.read_bytes()) for path in (args.snapshot, args.vocabulary, args.config)]
    manifest = json.loads((args.assets / "manifest.json").read_bytes())
    term_path = (args.assets / manifest["terms"]["url"]).resolve()
    if not term_path.is_relative_to(args.assets.resolve()):
        raise ValueError("Term asset path escapes its manifest directory")
    raw = term_path.read_bytes()
    if digest(raw) != manifest["terms"]["sha256"] or manifest["build_id"] != digest(json_bytes(snapshot)):
        raise ValueError("Embedding source assets have stale hashes or snapshot binding")
    term_document = json.loads(raw)
    if args.check:
        validate_inputs(json.loads(args.output.read_bytes()), snapshot, term_document, config, vocabulary)
        print(json.dumps({"complete": True, "checked": str(args.output)}))
        return
    selected = matched_records(snapshot, term_document, config, vocabulary)
    if args.plan:
        print(json.dumps({"records": len(selected), "per_mech": dict(sorted(Counter(r["mech"] for r in selected).items())),
                          "discussions": len(snapshot["items"]), "output": str(args.output),
                          "record_cache": str(args.record_cache), "canary_record": selected[0]["id"] if selected else None}, indent=2))
        return
    projected, paths = acquire_records(selected, config, args.repos_root, args.cache_root, args.record_cache, canary=args.canary)
    if args.canary:
        print(json.dumps({"complete": True, "canary": True, "records": len(projected), "cache_paths": paths,
                          "source_sha256": projected[0]["source"]["sha256"], "description_status": projected[0]["description_status"]}))
        return
    inputs = build_inputs(snapshot, term_document, projected)
    validate_inputs(inputs, snapshot, term_document, config, vocabulary)
    write_atomic(args.output, json_bytes(inputs))
    if not args.output.stat().st_size or json.loads(args.output.read_bytes()) != inputs:
        raise ValueError("Embedding inputs were not persisted intact")
    print(json.dumps({"complete": True, "output": str(args.output), "sha256": digest(args.output.read_bytes()), "coverage": inputs["coverage"]}))


if __name__ == "__main__":
    main()
