---
layout: page
title: "KG-Microbe"
description: "KG-Microbe is a modular knowledge graph led by Dr. Marcin P. Joachimiak for AI-driven growth preference prediction and cultivation insights."
permalink: /kg-microbe/
---

# KG-Microbe — Knowledge Graph for Microbiology

**KG-Microbe is a comprehensive, modular knowledge graph for microbiology and microbiome research developed by Dr. Marcin P. Joachimiak at Lawrence Berkeley National Laboratory in Berkeley, California.**

## Overview

KG-Microbe is a comprehensive, modular knowledge graph designed specifically for microbiology and microbiome research. Developed by [Dr. Marcin P. Joachimiak](https://biosciences.lbl.gov/profiles/marcin-p-joachimiak/) at Lawrence Berkeley National Laboratory in Berkeley, California, this innovative resource integrates diverse microbial data sources to enable AI-driven insights for growth preference prediction and culture optimization.

It is an AI-ready knowledge graph of microbial traits, carrying **3,000+ organismal traits** and **30,000+ genomic traits**, organized by the [METPO ontology](https://github.com/berkeleybop/metpo). It is registered in the [KG-Registry](https://kghub.org/kg-registry/resource/kg-microbe/kg-microbe).

## Key Features

### 🧬 Modular Architecture
- **Scalable Design**: Built with modularity in mind for easy expansion and maintenance
- **Flexible Integration**: Seamlessly incorporates new data sources and ontologies
- **Standardized Framework**: Uses consistent data models across all modules

### 🤖 AI/ML Integration
- **Growth Preference Prediction**: Machine learning models trained on integrated knowledge graph data
- **Culture Optimization**: AI-driven recommendations for optimal cultivation conditions
- **Pattern Discovery**: Automated identification of microbial relationships and preferences

### 📊 Comprehensive Data Sources
- **Taxonomic Information**: Integrated microbial taxonomy and phylogenetic relationships
- **Growth Conditions**: Comprehensive collection of experimental growth parameters
- **Environmental Data**: Habitat and ecological context information
- **Genomic Features**: Integration with genomic and functional annotations

## Technical Architecture

### Data Integration Pipeline
KG-Microbe employs a sophisticated ETL (Extract, Transform, Load) pipeline that:
- Extracts data from multiple heterogeneous sources
- Transforms data using standardized ontologies and vocabularies
- Loads integrated data into a unified knowledge graph structure

### METPO Ontology
The **Microbial Ecophysiological Trait and Phenotype Ontology (METPO)** provides:
- Standardized vocabulary for growth preferences
- Controlled terms for experimental conditions
- Hierarchical classification of microbial traits
- Semantic relationships between concepts

## Applications

### Research Applications
- **Cultivation Studies**: Predict optimal growth conditions for uncultured microbes
- **Comparative Microbiology**: Analyze growth patterns across different species
- **Ecological Modeling**: Understand microbial community dynamics
- **Biotechnology**: Optimize industrial cultivation processes

### AI/ML Use Cases
- **Predictive Modeling**: Train models to predict growth preferences
- **Recommendation Systems**: Suggest cultivation strategies
- **Knowledge Discovery**: Identify novel microbial relationships
- **Data Mining**: Extract patterns from large-scale microbial datasets

## Projects Built on KG-Microbe

The kg-microbe knowledge graph serves as the foundation for numerous CultureBotAI projects:

### Data Integration Projects
- **[CultureMech](/culturemech/) & [MicroMediaParam](/resources/#micromediaparam)** - Integrate chemical compound data with standardized identifiers
- **[MediaIngredientMech](/mediaingredientmech/)** - LLM-assisted ingredient ontology mapping (ChEBI, PubChem, METPO)
- **[assay-metadata](/resources/#assay-metadata-bacdive-api-assay-metadata-extractor)** - Add phenotypic assay results from 99K+ BacDive strains
- **MATE-LLM** - Literature-derived cultivation data extraction *(private repo, public release planned)*
- **eggnog_runner / eggnogtable** - Genome functional annotation pipeline *(eggnogtable is private, public release planned)*
- **[auto-term-catalog](/resources/#auto-term-catalog---automated-term-extraction)** - OntoGPT term extraction for ontology grounding

### Prediction & Analysis Tools
- **[MicroGrowAgents](/microgrowagents/)** - Multi-agent system using kg-microbe for evidence-based media design
- **MicroGrowLink** - Graph transformer models trained on kg-microbe structure *(private repo, public release planned)*
- **[neurosymbolreason](/resources/#neurosymbolreason---neurosymbolic-analogy-reasoning)** - Neurosymbolic analogy reasoning over kg-microbe embeddings
- **[microbe-rules](/resources/#microbe-rules-machine-learning-models-for-microbial-data)** - ML model comparison framework
- **[CommunityMech](/communitymech/)** - Multi-organism community interaction modeling
- **[PFAS-AI](/resources/#pfas-ai-machine-learning-enabled-pfas-biodegradation-pipeline)** & PFASCommunityAgents - PFAS biodegradation research *(PFASCommunityAgents is private, public release planned)*
- **CMM-AI** - Lanthanide bioprocessing research leveraging metabolic data *(private repo, public release planned)*

### Web Services
- **[MicroGrowLinkService](/resources/#microgrowlinkservice)** - RESTful API providing programmatic access to predictions

[Explore all projects and their relationships →](/resources/#project-ecosystem--workflows)

## Access and Usage

### Repository
- **GitHub**: [Knowledge-Graph-Hub/kg-microbe](https://github.com/Knowledge-Graph-Hub/kg-microbe)
- **Documentation**: Comprehensive guides and API documentation
- **Examples**: Sample queries and use case demonstrations

### Data Formats
- **RDF/OWL**: Semantic web standards for knowledge representation
- **JSON-LD**: Structured data format for web integration
- **TSV/CSV**: Tabular formats for data analysis
- **SPARQL**: Query language for graph traversal

## Citation

If you use KG-Microbe in your research, please cite our GigaScience paper:

### APA Format
Santangelo, B. E., Hegde, H., Caufield, J. H., Reese, J., Kliegr, T., Hunter, L. E., Lozupone, C. A., Mungall, C. J., & Joachimiak, M. P. (2026). KG-Microbe - Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*, giag077. https://doi.org/10.1093/gigascience/giag077

### BibTeX
```bibtex
@article{santangelo2026kgmicrobe,
  title={KG-Microbe - Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences},
  author={Santangelo, Brook E and Hegde, Harshad and Caufield, J Harry and Reese, Justin and Kliegr, Tomas and Hunter, Lawrence E and Lozupone, Catherine A and Mungall, Christopher J and Joachimiak, Marcin P},
  journal={GigaScience},
  year={2026},
  doi={10.1093/gigascience/giag077},
  url={https://doi.org/10.1093/gigascience/giag077}
}
```

**DOI:** [10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)

## Models Built on KG-Microbe

KG-Microbe is the training substrate for several prediction approaches, spanning the interpretability spectrum:

- **Boosted trees** — compared against the approaches below for taxa–media pairing in the [RuleML/GOBLIN lecture](https://youtu.be/p_WiR-5E9x0); no separate release
- **[Explainable rule mining](https://doi.org/10.1016/j.csbj.2025.10.014)** — human-readable association rules predicting cultivation media from microbial traits, (*CSBJ* 2025). The [RuleML/GOBLIN lecture](https://youtu.be/p_WiR-5E9x0) reports accuracy comparable to state-of-the-art and gives an example of a learned rule: *if β-galactosidase activity and isolated from a marine environment, then 87% likely to grow on Marine Broth*
- **[KOGUT](/resources/#kogut-transformer)** — relational graph transformer trained on the merged graph (1,379,337 nodes, 2,960,472 edges, 24 Biolink relation types) for growth media link prediction
- **[MicroGrowAgents](/microgrowagents/)** — multi-agent system that reasons over the graph alongside literature and genome evidence
- **[MicroGrowLink](/resources/#microgrowlink)** — graph and transformer models for media link prediction

## Related Resources

- [CultureBotAI Home](/) - Main project page
- [Research Areas](/research/) - Detailed research focus
- [Publications](/publications/) - Complete publication list
- [KG-Registry entry](https://kghub.org/kg-registry/resource/kg-microbe/kg-microbe) - Registry record for the knowledge graph
- [RuleML/GOBLIN lecture](https://youtu.be/p_WiR-5E9x0) - Talk covering the graph, METPO, and the three prediction approaches
- [About Dr. Joachimiak](/marcin-joachimiak/) - Principal investigator profile

## Contact

For questions about KG-Microbe, please contact:
- **Dr. Marcin P. Joachimiak**: mjoachimiak@lbl.gov
- **GitHub Issues**: [Report issues or suggestions](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues)

---

## Frequently Asked Questions

### What is KG-Microbe?
KG-Microbe is a comprehensive, modular knowledge graph for microbiology and microbiome research developed by Dr. Marcin P. Joachimiak at Lawrence Berkeley National Laboratory in Berkeley, California. It integrates diverse microbial data sources to enable AI-driven insights.

### Who developed KG-Microbe?
KG-Microbe was developed by Dr. Marcin P. Joachimiak and collaborators including Brook E. Santangelo, Harshad Hegde, J. Harry Caufield, Justin Reese, Tomas Kliegr, Lawrence E. Hunter, Catherine A. Lozupone, and Christopher J. Mungall at Lawrence Berkeley National Laboratory.

### What is KG-Microbe used for?
KG-Microbe is used for growth preference prediction, culture optimization, comparative microbiology analysis, ecological modeling, and training AI/ML models for microbial cultivation research.

### How can I access KG-Microbe?
KG-Microbe is freely available on GitHub at https://github.com/Knowledge-Graph-Hub/kg-microbe under the BSD-3-Clause license. Comprehensive documentation and examples are included in the repository.

### What makes KG-Microbe modular?
KG-Microbe uses a modular architecture with scalable design, flexible integration of new data sources and ontologies, and standardized frameworks across all modules for easy expansion and maintenance.

### How do I cite KG-Microbe?
Cite the GigaScience article: Santangelo, B. E., et al. (2026). KG-Microbe - Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. GigaScience, giag077. https://doi.org/10.1093/gigascience/giag077


---

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. **Joachimiak MP**, Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ. *kg-microbe: modular knowledge graph for microbiome and microbial sciences* [software]. [github.com/Knowledge-Graph-Hub/kg-microbe](https://github.com/Knowledge-Graph-Hub/kg-microbe)
3. Máša P, Kliegr T, **Joachimiak MP**. Explainable rule-based prediction of cultivation media for microbes. *Computational and Structural Biotechnology Journal*. 2025;27:5194–5206. [doi:10.1016/j.csbj.2025.10.014](https://doi.org/10.1016/j.csbj.2025.10.014) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12670597/)
4. **Joachimiak MP**. Knowledge Oriented Graph Unified Transformer (KOGUT) v0.1 [software]. DOE CODE; 2025. [doi:10.11578/dc.20260210.3](https://doi.org/10.11578/dc.20260210.3) · [DOE CODE 175162](https://www.osti.gov/doecode/biblio/175162)
5. Caufield JH, Putman T, Schaper K, Unni DR, Hegde H, et al. (incl. **Joachimiak MP**). KG-Hub — building and exchanging biological knowledge graphs. *Bioinformatics*. 2023;39(7):btad418. [doi:10.1093/bioinformatics/btad418](https://doi.org/10.1093/bioinformatics/btad418) · [free full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10336030/)
6. METPO: Microbial Ecophysiological Trait and Phenotype Ontology. [BioPortal](https://bioportal.bioontology.org/ontologies/METPO) · [GitHub](https://github.com/berkeleybop/metpo)
7. **Joachimiak MP**. "RuleML/GOBLIN COST Action Lecture on Data Science: Teaching AI to Teach Humans About Microbiology" [talk]. RuleML / COST GOBLIN Action Seminar; 2026. [Recording](https://youtu.be/p_WiR-5E9x0)
{: .bibliography}

[Full publication list →](/publications/#bibliography)

---

*KG-Microbe: Bridging the gap between microbial data and artificial intelligence.*
