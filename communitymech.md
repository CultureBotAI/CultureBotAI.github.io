---
layout: default
title: "CommunityMech"
description: "LinkML-based modeling of microbial communities with evidence-based ecological interactions for consortium design and multi-organism cultivation"
permalink: /communitymech/
---

# CommunityMech: Microbial Community Mechanisms Knowledge Base

## Overview

**CommunityMech** is a LinkML-based knowledge base for modeling microbial community interactions and multi-organism cultivation systems. It provides structured representation of community composition, ecological interactions (syntrophy, competition, facilitation), and evidence-based relationship tracking to support consortium design and polyculture optimization.

**The Challenge**: Microbial communities exhibit complex ecological interactions that are critical for successful cultivation, yet these relationships are scattered across literature in unstructured formats. Single-organism cultivation data cannot capture the syntrophic dependencies, competitive exclusions, and facilitative interactions that determine community assembly and stability.

**The Solution**: CommunityMech provides a structured schema for representing community-level cultivation data, interaction networks, and temporal dynamics. It extends the single-organism focus of [CultureMech](/culturemech/) to multi-species systems, enabling systematic analysis of community cultivation requirements.

---

## Key Features

### 🔬 LinkML Schema Design
- Structured data model for community composition
- Interaction type classification with evidence codes
- Temporal dynamics representation
- Validation and quality control

### 🌐 Ecological Interactions Framework
- **Positive interactions**: mutualism, commensalism, syntrophy, facilitation
- **Negative interactions**: competition, inhibition, predation, parasitism
- **Neutral interactions**: no observable effect
- **Context-dependent relationships**: conditional on environmental factors

### 📚 Evidence-Based Tracking
- Literature provenance for each interaction claim
- Experimental evidence types (co-culture, metabolomics, genomics)
- Confidence levels and validation status
- Mechanism descriptions (metabolite exchange, signaling, etc.)

### 🧬 Community Assembly Modeling
- Core species vs. accessory species
- Functional redundancy analysis
- Keystone species identification
- Succession and temporal dynamics

### 📊 Network Visualization
- Interaction network graphs
- Community structure analysis
- Export to Cytoscape, Gephi formats
- Integration with network analysis tools

### 💾 Multi-Format Export
- JSON, RDF, TSV outputs
- LinkML-compatible schemas
- Integration with kg-microbe
- API-ready structured data

---

## Technical Architecture

### Community Modeling Pipeline

```
Literature & Experimental Data
    ↓
Community Composition Extraction
    ↓
Interaction Identification
    ↓
Evidence Classification
    ↓
LinkML Schema Validation
    ↓
CommunityMech Knowledge Base
    ↓
├─ Consortium Design (PFASCommunityAgents)
├─ Growth Predictions (Multi-organism models)
└─ Community Analysis (Network metrics)
```

### Integration with CultureBotAI Ecosystem

**CommunityMech** extends single-organism cultivation data to multi-species systems:

- **Builds Upon**:
  - [CultureMech](/culturemech/) - Single-organism media requirements
  - [kg-microbe](/kg-microbe/) - Taxonomic and phenotypic data
  - Literature-derived interaction data

