#!/usr/bin/env python3
"""Measure the complete public embedding map and field contributions (#609).

2026-11-15. Inputs: retained inputs/layout/vectors, snapshot, native vocabulary,
source configuration and the published term asset. Output: a JSON measurement
receipt under .temp/gap-embedding-20261115. Uses the real validated bundle builder;
does not change scientific artifacts, the public schema or publication budgets.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
from embedding_bundle import build_document, public_bytes
from snapshot import digest, json_bytes, write_atomic


def read_json(path):
    return json.loads(path.read_bytes())


def size_of(value):
    raw = public_bytes(value)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    return {"json_bytes": len(raw), "gzip_level9_bytes": len(compressed),
            "gzip_level9_mib": round(len(compressed) / 1024**2, 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=ROOT / "assets/gaps")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".temp/gap-embedding-20261115/asset-measurements.json")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / ".temp"):
        raise ValueError("Measurement receipts must remain in this repository's .temp directory")
    manifest = read_json(args.assets / "manifest.json")
    term_path = args.assets / manifest["terms"]["url"]
    terms_raw = term_path.read_bytes()
    if digest(terms_raw) != manifest["terms"]["sha256"]:
        raise ValueError("Published term bytes do not match their manifest")
    terms = json.loads(terms_raw)
    inputs = read_json(ROOT / "_gaps/embedding-inputs.json")
    layout = read_json(ROOT / "_gaps/embedding-layout.json")
    document = build_document(
        read_json(ROOT / "_gaps/snapshot.json"), terms, inputs, layout,
        ROOT / "_gaps/embedding-vectors.npy", read_json(ROOT / "_gaps/sources.json"),
        read_json(ROOT / "_gaps/term-vocabulary.json"))
    raw = public_bytes(document)
    full = size_of(document)
    # Independent compression sizes are descriptive, not additive contributions:
    # removing a field also changes gzip's dictionary and cross-field compression.
    components = {
        "retained_layout": layout,
        "layout_points": layout["points"],
        "layout_metadata_without_points": {k: v for k, v in layout.items() if k != "points"},
        "native_records": document["records"],
        "discussion_contexts": document["contexts"],
        "additional_bundle_metadata": {k: v for k, v in document.items()
                                       if k not in layout and k not in {"records", "contexts"}},
        "point_neighbors_only": [point["neighbors"] for point in document["points"]],
        "native_source_provenance_only": [record["source"] for record in document["records"]],
        "native_descriptions_only": [record["description"] for record in document["records"]],
        "context_matched_terms_only": [row["matched_terms"] for row in document["contexts"]],
        "context_record_references_only": [row["record_ids"] for row in document["contexts"]],
    }
    # These omissions exist only in memory to attribute payload size. They are not
    # proposed public formats and no reduced scientific document is written.
    variants = {}
    for field in ("records", "contexts"):
        variants["without_" + field] = {k: v for k, v in document.items() if k != field}
    for name, section, field in (
        ("without_point_neighbors", "points", "neighbors"),
        ("without_native_descriptions", "records", "description"),
        ("without_native_source_provenance", "records", "source"),
        ("without_context_matched_terms", "contexts", "matched_terms"),
    ):
        reduced = deepcopy(document)
        for row in reduced[section]:
            row.pop(field)
        variants[name] = reduced
    marginal = {}
    for name, value in variants.items():
        measured = size_of(value)
        marginal[name] = {**measured, "gzip_level9_bytes_saved":
                          full["gzip_level9_bytes"] - measured["gzip_level9_bytes"]}
    receipt = {
        "schema_version": 1,
        "method": "Exact embedding_bundle.build_document result and strict public_bytes serializer; canonical UTF-8 JSON; gzip mtime=0",
        "compression": {"python": sys.version.split()[0], "zlib": zlib.ZLIB_RUNTIME_VERSION,
                        "default_compresslevel": 9,
                        "http_transfer_note": "These are reproducible gzip estimates, not measured negotiated HTTP transfer sizes."},
        "public_document_sha256": digest(raw),
        "inputs_sha256": document["inputs_sha256"],
        "retained_layout_sha256": digest(json_bytes(layout)),
        "retained_vectors_sha256": document["vectors"]["sha256"],
        "counts": {"points": len(document["points"]), "records": len(document["records"]),
                   "contexts": len(document["contexts"]),
                   "neighbor_references": sum(len(row["neighbors"]) for row in document["points"])},
        "full_public_document": {**full, "gzip_by_level_bytes": {
            str(level): len(gzip.compress(raw, compresslevel=level, mtime=0)) for level in (1, 6, 9)}},
        "independent_components": {name: size_of(value) for name, value in components.items()},
        "marginal_removal_measurements": marginal,
        "interpretation": "Component compression is not additive. Removal variants diagnose byte cost only; preserve native definitions, provenance and exact original-space neighbor evidence.",
        "budget_comparisons": {str(mib) + "_mib": {
            "budget_bytes": mib * 1024**2,
            "headroom_bytes": mib * 1024**2 - full["gzip_level9_bytes"],
            "utilization_percent": round(100 * full["gzip_level9_bytes"] / (mib * 1024**2), 3),
        } for mib in (2, 3, 4, 5)},
    }
    write_atomic(args.output, json_bytes(receipt))
    if read_json(args.output) != receipt:
        raise ValueError("Measurement receipt failed its persisted reload check")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
