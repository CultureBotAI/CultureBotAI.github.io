"""Unit tests for cross-Mech gap synthesis analytics and normalization."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
SPEC = importlib.util.spec_from_file_location("gap_analytics", ROOT / "scripts/gaps/analytics.py")
analytics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analytics)


def canonical_digest(payload):
    return analytics.digest(analytics.json_bytes(payload))


class GapAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            {
                "id": "TraitMech:r1:d1",
                "mech": "TraitMech",
                "record_id": "TraitMech:r1",
                "record_label": "Phage defense trait",
                "prompt": "Which phage trigger activates the defensefinder effector?",
                "rationale": "Phage trigger specificity remains untested.",
                "kind": "KNOWLEDGE_GAP",
                "status": "OPEN",
                "lane": "recorded",
                "posed_date": "2026-03-10",
                "resolved_date": None,
                "attaches_to": ["causal_graphs#edge1", "GO:0043625"],
                "evidence": [{"reference": "doi:10.1128/JB.00276-19", "supports": "PARTIAL", "explanation": "Indirect assay."}],
                "evidence_refs": ["doi:10.1128/JB.00276-19"],
                "proposed_experiments": [{"name": "Phage plaque panel", "approach": "Challenge isogenic knockouts"}],
                "source": {"url": "https://github.com/CultureBotAI/TraitMech/blob/" + "1" * 40 + "/a.yaml"},
            },
            {
                "id": "CellStructureMech:r2:d2",
                "mech": "CellStructureMech",
                "record_id": "CellStructureMech:r2",
                "record_label": "Outer envelope complex",
                "prompt": "Which phage trigger remodels the defensefinder assembly?",
                "rationale": "Envelope remodeling under phage trigger stress is unknown.",
                "kind": "KNOWLEDGE_GAP",
                "status": "RESOLVED",
                "lane": "recorded",
                "posed_date": "2026-03-15",
                "resolved_date": "2026-04-02",
                "attaches_to": ["components[0].localization"],
                "evidence": [{"reference": "DOI:10.1128/jb.00276-19", "supports": "SUPPORT"}],
                "evidence_refs": ["DOI:10.1128/jb.00276-19", "PMID:998877"],
                "proposed_experiments": [],
                "source": {"url": "https://github.com/CultureBotAI/CellStructureMech/blob/" + "2" * 40 + "/b.yaml"},
            },
            {
                "id": "CommunityMech:r3:d3",
                "mech": "CommunityMech",
                "record_id": "CommunityMech:r3",
                "record_label": "Marine biofilm",
                "prompt": "How does iron exchange stabilize biofilm growth?",
                "rationale": "Iron siderophore transfer is hypothesized.",
                "kind": "CURATION_TODO",
                "status": "OPEN",
                "lane": "recorded",
                "attaches_to": [],
                "evidence": [],
                "evidence_refs": ["pmid:998877"],
                "proposed_experiments": ["Co-culture isotope tracing"],
                "source": {"url": "https://github.com/CultureBotAI/CommunityMech/blob/" + "3" * 40 + "/c.yaml"},
            },
        ]
        self.snapshot = {"schema_version": 1, "items": self.items}
        self.build_id = canonical_digest(self.snapshot)
        self.term_doc = {
            "schema_version": 1,
            "build_id": self.build_id,
            "terms": [
                {
                    "id": "term-iron",
                    "label": "iron",
                    "canonical_id": "CHEBI:18248",
                    "entity_refs": [{"mech": "CofactorMech", "record_id": "CHEBI:18248"}],
                    "postings": [{"discussion_id": "CommunityMech:r3:d3", "count": 2}],
                }
            ],
        }
        dup_hash = "e" * 64
        self.embedding_doc = {
            "schema_version": 1,
            "build_id": self.build_id,
            "terms_sha256": canonical_digest(self.term_doc),
            "inputs_sha256": "f" * 64,
            "points": [
                {
                    "id": "TraitMech:r1:d1",
                    "x": 1.0,
                    "y": 2.0,
                    "input_sha256": dup_hash,
                    "token_count": 20,
                    "chunk_count": 1,
                    "neighbors": [
                        {"id": "CellStructureMech:r2:d2", "cosine_similarity": 0.912},
                        {"id": "CommunityMech:r3:d3", "cosine_similarity": 0.41},
                    ],
                },
                {
                    "id": "CellStructureMech:r2:d2",
                    "x": 1.2,
                    "y": 2.1,
                    "input_sha256": dup_hash,
                    "token_count": 20,
                    "chunk_count": 1,
                    "neighbors": [
                        {"id": "TraitMech:r1:d1", "cosine_similarity": 0.912},
                        {"id": "CommunityMech:r3:d3", "cosine_similarity": 0.39},
                    ],
                },
                {
                    "id": "CommunityMech:r3:d3",
                    "x": -3.0,
                    "y": -1.5,
                    "input_sha256": "a" * 64,
                    "token_count": 18,
                    "chunk_count": 1,
                    "neighbors": [
                        {"id": "TraitMech:r1:d1", "cosine_similarity": 0.41},
                    ],
                },
            ],
        }

    def test_attach_layer_and_reference_normalization(self):
        self.assertEqual(analytics.normalize_attach_layer("causal_graphs#edge1"), "causal_graphs")
        self.assertEqual(analytics.normalize_attach_layer("components[0].localization"), "components")
        self.assertEqual(analytics.normalize_attach_layer("ecological_interactions/0"), "ecological_interactions")
        self.assertEqual(analytics.normalize_attach_layer("GO:0043625"), "entity_curie")
        self.assertEqual(analytics.normalize_attach_layer("obo.go:00001#frag"), "entity_curie")
        self.assertEqual(analytics.normalize_attach_layer("https://example.org/slot/1#frag"), "external_uri")
        self.assertEqual(analytics.normalize_attach_layer(""), "")
        self.assertEqual(analytics.normalize_reference_key("doi:10.1128/JB.00276-19"), "DOI:10.1128/jb.00276-19")
        self.assertEqual(analytics.normalize_reference_key("https://doi.org/10.1128/JB.00276-19"), "DOI:10.1128/jb.00276-19")
        self.assertEqual(analytics.normalize_reference_key("https://dx.doi.org/10.1039/C1MB05328K"), "DOI:10.1039/c1mb05328k")
        self.assertEqual(analytics.normalize_reference_key("pmid: 998877 "), "PMID:998877")
        self.assertEqual(analytics.normalize_reference_key("https://pubmed.ncbi.nlm.nih.gov/998877/"), "PMID:998877")

    def test_analytics_document_summarizes_blindspots_experiments_citations_and_bridges(self):
        doc = analytics.build_analytics_document(self.snapshot, self.term_doc, self.embedding_doc)
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["build_id"], self.build_id)

        unmatched = doc["unmatched_coverage"]
        self.assertEqual(unmatched["total_discussions"], 3)
        self.assertEqual(unmatched["matched_discussions"], 1)
        self.assertEqual(unmatched["unmatched_discussions"], 2)
        self.assertEqual(unmatched["gaps_only"]["total_discussions"], 2)
        self.assertEqual(unmatched["gaps_only"]["unmatched_discussions"], 2)
        phrases = {entry["phrase"]: entry["discussions"] for entry in unmatched["gaps_only"]["candidate_phrases"]}
        self.assertEqual(phrases.get("phage trigger"), 2)
        self.assertEqual(phrases.get("defensefinder"), 2)

        exps = doc["proposed_experiments"]
        self.assertEqual(exps["discussions_with_experiments"], 2)
        self.assertEqual(exps["total_experiments"], 2)
        self.assertEqual(exps["by_mech"], {"CommunityMech": 1, "TraitMech": 1})

        citations = doc["citations"]
        self.assertEqual(citations["distinct_normalized_refs"], 2)
        self.assertEqual(citations["cross_mech_ref_count"], 2)
        cross_refs = {entry["ref"]: entry["mechs"] for entry in citations["cross_mech_refs"]}
        self.assertEqual(cross_refs["DOI:10.1128/jb.00276-19"], ["CellStructureMech", "TraitMech"])
        self.assertEqual(cross_refs["PMID:998877"], ["CellStructureMech", "CommunityMech"])

        bridges = doc["embedding_bridges"]
        self.assertIsNotNone(bridges)
        self.assertEqual(bridges["discussions_with_cross_mech_top1"], 3)
        self.assertEqual(bridges["duplicate_cluster_count"], 1)
        self.assertEqual(bridges["duplicate_discussion_count"], 2)
        top_pair = bridges["cross_mech_pairs"][0]
        self.assertEqual({top_pair["id_a"], top_pair["id_b"]}, {"TraitMech:r1:d1", "CellStructureMech:r2:d2"})
        self.assertAlmostEqual(top_pair["cosine_similarity"], 0.912, places=3)

    def test_analytics_rejects_unlisted_mech_content(self):
        tainted = json.loads(json.dumps(self.snapshot))
        tainted["items"][0]["rationale"] = "Mentions UnlistedExampleMech in prose."
        tainted_term = json.loads(json.dumps(self.term_doc))
        tainted_term["build_id"] = canonical_digest(tainted)
        with self.assertRaisesRegex(ValueError, "Unlisted or withheld Mech"):
            analytics.build_analytics_document(tainted, tainted_term, None)

        tainted_term_only = json.loads(json.dumps(self.term_doc))
        tainted_term_only["terms"][0]["label"] = "UnlistedExampleMech cofactor"
        with self.assertRaisesRegex(ValueError, "Unlisted or withheld Mech"):
            analytics.build_analytics_document(self.snapshot, tainted_term_only, None)

        tainted_emb = json.loads(json.dumps(self.embedding_doc))
        tainted_emb["model_note"] = "UnlistedExampleMech"
        with self.assertRaisesRegex(ValueError, "Unlisted or withheld Mech"):
            analytics.build_analytics_document(self.snapshot, self.term_doc, tainted_emb)

    def test_entity_cohesion_and_sidecar_binding_guards(self):
        items = []
        points = []
        for idx in range(5):
            did = f"TraitMech:r{idx}:d{idx}" if idx < 3 else f"CommunityMech:r{idx}:d{idx}"
            mech = "TraitMech" if idx < 3 else "CommunityMech"
            items.append({
                "id": did,
                "mech": mech,
                "record_id": f"{mech}:r{idx}",
                "record_label": f"Record {idx}",
                "prompt": f"How does siderophore uptake operate in case {idx}?",
                "rationale": "Mechanism remains open.",
                "kind": "KNOWLEDGE_GAP",
                "status": "OPEN",
                "lane": "recorded",
                "attaches_to": [],
                "evidence": [],
                "evidence_refs": [],
                "proposed_experiments": [],
                "source": {"url": f"https://github.com/CultureBotAI/{mech}/blob/" + "1" * 40 + f"/{idx}.yaml"},
            })
        for idx in range(5):
            did = items[idx]["id"]
            other = items[(idx + 1) % 4]["id"] if idx < 4 else items[0]["id"]
            neighbors = [{"id": other, "cosine_similarity": 0.85}] if idx < 4 else []
            points.append({
                "id": did,
                "x": float(idx),
                "y": float(idx) * 0.5,
                "input_sha256": f"{idx:064x}",
                "token_count": 12,
                "chunk_count": 1,
                "neighbors": neighbors,
            })
        snapshot = {"schema_version": 1, "items": items}
        build_id = canonical_digest(snapshot)
        term_doc = {
            "schema_version": 1,
            "build_id": build_id,
            "terms": [{
                "id": "term-siderophore",
                "label": "siderophore",
                "canonical_id": "CHEBI:26672",
                "entity_refs": [{"mech": "CofactorMech", "record_id": "CHEBI:26672"}],
                "postings": [{"discussion_id": item["id"], "count": 1} for item in items],
            }],
        }
        terms_sha = canonical_digest(term_doc)
        emb_doc = {
            "schema_version": 1,
            "build_id": build_id,
            "terms_sha256": terms_sha,
            "inputs_sha256": "c" * 64,
            "points": points,
        }
        doc = analytics.build_analytics_document(snapshot, term_doc, emb_doc)
        self.assertEqual(doc["terms_sha256"], terms_sha)
        self.assertEqual(doc["embedding_inputs_sha256"], "c" * 64)
        cohesion = doc["embedding_bridges"]["entity_cohesion"]
        self.assertEqual(len(cohesion), 1)
        self.assertEqual(cohesion[0]["id"], "term-siderophore")
        self.assertEqual(cohesion[0]["discussions"], 5)
        self.assertEqual(cohesion[0]["discussion_mech_count"], 2)
        self.assertAlmostEqual(cohesion[0]["neighbor_hit_rate"], 0.8)
        self.assertAlmostEqual(cohesion[0]["within_entity_neighbor_share"], 1.0)
        self.assertAlmostEqual(cohesion[0]["mean_same_entity_cosine"], 0.85)

        bad_term = json.loads(json.dumps(term_doc))
        bad_term["build_id"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Term recognition input does not match"):
            analytics.build_analytics_document(snapshot, bad_term, None)

        bad_emb_build = json.loads(json.dumps(emb_doc))
        bad_emb_build["build_id"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Embedding bundle input does not match gap snapshot"):
            analytics.build_analytics_document(snapshot, term_doc, bad_emb_build)

        bad_emb_terms = json.loads(json.dumps(emb_doc))
        bad_emb_terms["terms_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Embedding bundle input does not match term recognition"):
            analytics.build_analytics_document(snapshot, term_doc, bad_emb_terms)

        bad_emb_inputs = json.loads(json.dumps(emb_doc))
        bad_emb_inputs["inputs_sha256"] = "not-a-sha256"
        with self.assertRaisesRegex(ValueError, "missing valid inputs_sha256"):
            analytics.build_analytics_document(snapshot, term_doc, bad_emb_inputs)


if __name__ == "__main__":
    unittest.main()
