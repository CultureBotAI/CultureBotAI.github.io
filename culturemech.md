---
layout: default
title: "CultureMech"
description: "Comprehensive collection of 10,000+ culture media recipes from major international repositories with LinkML schema, ontology grounding, and browser-based exploration"
permalink: /culturemech/
---

# CultureMech: Microbial Culture Media Knowledge Graph

## Overview

**CultureMech** is a comprehensive knowledge graph containing over 10,000 culture media recipes from major international repositories. It transforms unstructured media composition text from literature and laboratory records into standardized, machine-readable data through automated chemical entity extraction and ontology-based grounding.

**The Challenge**: Microbial cultivation protocols are scattered across scientific literature, culture collection databases, and laboratory notebooks in unstructured text formats. This makes it difficult to systematically analyze growth requirements, compare media compositions, or leverage this data for AI-driven predictions.

**The Solution**: CultureMech automatically extracts chemical entities from text-based media descriptions, parses concentrations, and grounds ingredients to standard chemical ontologies (ChEBI, PubChem), creating a unified knowledge graph that powers downstream AI tools.

---

## Key Features

### 🧬 Comprehensive Coverage
- **10,000+ culture media recipes** from major international culture collections
- Coverage spans bacteria, archaea, fungi, and other microorganisms
- Integration with ATCC, DSMZ, JCM, and other major repositories
- Historical and contemporary cultivation protocols

### 🔬 Chemical Entity Extraction
- Automated parsing of media composition text
- Chemical compound recognition and identification
- Concentration extraction and normalization
- Support for complex media formulations

### 🗂️ Ontology Grounding
- **ChEBI** (Chemical Entities of Biological Interest) integration
- **PubChem** compound mapping
- Standardized chemical identifiers
- Semantic interoperability with other knowledge graphs

### 📊 LinkML Schema
- Structured data model for media compositions
- Validation and quality control
- Export to multiple formats (JSON, RDF, TSV)
- Extensible schema for new data types

