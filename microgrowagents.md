---
layout: default
title: "MicroGrowAgents"
description: "Agent-based AI system for microbial cultivation and growth media design, integrating knowledge graphs, literature mining, and genome-guided reasoning across 864,363 validated species."
permalink: /microgrowagents/
---

# MicroGrowAgents: Multi-Agent AI for Microbial Cultivation

## Overview

**MicroGrowAgents** is an agent-based system for AI-driven microbial cultivation and growth media design. It bridges the microbial cultivation gap through AI-powered multi-agent systems that integrate knowledge graphs, machine learning, and experimental automation.

**The Challenge**: Designing growth media for novel or fastidious organisms is slow and largely manual. The knowledge needed — cultivation protocols, metabolic capabilities, chemical requirements — is scattered across literature, genomes, and culture collection databases, and no single model captures all of it.

**The Solution**: MicroGrowAgents is a hierarchical agentic-AI framework of **100+ specialist agents**. Each is focused on one source of evidence (literature, cross-organism analogy, genome function, media formulation), and their outputs are combined into organism-specific, evidence-based media recommendations grounded in the [kg-microbe knowledge graph](/kg-microbe/). The four principal agent roles below sit at the top of that hierarchy.

---

## Principal Agents

The framework organizes its 100+ specialist agents under four principal roles.

### 📚 LiteratureAgent
Mines 245+ papers for cultivation protocols, extracting growth conditions and media compositions from the published record.

### 🔁 AnalogyReasoningAgent
Performs cross-organism comparison and reasoning, transferring cultivation knowledge from well-characterized organisms to related, less-studied taxa.

### 🧬 GenomeFunctionAgent
Detects auxotrophies from genome annotations — built on 57 Bakta-annotated genomes spanning 667K features — to predict which nutrients an organism cannot synthesize and therefore requires in its media.

### 🧪 MediaFormulationAgent
Produces schema-driven media recommendations with evidence-based ingredient suggestions, assembling the other agents' findings into a concrete, formulatable recipe.

---

## Key Achievements

- **864,363 validated species** across bacteria, archaea, fungi, and protozoa (GTDB + LPSN + NCBI)
- **Multi-modal reasoning** combining literature mining, metabolic modeling (FBA / gap-filling), and chemical similarity (208K+ embeddings)
- **Genome-guided design** for organism-specific media formulation

---

## Technical Architecture

### Multi-Agent Reasoning Pipeline

```
Target Organism
    ↓
┌─────────────────────────────────────────────┐
│  LiteratureAgent   AnalogyReasoningAgent      │
│  GenomeFunctionAgent   MediaFormulationAgent  │
└─────────────────────────────────────────────┘
    ↓ (evidence integration over kg-microbe)
Organism-Specific Media Recommendation
```

### Integration with the CultureBotAI Ecosystem

- **Depends on**:
  - [kg-microbe](/kg-microbe/) - knowledge graph foundation
  - [MicroMediaParam](/resources/#micromediaparam) - chemical compound mappings
  - [eggnogtable](/resources/#eggnogtable) - genome functional annotations
  - [MATE-LLM](/resources/#mate-llm) - literature extraction

- **Feeds Into**:
  - Media formulation recommendations
  - [PFASCommunityAgents](/resources/#pfascommunityagents) - consortium design

- **Works With**:
  - [MicroGrowLink](/resources/#microgrowlink) - complementary graph/transformer-based prediction approach

---

## Repository & Documentation

- **GitHub**: [github.com/CultureBotAI/MicroGrowAgents](https://github.com/CultureBotAI/MicroGrowAgents) *(private repository — public release planned)*
- **Preprint**: [MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering](https://doi.org/10.64898/2026.06.04.729985) (bioRxiv, 2026)
- **License**: BSD-3-Clause
- **Languages**: Python, HTML, Shell, R
- **Topics**: `ai4curation` · `monarchinitiative`

---

## Related Tools

- **[CultureMech](/culturemech/)** - Microbial culture media knowledge graph (10,000+ recipes)
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient ontology mapping
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[TraitMech](https://culturebotai.github.io/TraitMech/)** - Microbial ecophysiological trait knowledge base
- **[ProteinTraitsMech](https://culturebotai.github.io/proteintraitsmech/)** - Protein sequence, structure, and function traits
- **[MicroGrowLink](/resources/#microgrowlink)** - Graph-based growth media prediction
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Research Impact

MicroGrowAgents is part of the [KG-Microbe knowledge graph](/kg-microbe/) ecosystem developed at Lawrence Berkeley National Laboratory. It supports:

- AI-driven media design for novel and fastidious organisms
- Genome-guided prediction of nutritional requirements
- Evidence-based cultivation protocol synthesis from literature
- Data-driven cultivation optimization

**Applications**: The [RuleML/GOBLIN lecture](https://youtu.be/p_WiR-5E9x0) reports high-throughput results in which MicroGrowAgents and [KOGUT](/resources/#kogut-transformer) improved growth and rare-earth-element depletion in *Methylorubrum extorquens* AM1.

**Citation**: Naseem, S., Miller, M. A., Martinez-Gomez, N. C., Sun, N., & Joachimiak, M. P. (2026). MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering. *bioRxiv*. [10.64898/2026.06.04.729985](https://doi.org/10.64898/2026.06.04.729985)

See also the [KG-Microbe publication](https://doi.org/10.1093/gigascience/giag077) in *GigaScience* for details on the broader knowledge graph ecosystem.

---

## Contact & Collaboration

For questions about MicroGrowAgents or collaboration opportunities:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory

---

## Bibliography

1. Naseem S, Miller MA, Martinez-Gomez NC, Sun N, **Joachimiak MP**. MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering. *bioRxiv*. 2026. [doi:10.64898/2026.06.04.729985](https://doi.org/10.64898/2026.06.04.729985)
2. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
3. Máša P, Kliegr T, **Joachimiak MP**. Explainable rule-based prediction of cultivation media for microbes. *Computational and Structural Biotechnology Journal*. 2025;27:5194–5206. [doi:10.1016/j.csbj.2025.10.014](https://doi.org/10.1016/j.csbj.2025.10.014) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12670597/)
4. **Joachimiak MP**. Knowledge Oriented Graph Unified Transformer (KOGUT) v0.1 [software]. DOE CODE; 2025. [doi:10.11578/dc.20260210.3](https://doi.org/10.11578/dc.20260210.3) · [DOE CODE 175162](https://www.osti.gov/doecode/biblio/175162)
5. **Joachimiak MP**. "RuleML/GOBLIN COST Action Lecture on Data Science: Teaching AI to Teach Humans About Microbiology" [talk]. RuleML / COST GOBLIN Action Seminar; 2026. [Recording](https://youtu.be/p_WiR-5E9x0)
{: .bibliography}

[Full publication list →](/publications/#bibliography)
