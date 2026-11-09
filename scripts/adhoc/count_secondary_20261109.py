#!/usr/bin/env python3
"""Recount secondary card and explanatory figures for the November 9 refresh PR.

Inputs: clean pinned snapshot records, using existing fleet record globs.
Outputs: JSON receipts (counts, exact field definitions and pin provenance).
These are descriptive counters; they do not alter census/overlap methodology.
Date: 2026-11-09. Use --only TraitMech for the persisted-output canary.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import roots


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--only")
    args = parser.parse_args()
    roots.MECHS_ROOT = str(args.snapshot / "mechs")
    os.environ["MECHS_ROOT"] = roots.MECHS_ROOT
    os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"
    os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
    os.environ["XDG_CONFIG_HOME"] = "/tmp"
    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]
    names = [
        "TraitMech",
        "CellStructureMech",
        "PathwayMech",
        "CMMMech",
        "MediaIngredientMech",
        "AntibioticMech",
        "NaturalProductMech",
        "CommunityMech",
        "HabitatMech",
        "AIMech",
    ]
    output = {}
    for name in names:
        if args.only and name != args.only:
            continue
        counts = Counter()
        statuses, categories, material_kinds = Counter(), Counter(), Counter()
        taxa, references = set(), set()
        for path in roots.record_paths(name):
            text = Path(path).read_text()
            doc = yaml.load(text, Loader=yaml.CSafeLoader)
            counts["records"] += 1
            statuses[
                str(doc.get("curation_status", doc.get("mapping_status", doc.get("status"))))
            ] += 1
            category_key = {
                "TraitMech": "trait_category",
                "CellStructureMech": "structure_category",
                "HabitatMech": "habitat_category",
                "CommunityMech": "community_type",
            }.get(name, "category")
            categories[str(doc.get(category_key))] += 1
            material_kinds[str(doc.get("material_kind"))] += 1
            graphs = doc.get("causal_graphs") or []
            counts["inline_graph_records"] += bool(graphs)
            counts["inline_graphs"] += len(graphs)
            counts["component_records"] += bool(doc.get("components"))
            counts["history_records"] += bool(doc.get("curation_history"))
            counts["history_events"] += len(doc.get("curation_history") or [])
            counts["mechanism_records"] += bool(doc.get("mechanisms"))
            counts["mechanisms"] += len(doc.get("mechanisms") or [])
            counts["mechanistic_edges"] += len(doc.get("mechanistic_edges") or [])
            counts["ncbitaxon_mention_records"] += bool(re.search(r"NCBITaxon:\d+", text))
            counts["chebi_mention_records"] += bool(re.search(r"CHEBI:\d+", text))
            counts["mode_of_action_records"] += bool(doc.get("mode_of_action"))
            counts["molecular_target_records"] += bool(doc.get("molecular_targets"))
            counts["biosynthetic_pathway_records"] += bool(doc.get("biosynthetic_pathway"))
            if name == "MediaIngredientMech":
                community_synonym = any(
                    s.get("source") == "communitymech-unmapped"
                    for s in doc.get("synonyms") or []
                    if isinstance(s, dict)
                )
                counts["community_synonym_records"] += community_synonym
                counts["community_synonym_with_source_id_records"] += (
                    community_synonym and "source_id=communitymech.ingredient:" in text
                )
            if name == "HabitatMech":
                counts["trait_nodes"] += sum(n.get("node_type") == "TRAIT" for n in nodes(doc))
                sources = {
                    a.get("source")
                    for a in (doc.get("source_attestations") or [])
                    if isinstance(a, dict) and a.get("source")
                }
                counts["attested_by_at_least_2_sources"] += len(sources) >= 2
            if name == "AntibioticMech":
                ident = str(doc.get("identifier", ""))
                is_minted = ident.lower().startswith("antibioticmech:")
                counts["minted_ids"] += is_minted
                counts["grounded_ids"] += not is_minted
            if name == "NaturalProductMech":
                counts["antibiotic_linked_records"] += any(
                    link.get("corpus") == "AntibioticMech"
                    for link in doc.get("related_records") or []
                )
                refs = doc.get("causal_graph_refs") or []
                counts["referenced_graphs"] += len(refs)
                counts["all_graph_records"] += bool(graphs or refs)
                counts["occurrence_records"] += bool(doc.get("occurrences"))
                counts["producer_claims"] += len(doc.get("producer_organisms") or [])
                counts["producer_records"] += bool(doc.get("producer_organisms"))
                counts["biosynthetic_gene_cluster_records"] += bool(
                    doc.get("biosynthetic_gene_clusters")
                )
                counts["bioactivity_records"] += bool(doc.get("bioactivities"))
            if name == "CellStructureMech":
                counts["go_ids"] += str(doc.get("identifier", "")).startswith("GO:")
                counts["graph_edges"] += sum(len(g.get("edges") or []) for g in graphs)
            if name == "PathwayMech":
                for item in doc.get("taxa") or []:
                    if isinstance(item, dict):
                        taxa.add(item.get("id"))
                for item in doc.get("references") or []:
                    if isinstance(item, dict):
                        references.add(item.get("id"))
                for item in nodes(doc):
                    counts["source_assertions"] += bool(item.get("source_assertion"))
                    counts["quoted_evidence_items"] += bool(item.get("quote"))
                    counts["evidence_items"] += len(item.get("evidence") or [])
        output[name] = {
            "pin": pins[name]["sha"],
            "counts": dict(counts),
            "statuses": dict(statuses),
            "categories": dict(categories),
            "material_kinds": dict(material_kinds),
            "distinct_top_level_taxa_ids": len(taxa - {None}),
            "distinct_top_level_reference_ids": len(references - {None}),
        }
        print(name, json.dumps(output[name], sort_keys=True), flush=True)
    out_dir = ROOT / "_fleet/reviews/refresh-20261109"
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / ("secondary-" + (args.only or "fleet") + ".json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    assert destination.stat().st_size > 100
    print(f"VERIFIED nonempty receipt: {destination}")


if __name__ == "__main__":
    main()
