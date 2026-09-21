---
layout: default
title: "CommunityMech"
description: "Autonomous knowledge factory for microbial communities, using LinkML-based modeling with evidence-based ecological interactions for consortium design and multi-organism cultivation"
permalink: /communitymech/
---

# CommunityMech: Autonomous Knowledge Factory for Microbial Communities

## Overview

**CommunityMech** is an autonomous knowledge factory for microbial community composition, ecological interactions, cultivation conditions, environments, and supporting evidence, with human oversight. Canonical YAML records feed schema validation, static browsing, and graph exports. [Repository overview](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md).

The repository contains **392 community records** and **four additional isolate records**. The published site lists **392 communities across 16 categories**, checked on September 20, 2026. Its landing page also advertises **512-dimensional v3 embeddings**; the embedding views are separate derived artifacts and can cover a different set of records from the current browser. [Published site](https://culturebotai.github.io/CommunityMech/).

## Explore the Published Site

- **[Record browser](https://culturebotai.github.io/CommunityMech/browser.html)** — filter communities by category, ecological state, metals, and rare-earth elements.
- **[PaCMAP embedding map](https://culturebotai.github.io/CommunityMech/community_umap.html)** — explore similarity based on community taxonomic composition.
- **[Graph layout](https://culturebotai.github.io/CommunityMech/community_graph.html)** — explore another layout of the community embedding space.

## Data Architecture

| Location | Contents |
|---|---|
| `kb/communities/` | Canonical microbial community records |
| `data/isolates/` | Additional records using the community schema |
| `kb/taxa/` | Reusable taxon, genome, and gene records |
| `references_cache/` | Source text used by evidence checks |
| `history/` | Append-only curation provenance |
| `docs/` | Published HTML and maintainer documentation |

A community record can describe taxonomic membership, functional roles, environmental context, cultivation conditions, and directed ecological interactions. Ontology identifiers are paired with labels, and evidence is attached to the assertions it supports. Schema validation checks structure; literature validation separately checks evidence against source text. [Validation and evidence workflow](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md#validate-records).

## Example: A Curated Community

The [Yogurt Two-Species Starter Culture record](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/kb/communities/Yogurt_TwoSpecies_Starter_Culture.yaml), `CommunityMech:000164`, documents *Streptococcus thermophilus* and *Lactobacillus delbrueckii* subsp. *bulgaricus*. It records cross-feeding interactions with taxon and metabolite identifiers and supporting literature.

The [README's schema-validated example](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md#schema-valid-example) shows how that record represents membership, formate exchange, and evidence. Use the linked YAML for the complete current record.

## Getting Started

Development and CI use **Python 3.13**, `uv`, and `just`. Run commands from a source checkout:

```bash
git clone https://github.com/CultureBotAI/CommunityMech.git
cd CommunityMech
just install
just test
```

Validate a tracked community:

```bash
community_record=kb/communities/Yogurt_TwoSpecies_Starter_Culture.yaml
just validate "$community_record"
just validate-strict "$community_record"
just validate-gtdb "$community_record"
just validate-gtdb-domain "$community_record"
just validate-terms "$community_record"
```

Evidence checking is a separate step and may use network access:

```bash
just validate-references-explained "$community_record"
```

The repository documents a corpus-wide evidence-repair backlog. A structurally valid record does not by itself establish that all of its scientific assertions have been verified. [Current validation status](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md#validate-records).

## Generate Pages and Graph Exports

```bash
just gen-html
just check-docs-current
just gen-browser
just kgx-export
just kgx-validate
```

GitHub Pages serves the committed `docs/` tree. Update community YAML or rendering templates before regenerating derived HTML. Embedding-map generation additionally needs the local embedding artifact described in the [visualization guide](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/docs/UMAP_VISUALIZATION.md).

The KGX exporter writes `nodes.tsv`, `edges.tsv`, and `manifest.json` under `output/kgx/`; release artifacts compress the two TSV files. Edges carry deterministic identifiers, relation predicates, source attribution, and available publication/supporting-text evidence. These exports support downstream graph integration and community analysis. [KGX contract](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md#kgx-downstream-contract).

## Integration with the X-Mech Suite

Community records can refer to [CultureMech](/culturemech/) media and [MediaIngredientMech](/mediaingredientmech/) ingredients. CommunityMech contributes structured community evidence for downstream consortium research, including [PFASCommunityAgents](/resources/#pfascommunityagents). Consult each downstream project's documentation for its supported integration interface.

## Repository & Documentation

- **[Repository](https://github.com/CultureBotAI/CommunityMech)** and **[published site](https://culturebotai.github.io/CommunityMech/)**
- **[Schema](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/src/communitymech/schema/communitymech.yaml)**
- **[Curation workflow](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/README.md#curation-workflow)**
- **License:** [BSD-3-Clause](https://github.com/CultureBotAI/CommunityMech/blob/f4c11ab38ae39b9a50abe194ef69b1fc4ec007f2/LICENSE)

---

## Related Tools

- **[X-Mech Suite overview](/mechs/)** - All ten Mechs, their shared vocabulary and cross-references, and the culturebotai-claw orchestrator
- **[TaxonMech](https://culturebotai.github.io/TaxonMech/)** - Microbial taxa and strains grounded in NCBI Taxonomy, harmonized with GTDB, LPSN and BacDive
- **[HabitatMech](https://culturebotai.github.io/HabitatMech/)** - Habitats harmonized from GOLD, BacDive, PREGO and Madin et al. into ENVO-grounded records
- **[TraitMech](https://culturebotai.github.io/TraitMech/)** - Autonomous knowledge factory for microbial ecophysiological traits
- **[CellStructureMech](https://culturebotai.github.io/CellStructureMech/)** - Microbial cell structures, between the trait and protein layers
- **[ProteinTraitsMech](https://culturebotai.github.io/proteintraitsmech/)** - Protein sequence, structure, and function traits
- **[NaturalProductMech](https://culturebotai.github.io/NaturalProductMech/)** - Natural product structures with their producer organisms and gene clusters
- **[AntibioticMech](https://culturebotai.github.io/AntibioticMech/)** - Antimicrobial structures harmonizing ChEBI and CARD/ARO
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient curation
- **[CultureMech](/culturemech/)** - Single-organism media requirements (6,286 canonical media)
- **[PFASCommunityAgents](/resources/#pfascommunityagents)** - AI-driven consortium design for PFAS biodegradation
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph (864K+ species)
- **[MicroGrowAgents](/microgrowagents/)** - Multi-agent media design system

---

## Publications & Citations

### Primary Citation

If you use CommunityMech in your research, please cite:

> Santangelo BE, et al. (2026). KG-Microbe - Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*, giag077. doi: [10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)

### Related Publications

- Community assembly principles in microbial cultivation
- Syntrophic partnerships in engineered systems
- PFAS biodegradation consortium design

---

## Contact & Collaboration

For questions about CommunityMech or consortium design projects:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory

---

## Acknowledgments

CommunityMech development is supported by:
- Lawrence Berkeley National Laboratory
- U.S. Department of Energy, Office of Science
- Environmental Genomics and Systems Biology Division
- ABPDU (Advanced Biofuels and Bioproducts Process Development Unit)

---

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. Naseem S, Miller MA, Martinez-Gomez NC, Sun N, **Joachimiak MP**. MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering. *bioRxiv*. 2026. [doi:10.64898/2026.06.04.729985](https://doi.org/10.64898/2026.06.04.729985)
3. Máša P, Kliegr T, **Joachimiak MP**. Explainable rule-based prediction of cultivation media for microbes. *Computational and Structural Biotechnology Journal*. 2025;27:5194–5206. [doi:10.1016/j.csbj.2025.10.014](https://doi.org/10.1016/j.csbj.2025.10.014) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12670597/)
{: .bibliography}

[Full publication list →](/publications/#bibliography)
