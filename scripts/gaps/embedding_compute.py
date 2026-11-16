#!/usr/bin/env python3
"""Compute the retained knowledge-gap embedding layout for issue #609; 2026-11-15.

Inputs: embedding-inputs.json and the pinned, already cached BGE model. Outputs:
incremental verified vector cache, embedding-vectors.npy, embedding-layout.json.
No downloads or service calls. Run --probe, --plan, then --canary before the full
command, keeping device, batch size, cache and output paths unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "BAAI/bge-large-en-v1.5"
MODEL_REVISION = "d4aa6901d3a41ba39fb536a557fa166f842b0e09"
MODEL_WEIGHTS_SHA256 = "45e1954914e29bd74080e6c1510165274ff5279421c89f76c418878732f64ae7"
MODEL_DIMENSIONS = 1024
CHUNK_TOKENS = 480
DEFAULT_MODEL_PATH = (Path.home() / ".cache/huggingface/hub/models--BAAI--bge-large-en-v1.5"
                      / "snapshots" / MODEL_REVISION)
MODEL_FILES = ("config.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt",
               "special_tokens_map.json", "model.safetensors", "1_Pooling/config.json")
# SHA256 of the exact local HF snapshot at MODEL_REVISION, verified 2026-11-15
# for issue #611. Pin tokenizer/config bytes as well as weights: recording hashes
# alone would let an altered tokenizer incorrectly claim this model revision.
MODEL_FILE_SHA256 = {
    "config.json": "446712fac367857b4b1302762fe1cd7bfa8b3c4b77b4dc5d77c4025407660896",
    "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    "tokenizer_config.json": "9261e7d79b44c8195c1cada2b453e55b00aeb81e907a6664974b4d7776172ab3",
    "vocab.txt": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3",
    "special_tokens_map.json": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3",
    "model.safetensors": MODEL_WEIGHTS_SHA256,
    "1_Pooling/config.json": "e54c164a07274f2eb45bb724f54a79d1efcc90c41573887cd9a29aeee0597352",
}
PACKAGES = ("numpy", "torch", "transformers", "tokenizers", "huggingface-hub",
            "safetensors", "scipy", "scikit-learn", "pacmap", "numba", "faiss-cpu")
ENCODING_POLICY = {
    "version": 1,
    "tokenization": "Pinned BERT tokenizer; entire input; no special tokens or truncation",
    "chunks": "Non-overlapping consecutive content-token spans of at most 480 tokens",
    "special_tokens": "One BERT CLS token before and SEP token after every chunk",
    "chunk_pooling": "L2-normalized final-layer CLS representation",
    "document_pooling": "Content-token-count-weighted mean of chunk vectors, then L2 normalization",
    "instruction": None,
    "precision": "float32 inference and retained vectors; float64 weighted accumulation",
}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(path.name + ".tmp")
    staged.write_bytes(json_bytes(value))
    if json.loads(staged.read_bytes()) != value:
        raise ValueError(f"JSON did not persist correctly: {path}")
    staged.replace(path)


def workspace_path(path):
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"Output/cache path must be within the website repository: {path}")
    return resolved


def offline_environment(cache):
    # Only process-local settings; no neighboring environment or model file is edited.
    sys.dont_write_bytecode = True
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY",
                 "PYTHONDONTWRITEBYTECODE"):
        os.environ[name] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    for name in ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    os.environ["NUMBA_CACHE_DIR"] = str(cache.parent / "numba-cache")


def runtime(device, batch_size):
    import numpy as np
    import torch
    import transformers
    import pacmap
    import faiss
    from sklearn.manifold import trustworthiness
    del np, transformers, pacmap, trustworthiness
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is unavailable; select and canary a working backend explicitly")
    torch.set_num_threads(1)
    torch.manual_seed(42)
    faiss.omp_set_num_threads(1)
    return {"device": device, "batch_size": batch_size, "python": platform.python_version(),
            "packages": {name: importlib.metadata.version(name) for name in PACKAGES},
            "projection_threads": 1, "dtype": "float32",
            "reproducibility": "Pinned inputs, model and runtime; retained vectors and coordinates are authoritative. "
                               "Cross-device or cross-version floating-point identity is not asserted."}


def model_descriptor(model_path, runtime_info):
    missing = [name for name in MODEL_FILES if not (model_path / name).is_file()]
    if missing:
        raise ValueError(f"Pinned local model is incomplete: {missing}")
    config = json.loads((model_path / "config.json").read_bytes())
    pooling = json.loads((model_path / "1_Pooling/config.json").read_bytes())
    if (config.get("model_type") != "bert" or config.get("hidden_size") != MODEL_DIMENSIONS
            or config.get("max_position_embeddings") != 512 or not pooling.get("pooling_mode_cls_token")):
        raise ValueError("Cached model does not satisfy the pinned BGE/BERT CLS contract")
    file_hashes = {name: file_sha(model_path / name) for name in MODEL_FILES}
    changed = [name for name in MODEL_FILES if file_hashes[name] != MODEL_FILE_SHA256[name]]
    if changed:
        raise ValueError(f"Local BGE files differ from the pinned snapshot: {', '.join(changed)}")
    return {"name": MODEL_NAME, "revision": MODEL_REVISION, "dimensions": MODEL_DIMENSIONS,
            "chunk_tokens": CHUNK_TOKENS, "max_sequence_length": 512, "license": "MIT",
            "files": file_hashes,
            "encoding_policy": ENCODING_POLICY, "runtime": runtime_info}


def validate_inputs(inputs):
    if inputs.get("schema_version") != 1 or not inputs.get("policy"):
        raise ValueError("Unsupported embedding input contract")
    items = inputs.get("items", [])
    ids = [item.get("discussion_id") for item in items]
    if not items or any(not isinstance(key, str) or not key for key in ids):
        raise ValueError("Embedding inputs require nonempty discussion IDs")
    if ids != sorted(set(ids)):
        raise ValueError("Embedding input IDs must be unique and sorted")
    for item in items:
        text = item.get("input_text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Empty embedding input: {item['discussion_id']}")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != item.get("input_sha256"):
            raise ValueError(f"Stale embedding input hash: {item['discussion_id']}")
    return items


def chunk_spans(token_count):
    if type(token_count) is not int or token_count <= 0:
        raise ValueError("A document must contain at least one content token")
    return [(start, min(start + CHUNK_TOKENS, token_count))
            for start in range(0, token_count, CHUNK_TOKENS)]


def cache_identity(input_sha256, model):
    return {"schema_version": 1, "input_sha256": input_sha256, "model_sha256": digest(model)}


def tokenize(items, model_path):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True,
                                               trust_remote_code=False, use_fast=True)
    if (tokenizer.cls_token_id, tokenizer.sep_token_id, tokenizer.pad_token_id) != (101, 102, 0):
        raise ValueError("Unexpected special token IDs for the pinned BERT tokenizer")
    result = []
    for item in items:
        tokens = tokenizer(item["input_text"], add_special_tokens=False, truncation=False,
                           return_attention_mask=False, return_token_type_ids=False)["input_ids"]
        spans = chunk_spans(len(tokens))
        result.append({"item": item, "token_ids": tokens, "spans": spans,
                       "token_count": len(tokens), "chunk_token_counts": [end - start for start, end in spans]})
    return result


def validate_vector(vector):
    import numpy as np
    if vector.dtype != np.dtype("float32") or vector.shape != (MODEL_DIMENSIONS,):
        raise ValueError("Cached vector must be one float32 BGE vector")
    if not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector.astype(float)), 1, atol=2e-6):
        raise ValueError("Cached vector must be finite and L2 normalized")


def cached_vector(cache, document, model):
    import numpy as np
    identity = cache_identity(document["item"]["input_sha256"], model)
    key = digest(identity)
    metadata_path, vector_path = cache / (key + ".json"), cache / (key + ".npy")
    if not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_bytes())
    expected = {**identity, "token_count": document["token_count"],
                "chunk_count": len(document["spans"]), "chunk_token_counts": document["chunk_token_counts"]}
    if any(metadata.get(name) != value for name, value in expected.items()):
        raise ValueError(f"Stale cache metadata: {key}")
    if file_sha(vector_path) != metadata.get("vector_sha256"):
        raise ValueError(f"Cached vector hash mismatch: {key}")
    vector = np.load(vector_path, allow_pickle=False)
    validate_vector(vector)
    return vector


def save_vector(cache, document, model, vector):
    import numpy as np
    validate_vector(vector)
    identity = cache_identity(document["item"]["input_sha256"], model)
    key = digest(identity)
    cache.mkdir(parents=True, exist_ok=True)
    vector_path = cache / (key + ".npy")
    staged = vector_path.with_suffix(".npy.tmp")
    with staged.open("wb") as handle:
        np.save(handle, np.asarray(vector, dtype="<f4"), allow_pickle=False)
    staged.replace(vector_path)
    write_json(cache / (key + ".json"), {
        **identity, "token_count": document["token_count"], "chunk_count": len(document["spans"]),
        "chunk_token_counts": document["chunk_token_counts"], "vector_sha256": file_sha(vector_path)})
    reloaded = cached_vector(cache, document, model)
    if not np.array_equal(vector, reloaded):
        raise ValueError("Vector cache did not persist exactly")


def pending_documents(documents, model, cache, *, force=False):
    """Select real work, bypassing all cache hits for a fresh canary (issue #610)."""
    pending = {}
    hits = 0
    for document in documents:
        if not force and cached_vector(cache, document, model) is not None:
            hits += 1
        else:
            pending.setdefault(document["item"]["input_sha256"], document)
    return pending, hits


def encode_missing(documents, model_path, model, cache, *, force=False):
    import numpy as np
    import torch
    from transformers import AutoModel
    pending, hits = pending_documents(documents, model, cache, force=force)
    if not pending:
        return {"cache_hits": hits, "encoded_unique_inputs": 0, "encoded_chunks": 0, "inference_seconds": 0.0}
    print(f"Loading pinned local BGE on {model['runtime']['device']}; "
          f"{len(pending)} uncached unique inputs", flush=True)
    encoder = AutoModel.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False,
                                        dtype=torch.float32, attn_implementation="eager")
    encoder.eval().to(model["runtime"]["device"])
    batch_size = model["runtime"]["batch_size"]
    sums = {key: np.zeros(MODEL_DIMENSIONS, dtype=np.float64) for key in pending}
    remaining = {key: len(document["spans"]) for key, document in pending.items()}
    jobs = ((key, document["token_ids"][start:end], end - start)
            for key, document in pending.items() for start, end in document["spans"])
    complete, encoded_chunks = 0, 0
    started = time.monotonic()
    while True:
        batch = []
        for _ in range(batch_size):
            job = next(jobs, None)
            if job is None:
                break
            batch.append(job)
        if not batch:
            break
        length = max(len(tokens) + 2 for _, tokens, _ in batch)
        if length > 512:
            raise ValueError("Chunk overflow would discard input tokens")
        input_ids = np.zeros((len(batch), length), dtype=np.int64)
        attention_mask = np.zeros_like(input_ids)
        for index, (_, tokens, _) in enumerate(batch):
            sequence = [101] + tokens + [102]
            input_ids[index, :len(sequence)] = sequence
            attention_mask[index, :len(sequence)] = 1
        tensors = {"input_ids": torch.as_tensor(input_ids, device=model["runtime"]["device"]),
                   "attention_mask": torch.as_tensor(attention_mask, device=model["runtime"]["device"]),
                   "token_type_ids": torch.zeros(input_ids.shape, dtype=torch.long, device=model["runtime"]["device"])}
        with torch.inference_mode():
            hidden = encoder(**tensors).last_hidden_state[:, 0]
            vectors = torch.nn.functional.normalize(hidden.float(), p=2, dim=1).cpu().numpy()
        for (key, _, count), vector in zip(batch, vectors, strict=True):
            sums[key] += vector.astype(float) * count
            remaining[key] -= 1
            encoded_chunks += 1
            if remaining[key] == 0:
                pooled = sums.pop(key) / pending[key]["token_count"]
                norm = np.linalg.norm(pooled)
                if not np.isfinite(norm) or norm == 0:
                    raise ValueError("Invalid weighted chunk embedding")
                save_vector(cache, pending[key], model, (pooled / norm).astype(np.float32))
                complete += 1
                if complete == 1 or complete % 50 == 0 or complete == len(pending):
                    print(f"Persisted/reloaded {complete}/{len(pending)} unique input vectors; "
                          f"{encoded_chunks} chunks; {time.monotonic() - started:.1f}s", flush=True)
    if any(remaining.values()):
        raise ValueError("Not every content-token chunk was encoded")
    return {"cache_hits": hits, "encoded_unique_inputs": len(pending), "encoded_chunks": encoded_chunks,
            "inference_seconds": round(time.monotonic() - started, 3)}