- **Feeds Into**:
  - [PFASCommunityAgents](/resources/#pfascommunityagents) - AI-driven consortium design for PFAS biodegradation
  - Multi-organism growth prediction models
  - Community optimization workflows

- **Enables**:
  - Syntrophic community engineering
  - Consortium stability prediction
  - Microbiome cultivation optimization

---

## Ecological Interactions Framework

### Positive Interactions

#### Syntrophy
Obligate metabolic cooperation where one organism depends on metabolites produced by another.

**Example**: *Syntrophus* species and methanogenic archaea
```json
{
  "interaction_type": "syntrophy",
  "partner_1": {"taxon": "Syntrophus aciditrophicus", "role": "fatty acid oxidizer"},
  "partner_2": {"taxon": "Methanospirillum hungatei", "role": "H2 consumer"},
  "mechanism": "Interspecies hydrogen transfer",
  "evidence": "PMID:12345678",
  "context": "Anaerobic conditions, <10 µM H2"
}
```

#### Mutualism
Both organisms benefit from the interaction.

#### Commensalism
One organism benefits, the other is unaffected.

#### Facilitation
One organism modifies the environment to benefit another (e.g., O2 removal for anaerobes).

### Negative Interactions

#### Competition
Organisms compete for the same resources.

**Example**: Carbon source competition
```json
{
  "interaction_type": "competition",
  "partner_1": {"taxon": "Escherichia coli"},
  "partner_2": {"taxon": "Salmonella enterica"},
  "mechanism": "Glucose uptake competition",
  "outcome": "Competitive exclusion at low glucose",
  "evidence": "PMID:87654321"
}
```

#### Inhibition
One organism produces compounds that inhibit another (antibiotics, bacteriocins, pH changes).

### Context-Dependent Interactions

Many interactions depend on environmental conditions:

```json
{
  "interaction_type": "context_dependent",
  "partner_1": {"taxon": "Pseudomonas putida"},
  "partner_2": {"taxon": "Bacillus subtilis"},
  "conditions": [
    {"context": "High nutrient", "interaction": "competition"},
    {"context": "Low nutrient", "interaction": "facilitation",
     "mechanism": "P. putida exopolysaccharide aids B. subtilis biofilm"}
  ]
}
```

---

## LinkML Schema

CommunityMech uses LinkML (Linked Data Modeling Language) for structured, validated data representation:

### Core Classes

```yaml
classes:
  MicrobialCommunity:
    description: A collection of microbial species cultivated together
    attributes:
      community_id:
        range: string
        required: true
      members:
        range: CommunityMember
        multivalued: true
      interactions:
        range: Interaction
        multivalued: true
      cultivation_conditions:
        range: CultivationConditions

  CommunityMember:
    description: A microbial species within a community
    attributes:
      taxon:
        range: string
        description: NCBI taxonomy ID or species name
      abundance:
        range: float
        description: Relative abundance (0-1)
      role:
        range: FunctionalRole
        description: Primary/secondary producer, degrader, etc.

  Interaction:
    description: Ecological interaction between community members
    attributes:
      interaction_type:
        range: InteractionType
        required: true
      partner_1:
        range: CommunityMember
      partner_2:
        range: CommunityMember
      mechanism:
        range: string
        description: Molecular mechanism (if known)
      evidence:
        range: Evidence
        multivalued: true
      confidence:
        range: float
        description: Confidence score (0-1)
```

---

## Use Cases

### 1. PFAS Biodegradation Consortia Design

Design optimized microbial consortia for PFAS (per- and polyfluoroalkyl substances) biodegradation:

```json
{
  "community_name": "PFAS-degrading consortium v2.1",
  "target_compound": "PFOA (perfluorooctanoic acid)",
  "members": [
    {
      "taxon": "Acidimicrobium sp. A6",
      "role": "PFOA defluorination",
      "evidence": "Genomic capacity (pfa gene cluster)"
    },
    {
      "taxon": "Pseudomonas sp. B12",
      "role": "Short-chain intermediate degradation",
      "evidence": "Growth on fluoroacetate"
    },
    {
      "taxon": "Rhizobium sp. C3",
      "role": "Nitrogen fixation support",
      "evidence": "nif genes, enhances P. sp. B12 growth"
    }
  ],
  "interactions": [
    {
      "type": "syntrophy",
      "partners": ["A6", "B12"],
      "mechanism": "A6 defluorinates PFOA → B12 degrades short-chain products"
    },
    {
      "type": "facilitation",
      "partners": ["C3", "B12"],
      "mechanism": "N2 fixation supports B12 under N-limited conditions"
    }
  ]
}
```

### 2. Syntrophic Community Engineering

Model obligate syntrophic partnerships for anaerobic digestion or specialized metabolism:

- Fatty acid oxidizers + methanogens
- Fermenters + hydrogen consumers
- Primary degraders + secondary consumers

### 3. Microbiome Cultivation

Optimize cultivation of complex microbiomes from environmental samples:

- Capture keystone species interactions
- Identify core vs. accessory species
- Design media supporting multiple trophic levels

### 4. Community Stability Prediction

Predict which community compositions will remain stable under specific conditions:

- Identify competitive exclusion risks
- Model syntrophic dependencies
- Assess resilience to perturbations

### 5. Bioaugmentation Strategy

Design bioaugmentation strategies by modeling how introduced species will interact with existing communities.

---

## Example: Methanogenic Consortium

### Community Definition

```json
{
  "community_id": "METHAN-01",
  "name": "Anaerobic digester methanogenic consortium",
  "members": [
    {
      "taxon_id": "NCBI:572546",
      "name": "Syntrophus aciditrophicus",
      "role": "Fatty acid oxidizer",
      "abundance": 0.15
    },
    {
      "taxon_id": "NCBI:879972",
      "name": "Methanospirillum hungatei",
      "role": "Hydrogenotrophic methanogen",
      "abundance": 0.25
    },
    {
      "taxon_id": "NCBI:2159",
      "name": "Methanosarcina barkeri",
      "role": "Acetoclastic methanogen",
      "abundance": 0.20
    },
    {
      "taxon_id": "NCBI:1736",
      "name": "Clostridium cellulolyticum",
      "role": "Cellulose degrader",
      "abundance": 0.40
    }
  ],
  "interactions": [
    {
      "type": "syntrophy",
      "partner_1": "Syntrophus aciditrophicus",
      "partner_2": "Methanospirillum hungatei",
      "mechanism": "Interspecies hydrogen transfer",
      "metabolites": ["H2", "formate"],
      "evidence": {
        "type": "co-culture",
        "reference": "PMID:12345678",
        "confidence": 0.95
      }
    },
    {
      "type": "facilitation",
      "partner_1": "Clostridium cellulolyticum",
      "partner_2": "Syntrophus aciditrophicus",
      "mechanism": "Cellulose → short-chain fatty acids",
      "metabolites": ["acetate", "butyrate", "propionate"],
      "evidence": {
        "type": "metabolomics",
        "reference": "PMID:23456789",
        "confidence": 0.90
      }
    },
    {
      "type": "competition",
      "partner_1": "Methanospirillum hungatei",
      "partner_2": "Methanosarcina barkeri",
      "mechanism": "Acetate utilization",
      "context": "High acetate concentrations",
      "outcome": "M. barkeri outcompetes at >5 mM acetate",
      "evidence": {
        "type": "competition assay",
        "reference": "PMID:34567890",
        "confidence": 0.85
      }
    }
  ],
  "cultivation_conditions": {
    "temperature": 37,
    "ph": 7.2,
    "atmosphere": "Anaerobic (N2/CO2, 80:20)",
    "media": "DSMZ Medium 641 (Methanogenic Medium)"
  }
}
```

### Network Visualization

```
    [C. cellulolyticum] --(SCFAs)--> [S. aciditrophicus]
                                            |
                                        (H2, formate)
                                            ↓
                                   [M. hungatei] -----> CH4
                                            |
                                      (competition)
                                            ↓
                                   [M. barkeri] ------> CH4
```

---

## Repository & Documentation

- **GitHub**: [github.com/CultureBotAI/CommunityMech](https://github.com/CultureBotAI/CommunityMech)
- **Web Interface**: [culturebotai.github.io/CommunityMech](https://culturebotai.github.io/CommunityMech/)
- **License**: BSD-3-Clause
- **Language**: Python

### Topics
`microbes` · `microbial-communities` · `microbial-community-assembly` · `microbial-ecology` · `microbial-interactions` · `microbiology` · `microbiome` · `microbiome-analysis` · `microbiome-data` · `microbial-community-dynamics`

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/CultureBotAI/CommunityMech.git
cd CommunityMech

# Install dependencies
pip install -r requirements.txt

# Validate LinkML schema
linkml-validate --schema schema/community_mech.yaml data/example_community.json
```

### Basic Usage

```python
from communitymech import CommunityModel

# Load a community from data
community = CommunityModel.load("data/methanogenic_consortium.json")

# Access community members
for member in community.members:
    print(f"{member.name}: {member.role} ({member.abundance:.2%})")

# Query interactions
syntrophic = community.get_interactions(type="syntrophy")
for interaction in syntrophic:
    print(f"{interaction.partner_1} <-> {interaction.partner_2}")
    print(f"  Mechanism: {interaction.mechanism}")

# Export network for visualization
community.export_network("community_network.graphml")

# Validate community composition
validation = community.validate()
print(f"Validation status: {validation.status}")
```

---

## Integration with PFASCommunityAgents

CommunityMech provides the knowledge base for [PFASCommunityAgents](/resources/#pfascommunityagents), an AI-driven consortium design system:

```python
from pfascommunityagents import ConsortiumDesigner
from communitymech import CommunityModel

# Load existing community knowledge
knowledge_base = CommunityModel.load_knowledge_base()

# Design consortium for PFOA degradation
designer = ConsortiumDesigner(knowledge_base)
consortium = designer.design_for_target(
    compound="PFOA",
    objectives=["complete_mineralization", "stability", "rapid_growth"],
    constraints=["aerobic_conditions", "temperature_range_20_30C"]
)

# Export designed consortium
consortium.save("pfoa_consortium_v1.json")
```

---

## Research Impact

CommunityMech enables systematic study of microbial community cultivation by:

- **Capturing interaction networks** from literature and experiments
- **Enabling consortium design** based on ecological principles
- **Supporting polyculture optimization** for industrial applications
- **Advancing microbiome cultivation** for uncultured taxa

It is part of the [KG-Microbe knowledge graph](/kg-microbe/) ecosystem at Lawrence Berkeley National Laboratory, supporting research in environmental biotechnology, bioremediation, and microbial ecology.

---

## Related Tools

- **[CultureMech](/culturemech/)** - Single-organism media requirements (10,000+ recipes)
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient curation
- **[PFASCommunityAgents](/resources/#pfascommunityagents)** - AI-driven consortium design for PFAS biodegradation
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph (864K+ species)
- **[MicroGrowAgents](/resources/#microgrowagents)** - Multi-agent media design system

---

## Publications & Citations

### Primary Citation

If you use CommunityMech in your research, please cite:

> Joachimiak MP, et al. (2025). KG-Microbe: A modular knowledge graph for microbial cultivation. *bioRxiv*. doi: [10.1101/2025.02.24.639989](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1)

### Related Publications

- Community assembly principles in microbial cultivation
- Syntrophic partnerships in engineered systems
- PFAS biodegradation consortium design

---

## Future Directions

### Planned Features
- **Temporal dynamics modeling** - Succession and community stability over time
- **Spatial structure** - Biofilm and aggregation modeling
- **Metabolic flux integration** - Quantitative metabolite exchange
- **Automated literature mining** - Extract interactions from publications
- **3D visualization** - Interactive community network exploration

### Community Contributions
We welcome contributions for:
- New interaction types and mechanisms
- Validated community datasets
- Cultivation protocols for consortia
- Integration with metabolic models

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
