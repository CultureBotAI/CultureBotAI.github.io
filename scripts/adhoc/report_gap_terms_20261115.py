"""Audit generated term occurrences and precision samples; 2026-11-15 explorer.

Inputs: retained gap snapshot/vocabulary and generated manifest/assets. Output:
one requested JSON report. Validates hashes, exact source spans and counts before
writing; never modifies source records, vocabulary, assets, or published pages.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
from terms import _digest, iter_item_texts, normalize_surface


def read_json(path):
    return json.loads(Path(path).read_text())


def asset(root, descriptor):
    path = (root / descriptor["url"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Asset path escapes its directory")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != descriptor["sha256"]:
        raise ValueError(f"Asset digest mismatch: {path}")
    return json.loads(data)


def summarize(term_document, selected_ids):
    rows, by_discussion = [], defaultdict(set)
    labels = {term["id"]: term["label"] for term in term_document["terms"]}
    for term in term_document["terms"]:
        postings = [posting for posting in term["postings"] if posting["discussion_id"] in selected_ids]
        if not postings:
            continue
        rows.append({"id": term["id"], "label": term["label"],
                     "occurrences": sum(posting["count"] for posting in postings),
                     "discussions": len(postings), "canonical_id": term["canonical_id"],
                     "provenance_mechs": sorted({ref["mech"] for ref in term["entity_refs"]})})
        for posting in postings:
            by_discussion[posting["discussion_id"]].add(term["id"])
    rows.sort(key=lambda row: (-row["occurrences"], unicodedata.normalize("NFKC", row["label"]).lower(), row["id"]))
    rank = {row["id"]: index for index, row in enumerate(rows[:20])}
    pairs = Counter(pair for ids in by_discussion.values()
                    for pair in combinations(sorted((key for key in ids if key in rank), key=rank.get), 2))
    ranked_pairs = sorted(pairs.items(), key=lambda entry: (-entry[1], rank[entry[0][0]], rank[entry[0][1]]))
    return {"eligible_discussions": len(selected_ids), "discussions_with_terms": len(by_discussion),
            "recognized_terms": len(rows), "accepted_occurrences": sum(row["occurrences"] for row in rows),
            "top_30_terms": rows[:30],
            "top_50_terms": rows[:50],
            "pair_universe": "Twenty most frequent terms in this selected discussion scope",
            "pair_universe_term_ids": list(rank),
            "top_20_pairs": [{"term_ids": list(pair), "labels": [labels[key] for key in pair],
                              "discussions": count} for pair, count in ranked_pairs[:20]]}


def audit(snapshot, vocabulary, manifest, asset_root):
    build_id = _digest(snapshot)
    if manifest["build_id"] != build_id or vocabulary["snapshot_sha256"] != build_id:
        raise ValueError("Snapshot, vocabulary and manifest do not share a build")
    if vocabulary["source_config_sha256"] != snapshot["source_config_sha256"]:
        raise ValueError("Vocabulary config differs from the snapshot")
    document = asset(asset_root, manifest["terms"])
    if document["build_id"] != build_id or document["vocabulary_sha256"] != _digest(vocabulary):
        raise ValueError("Term document input digests differ")
    binding = {"build_id": build_id, "vocabulary_sha256": _digest(vocabulary), "policy": document["policy"]}
    if document["term_build_id"] != _digest(binding):
        raise ValueError("Term build ID differs from its input/policy binding")
    index = asset(asset_root, manifest["index"])
    items = {item["id"]: item for item in snapshot["items"]}
    if len(items) != len(snapshot["items"]) or {row["id"] for row in index["items"]} != set(items):
        raise ValueError("Discussion IDs differ from the complete index")
    fields = {key: dict(iter_item_texts(value)) for key, value in items.items()}
    seen_terms, samples = set(), []
    for term in document["terms"]:
        if term["id"] in seen_terms:
            raise ValueError("Duplicate term identity")
        seen_terms.add(term["id"])
        seen_discussions = set()
        for posting in term["postings"]:
            key = posting["discussion_id"]
            if key not in items or key in seen_discussions:
                raise ValueError("Missing or duplicate discussion posting")
            seen_discussions.add(key)
            if type(posting["count"]) is not int or posting["count"] <= 0 or posting["count"] != len(posting["mentions"]):
                raise ValueError("Posting count does not match its raw occurrences")
            seen_mentions = set()
            for mention in posting["mentions"]:
                field, start, end = mention["field"], mention["start"], mention["end"]
                text = fields[key].get(field)
                if text is None or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
                    raise ValueError("Mention does not address an allowed original text field")
                if text[start:end] != mention["text"] or normalize_surface(text[start:end]) != mention["matched_as"]:
                    raise ValueError("Mention span or normalized match differs from original text")
                identity = (field, start, end)
                if identity in seen_mentions:
                    raise ValueError("A term occurrence is counted twice in a posting")
                seen_mentions.add(identity)
                sample = {"term_id": term["id"], "label": term["label"], "discussion_id": key,
                          "mech": items[key]["mech"], "field": field, "text": mention["text"],
                          "start": start, "end": end, "context": text[max(0, start - 80):end + 80],
                          "source_url": items[key]["source"]["url"]}
                seed = hashlib.sha256((term["id"] + key + field + str(start)).encode()).hexdigest()
                samples.append((seed, sample))
    all_scope = summarize(document, set(items))
    default_ids = {key for key, item in items.items() if item["lane"] != "candidate" and
                   item["kind"] in {"KNOWLEDGE_GAP", "HUMAN_MODEL_MISMATCH"} and
                   item["status"] in {"OPEN", "UNDER_DISCUSSION"}}
    for field in ("recognized_terms", "accepted_occurrences", "discussions_with_terms"):
        if all_scope[field] != document["summary"][field]:
            raise ValueError(f"Summary {field} differs from verified postings")
    sources = sorted({item["mech"] for item in items.values()} |
                     {source["name"] for source in snapshot.get("sources", [])})
    top_ids = {row["id"] for row in all_scope["top_30_terms"]}
    ordered_samples = sorted(samples)
    top_samples = {}
    for _seed, sample in ordered_samples:
        if sample["term_id"] in top_ids:
            top_samples.setdefault(sample["term_id"], sample)
    return {"schema_version": 1, "build_id": build_id, "term_build_id": document["term_build_id"],
            "verified": {"asset_hashes": True, "snapshot_binding": True, "all_posting_counts": True,
                         "all_unicode_codepoint_spans": True, "metadata_excluded": True},
            "all_scope": all_scope, "default_scope": summarize(document, default_ids),
            "per_gap_mech": {name: summarize(document, {key for key, value in items.items() if value["mech"] == name})
                             for name in sources},
            "ambiguity_summary": {key: document["summary"].get(key, 0) for key in
                                  ("ambiguous_occurrences", "case_rejected_occurrences",
                                   "unicode_boundary_rejected_occurrences", "policy_rejected_occurrences",
                                   "excluded_forms", "denied_surfaces")},
            "largest_ambiguities": sorted(document["ambiguities"], key=lambda row: (-row["occurrences"], row["surface"]))[:20],
            "top_term_precision_samples": [top_samples[key] for key in sorted(top_samples)],
            "deterministic_precision_samples": [sample for _seed, sample in ordered_samples[:30]],
            "vocabulary_coverage": document["vocabulary_sources"], "policy": document["policy"],
            "interpretation": "Occurrence counts are lexical matches, not evidence of biological interaction or research priority."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "_gaps/snapshot.json")
    parser.add_argument("--vocabulary", type=Path, default=ROOT / "_gaps/term-vocabulary.json")
    parser.add_argument("--assets", type=Path, default=ROOT / "assets/gaps")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(read_json(args.snapshot), read_json(args.vocabulary),
                   read_json(args.manifest or args.assets / "manifest.json"), args.assets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not args.output.is_file() or args.output.stat().st_size == 0:
        raise RuntimeError("Report was not persisted")
    counts = {scope: {key: value for key, value in report[scope].items() if isinstance(value, int)}
              for scope in ("all_scope", "default_scope")}
    print(json.dumps({"output": str(args.output), **counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