def encode_canary(candidate, model_path, model, cache):
    """A successful canary always proves new inference plus persisted reload."""
    run = encode_missing([candidate], model_path, model, cache, force=True)
    if run.get("encoded_unique_inputs") != 1 or run.get("encoded_chunks") != len(candidate["spans"]):
        raise ValueError("Canary must freshly encode exactly one complete real input; cache hits cannot pass")
    if cached_vector(cache, candidate, model) is None:
        raise ValueError("Canary did not persist a reloadable vector")
    return run


def projection(vectors, ids):
    import numpy as np
    import pacmap
    from sklearn.decomposition import PCA
    from sklearn.manifold import trustworthiness
    from sklearn.metrics import pairwise_distances
    if len(ids) < 32:
        raise ValueError("The public PaCMAP layout requires at least 32 records; canary only writes verified vectors")
    params = {"n_components": 2, "n_neighbors": 15, "random_state": 42,
              "distance": "euclidean", "apply_pca": False, "knn_backend": "faiss",
              "MN_ratio": 0.5, "FP_ratio": 2.0, "num_iters": (100, 100, 250), "lr": 1.0}
    print(f"Projecting {len(ids)} retained vectors with PaCMAP", flush=True)
    authoritative = vectors.copy()
    coordinates = pacmap.PaCMAP(**params).fit_transform(vectors.copy(), init="pca")
    if (not np.array_equal(vectors, authoritative)
            or not np.allclose(np.linalg.norm(vectors.astype(float), axis=1), 1, atol=2e-6)):
        raise ValueError("Projection modified the authoritative normalized embedding vectors")
    if coordinates.shape != (len(ids), 2) or not np.isfinite(coordinates).all():
        raise ValueError("PaCMAP returned invalid coordinates")
    normalized = vectors.astype(float)
    normalized /= np.linalg.norm(normalized, axis=1, keepdims=True)
    similarities = np.clip(normalized @ normalized.T, -1, 1)
    np.fill_diagonal(similarities, -np.inf)
    # IDs are sorted, so stable sorting gives deterministic ID tie-breaking.
    ordered = np.argsort(-similarities, axis=1, kind="stable")[:, :15]
    neighbors = [[{"id": ids[j], "cosine_similarity": round(float(similarities[i, j]), 8)}
                  for j in ordered[i]] for i in range(len(ids))]
    # Round first, then resolve newly equal public scores by ID as documented.
    for rows in neighbors:
        rows.sort(key=lambda row: (-row["cosine_similarity"], row["id"]))
    pca = PCA(n_components=2, svd_solver="full")
    baseline = pca.fit_transform(normalized)
    distance_2d = pairwise_distances(coordinates, metric="euclidean")
    np.fill_diagonal(distance_2d, np.inf)
    projected_neighbors = np.argsort(distance_2d, axis=1, kind="stable")[:, :15]
    overlap = [len(set(a) & set(b)) / 15 for a, b in zip(ordered, projected_neighbors, strict=True)]
    diagnostics = {
        "trustworthiness_k15_cosine": float(trustworthiness(normalized, coordinates, n_neighbors=15, metric="cosine")),
        "neighbor_overlap_k15": {"mean": float(np.mean(overlap)), "median": float(np.median(overlap)),
                                 "minimum": float(np.min(overlap)), "maximum": float(np.max(overlap))},
        "pca_baseline": {"explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                         "trustworthiness_k15_cosine": float(trustworthiness(normalized, baseline, n_neighbors=15, metric="cosine"))},
        "duplicate_vector_rows": len(vectors) - len(np.unique(vectors, axis=0)),
        "authoritative_vectors_unchanged_by_projection": True,
        "interpretation": "Exploratory projection of text representations; two-dimensional distances are lossy "
                          "and are not evidence of biological relationships. Neighbors use original-space cosine similarity.",
    }
    return coordinates, neighbors, {"method": "PaCMAP", "version": importlib.metadata.version("pacmap"),
                                      **params, "num_iters": list(params["num_iters"]), "init": "pca",
                                      "input": "L2-normalized float32 retained embeddings", "threads": 1}, diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "_gaps/embedding-inputs.json")
    parser.add_argument("--output", type=Path, default=ROOT / "_gaps/embedding-layout.json")
    parser.add_argument("--vectors", type=Path, default=ROOT / "_gaps/embedding-vectors.npy")
    parser.add_argument("--cache", type=Path, default=ROOT / ".temp/gap-embedding-20261115/vectors")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    parser.add_argument("--batch-size", type=int, default=8)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--probe", action="store_true", help="Import dependencies and report local backend; no inference")
    mode.add_argument("--plan", action="store_true", help="Validate and tokenize inputs; no inference/output publication")
    mode.add_argument("--canary", action="store_true", help="Encode and reload exactly one real multichunk document")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    args.cache, args.output, args.vectors = map(workspace_path, (args.cache, args.output, args.vectors))
    if args.output.parent != args.vectors.parent or args.vectors.name != "embedding-vectors.npy":
        raise ValueError("Layout and embedding-vectors.npy must share their retained artifact directory")
    offline_environment(args.cache)
    runtime_info = runtime(args.device, args.batch_size)
    if args.probe:
        print(json.dumps({"offline": True, "runtime": runtime_info, "model_path": str(args.model_path),
                          "model_files_present": all((args.model_path / name).is_file() for name in MODEL_FILES)}, indent=2))
        return
    inputs = json.loads(args.inputs.read_bytes())
    items = validate_inputs(inputs)
    model = model_descriptor(args.model_path, runtime_info)
    documents = tokenize(items, args.model_path)
    token_counts = sorted(row["token_count"] for row in documents)
    total_chunks = sum(len(row["spans"]) for row in documents)
    candidate = next((row for row in documents if len(row["spans"]) > 1), None)
    if candidate is None:
        raise ValueError("The end-to-end canary requires a real multichunk input")
    cached = sum(cached_vector(args.cache, row, model) is not None for row in documents)
    plan = {"documents": len(items), "cached_documents": cached, "content_tokens": sum(token_counts),
            "chunks": total_chunks, "max_tokens": token_counts[-1], "median_tokens": token_counts[len(token_counts) // 2],
            "canary_id": candidate["item"]["discussion_id"], "canary_tokens": candidate["token_count"],
            "canary_chunks": len(candidate["spans"]), "runtime": runtime_info, "model_sha256": digest(model),
            "inputs_sha256": digest(inputs)}
    print(json.dumps(plan, indent=2), flush=True)
    if args.plan:
        return
    canary_path = args.cache.parent / "canary.json"
    binding = {"inputs_sha256": digest(inputs), "model_sha256": digest(model), "cache": str(args.cache.relative_to(ROOT)),
               "output": str(args.output.relative_to(ROOT)), "vectors": str(args.vectors.relative_to(ROOT))}
    if args.canary:
        receipt = {"complete": False, **binding, "discussion_id": candidate["item"]["discussion_id"],
                   "input_sha256": candidate["item"]["input_sha256"], "token_count": candidate["token_count"],
                   "chunk_token_counts": candidate["chunk_token_counts"], "plan": plan}
        write_json(canary_path, receipt)
        receipt["run"] = encode_canary(candidate, args.model_path, model, args.cache)
        receipt.update(complete=True, reloaded_vector_valid=True,
                       complete_token_coverage=sum(candidate["chunk_token_counts"]) == candidate["token_count"])
        write_json(canary_path, receipt)
        print(json.dumps({"canary_complete": True, "receipt": str(canary_path), "run": receipt["run"]}), flush=True)
        return
    if not canary_path.is_file():
        raise ValueError("Run and inspect exactly one --canary before the full batch")
    canary = json.loads(canary_path.read_bytes())
    if not canary.get("complete") or any(canary.get(key) != value for key, value in binding.items()):
        raise ValueError("Successful canary does not match this input/runtime/cache/output configuration")
    if cached_vector(args.cache, candidate, model) is None:
        raise ValueError("The verified canary vector is no longer available")
    run = encode_missing(documents, args.model_path, model, args.cache)
    import numpy as np
    vectors = np.stack([cached_vector(args.cache, row, model) for row in documents]).astype("<f4")
    ids = [row["discussion_id"] for row in items]
    coordinates, neighbors, method, diagnostics = projection(vectors, ids)
    args.vectors.parent.mkdir(parents=True, exist_ok=True)
    staged = args.vectors.with_suffix(".npy.tmp")
    with staged.open("wb") as handle:
        np.save(handle, vectors, allow_pickle=False)
    if not np.array_equal(np.load(staged, allow_pickle=False), vectors):
        raise ValueError("Retained vector matrix failed its reload check")
    staged.replace(args.vectors)
    layout = {
        "schema_version": 1, "build_id": inputs["build_id"], "terms_sha256": inputs["terms_sha256"],
        "inputs_sha256": digest(inputs), "input_policy": inputs["policy"], "model": model,
        "projection": method, "diagnostics": diagnostics, "coverage": {
            "input_discussions": len(items), "embedded_discussions": len(items), "missing_discussions": 0,
            "content_tokens": sum(token_counts), "encoded_content_tokens": sum(token_counts),
            "chunks": total_chunks, "zero_vectors": 0, "truncated_tokens": 0,
            "unique_input_texts": len({row["input_sha256"] for row in items})},
        "vectors": {"file": args.vectors.name, "sha256": file_sha(args.vectors),
                    "dtype": "float32", "shape": list(vectors.shape)},
        "points": [{"id": row["item"]["discussion_id"], "x": round(float(coordinates[i, 0]), 8),
                    "y": round(float(coordinates[i, 1]), 8), "input_sha256": row["item"]["input_sha256"],
                    "token_count": row["token_count"], "chunk_count": len(row["spans"]),
                    "chunk_token_counts": row["chunk_token_counts"], "neighbors": neighbors[i]}
                   for i, row in enumerate(documents)],
    }
    write_json(args.output, layout)
    write_json(args.cache.parent / "run.json", {"complete": True, **binding, "run": run,
                                              "layout_sha256": file_sha(args.output), "vectors": layout["vectors"]})
    print(json.dumps({"complete": True, "points": len(items), "layout": str(args.output), "run": run}), flush=True)


if __name__ == "__main__":
    main()
