"""Term-linking semantics and source spans for the gap explorer, 2026-11-15."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("gap_terms", Path(__file__).parents[1] / "scripts/gaps/terms.py")
terms = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(terms)
AUDIT_SPEC = importlib.util.spec_from_file_location("gap_term_audit", Path(__file__).parents[1] /
                                                   "scripts/adhoc/report_gap_terms_20261115.py")
audit = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit)


def entity(key, label, aliases=(), canonical_id=None, mech="TraitMech"):
    return {"id": key, "record_id": "Local:" + key, "canonical_id": canonical_id or "Local:" + key,
            "mech": mech, "label": label, "aliases": list(aliases),
            "source": {"repository": "CultureBotAI/" + mech, "revision": "a" * 40,
                       "path": "data/" + key + ".yaml", "sha256": "b" * 64,
                       "url": "https://github.com/CultureBotAI/" + mech + "/blob/" + "a" * 40 + "/data/" + key + ".yaml",
                       "license": "CC-BY-4.0"}}


def item(key, prompt, **fields):
    return {"id": key, "prompt": prompt, "rationale": "", "resolution_note": "",
            "evidence": [], "proposed_experiments": [], "mech": "TraitMech", **fields}


def native_entity(record_id, label, aliases=(), mech="ProteinTraitsMech"):
    row = entity(record_id, label, aliases, canonical_id=record_id, mech=mech)
    row["record_id"] = record_id
    return row


def inputs(items, entities):
    snapshot = {"schema_version": 1, "source_config_sha256": "c" * 64, "items": items}
    vocabulary = {"schema_version": 1, "snapshot_sha256": terms._digest(snapshot),
                  "source_config_sha256": snapshot["source_config_sha256"], "sources": [], "terms": entities}
    return snapshot, vocabulary


def build(items, entities):
    return terms.build_term_document(*inputs(items, entities))


class GapTermTests(unittest.TestCase):
    def test_repeated_mentions_and_copied_fields_are_raw_occurrences(self):
        doc = build([item("d1", "Iron, iron and iron.", rationale="iron"), item("d2", "iron")],
                    [entity("iron", "iron")])
        self.assertEqual([p["count"] for p in doc["terms"][0]["postings"]], [4, 1])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 5)
        self.assertEqual(doc["summary"]["discussions_with_terms"], 2)

    def test_owning_metadata_does_not_manufacture_mentions(self):
        row = item("d", "Question?", record_label="iron", aliases=["iron"], record_id="iron",
                   attaches_to=["iron"], evidence_refs=["iron"], source={"url": "iron"})
        self.assertEqual(build([row], [entity("iron", "iron")])["terms"], [])

    def test_full_detail_fields_match_without_reference_metadata(self):
        row = item("d", "Question?", resolution_note="iron",
                   evidence=[{"reference": "iron", "explanation": "iron"}],
                   proposed_experiments=[{"experiment_id": "iron", "name": "iron",
                                          "model_systems": ["iron"], "readouts": ["iron"]}])
        posting = build([row], [entity("iron", "iron")])["terms"][0]["postings"][0]
        self.assertEqual(posting["count"], 5)
        self.assertNotIn("experiment_id", " ".join(m["field"] for m in posting["mentions"]))

    def test_word_boundaries_and_leftmost_longest_overlap(self):
        doc = build([item("d", "anaerobic; aerobic growth; aerobic.")],
                    [entity("a", "aerobic"), entity("g", "aerobic growth")])
        by_label = {term["label"]: term for term in doc["terms"]}
        self.assertEqual(by_label["aerobic"]["postings"][0]["count"], 1)
        self.assertEqual(by_label["aerobic growth"]["postings"][0]["count"], 1)

    def test_ambiguous_long_phrase_suppresses_nested_fallback(self):
        doc = build([item("d", "iron transport")],
                    [entity("i", "iron"), entity("t1", "iron transport"), entity("t2", "iron transport")])
        self.assertEqual(doc["terms"], [])
        self.assertEqual(doc["summary"]["ambiguous_occurrences"], 1)

    def test_alias_collision_is_not_resolved_by_owning_mech(self):
        doc = build([item("d", "transport")],
                    [entity("t", "trait", ["transport"]), entity("p", "protein", ["transport"], mech="ProteinTraitsMech")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 0)
        self.assertEqual(len(doc["ambiguities"][0]["candidate_ids"]), 2)

    def test_exact_canonical_curie_groups_documents_and_explicit_cofactor_identity(self):
        doc = build([item("d", "biotin biotin")],
                    [entity("mim", "biotin", canonical_id="CHEBI:15956", mech="MediaIngredientMech"),
                     entity("cofactor", "Biotin", canonical_id="chebi:15956", mech="CofactorMech")])
        self.assertEqual(len(doc["terms"]), 1)
        term = doc["terms"][0]
        self.assertEqual(term["canonical_id"], "CHEBI:15956")
        self.assertEqual(len(term["entity_refs"]), 2)
        self.assertEqual(term["postings"][0]["count"], 2)

    def test_unknown_or_local_ids_do_not_merge_across_sources(self):
        doc = build([item("d", "biotin")],
                    [entity("one", "biotin", canonical_id="local:one"),
                     entity("two", "biotin", canonical_id="local:one")])
        self.assertEqual(doc["terms"], [])
        self.assertEqual(doc["summary"]["ambiguous_occurrences"], 1)

    def test_short_acronyms_are_case_sensitive_and_common_words_excluded(self):
        doc = build([item("d", "ATP atp Atp In in As as At at He he May may lead unknown unclassified")],
                    [entity("atp", "ATP"), *[entity(word, word) for word in
                                             ("In", "As", "At", "He", "May", "lead", "unknown", "unclassified")]])
        self.assertEqual([term["label"] for term in doc["terms"]], ["ATP"])
        self.assertEqual(doc["terms"][0]["postings"][0]["count"], 1)
        self.assertEqual(doc["summary"]["case_rejected_occurrences"], 2)
        self.assertIn("lead", doc["summary"]["excluded_forms"])

    def test_short_symbols_excluded_but_explicit_ids_and_long_names_work(self):
        doc = build([item("d", "Fe Fe3+ iron(III) CHEBI:123")],
                    [entity("iron", "iron(III)", ["Fe"], canonical_id="CHEBI:123")])
        self.assertEqual(doc["terms"][0]["postings"][0]["count"], 2)

    def test_ordinary_reduces_does_not_assert_biochemical_redox_relation(self):
        # #584: retained TraitMech SDIC4 rationale uses "reduces phage adsorption",
        # while METPO:2000017 specifically denotes reduction of a chemical substrate.
        doc = build([item("d", "SDIC4 reduces phage adsorption. Which partner reduces each carboxylate? "
                               "The explicit relation is METPO:2000017.")],
                    [entity("redox", "reduces", canonical_id="METPO:2000017")])
        posting = doc["terms"][0]["postings"][0]
        self.assertEqual(posting["count"], 1)
        self.assertEqual(posting["mentions"][0]["text"], "METPO:2000017")
        self.assertIn("reduces", doc["summary"]["excluded_forms"])
        self.assertIn("negated", doc["policy"]["interpretation"])

    def test_generic_verbs_do_not_assert_specific_metabolic_properties(self):
        # #586: imports of synonymy, assembly of arrays, and extracellular
        # accumulation do not establish the specific intracellular predicates.
        doc = build([item("d", "This pass imports GO synonymy. Hrs1 produces arrays. "
                               "A metabolite accumulates during fermentation. METPO:2000208")],
                    [entity("import", "imports", canonical_id="METPO:2000208"),
                     entity("produce", "produces", canonical_id="METPO:2000202"),
                     entity("accumulate", "accumulates", canonical_id="METPO:2000210")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 1)
        self.assertEqual(doc["terms"][0]["postings"][0]["mentions"][0]["text"], "METPO:2000208")

    def test_numeric_only_native_forms_do_not_link_measurements_or_issue_numbers(self):
        # #590: source-derived forms from the retained MIM and Culture vocabularies.
        doc = build([item("d", "100 mbar CO; issue #815; 1728. CHEBI:9177 CultureMech:002824")],
                    [native_entity("CHEBI:9177", "sodium Deoxycholate", ["100"], "MediaIngredientMech"),
                     native_entity("CultureMech:002824", "TRYPTICASE SOY BROTH AGAR", ["815"], "CultureMech"),
                     native_entity("CHEBI:16199", "Urea", ["1728"], "MediaIngredientMech")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 2)
        self.assertTrue({"100", "815", "1728"}.issubset(doc["summary"]["excluded_forms"]))
        self.assertEqual({m["text"] for t in doc["terms"] for p in t["postings"] for m in p["mentions"]},
                         {"CHEBI:9177", "CultureMech:002824"})

    def test_internal_capital_gene_symbols_preserve_case_without_losing_full_names(self):
        # #591: native NCBIfam symbols are not the ordinary English words.
        doc = build([item("d", "part Part coat mode parT coaT modE choice-of-anchor T family protein")],
                    [native_entity("NCBIfam:NF049844", "type II RES/Xre toxin-antitoxin system toxin", ["parT"]),
                     native_entity("NCBIfam:NF041740", "choice-of-anchor T family protein", ["coaT"]),
                     native_entity("NCBIfam:NF007957", "molybdenum-dependent transcriptional regulator", ["modE"])])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 4)
        self.assertEqual(doc["summary"]["case_rejected_occurrences"], 4)

    def test_this_family_requires_symbol_case_across_both_canonical_owners(self):
        # #605: ordinary "this family" was assigned to PF02597 by both vocabularies.
        entries = [entity("this-" + mech, "ThiS family", ["ThiS"],
                          canonical_id="Pfam:PF02597", mech=mech)
                   for mech in ("DUFMech", "ProteinTraitsMech")]
        text = ("this family; This family; THIS family; thiS family; "
                "ThiS family; ThiS Family; ThiS FAMILY; ThiS\nfamily; "
                "Pfam:PF02597; ThiS; this.")
        doc = build([item("d", text)], entries)
        self.assertEqual(len(doc["terms"]), 1)
        term = doc["terms"][0]
        self.assertEqual(term["canonical_id"], "PFAM:PF02597")
        self.assertEqual({ref["mech"] for ref in term["entity_refs"]},
                         {"DUFMech", "ProteinTraitsMech"})
        self.assertEqual([mention["text"] for mention in term["postings"][0]["mentions"]],
                         ["ThiS family", "ThiS Family", "ThiS FAMILY", "ThiS\nfamily", "Pfam:PF02597"])
        self.assertEqual(doc["summary"]["case_rejected_occurrences"], 4)
        self.assertIn("ThiS", doc["summary"]["excluded_forms"])

    def test_this_family_rule_preserves_unrelated_descriptive_label_case_folding(self):
        entries = [entity("primase", "DnaG Primase"),
                   entity("rnase", "Wobble nucleotide-excising tRNase")]
        doc = build([item("d", "DnaG primase; wobble nucleotide-excising tRNase")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 2)

    def test_source_scoped_denials_keep_full_names_ids_and_collision_blocking(self):
        # #592: native synonyms are retained as blocked candidates, so denying
        # one sense must not silently assign that span to a competing concept.
        entries = [native_entity("ENVO:00000084", "mountain pass", ["pass"], "HabitatMech"),
                   native_entity("ENVO:00000020", "lake", ["broad"], "HabitatMech"),
                   native_entity("ENVO:01000910", "soil biocrust", ["Biological"], "HabitatMech"),
                   native_entity("UBERON:0006726", "outer canthus", ["Outer"], "HabitatMech"),
                   native_entity("MI:1110", "predicted interaction", ["predicted"]),
                   entity("competing", "pass"), entity("valid", "broad host range")]
        doc = build([item("d", "first pass; too broad; biological assignment; outer ring; predicted peptide. "
                               "mountain pass; lake; soil biocrust; outer canthus; predicted interaction; "
                               "ENVO:00000084; broad host range")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 7)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 5)
        self.assertNotIn("pass", [term["label"] for term in doc["terms"]])
        self.assertIn("broad host range", [term["label"] for term in doc["terms"]])
        self.assertEqual(len(doc["summary"]["denied_surfaces"]), 5)

    def test_specific_groups_and_pathways_require_ids_for_underspecified_labels(self):
        # #593/#594: pinned source definitions distinguish an ortholog group,
        # viral pathways and morphology from the retained ordinary contexts.
        entries = [native_entity("OrthoDB:110285at2759", "protein"),
                   native_entity("Reactome:R-HSA-168298", "Release"),
                   native_entity("Reactome:R-HSA-168302", "Budding"),
                   native_entity("PATO:0000141", "structure"),
                   entity("family", "protein family")]
        prose = "bacterial protein; nitrogen release; budding yeast; graph outcome structure; protein family. "
        doc = build([item("d", prose + " ".join(row["record_id"] for row in entries[:4]))], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 5)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 4)
        self.assertIn("protein family", [term["label"] for term in doc["terms"]])
        for term in doc["terms"]:
            if term["label"] != "protein family":
                self.assertEqual(term["postings"][0]["mentions"][0]["text"], term["entity_refs"][0]["record_id"])

    def test_default_cloud_homonyms_retain_specific_names_and_identifiers(self):
        # #596: retained figure/cache, disease-suppression and ion contexts.
        entries = [native_entity("Pfam:CL0165", "Cache"),
                   native_entity("NCIT:C71971", "Fig", mech="MediaIngredientMech"),
                   native_entity("MI:0796", "genetic suppression (sensu unexpected)", ["suppression"]),
                   native_entity("ENVO:01001069", "metallic material", ["metal"], "HabitatMech")]
        doc = build([item("d", "Reviewed cache; Fig. 7b; Fusarium suppression; dissolved metal ions. "
                               "Pfam:CL0165 NCIT:C71971 genetic suppression (sensu unexpected) metallic material")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 4)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 4)

    def test_broad_source_classes_and_valid_chemical_aliases_remain_recognizable(self):
        # Top-cloud sense checks found these broad native definitions applicable;
        # precision protections must not become a general stoplist for biology.
        entries = [native_entity("AIO:Model", "Model", mech="AIMech"),
                   native_entity("NCIT:C120264", "Substrate", mech="MediaIngredientMech"),
                   native_entity("proteintraitsmech:EVO_CONSERVED", "conserved protein", ["conserved"]),
                   native_entity("CHEBI:6824", "hexamethylenetetramine", ["hexamine"], "AntibioticMech")]
        doc = build([item("d", "A model of conserved protein activity uses a substrate; hexamine removal.")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 4)

    def test_followup_protein_and_source_homonyms_keep_valid_descriptions_and_ids(self):
        # #597: the final seeded/default-cloud audit uses these exact contexts.
        entries = [native_entity("EC:3.5.1.88", "peptide deformylase", ["PDF"]),
                   native_entity("UniProtKB-KW:KW-0732", "Signal", ["Signal peptide"]),
                   native_entity("PROSITE:PDOC00955", "Link"),
                   native_entity("habitatmech:GOLD.5df162af13", "Modeled", mech="HabitatMech"),
                   native_entity("ENVO:00000020", "lake", ["mere"], "HabitatMech")]
        doc = build([item("d", "author-PDF Methods; Nile Red signal; part_of link; modeled as a graph node; "
                               "Mere possession. peptide deformylase; Signal peptide; PROSITE:PDOC00955; "
                               "habitatmech:GOLD.5df162af13; lake")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 5)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 5)

    def test_top_hundred_generic_habitat_aliases_and_placeholders_are_scoped(self):
        # #597 top100 extension; full names and explicit identifiers survive.
        entries = [native_entity("ENVO:00000040", "waterfall", ["cascade", "force"], "HabitatMech"),
                   native_entity("ENVO:00002144", "cave wall", ["Wall"], "HabitatMech"),
                   native_entity("UBERON:0002183", "lobar bronchus", ["Secondary"], "HabitatMech"),
                   native_entity("ENVO:00000064", "road", ["drive", "drove"], "HabitatMech"),
                   native_entity("IDPO:0000006", "order"),
                   native_entity("NCBITaxon:32644", "unidentified", ["collection"], "TaxonMech")]
        prose = ("cascade stages; mechanical force; cell wall; secondary plastids; MAGs drive flux; "
                 "analysis order; collection provenance; unidentified protein. ")
        doc = build([item("d", prose + "waterfall; cave wall; lobar bronchus; road; IDPO:0000006; NCBITaxon:32644")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 6)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 8)

    def test_top_hundred_protein_symbols_do_not_resolve_incompatible_source_senses(self):
        # #597: source-checked chemical, defense-system and unresolved-profile
        # contexts do not establish these particular protein families/activities.
        entries = [native_entity("SCOP:46726", "Paired protein"),
                   native_entity("Pfam:PF12361", "Duffy-antigen binding protein", ["DBP"]),
                   native_entity("NCBIfam:NF045600", "sterol transporter cytoplasmic membrane protein BstA", ["BstA"]),
                   native_entity("EC:1.14.13.8", "flavin-containing monooxygenase", ["FMO"])]
        prose = "taxon-paired protein accessions; 2,4-DBP removal; BstA phage defense; unresolved Lamassu FMO. "
        doc = build([item("d", prose + "SCOP:46726; Duffy-antigen binding protein; "
                               "sterol transporter cytoplasmic membrane protein BstA; flavin-containing monooxygenase")], entries)
        self.assertEqual(doc["summary"]["accepted_occurrences"], 4)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 4)

    def test_organism_associations_do_not_identify_physical_molecular_complexes(self):
        # #597: conservative loss of valid bare pulldown mentions is explicit.
        doc = build([item("d", "persistent parasitism association; pulldown association; MI:0914")],
                    [native_entity("MI:0914", "association")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 1)
        self.assertEqual(doc["summary"]["policy_rejected_occurrences"], 2)
        self.assertEqual(doc["terms"][0]["postings"][0]["mentions"][0]["text"], "MI:0914")

    def test_chemical_punctuation_is_not_erased(self):
        doc = build([item("d", "iron(II) iron(III) iron-II")],
                    [entity("two", "iron(II)"), entity("three", "iron(III)")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 2)

    def test_unicode_source_spans_survive_ligatures_accents_whitespace_and_emoji(self):
        text = "🧪 ﬁbroblast; cafe\u0301; iron\t\n transport; 가나다."
        doc = build([item("d", text)], [entity("f", "fibroblast"), entity("c", "café"),
                                       entity("i", "iron transport"), entity("k", "가나다")])
        actual = set()
        for term in doc["terms"]:
            for mention in term["postings"][0]["mentions"]:
                self.assertEqual(text[mention["start"]:mention["end"]], mention["text"])
                actual.add(mention["text"])
        self.assertEqual(actual, {"ﬁbroblast", "cafe\u0301", "iron\t\n transport", "가나다"})

    def test_combining_marks_prevent_partial_word_matches_and_overwide_spans(self):
        # #585: noncomposing marks are outside Python re's \w, but remain part
        # of the word. A valid complete marked term must still be recognized.
        text = "iron\u0329 \u034firon iron"
        doc = build([item("d", text)], [entity("i", "iron")])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 1)
        mention = doc["terms"][0]["postings"][0]["mentions"][0]
        self.assertEqual((mention["start"], mention["end"]), (12, 16))
        self.assertEqual(terms.normalize_surface(text[mention["start"]:mention["end"]]), mention["matched_as"])
        marked = build([item("d", "iron\u0329")], [entity("marked", "iron\u0329")])
        self.assertEqual(marked["summary"]["accepted_occurrences"], 1)
        overlay = build([item("d", "iron\u0338")], [entity("i", "iron")])
        self.assertEqual(overlay["terms"], [])

    def test_placeholder_display_falls_back_to_id_without_rewriting_source_label(self):
        # #587: ComplexPortal's retained '-' native labels cannot name a cloud
        # entry; the identifier is already an explicit, provenance-backed name.
        row = entity("complex", "-", canonical_id="ComplexPortal:CPX-123")
        row["record_id"] = "ComplexPortal:CPX-123"
        doc = build([item("d", "ComplexPortal:CPX-123")], [row])
        self.assertEqual(doc["terms"][0]["label"], "ComplexPortal:CPX-123")
        self.assertEqual(doc["terms"][0]["labels"], ["-"])
        self.assertEqual(doc["terms"][0]["entity_refs"][0]["label"], "-")

    def test_regex_prefilter_preserves_collisions_provenance_and_full_match_results(self):
        records = [entity("iron", "iron", ["absent alternate phrase"], canonical_id="CHEBI:18248"),
                   entity("second", "unmentioned iron label", canonical_id="CHEBI:18248", mech="CofactorMech"),
                   entity("amb1", "collision"), entity("amb2", "collision"),
                   entity("complex", "-", ["absent alias " + str(i) for i in range(1000)])]
        snapshot, vocab = inputs([item("d", "Iron collision CHEBI:18248")], records)
        filtered = terms.build_term_document(snapshot, vocab)
        with patch.object(terms, "make_surface_prefilter", return_value=lambda _form: True):
            unfiltered = terms.build_term_document(snapshot, vocab)
        self.assertEqual(filtered, unfiltered)
        self.assertEqual(len(filtered["terms"][0]["entity_refs"]), 2)
        self.assertEqual(filtered["summary"]["ambiguous_occurrences"], 1)

    def test_identical_aliases_of_one_entity_do_not_double_count(self):
        doc = build([item("d", "iron Iron")], [entity("iron", "iron", ["iron", "Iron", "IRON"])])
        self.assertEqual(doc["summary"]["accepted_occurrences"], 2)

    def test_prefilter_is_superset_without_cross_field_fabrication(self):
        snapshot, _ = inputs([item("d", "ATP aerobic iron", rationale="transport")], [])
        possible = terms.make_surface_prefilter(snapshot)
        self.assertTrue(possible("atp"))
        self.assertTrue(possible("aerobic"))
        self.assertFalse(possible("aero"))  # A partial word cannot pass final boundaries.
        self.assertFalse(possible("iron transport"))
        self.assertFalse(possible("nonexistent"))

    def test_reproducibility_and_inputs_are_bound(self):
        snapshot, vocab = inputs([item("d", "iron")], [entity("i", "iron")])
        before = copy.deepcopy((snapshot, vocab))
        first = terms.build_term_document(snapshot, vocab)
        self.assertEqual(first, terms.build_term_document(snapshot, vocab))
        self.assertEqual((snapshot, vocab), before)
        self.assertEqual(first["build_id"], terms._digest(snapshot))
        changed = copy.deepcopy(vocab)
        changed["terms"][0]["source"]["license"] = "CC0-1.0"
        self.assertNotEqual(first["term_build_id"], terms.build_term_document(snapshot, changed)["term_build_id"])
        changed["snapshot_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "different discussion snapshot"):
            terms.build_term_document(snapshot, changed)

    def test_malformed_and_duplicate_inputs_fail(self):
        for change in (lambda v: v["terms"].append(copy.deepcopy(v["terms"][0])),
                       lambda v: v["terms"][0].update(aliases=[{}]),
                       lambda v: v["terms"][0].update(source={})):
            snapshot, vocab = inputs([item("d", "iron")], [entity("i", "iron")])
            change(vocab)
            with self.assertRaises(ValueError):
                terms.build_term_document(snapshot, vocab)
        with self.assertRaisesRegex(ValueError, "Discussion IDs"):
            build([item("d", "iron"), item("d", "iron")], [entity("i", "iron")])

    def test_pair_counts_use_distinct_discussions_after_scope_selection(self):
        doc = build([item("one", "iron iron sulfur"), item("two", "iron sulfur sulfur")],
                    [entity("i", "iron"), entity("s", "sulfur")])
        all_scope = audit.summarize(doc, {"one", "two"})
        self.assertEqual(all_scope["accepted_occurrences"], 6)
        self.assertEqual(all_scope["top_20_pairs"][0]["discussions"], 2)
        self.assertEqual(audit.summarize(doc, {"two"})["top_20_pairs"][0]["discussions"], 1)

    def test_diagnostic_pairs_use_the_browser_top_twenty_term_universe(self):
        rows = [item(str(i), f"entity{i:02} entity{i:02}") for i in range(20)]
        rows.append(item("pair", "entity00 entity20"))
        doc = build(rows, [entity(str(i), f"entity{i:02}") for i in range(21)])
        report = audit.summarize(doc, {row["id"] for row in rows})
        self.assertEqual(len(report["pair_universe_term_ids"]), 20)
        self.assertEqual(report["top_20_pairs"], [])

    def test_diagnostic_validates_actual_artifacts_and_rejects_wrong_spans(self):
        snapshot, vocab = inputs([item("d", "iron iron", kind="KNOWLEDGE_GAP", status="OPEN",
                                      lane="recorded", source={"url": "https://example.org/source"})],
                                 [entity("i", "iron")])
        doc = terms.build_term_document(snapshot, vocab)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def write(name, payload):
                data = terms._json_bytes(payload)
                (root / name).write_bytes(data)
                return {"url": name, "sha256": hashlib.sha256(data).hexdigest()}

            manifest = {"build_id": doc["build_id"], "terms": write("terms.json", doc),
                        "index": write("index.json", {"items": snapshot["items"]})}
            report = audit.audit(snapshot, vocab, manifest, root)
            self.assertTrue(report["verified"]["all_unicode_codepoint_spans"])
            self.assertEqual(report["default_scope"]["accepted_occurrences"], 2)
            self.assertEqual(json.loads(json.dumps(report))["all_scope"]["accepted_occurrences"], 2)
            doc["terms"][0]["postings"][0]["mentions"][0]["start"] = 1
            manifest["terms"] = write("terms.json", doc)
            with self.assertRaisesRegex(ValueError, "span"):
                audit.audit(snapshot, vocab, manifest, root)


if __name__ == "__main__":
    unittest.main()
