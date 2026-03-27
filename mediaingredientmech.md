---
layout: default
title: "MediaIngredientMech"
description: "Curated media ingredient ontology mappings with LLM-assisted workflows for standardizing microbial cultivation ingredient data"
permalink: /mediaingredientmech/
---

# MediaIngredientMech: LLM-Assisted Media Ingredient Curation

## Overview

**MediaIngredientMech** leverages Large Language Models (LLMs) to curate and standardize media ingredient ontology mappings for microbial cultivation research. It addresses the challenge of inconsistent ingredient naming and ambiguous chemical identifiers in cultivation protocols through AI-assisted semantic matching and human-in-the-loop validation workflows.

**The Challenge**: Media ingredients are described using inconsistent terminology across scientific literature, culture collections, and laboratory protocols. The same chemical compound might be referred to by common names, trade names, systematic IUPAC names, or ambiguous abbreviations, making automated data integration difficult.

**The Solution**: MediaIngredientMech uses LLMs to intelligently map ingredient names to standardized ontology terms (ChEBI, PubChem, METPO), with confidence scoring, batch processing capabilities, and curation workflows for ambiguous cases.

---

## Key Features

### 🤖 LLM-Powered Semantic Matching
- Leverages foundation models for ingredient name normalization
- Context-aware mapping considering cultivation domain knowledge
- Handles synonyms, abbreviations, and trade names
- Multi-ontology alignment (ChEBI, PubChem, custom vocabularies)

### 📋 Curation Workflows
- Automated processing for high-confidence matches
- Human-in-the-loop validation for ambiguous cases
- Batch processing of large datasets
- Quality control and consistency checking

### 📊 Quality Metrics
- Confidence scores for each mapping
- Provenance tracking for curation decisions
- Validation status and review history
- Inter-annotator agreement metrics

### 🔗 Ontology Integration
- **ChEBI** (Chemical Entities of Biological Interest)
- **PubChem** compound database
- **METPO** (Microbial Ecology and Taxonomy Phenotypic Ontology)
- Custom microbial cultivation vocabularies

### 💾 Standardized Outputs
- Export to JSON, TSV, RDF formats
- Integration with LinkML schemas
- Compatible with kg-microbe knowledge graph
- API-ready structured data

---

## Technical Architecture

### LLM-Assisted Mapping Pipeline

```
Raw Ingredient Names
    ↓
Text Preprocessing & Normalization
    ↓
LLM Semantic Analysis
    ↓
Ontology Candidate Retrieval
    ↓
Confidence Scoring
    ↓
├─ High Confidence → Automated Mapping
└─ Low Confidence → Human Curation Queue
    ↓
Validated Mappings
    ↓
Export to Knowledge Graph
```

### Integration with CultureBotAI Ecosystem

**MediaIngredientMech** enhances the AI curation pipeline by providing semantic standardization:

- **Receives Input From**:
  - [CultureMech](/culturemech/) - Extracted chemical entities from media recipes
  - Manual curation efforts
  - Legacy database imports
  - Literature mining outputs

- **Feeds Into**:
  - [MicroMediaParam](/resources/#micrmedparam) - Enhanced ingredient standardization
  - [kg-microbe](/kg-microbe/) - Ontology-grounded knowledge graph
  - [MicroGrowAgents](/resources/#microgrowagents) - Evidence-based media design

- **Complements**:
  - [CultureMech](/culturemech/) - Chemical entity extraction
  - [CommunityMech](/communitymech/) - Community-level curation

---

## LLM-Assisted Workflows

### Workflow 1: Automated High-Confidence Mapping

For ingredient names with clear, unambiguous mappings:

```python
# Example: High-confidence automated mapping
ingredient = "glucose"
result = mediaingredient_mech.map(ingredient)
# → {
#     "input": "glucose",
#     "mapped_term": "D-glucose",
#     "chebi_id": "CHEBI:17234",
#     "confidence": 0.99,
#     "status": "automated"
# }
```

### Workflow 2: Ambiguous Case Resolution

For ingredients with multiple possible interpretations:

```python
# Example: Ambiguous ingredient requiring curation
ingredient = "peptone"
result = mediaingredient_mech.map(ingredient)
# → {
#     "input": "peptone",
#     "candidates": [
#         {"term": "peptone", "chebi_id": "CHEBI:8429", "confidence": 0.65},
#         {"term": "proteose peptone", "source": "common_name", "confidence": 0.55},
#         {"term": "casein peptone", "source": "common_name", "confidence": 0.50}
#     ],
#     "status": "requires_curation",
#     "rationale": "Multiple peptone types exist; context needed"
# }
```

### Workflow 3: Batch Processing

Process large datasets efficiently:

```python
# Example: Batch processing of ingredients
ingredients = load_ingredients_from_csv("media_ingredients.csv")
results = mediaingredient_mech.batch_map(ingredients,
                                         confidence_threshold=0.8)

# Separate by curation status
automated = results.filter(status="automated")
needs_review = results.filter(status="requires_curation")

# Export results
automated.export("mapped_ingredients.json")
needs_review.export("curation_queue.json")
```

---

## Use Cases

### 1. Legacy Data Standardization
Standardize ingredient names from historical culture collection records to enable modern computational analysis.

### 2. Literature Mining Enhancement
Improve the quality of ingredient extraction from scientific publications by resolving ambiguous names to specific chemical entities.

### 3. Cross-Database Integration
Harmonize ingredient vocabularies across different culture collections (ATCC, DSMZ, JCM) for unified querying and analysis.

### 4. AI Training Data Preparation
Create high-quality, ontology-grounded training datasets for machine learning models predicting growth requirements.

### 5. Real-Time Laboratory Support
Provide ingredient standardization as a service for laboratory information management systems (LIMS) during data entry.

---

## Ontology Integration

### ChEBI (Chemical Entities of Biological Interest)

Primary ontology for chemical compound identification:
- Systematic chemical classification
- Hierarchical relationships (is_a, has_part)
- Molecular formulas and structures
- Cross-references to other databases

### PubChem

Complementary chemical database integration:
- Compound identifiers (CID)
- Chemical structure search
- Bioassay data links
- Literature references

### METPO (Microbial Ecology and Taxonomy Phenotypic Ontology)

Domain-specific ontology for microbial cultivation:
- Growth condition terms
- Media component vocabulary
- Phenotypic trait descriptions
- Integration with kg-microbe

---

## Quality Control Features

### Confidence Scoring
- **0.90-1.00**: High confidence (automated approval)
- **0.70-0.89**: Medium confidence (optional review)
- **0.00-0.69**: Low confidence (requires curation)

### Validation Checks
- Taxonomic appropriateness (e.g., plant extracts for phototrophs)
- Chemical compatibility (e.g., pH stability)
- Concentration reasonableness
- Cross-reference consistency

### Provenance Tracking
- Mapping algorithm version
- LLM model and parameters used
- Human curator identity (if applicable)
- Timestamp and review history

---

## Example: Ingredient Mapping

### Input Data

```csv
ingredient_name,source,context
"NaCl","ATCC Medium 1","Marine bacterium medium"
"table salt","Lab protocol","General bacteriology"
"sodium chloride","Literature","Halophile cultivation"
"salt","DSMZ 514","Seawater-based medium"
```

### MediaIngredientMech Processing

```json
{
  "mappings": [
    {
      "input": "NaCl",
      "standardized_name": "sodium chloride",
      "chebi_id": "CHEBI:26710",
      "chebi_name": "sodium chloride",
      "confidence": 0.99,
      "status": "automated",
      "synonyms": ["NaCl", "table salt", "salt", "halite"]
    },
    {
      "input": "table salt",
      "standardized_name": "sodium chloride",
      "chebi_id": "CHEBI:26710",
      "confidence": 0.95,
      "status": "automated",
      "note": "Common name mapped to systematic term"
    },
    {
      "input": "salt",
      "candidates": [
        {"name": "sodium chloride", "chebi_id": "CHEBI:26710", "confidence": 0.75},
        {"name": "salts", "chebi_id": "CHEBI:24866", "confidence": 0.65}
      ],
      "status": "requires_curation",
      "rationale": "Ambiguous: could refer to specific salt (NaCl) or general salt category"
    }
  ]
}
```

---

## Repository & Documentation

- **GitHub**: [github.com/CultureBotAI/MediaIngredientMech](https://github.com/CultureBotAI/MediaIngredientMech)
- **License**: To be determined
- **Language**: Python
- **Status**: Active development (Public as of March 2026)

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/CultureBotAI/MediaIngredientMech.git
cd MediaIngredientMech

# Install dependencies
pip install -r requirements.txt

# Configure LLM API keys (if using external models)
export OPENAI_API_KEY="your-api-key"
# or
export ANTHROPIC_API_KEY="your-api-key"
```

### Basic Usage

```python
from mediaingredientmech import IngredientMapper

# Initialize mapper
mapper = IngredientMapper(
    ontology="chebi",
    confidence_threshold=0.8
)

# Map a single ingredient
result = mapper.map_ingredient("yeast extract")
print(f"Mapped to: {result.chebi_name} ({result.chebi_id})")

# Batch processing
ingredients = ["peptone", "glucose", "NaCl", "agar"]
results = mapper.batch_map(ingredients)

# Export mappings
results.to_json("ingredient_mappings.json")
```

---

## Research Impact

MediaIngredientMech improves data quality throughout the CultureBotAI ecosystem by providing:

- **Semantic consistency** across heterogeneous data sources
- **Reduced manual curation burden** through intelligent automation
- **Enhanced AI training data** with ontology-grounded ingredient terms
- **Interoperability** with broader biological knowledge graphs

It is part of the [KG-Microbe knowledge graph](/kg-microbe/) project at Lawrence Berkeley National Laboratory.

---

## Related Tools

- **[CultureMech](/culturemech/)** - Chemical entity extraction from media recipes (10,000+ recipes)
- **[CommunityMech](/communitymech/)** - Microbial community interaction modeling
- **[MicroMediaParam](/resources/#micrmedparam)** - Chemical compound standardization (78% ChEBI coverage)
- **[kg-microbe](/kg-microbe/)** - Central knowledge graph for microbial cultivation

---

## Future Directions

### Planned Enhancements
- Multi-language ingredient name support
- Integration with additional ontologies (FoodOn, NCIT)
- Real-time curation web interface
- Federated learning for cross-institutional curation
- Active learning to prioritize human curation efforts

### Community Contributions
We welcome contributions for:
- Additional ingredient vocabularies
- Ontology mapping rules
- Validation datasets
- Integration with laboratory systems

---

## Contact & Collaboration

For questions about MediaIngredientMech or to contribute:

- **Principal Investigator**: [Dr. Marcin P. Joachimiak](/marcin-joachimiak/)
- **Email**: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **Organization**: [CultureBotAI](https://github.com/CultureBotAI)
- **Laboratory**: Environmental Genomics and Systems Biology Division, Lawrence Berkeley National Laboratory

---

## Citation

If you use MediaIngredientMech in your research, please cite the [KG-Microbe preprint](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1) and reference this tool:

```
MediaIngredientMech: LLM-Assisted Media Ingredient Curation
CultureBotAI Organization
https://github.com/CultureBotAI/MediaIngredientMech
```
