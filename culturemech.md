---
layout: default
title: "CultureMech"
description: "Autonomous knowledge factory for microbial culture media: 15,878 curated recipes from major international repositories, deduplicated into 6,286 canonical media, with LinkML schema, ontology grounding, and browser-based exploration"
permalink: /culturemech/
---

# CultureMech: Autonomous Knowledge Factory for Culture Media

## Overview

**CultureMech** is an autonomous knowledge factory for microbial culture media, combining ontology grounding, validation, provenance, and recipe deduplication with human oversight. Its current repository holds **15,878 normalized records** and **6,286 merged canonical media**. Normalized records preserve each source's formulation; merged records provide the deduplicated view. [Repository snapshot](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/README.md#corpus-snapshot).

## Explore the Published Site

- **[Recipe browser](https://culturebotai.github.io/CultureMech/app/browser.html)** — search source-specific recipes and filter by category, medium type, physical state, target organism, and ingredients.
- **[Ingredient-derived media map](https://culturebotai.github.io/CultureMech/app/umap.html#umap-derived)** — explore media using aggregated ingredient embeddings.
- **[Direct media map](https://culturebotai.github.io/CultureMech/app/umap.html#umap-direct)** — explore the medium nodes' own KG-Microbe embeddings.
- **[Graph layout](https://culturebotai.github.io/CultureMech/app/umap_graph.html)** — another view of media similarity.

Counts and links were checked on September 20, 2026. The published landing page still displays a legacy recipe total; the counts above come from the current repository's generated corpus inventory.

## Data Architecture

| Layer | Location | Purpose |
|---|---|---|
| Raw sources | `data/raw/` | Original source payloads |
| Raw YAML | `data/raw_yaml/` | Source-shaped conversions |
| Normalized records | `data/normalized_yaml/` | Authoritative source-specific curation and browser input |
| Merged records | `data/merge_yaml/merged/` | Reproducible deduplicated media |

Source imports include MediaDive/DSMZ, TogoMedium, KOMODO, and collection-specific recipes. The normalized inventory contains 14,305 bacterial, 743 archaeal, 249 algal, 126 fungal, and 455 specialized records. These categories sum to the normalized total, not the canonical total. [Data layers](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/docs/DATA_LAYERS.md).

## Curation and Validation

Records carry ingredient amounts, ontology identifiers and labels, source references, and curation history. The LinkML schema separates composition type, nutritional class, and functional role while retaining the compatibility `medium_type` field. Validation checks schema shape, stricter record invariants, and recipe identifiers.

[MediaIngredientMech](/mediaingredientmech/) supplies ingredient identity and mapping artifacts. CultureMech retains recipe-specific composition and provenance. These structured outputs support downstream knowledge-graph integration, comparative media analysis, and cultivation research. [Schema](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/src/culturemech/schema/culturemech.yaml) · [Curation guide](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/docs/CONTRIBUTING.md).

## Example: A Tracked Recipe

The repository's [LB medium record](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/data/normalized_yaml/bacterial/lb_medium.yaml) has the stable identifier `CultureMech:008037` and preserves its TogoMedium/NBRC source. Its sodium-chloride ingredient illustrates the actual nested record format:

```yaml
preferred_term: NaCl
concentration:
  value: '5'
  unit: G_PER_L
source: NBRC Medium 275
term:
  id: CHEBI:26710
  label: sodium chloride
```

This is an ingredient excerpt; the complete recipe also contains other ingredients, medium classification, source details, and history.

## Getting Started

Development and CI use **Python 3.13**, `uv`, and `just`. The current checkout workflow is:

```bash
git clone https://github.com/CultureBotAI/CultureMech.git
cd CultureMech
uv sync --frozen --extra dev
just validate-schema data/normalized_yaml/bacterial/lb_medium.yaml
just test-fast
```

To generate local outputs:

```bash
just build-browser
just gen-pages
just gen-media-pages
just serve-browser
```

For one recipe, use `just gen-page data/normalized_yaml/bacterial/lb_medium.yaml`; the result is written under `pages/single/`. See the [current quick start](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/docs/QUICK_START.md) for the full workflow.

## Repository & Documentation

- **[Repository](https://github.com/CultureBotAI/CultureMech)** and **[published site](https://culturebotai.github.io/CultureMech/)**
- **[Recipe identifier lifecycle](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/docs/RECIPE_ID_LIFECYCLE.md)**
- **[Citation metadata](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/CITATION.cff)**
- **License:** [CC0-1.0](https://github.com/CultureBotAI/CultureMech/blob/866b335301a53838c2868515e68ec96a11528f17/LICENSE)

---

## Related Tools

- **[X-Mech Suite overview](/mechs/)** - All ten Mechs, their shared vocabulary and cross-references, and the culturebotai-claw orchestrator
- **[TaxonMech](https://culturebotai.github.io/TaxonMech/)** - Microbial taxa and strains grounded in NCBI Taxonomy, harmonized with GTDB, LPSN and BacDive
- **[HabitatMech](https://culturebotai.github.io/HabitatMech/)** - Habitats harmonized from GOLD, BacDive, PREGO and Madin et al. into ENVO-grounded records
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[TraitMech](https://culturebotai.github.io/TraitMech/)** - Autonomous knowledge factory for microbial ecophysiological traits
- **[CellStructureMech](https://culturebotai.github.io/CellStructureMech/)** - Microbial cell structures, between the trait and protein layers
- **[ProteinTraitsMech](https://culturebotai.github.io/proteintraitsmech/)** - Protein sequence, structure, and function traits
- **[NaturalProductMech](https://culturebotai.github.io/NaturalProductMech/)** - Natural product structures with their producer organisms and gene clusters
- **[AntibioticMech](https://culturebotai.github.io/AntibioticMech/)** - Antimicrobial structures harmonizing ChEBI and CARD/ARO
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient ontology mapping
- **[MicroMediaParam](/resources/#micromediaparam)** - Chemical compound standardization and ChEBI mapping
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Research Impact

CultureMech is part of the [KG-Microbe knowledge graph](/kg-microbe/) ecosystem developed at Lawrence Berkeley National Laboratory. It supports:

- Data-driven cultivation optimization
- AI-powered growth prediction
- Systematic analysis of microbial growth requirements
- Evidence-based media design for novel organisms

**Citation**: See the [KG-Microbe publication](https://doi.org/10.1093/gigascience/giag077) in *GigaScience* for details on the broader knowledge graph ecosystem.

---

## Contact & Collaboration

For questions about CultureMech or collaboration opportunities:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory

---

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. Máša P, Kliegr T, **Joachimiak MP**. Explainable rule-based prediction of cultivation media for microbes. *Computational and Structural Biotechnology Journal*. 2025;27:5194–5206. [doi:10.1016/j.csbj.2025.10.014](https://doi.org/10.1016/j.csbj.2025.10.014) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12670597/)
3. METPO: Microbial Ecophysiological Trait and Phenotype Ontology. [BioPortal](https://bioportal.bioontology.org/ontologies/METPO) · [GitHub](https://github.com/berkeleybop/metpo)
{: .bibliography}

[Full publication list →](/publications/#bibliography)
