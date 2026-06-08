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

**The Solution**: MicroGrowAgents coordinates a team of specialized agents, each focused on one source of evidence (literature, cross-organism analogy, genome function, media formulation). Their outputs are combined into organism-specific, evidence-based media recommendations grounded in the [kg-microbe knowledge graph](/kg-microbe/).

---

## Specialized Agents

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

- **GitHub**: [github.com/CultureBotAI/MicroGrowAgents](https://github.com/CultureBotAI/MicroGrowAgents)
- **License**: BSD-3-Clause
- **Languages**: Python, HTML, Shell, R
- **Topics**: `ai4curation` · `monarchinitiative`

---

## Related Tools

- **[CultureMech](/culturemech/)** - Microbial culture media knowledge graph (10,000+ recipes)
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient ontology mapping
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[MicroGrowLink](/resources/#microgrowlink)** - Graph-based growth media prediction
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Research Impact

MicroGrowAgents is part of the [KG-Microbe knowledge graph](/kg-microbe/) ecosystem developed at Lawrence Berkeley National Laboratory. It supports:

- AI-driven media design for novel and fastidious organisms
- Genome-guided prediction of nutritional requirements
- Evidence-based cultivation protocol synthesis from literature
- Data-driven cultivation optimization

**Citation**: See the [KG-Microbe preprint](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1) for details on the broader knowledge graph ecosystem.

---

## Contact & Collaboration

For questions about MicroGrowAgents or collaboration opportunities:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory
