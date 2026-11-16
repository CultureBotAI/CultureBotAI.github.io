"""Publication guards for retained gap vectors and maps; issue #609, 2026-11-15."""
import copy
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/gaps"))
import embedding_bundle as bundle


def npy(rows):
    header = repr({"descr": "<f4", "fortran_order": False, "shape": (len(rows), len(rows[0]))})
    header = (header + " " * ((64 - (10 + len(header) + 1) % 64) % 64) + "\n").encode("latin1")
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header + b"".join(
        struct.pack("<" + "f" * len(row), *row) for row in rows)


class EmbeddingBundleTests(unittest.TestCase):
    def setUp(self):
        self.rows = [[float(column == index) for column in range(1024)] for index in range(3)]
        self.raw = npy(self.rows)
        self.inputs = {"build_id": "a" * 64, "terms_sha256": "b" * 64,
                       "policy": {"composition": "combined text"},
                       "items": [{"discussion_id": key, "input_sha256": bundle.digest(key.encode())}
                                 for key in ("gap-a", "gap-b", "gap-c")]}
        self.layout = {"schema_version": 1, "build_id": self.inputs["build_id"],
                       "terms_sha256": self.inputs["terms_sha256"],
                       "inputs_sha256": bundle.digest(bundle.json_bytes(self.inputs)),
                       "input_policy": self.inputs["policy"],
                       "model": {"name": bundle.MODEL_NAME, "revision": bundle.MODEL_REVISION,
                                 "dimensions": 1024, "chunk_tokens": 480},
                       "projection": {"method": "PaCMAP", "random_state": 42},
                       "vectors": {"file": "embedding-vectors.npy", "sha256": bundle.digest(self.raw),
                                   "dtype": "float32", "shape": [3, 1024]},
                       "diagnostics": {"trustworthiness_k15_cosine": .9,
                           "neighbor_overlap_k15": {"mean": .5, "median": .4, "minimum": 0, "maximum": 1},
                           "pca_baseline": {"trustworthiness_k15_cosine": .7, "explained_variance_ratio": [.4, .2]},
                           "duplicate_vector_rows": 0, "authoritative_vectors_unchanged_by_projection": True,
                           "interpretation": "Exploratory text projection"}, "coverage": {
                           "input_discussions": 3, "embedded_discussions": 3, "missing_discussions": 0,
                           "content_tokens": 1506, "encoded_content_tokens": 1506, "chunks": 6,
                           "zero_vectors": 0, "truncated_tokens": 0, "unique_input_texts": 3},
                       "points": [{"id": item["discussion_id"], "x": index, "y": -index,
                                   "input_sha256": item["input_sha256"], "token_count": 502,
                                   "chunk_count": 2, "chunk_token_counts": [480, 22],
                                   "neighbors": [{"id": other["discussion_id"], "cosine_similarity": 0.0}
                                                 for other in self.inputs["items"] if other is not item]}
                                  for index, item in enumerate(self.inputs["items"])]}

    def test_complete_normalized_vectors_and_stable_points_publish(self):
        before = copy.deepcopy((self.inputs, self.layout))
        bundle.validate_layout(self.inputs, self.layout, self.raw)
        self.assertEqual((self.inputs, self.layout), before)

    def test_stale_term_or_input_bindings_are_rejected(self):
        for key in ("build_id", "terms_sha256", "inputs_sha256"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.layout)
                changed[key] = "f" * 64
                with self.assertRaises(ValueError):
                    bundle.validate_layout(self.inputs, changed, self.raw)

    def test_missing_duplicate_reordered_and_unknown_points_are_rejected(self):
        for ids in (("gap-a", "gap-b"), ("gap-a", "gap-b", "gap-b"),
                    ("gap-c", "gap-b", "gap-a"), ("gap-a", "gap-b", "gap-x")):
            with self.subTest(ids=ids):
                changed = copy.deepcopy(self.layout)
                changed["points"] = [dict(self.layout["points"][0], id=key) for key in ids]
                with self.assertRaises(ValueError):
                    bundle.validate_layout(self.inputs, changed, self.raw)

    def test_nonfinite_coordinates_and_incomplete_chunks_are_rejected(self):
        for mutation in ({"x": math.nan}, {"y": True}, {"input_sha256": "x"},
                         {"token_count": 501}, {"chunk_count": 1}, {"chunk_token_counts": [502]},
                         {"chunk_token_counts": [480, 0, 22]}):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.layout)
                changed["points"][0].update(mutation)
                with self.assertRaises(ValueError):
                    bundle.validate_layout(self.inputs, changed, self.raw)

    def test_neighbors_must_reference_real_other_points_and_vector_scores(self):
        for neighbors in ([], [{"id": "gap-x", "cosine_similarity": 0}] * 2,
                          [{"id": "gap-a", "cosine_similarity": 0}, {"id": "gap-c", "cosine_similarity": 0}],
                          [{"id": "gap-b", "cosine_similarity": .1}, {"id": "gap-c", "cosine_similarity": 0}],
                          list(reversed(self.layout["points"][0]["neighbors"]))):
            with self.subTest(neighbors=neighbors):
                changed = copy.deepcopy(self.layout)
                changed["points"][0]["neighbors"] = neighbors
                with self.assertRaises(ValueError):
                    bundle.validate_layout(self.inputs, changed, self.raw)

    def test_vector_hash_shape_payload_norm_and_finiteness_are_checked(self):
        with self.assertRaisesRegex(ValueError, "changed"):
            bundle.validate_layout(self.inputs, self.layout, self.raw + b"x")
        for raw in (npy([[1.0]]), self.raw[:-1], self.raw + b"x"):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                bundle.read_vectors(raw, [3, 1024])
        for value in (math.nan, math.inf, 2.0, 0.0):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows)
                rows[0][0] = value
                with self.assertRaises(ValueError):
                    bundle.read_vectors(npy(rows), [3, 1024])

    def test_model_identity_policy_and_seed_cannot_silently_change(self):
        for field, mutation in (("model", {"revision": "moving-main"}), ("model", {"dimensions": 384}),
                                ("projection", {"random_state": None}), ("input_policy", {"composition": "different"})):
            changed = copy.deepcopy(self.layout)
            changed[field].update(mutation)
            with self.subTest(field=field, mutation=mutation), self.assertRaises(ValueError):
                bundle.validate_layout(self.inputs, changed, self.raw)

    def test_coverage_must_account_for_all_retained_tokens_and_rows(self):
        for field in self.layout["coverage"]:
            changed = copy.deepcopy(self.layout)
            changed["coverage"][field] += 1
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "coverage"):
                bundle.validate_layout(self.inputs, changed, self.raw)

    def test_malformed_projection_diagnostics_cannot_publish(self):
        for diagnostics in ({}, {"neighbor_overlap_k15": {"mean": math.nan}},
                            {**self.layout["diagnostics"], "trustworthiness_k15_cosine": 1.1},
                            {**self.layout["diagnostics"], "duplicate_vector_rows": 3},
                            {**self.layout["diagnostics"], "pca_baseline": {"trustworthiness_k15_cosine": .7,
                                                                         "explained_variance_ratio": [.9, .9]}},
                            {**self.layout["diagnostics"], "neighbor_overlap_k15": {
                                "mean": .4, "median": .5, "minimum": .6, "maximum": 1}}):
            changed = copy.deepcopy(self.layout)
            changed["diagnostics"] = diagnostics
            with self.subTest(diagnostics=diagnostics), self.assertRaises(ValueError):
                bundle.validate_layout(self.inputs, changed, self.raw)

    def test_browser_json_rejects_nonfinite_values_even_outside_diagnostics(self):
        self.assertEqual(bundle.public_bytes(self.layout), bundle.json_bytes(self.layout))
        for value in (math.nan, math.inf, -math.inf):
            changed = copy.deepcopy(self.layout)
            changed["model"]["unexpected_metric"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                bundle.public_bytes(changed)
            with self.assertRaises(ValueError):
                bundle.validate_layout(self.inputs, changed, self.raw)


if __name__ == "__main__":
    unittest.main()