### 🌐 Browser-Based Exploration
- Interactive web interface: [culturebotai.github.io/CultureMech](https://culturebotai.github.io/CultureMech/)
- Search and filter media recipes
- Browse by organism, chemical compound, or media type
- Download standardized data

---

## Technical Architecture

### Data Processing Pipeline

```
Raw Media Text
    ↓
Text Parsing & Cleaning
    ↓
Chemical Entity Recognition
    ↓
Concentration Extraction
    ↓
Ontology Mapping (ChEBI/PubChem)
    ↓
Structured Media Records
    ↓
CultureMech Knowledge Graph
```

### Integration with CultureBotAI Ecosystem

**CultureMech** serves as the foundation of the AI curation pipeline:

- **Input Sources**:
  - Culture collection databases (ATCC, DSMZ, JCM, NBRC)
  - Scientific literature
  - Laboratory cultivation protocols
  - BacDive phenotypic data

- **Feeds Into**:
  - [MicroMediaParam](/resources/#micromediaparam) - Chemical compound standardization (78% ChEBI coverage)
  - [kg-microbe](/kg-microbe/) - Central knowledge graph integration
  - [MicroGrowAgents](/resources/#microgrowagents) - AI-driven media design
  - [MicroGrowLink](/resources/#microgrowlink) - Graph-based growth predictions

- **Works With**:
  - [MediaIngredientMech](/mediaingredientmech/) - LLM-assisted ingredient ontology mapping
  - [assay-metadata](/resources/#assay-metadata-bacdive-api-assay-metadata-extractor) - Phenotypic assay integration

---

## Data Sources

CultureMech aggregates media recipes from:

### Major Culture Collections
- **ATCC** (American Type Culture Collection)
- **DSMZ** (German Collection of Microorganisms and Cell Cultures)
- **JCM** (Japan Collection of Microorganisms)
- **NBRC** (NITE Biological Resource Center)
- Additional international repositories

### Scientific Literature
- Peer-reviewed publications describing novel cultivation protocols
- Species descriptions with original growth conditions
- Optimization studies for specific organisms

### Standardized Media
- Common laboratory media (LB, TSA, PDA, etc.)
- Defined minimal media
- Enrichment and selective media
- Specialized media for extremophiles

---

## Use Cases

### 1. Historical Data Mining
Extract cultivation conditions from decades of scientific literature to identify patterns in growth requirements across the microbial kingdom.

### 2. Media Standardization
Normalize media recipes from different sources to enable cross-institutional comparisons and meta-analyses.

### 3. AI Model Training
Provide structured training data for machine learning models that predict optimal growth conditions for novel organisms.

### 4. Comparative Analysis
Analyze relationships between taxonomic groups and their chemical growth requirements to inform cultivation strategies.

### 5. Novel Organism Cultivation
Leverage phylogenetic relationships and chemical similarity to recommend starting media for uncultivated organisms.

---

## Example: Media Composition Extraction

**Input (Unstructured Text)**:
```
"R2A medium containing (per liter): yeast extract (0.5 g),
proteose peptone (0.5 g), casamino acids (0.5 g),
glucose (0.5 g), soluble starch (0.5 g), K2HPO4 (0.3 g),
MgSO4·7H2O (0.05 g), sodium pyruvate (0.3 g), pH 7.2"
```

**Output (Structured Data)**:
```json
{
  "media_name": "R2A",
  "components": [
    {"compound": "yeast extract", "amount": 0.5, "unit": "g/L", "chebi_id": "CHEBI:82594"},
    {"compound": "proteose peptone", "amount": 0.5, "unit": "g/L"},
    {"compound": "casamino acids", "amount": 0.5, "unit": "g/L"},
    {"compound": "glucose", "amount": 0.5, "unit": "g/L", "chebi_id": "CHEBI:17234"},
    {"compound": "soluble starch", "amount": 0.5, "unit": "g/L", "chebi_id": "CHEBI:28017"},
    {"compound": "dipotassium phosphate", "amount": 0.3, "unit": "g/L", "chebi_id": "CHEBI:131527"},
    {"compound": "magnesium sulfate heptahydrate", "amount": 0.05, "unit": "g/L", "chebi_id": "CHEBI:31795"},
    {"compound": "sodium pyruvate", "amount": 0.3, "unit": "g/L", "chebi_id": "CHEBI:113958"}
  ],
  "ph": 7.2
}
```

---

## Repository & Documentation

- **GitHub**: [github.com/CultureBotAI/CultureMech](https://github.com/CultureBotAI/CultureMech)
- **Web Interface**: [culturebotai.github.io/CultureMech](https://culturebotai.github.io/CultureMech/)
- **License**: CC0 1.0 Universal (Public Domain)
- **Language**: HTML, Python

### Topics
`growth-media` · `microbes` · `microbial-ecology` · `microbiology` · `cultivation` · `media` · `media-ingredients` · `microbial-growth` · `microbial-culturing`

---

## Getting Started

### Access the Data

1. **Browse Online**: Visit the [CultureMech web interface](https://culturebotai.github.io/CultureMech/)
2. **Download**: Access structured data from the [GitHub repository](https://github.com/CultureBotAI/CultureMech)
3. **API Integration**: Use with [kg-microbe](/kg-microbe/) for programmatic access

### Integration with Your Workflow

```python
# Example: Loading CultureMech data
from culturemech import MediaKG

# Load the knowledge graph
kg = MediaKG()

# Search for media by organism
media = kg.search_by_organism("Escherichia coli")

# Get chemical composition
composition = kg.get_composition("LB medium")

# Export to standard format
kg.export(format="json", output="media_data.json")
```

---

## Related Tools

- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient ontology mapping
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[MicroMediaParam](/resources/#micromediaparam)** - Chemical compound standardization and ChEBI mapping
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Research Impact

CultureMech is part of the [KG-Microbe knowledge graph](/kg-microbe/) ecosystem developed at Lawrence Berkeley National Laboratory. It supports:

- Data-driven cultivation optimization
- AI-powered growth prediction
- Systematic analysis of microbial growth requirements
- Evidence-based media design for novel organisms

**Citation**: See the [KG-Microbe preprint](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1) for details on the broader knowledge graph ecosystem.

---

## Contact & Collaboration

For questions about CultureMech or collaboration opportunities:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory
