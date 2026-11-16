"""Pure planning/cache-identity checks for issue #609; no model imports/inference."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("embedding_compute", Path(__file__).parents[1] /
                                            "scripts/gaps/embedding_compute.py")
compute = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compute)


class EmbeddingComputeTests(unittest.TestCase):
    def test_duplicate_vector_neighbors_exclude_identity_at_every_rank_not_zero_distance(self):
        # Three identical vectors have equal-distance FAISS results. Only the
        # first query is guaranteed to be rank zero in this shared ordering.
        ranks = [0, 1, 2, 3]
        squared_distances = [[0.0, 0.0, 0.0, 4.0]] * 3 + [[4.0, 4.0, 4.0, 0.0]]
        self.assertIn(1, ranks[1:3])  # Reproduces the dependency's rank-drop defect.
        pairs = []
        for query, distances in enumerate(squared_distances):
            neighbors, actual_distances = compute.identity_filtered_neighbors(ranks, distances, query, 4, 2)
            self.assertNotIn(query, neighbors)
            self.assertEqual(len(set(neighbors)), 2)
            if query < 3:
                self.assertEqual(neighbors, [index for index in range(3) if index != query])
                self.assertEqual(actual_distances, [0.0, 0.0])
            pairs.extend([query, neighbor] for neighbor in neighbors)
        self.assertEqual(compute.validate_projection_pairs(pairs, 4, 2),
                         {"count": 8, "per_point": 2, "self_pairs": 0, "duplicate_pairs": 0})

    def test_projection_pair_validation_rejects_missing_duplicate_self_and_reordered_pairs(self):
        pairs = [[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]]
        for changed in (pairs[:-1], [[0, 0], *pairs[1:]], [[0, 3], *pairs[1:]],
                        [[0, 1], [0, 1], *pairs[2:]], [pairs[2], *pairs[1:2], pairs[0], *pairs[3:]]):
            with self.assertRaises(ValueError):
                compute.validate_projection_pairs(changed, 3, 2)
        for indices, distances in (([0, 0, 1], [0.0, 0.0, 1.0]),
                                   ([0, 1, -1], [0.0, 1.0, 2.0]),
                                   ([0, 1, 2], [0.0, float("nan"), 1.0]),
                                   ([0, 1], [0.0, 1.0])):
            with self.assertRaises(ValueError):
                compute.identity_filtered_neighbors(indices, distances, 0, 3, 2)

    def test_model_revision_rejects_auxiliary_changes_with_identical_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory)
            for name in compute.MODEL_FILES:
                path = model_path / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode())
            (model_path / "config.json").write_text(json.dumps({
                "model_type": "bert", "hidden_size": 1024, "max_position_embeddings": 512}))
            (model_path / "1_Pooling/config.json").write_text(json.dumps({"pooling_mode_cls_token": True}))
            pinned = {name: compute.file_sha(model_path / name) for name in compute.MODEL_FILES}
            with patch.object(compute, "MODEL_FILE_SHA256", pinned):
                self.assertEqual(compute.model_descriptor(model_path, {})["files"], pinned)
                for name in compute.MODEL_FILES:
                    if name == "model.safetensors":
                        continue
                    original = (model_path / name).read_bytes()
                    (model_path / name).write_bytes(original + b"\n")
                    with self.assertRaisesRegex(ValueError, "differ from the pinned snapshot"):
                        compute.model_descriptor(model_path, {})
                    (model_path / name).write_bytes(original)
                    self.assertEqual(compute.file_sha(model_path / "model.safetensors"), pinned["model.safetensors"])

    def test_chunk_spans_cover_every_token_once_including_final_short_chunk(self):
        for count in (1, 480, 481, 960, 1973):
            spans = compute.chunk_spans(count)
            self.assertEqual([index for start, end in spans for index in range(start, end)], list(range(count)))
            self.assertTrue(all(0 < end - start <= 480 for start, end in spans))
        for bad in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                compute.chunk_spans(bad)

    def test_cache_identity_changes_with_input_runtime_and_model_policy(self):
        model = {"revision": "model-pin", "device": "cpu", "chunks": 480}
        original = compute.cache_identity("input-one", model)
        self.assertNotEqual(original, compute.cache_identity("input-two", model))
        for key, value in (("revision", "other-pin"), ("device", "mps"), ("chunks", 256)):
            self.assertNotEqual(original, compute.cache_identity("input-one", {**model, key: value}))

    def test_input_coverage_rejects_unsorted_duplicate_and_stale_text(self):
        def row(key):
            return {"discussion_id": key, "input_text": key, "input_sha256": hashlib.sha256(key.encode()).hexdigest()}
        inputs = {"schema_version": 1, "policy": {"version": 1}, "items": [row("a"), row("b")]}
        self.assertEqual(len(compute.validate_inputs(inputs)), 2)
        for items in ([row("a"), row("a")], [row("b"), row("a")], [{**row("a"), "input_text": "changed"}], []):
            with self.assertRaises(ValueError):
                compute.validate_inputs({**inputs, "items": items})

    def test_forced_canary_bypasses_existing_cache_without_changing_batch_resume(self):
        document = {"item": {"input_sha256": "already-cached"}, "spans": [(0, 480), (480, 601)]}
        with patch.object(compute, "cached_vector", return_value=object()) as cached:
            pending, hits = compute.pending_documents([document], {}, Path("cache"))
            self.assertEqual((pending, hits), ({}, 1))
            cached.reset_mock()
            pending, hits = compute.pending_documents([document], {}, Path("cache"), force=True)
            self.assertEqual((pending, hits), ({"already-cached": document}, 0))
            cached.assert_not_called()

    def test_canary_requires_fresh_complete_inference_and_persisted_vector(self):
        document = {"item": {"input_sha256": "already-cached"}, "spans": [(0, 480), (480, 601)]}
        complete = {"encoded_unique_inputs": 1, "encoded_chunks": 2}
        with patch.object(compute, "encode_missing", return_value=complete) as encode:
            with patch.object(compute, "cached_vector", return_value=object()):
                self.assertEqual(compute.encode_canary(document, Path("model"), {}, Path("cache")), complete)
                encode.assert_called_once_with([document], Path("model"), {}, Path("cache"), force=True)
            with patch.object(compute, "cached_vector", return_value=None):
                with self.assertRaisesRegex(ValueError, "persist"):
                    compute.encode_canary(document, Path("model"), {}, Path("cache"))
        for invalid in ({"encoded_unique_inputs": 0, "encoded_chunks": 0},
                        {"encoded_unique_inputs": 1, "encoded_chunks": 1},
                        {"encoded_unique_inputs": 2, "encoded_chunks": 2}):
            with patch.object(compute, "encode_missing", return_value=invalid):
                with self.assertRaisesRegex(ValueError, "freshly encode exactly one"):
                    compute.encode_canary(document, Path("model"), {}, Path("cache"))


if __name__ == "__main__":
    unittest.main()
