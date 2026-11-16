"""Validate and package retained knowledge-gap embeddings for issue #609.

Inputs: pinned discussion/term/input documents, layout metadata and NPY vectors.
Output: a deterministic public map document; no inference or projection in CI.
2026-11-15.
"""
from __future__ import annotations

import array
import ast
from copy import deepcopy
import math
from pathlib import Path
import sys

from snapshot import digest, json_bytes


MODEL_NAME = "BAAI/bge-large-en-v1.5"
MODEL_REVISION = "d4aa6901d3a41ba39fb536a557fa166f842b0e09"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_vectors(raw, expected_shape):
    """Read the narrow non-object NPY format we publish, without NumPy in CI."""
    require(raw[:6] == b"\x93NUMPY" and raw[6:8] in (b"\x01\x00", b"\x02\x00"),
            "Embedding vectors must be NPY version 1 or 2")
    size = 2 if raw[6] == 1 else 4
    require(len(raw) >= 8 + size, "Truncated vector header")
    header_length = int.from_bytes(raw[8:8 + size], "little")
    offset = 8 + size + header_length
    require(0 < header_length < 65536 and offset <= len(raw), "Invalid vector header length")
    try:
        header = ast.literal_eval(raw[8 + size:offset].decode("latin1"))
    except (ValueError, SyntaxError, UnicodeError) as error:
        raise ValueError("Invalid vector header") from error
    require(isinstance(header, dict) and header.get("descr") == "<f4"
            and header.get("fortran_order") is False and header.get("shape") == tuple(expected_shape),
            "Vector dtype, order or shape differs from its declared rows")
    require(len(raw) - offset == math.prod(expected_shape) * 4, "Vector payload length mismatch")
    values = array.array("f")
    require(values.itemsize == 4, "Platform float array is not float32")
    values.frombytes(raw[offset:])
    if sys.byteorder != "little":
        values.byteswap()
    width = expected_shape[1]
    for start in range(0, len(values), width):
        row = values[start:start + width]
        require(all(math.isfinite(value) for value in row), "Embedding vectors contain nonfinite values")
        require(abs(sum(value * value for value in row) - 1) < 0.002,
                "Embedding vectors must be L2 normalized")
    return values


def validate_layout(inputs, layout, raw_vectors):
    require(layout.get("schema_version") == 1, "Unsupported embedding layout version")
    for key in ("build_id", "terms_sha256"):
        require(layout.get(key) == inputs.get(key), "Embedding layout has stale " + key)
    require(layout.get("inputs_sha256") == digest(json_bytes(inputs)), "Embedding inputs digest mismatch")
    require(layout.get("input_policy") == inputs.get("policy"), "Embedding composition policy differs")
    model = layout.get("model", {})
    require(model.get("name") == MODEL_NAME and model.get("revision") == MODEL_REVISION,
            "Embedding model must identify the reviewed immutable model")
    require(model.get("dimensions") == 1024 and model.get("chunk_tokens") == 480,
            "Embedding dimensions or chunk budget differ from the reviewed model")
    projection = layout.get("projection", {})
    require(projection.get("method") == "PaCMAP" and projection.get("random_state") == 42,
            "Projection must identify the reviewed method and seed")
    items = inputs.get("items", [])
    ids = [item["discussion_id"] for item in items]
    require(ids and ids == sorted(set(ids)), "Embedding input IDs must be nonempty, unique and sorted")
    points = layout.get("points", [])
    require(isinstance(points, list) and [point.get("id") for point in points] == ids,
            "Embedding points must cover every input in the same order")
    vector_info = layout.get("vectors", {})
    require(vector_info.get("file") == "embedding-vectors.npy" and vector_info.get("dtype") == "float32"
            and vector_info.get("shape") == [len(ids), 1024], "Invalid retained vector descriptor")
    require(vector_info.get("sha256") == digest(raw_vectors), "Retained embedding vectors have changed")
    vectors = read_vectors(raw_vectors, vector_info["shape"])
    positions = {key: index for index, key in enumerate(ids)}
    for item, point in zip(items, points):
        require(point.get("input_sha256") == item.get("input_sha256"), "A point has stale input text")
        require(all(type(point.get(key)) in (float, int) and math.isfinite(point[key]) for key in ("x", "y")),
                "Embedding coordinates must be finite numbers")
        chunks = point.get("chunk_token_counts")
        require(isinstance(chunks, list) and chunks and all(type(n) is int and 0 < n <= 480 for n in chunks),
                "Invalid embedding token chunks")
        require(type(point.get("token_count")) is int and point["token_count"] == sum(chunks)
                and type(point.get("chunk_count")) is int and point["chunk_count"] == len(chunks),
                "Embedding chunk coverage does not account for all tokens")
        neighbors = point.get("neighbors")
        require(isinstance(neighbors, list) and len(neighbors) == min(15, len(ids) - 1),
                "Each point must retain its full nearest-neighbor list")
        neighbor_ids = [neighbor.get("id") for neighbor in neighbors]
        require(len(set(neighbor_ids)) == len(neighbor_ids)
                and all(key in positions and key != point["id"] for key in neighbor_ids),
                "Invalid, duplicate or self-referencing embedding neighbor")
        scores = [neighbor.get("cosine_similarity") for neighbor in neighbors]
        require(all(type(score) in (float, int) and math.isfinite(score) and -1.000001 <= score <= 1.000001
                    for score in scores), "Invalid cosine neighbor score")
        require(neighbors == sorted(neighbors, key=lambda row: (-row["cosine_similarity"], row["id"])),
                "Embedding neighbors must have stable similarity ordering")
        start = positions[point["id"]] * 1024
        row = vectors[start:start + 1024]
        for neighbor in neighbors:
            offset = positions[neighbor["id"]] * 1024
            actual = sum(left * right for left, right in zip(row, vectors[offset:offset + 1024]))
            require(abs(actual - neighbor["cosine_similarity"]) < 0.00002,
                    "A listed neighbor score differs from the original vectors")
    require(isinstance(layout.get("diagnostics"), dict) and layout["diagnostics"],
            "Projection diagnostics must be retained")
    coverage = layout.get("coverage", {})
    expected = {
        "input_discussions": len(ids), "embedded_discussions": len(ids), "missing_discussions": 0,
        "content_tokens": sum(point["token_count"] for point in points),
        "encoded_content_tokens": sum(point["token_count"] for point in points),
        "chunks": sum(point["chunk_count"] for point in points),
        "zero_vectors": 0, "truncated_tokens": 0,
        "unique_input_texts": len({item["input_sha256"] for item in items}),
    }
    require(isinstance(coverage, dict) and all(type(coverage.get(key)) is int and coverage[key] == value
                                             for key, value in expected.items()),
            "Embedding coverage differs from retained points and inputs")


def build_document(snapshot, term_document, inputs, layout, vector_path, config, vocabulary):
    from embedding_inputs import validate_inputs
    validate_inputs(inputs, snapshot, term_document, config, vocabulary)
    validate_layout(inputs, layout, Path(vector_path).read_bytes())
    document = deepcopy(layout)
    document["records"] = deepcopy(inputs["records"])
    document["contexts"] = [{"id": item["discussion_id"], "record_ids": item["record_ids"],
                             "matched_terms": deepcopy(item["matched_terms"])} for item in inputs["items"]]
    document["input_coverage"] = deepcopy(inputs["coverage"])
    document["term_build_id"] = term_document["term_build_id"]
    document["vocabulary_sha256"] = term_document["vocabulary_sha256"]
    return document
