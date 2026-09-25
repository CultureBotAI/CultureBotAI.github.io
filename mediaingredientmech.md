---
layout: default
title: "MediaIngredientMech"
description: "Autonomous knowledge factory for media ingredient ontology mappings with LLM-assisted workflows for standardizing microbial cultivation ingredient data"
permalink: /mediaingredientmech/
---

# MediaIngredientMech: Autonomous Knowledge Factory for Media Ingredients

## Overview

**MediaIngredientMech** is an autonomous knowledge factory for culture-media ingredient identity and ontology mappings, with LLM-assisted curation and human oversight. It maintains ingredient records, synonyms, mapping quality, environmental context, and an audit trail for curation decisions. [Repository overview](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/README.md).

The published browser contains **2,953 ingredients: 2,611 MAPPED, 261 UNMAPPED, 80 REJECTED, and 1 AMBIGUOUS**, giving **88% mapped coverage** after rounding. These figures were checked on September 24, 2026 against the [browser's live data index](https://culturebotai.github.io/MediaIngredientMech/data/ingredients.json).

## Explore the Published Site

- **[Ingredient browser](https://culturebotai.github.io/MediaIngredientMech/browser.html)** — search names, synonyms, and ontology identifiers; filter by source, mapping status, and mapping quality.
- **[Mapped ingredients](https://culturebotai.github.io/MediaIngredientMech/browser.html#status=MAPPED)** — browse the mapped subset.
- **[Embedding map](https://culturebotai.github.io/MediaIngredientMech/ingredient_umap.html)** and **[graph layout](https://culturebotai.github.io/MediaIngredientMech/ingredient_graph.html)** — explore ingredient relationships in KG-Microbe embedding space.

## What a Record Represents

An ingredient record identifies a practical reagent or formulation used in media. Curation distinguishes salts, hydrates, mixtures, and other forms, preserves raw names as synonyms, and records the convention used when sources are ambiguous. Mapping quality and curation status are separate fields. [Mapping semantics](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/MAPPING_SEMANTICS.md).

The current model includes:

- **Ingredient records** with identifiers, synonyms, mapping status, and curation history.
- **Ontology mappings** to ChEBI and FOODON, with quality ratings; the browser also exposes NCIT and CAS identifiers.
- **Environmental context** linked to ENVO terms with relevance qualifiers.
- **Curation events** that record provenance and LLM assistance.
- **Component relationships** for ingredients made of other components, with evidence and validation.

See the [schema reference](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/SCHEMA_REFERENCE.md), [environmental-context model](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/schema/environmental_context.md), and [component model](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/stock_components.md).

## Curation Workflow

Curators compare upstream recipe changes with the tracked ingredient corpus, make scoped updates with provenance, and validate ontology identifiers and labels through OAK/OLS. Ingredient occurrence counts help prioritize unmapped records. Validated mapping artifacts can then support coordinated downstream updates to [CultureMech](/culturemech/).

The former CultureMech collection writers are retired because their aggregate projections could overwrite ingredient curation. Current guidance is to review upstream changes and apply scoped updates to MIM-owned records. [Current workflow and migration status](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/README.md#use-the-curated-corpus).

## Getting Started

Development and CI use **Python 3.13**, `uv`, and `just`:

```bash
git clone https://github.com/CultureBotAI/MediaIngredientMech.git
cd MediaIngredientMech
just install
just gen-schema
just validate-all
```

For an interactive curation session:

```bash
just snapshot
just curate
just report
```

These are the repository's documented commands. See the [curation guide](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/CURATION_GUIDE.md) and [role-curation workflow](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/ROLE_CURATION_WORKFLOW.md) for record editing and validation.

## Exports and Integration

The project provides YAML records, browser JSON, generated inventories, SSSOM mappings, and a [standalone KGX ingredient graph](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/KGX_EXPORT.md). The [reviewed SSSOM release](https://github.com/CultureBotAI/MediaIngredientMech/releases/tag/mim-sssom-2026-09-21) holds 1,763 supported mappings. It keeps the 1,255 withheld mappings in a separate file. An [earlier release](https://github.com/CultureBotAI/MediaIngredientMech/releases/tag/mim-supported-2026-09-21) carries a KGX snapshot limited to supported assertions. SSSOM predicates preserve distinctions between exact, close, broader, and narrower matches. Registry identity mappings and ontology assertions have different meanings; downstream consumers should follow the [mapping contract](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/MAPPING_SEMANTICS.md).

Deep-research tools help select providers and prepare ingredient research. Their results remain curation proposals until identity and evidence are validated. [Provider workflow](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/README.md#deep-research-provider-triage).

## Repository & Documentation

- **[Repository](https://github.com/CultureBotAI/MediaIngredientMech)** and **[published site](https://culturebotai.github.io/MediaIngredientMech/)**
- **[Current mapping inventory](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/data/curated/ALL_INGREDIENTS.md)**
- **[Workflow guide](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/docs/WORKFLOWS.md)**
- **License:** CC0-1.0, as stated in the [repository](https://github.com/CultureBotAI/MediaIngredientMech/blob/dfce1c9342ca7aec41b50d0f6db8adb950bb72fe/README.md#license)

---

## Related Tools

- **[X-Mech Suite overview](/mechs/)** - All ten Mechs, their shared vocabulary and cross-references, and the culturebotai-claw orchestrator
- **[TaxonMech](https://culturebotai.github.io/TaxonMech/)** - Microbial taxa and strains grounded in NCBI Taxonomy, harmonized with GTDB, LPSN and BacDive
- **[HabitatMech](https://culturebotai.github.io/HabitatMech/)** - Habitats harmonized from GOLD, BacDive, PREGO and Madin et al. into ontology-grounded records
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[TraitMech](https://culturebotai.github.io/TraitMech/)** - Autonomous knowledge factory for microbial ecophysiological traits
- **[CellStructureMech](https://culturebotai.github.io/CellStructureMech/)** - Microbial cell structures, between the trait and protein layers
- **[ProteinTraitsMech](https://culturebotai.github.io/proteintraitsmech/)** - Protein sequence, structure, and function traits
- **[NaturalProductMech](https://culturebotai.github.io/NaturalProductMech/)** - Natural product structures with their producer organisms and gene clusters
- **[AntibioticMech](https://culturebotai.github.io/AntibioticMech/)** - Antimicrobial structures harmonizing ChEBI and CARD/ARO
- **[CultureMech](/culturemech/)** - Chemical entity extraction from media recipes (6,288 canonical media)
- **[MicroMediaParam](/resources/#micromediaparam)** - Chemical compound standardization (78% ChEBI coverage)
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Contact & Collaboration

For questions about MediaIngredientMech or to contribute:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory

---

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. Caufield JH, Hegde H, Emonet V, Harris NL, **Joachimiak MP**, et al. Structured Prompt Interrogation and Recursive Extraction of Semantics (SPIRES): a method for populating knowledge bases using zero-shot learning. *Bioinformatics*. 2024;40(3):btae104. [doi:10.1093/bioinformatics/btae104](https://doi.org/10.1093/bioinformatics/btae104) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10924283/)
3. METPO: Microbial Ecophysiological Trait and Phenotype Ontology. [BioPortal](https://bioportal.bioontology.org/ontologies/METPO) · [GitHub](https://github.com/berkeleybop/metpo)
{: .bibliography}

[Full publication list →](/publications/#bibliography)
