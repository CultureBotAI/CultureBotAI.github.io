---
layout: page
title: "Resources — KG-Microbe Knowledge Graph and AI Tools"
description: "Access KG-Microbe knowledge graph, METPO ontology, and AI tools for microbial cultivation developed by Dr. Marcin P. Joachimiak at CultureBotAI."
permalink: /resources/
---

# Resources & Tools — KG-Microbe Knowledge Graph and AI Tools

CultureBotAI led by Dr. Marcin P. Joachimiak develops and maintains various computational resources, databases, and tools for the microbial research community, including the comprehensive KG-Microbe knowledge graph.

## Quick Navigation

**New to CultureBotAI?** Start with [Project Ecosystem & Workflows](#project-ecosystem--workflows) to understand how tools work together.

**Looking for specific tools?**
- [AI Curation Tools](#-ai-curation-tools) - CultureMech, MediaIngredientMech, CommunityMech (NEW!)
- [Growth Media Prediction](#growth-media-prediction--design) - MicroGrowLink, MicroGrowAgents
- [Chemical Data Processing](#micromediaparam) - CultureMech, MicroMediaParam
- [Genome Analysis](#data-processing--analysis) - eggnog_runner, eggnogtable
- [Literature Mining](#ai-agent-systems) - MATE-LLM
- [Specialized Research](#specialized-research-pipelines) - PFAS, Lanthanide bioprocessing
- [Advanced Research Tools](#advanced-research-tools) - Neurosymbolic reasoning, term extraction (NEW!)
- [Developer Resources](#developer-resources) - Claude Code skills, APIs (NEW!)

**Want to see workflows?** Jump to [Common Workflows](#common-workflows)

## 🧬 KG-Microbe: Microbial Knowledge Graph

### Overview
[KG-Microbe](https://github.com/Knowledge-Graph-Hub/kg-microbe) is our flagship resource developed by Dr. Marcin P. Joachimiak - a comprehensive knowledge graph that integrates diverse microbial data sources to enable AI-driven insights and predictions.

**📄 [Read the Preprint](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1)** - bioRxiv publication detailing kg-microbe development and applications.

### 📋 METPO Ontology Integration

The [Microbial Ecology and Taxonomy Phenotypic Ontology (METPO)](https://bioportal.bioontology.org/ontologies/METPO) plays a crucial role in kg-microbe by providing standardized terminology for microbial phenotypes and ecological characteristics.

**Key Benefits:**
- **Knowledge Organization** - METPO terms provide semantic structure to organize diverse microbial data within the kg-microbe knowledge graph
- **Text Extraction** - Standardized ontology terms power automated literature mining and text extraction processes
- **Semantic Consistency** - Ensures consistent representation of microbial characteristics across different data sources

**Links:**
- **BioPortal:** [https://bioportal.bioontology.org/ontologies/METPO](https://bioportal.bioontology.org/ontologies/METPO)
- **GitHub Repository:** [https://github.com/microbiomedata/METPO](https://github.com/microbiomedata/METPO)

### Key Features
- **Multi-source integration** from major biological databases
- **Semantic consistency** through ontology-driven organization  
- **Machine-readable formats** (RDF, Neo4j, JSON-LD)
- **Regular updates** with automated data refresh pipelines
- **API access** for programmatic data retrieval

### Data Sources
kg-microbe integrates data from:
- **NCBI Taxonomy** - Microbial taxonomy and phylogeny
- **UniProt** - Protein sequences and functional annotations
- **GO (Gene Ontology)** - Functional gene classifications
- **Environmental ontologies** - Habitat and growth condition data
- **Literature sources** - Manually curated cultivation data

### Applications
- **Growth condition prediction** for uncultured organisms
- **Taxonomic relationship exploration** and phylogenetic analysis
- **Literature mining** for cultivation protocols
- **Cross-organism comparison** of growth preferences

### Getting Started
```bash
# Clone the repository
git clone https://github.com/Knowledge-Graph-Hub/kg-microbe.git

# Install dependencies
cd kg-microbe
pip install -r requirements.txt

# Build latest knowledge graph
kg download
kg transform
kg merge
```

## 🌐 Project Ecosystem & Workflows

### Understanding the CultureBotAI Ecosystem

The CultureBotAI toolkit consists of interconnected projects organized into a data processing pipeline with kg-microbe as the foundational knowledge graph.

### Architecture Overview

```
                         ┌─────────────────┐
                         │   kg-microbe    │
                         │  (Foundation)   │
                         └────────┬────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
  ┌──────▼──────┐      ┌─────────▼─────────┐    ┌────────▼────────┐
  │ Data        │      │ Chemical          │    │ Genome          │
  │ Ingestion   │      │ Processing        │    │ Analysis        │
  │             │      │                   │    │                 │
  │ • assay-    │      │ • CultureMech     │    │ • eggnog_runner │
  │   metadata  │      │ • MicroMediaParam │    │ • eggnogtable   │
  │ • MATE-LLM  │      │                   │    │                 │
  └──────┬──────┘      └─────────┬─────────┘    └────────┬────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   AI Agent Systems      │
                    │                         │
                    │ • MicroGrowAgents       │
                    │ • MicroGrowLink         │
                    │ • PFASCommunityAgents   │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
  ┌──────▼──────┐     ┌─────────▼─────────┐   ┌────────▼────────┐
  │ Specialized │     │ Web Services      │   │ Analysis        │
  │ Apps        │     │                   │   │ Tools           │
  │             │     │ • MicroGrowLink   │   │                 │
  │ • PFAS-AI   │     │   Service         │   │ • microbe-rules │
  │ • CMM-AI    │     │                   │   │                 │
  └─────────────┘     └───────────────────┘   └─────────────────┘
```

## 🤖 AI Curation Tools

The **X-Mech Suite** (CultureMech, MediaIngredientMech, CommunityMech) forms the AI-powered curation pipeline that transforms unstructured microbial cultivation data from literature and laboratory records into standardized, machine-readable knowledge graphs.

### Pipeline Overview

```
Raw Cultivation Records (Literature, Lab Protocols)
    ↓
CultureMech → Chemical Entity Extraction (10,000+ media recipes)
    ↓
MediaIngredientMech → LLM-Assisted Ontology Mapping
    ↓
CommunityMech → Community Interaction Modeling
    ↓
KG-Microbe Knowledge Graph
    ↓
AI Predictions (MicroGrowAgents, MicroGrowLink)
```

### CultureMech - Microbial Culture Media Knowledge Graph
**[Dedicated Page](/culturemech/)** | **[GitHub Repository](https://github.com/CultureBotAI/CultureMech)** | **[Web Interface](https://culturebotai.github.io/CultureMech/)** | CC0-1.0 License | 7 ⭐

Comprehensive collection of 10,000+ culture media recipes from major international repositories with LinkML schema, ontology grounding (ChEBI, PubChem), and browser-based exploration.

**What it does**: Extracts chemical entities from unstructured media composition text and grounds them to standard chemical ontologies.

**→ [Learn more on the dedicated CultureMech page](/culturemech/)**

---

### MediaIngredientMech - LLM-Assisted Ingredient Curation
**[Dedicated Page](/mediaingredientmech/)** | **[GitHub Repository](https://github.com/CultureBotAI/MediaIngredientMech)** | Python

Curated media ingredient ontology mappings with LLM-assisted workflows for standardizing microbial cultivation ingredient data. Uses Large Language Models to intelligently map ingredient names to standardized ontology terms.

**What it does**: Leverages LLMs for semantic matching of ambiguous ingredient names to ChEBI, PubChem, and METPO ontologies with human-in-the-loop validation.

**→ [Learn more on the dedicated MediaIngredientMech page](/mediaingredientmech/)**

---

### CommunityMech - Microbial Community Interaction Modeling
**[Dedicated Page](/communitymech/)** | **[GitHub Repository](https://github.com/CultureBotAI/CommunityMech)** | **[Web Interface](https://culturebotai.github.io/CommunityMech/)** | BSD-3-Clause License | 2 ⭐

LinkML-based modeling of microbial communities with evidence-based ecological interactions for consortium design and multi-organism cultivation.

**What it does**: Provides structured representation of community composition, syntrophic interactions, and cultivation requirements for multi-species systems.

**Related**: Powers [PFASCommunityAgents](#pfascommunityagents) for AI-driven consortium design.

**→ [Learn more on the dedicated CommunityMech page](/communitymech/)**

---

### Common Workflows

#### Workflow 1: Novel Organism Media Prediction
1. Start with organism taxonomy/genome
2. Run eggnog_runner + eggnogtable (functional annotation)
3. Query kg-microbe (related organisms, known preferences)
4. Use MicroGrowAgents (integrate genome, literature, analogies)
5. Get media recommendations with evidence

#### Workflow 2: Chemical Compound Knowledge Graph Integration
1. Start with media composition text
2. Run CultureMech (extract chemical entities)
3. Run MicroMediaParam (map to ChEBI/PubChem)
4. Integrate into kg-microbe (standardized chemical data)
5. Enable downstream media predictions

#### Workflow 3: PFAS Biodegradation Consortia Design
1. Query PFAS-AI database (identify candidate organisms)
2. Extract genome features (eggnog_runner/eggnogtable)
3. Query kg-microbe (environmental compatibility)
4. Use PFASCommunityAgents (design optimized consortia)
5. Get consortium composition + rationale

#### Workflow 4: Literature-Driven Culture Optimization
1. Run MATE-LLM (extract cultivation protocols from papers)
2. Integrate into kg-microbe (structured cultivation data)
3. Use MicroGrowAgents LiteratureAgent (mine similar organisms)
4. Get evidence-based media recommendations

### Getting Started Guide

**For Growth Media Prediction:**
- Start with: MicroGrowAgents or MicroGrowLink
- Prerequisites: Access to kg-microbe knowledge graph
- Recommended workflow: Workflow 1

**For Chemical Data Processing:**
- Start with: CultureMech or MicroMediaParam
- Prerequisites: Media composition text data
- Recommended workflow: Workflow 2

**For Specialized Research:**
- PFAS biodegradation: Start with PFAS-AI, then PFASCommunityAgents
- Lanthanide bioprocessing: Start with CMM-AI

**For Web-Based Access:**
- API users: Start with MicroGrowLinkService
- Prerequisites: HTTP client, REST API knowledge

## 🔧 CultureBotAI Software & Tools

### Growth Media Prediction & Design

#### MicroGrowLink
**[GitHub Repository](https://github.com/CultureBotAI/MicroGrowLink)** | Python

Knowledge graph-based framework for predicting microbial growth media using advanced graph and transformer models. Integrates microbial, chemical, and environmental data into a heterogeneous knowledge graph and applies link prediction to forecast which media enable growth of given taxa.

**Supported Models:**
- RGT (Relational Graph Transformer)
- HGT (Heterogeneous Graph Transformer)
- NBFNet (Neural Bellman-Ford Network)

**Key Features:**
- Heterogeneous knowledge graph integration
- Advanced transformer-based link prediction
- Multi-modal data integration (microbial, chemical, environmental)

**Related Projects:**
- **Depends on:** kg-microbe (knowledge graph foundation), MicroMediaParam (chemical compound mappings)
- **Feeds into:** Media formulation recommendations, MicroGrowLinkService (API deployment)
- **Works with:** MicroGrowAgents (complementary multi-agent predictions)

---

#### MicroGrowAgents
**[GitHub Repository](https://github.com/CultureBotAI/MicroGrowAgents)** | Python | [Documentation](https://CultureBotAI.github.io/MicroGrowAgents)

Agent-based system for AI-driven microbial cultivation and growth media design. Bridges the microbial cultivation gap through AI-powered multi-agent systems that integrate knowledge graphs, machine learning, and experimental automation.

**Specialized Agents:**
- **LiteratureAgent** - Mining 245+ papers for cultivation protocols
- **AnalogyReasoningAgent** - Cross-organism comparison and reasoning
- **GenomeFunctionAgent** - Auxotrophy detection from 57 Bakta-annotated genomes (667K features)
- **MediaFormulationAgent** - Schema-driven media recommendation with evidence-based ingredient suggestions

**Key Achievements:**
- 864,363 validated species across bacteria, archaea, fungi, and protozoa (GTDB + LPSN + NCBI)
- Multi-modal reasoning combining literature mining, metabolic modeling (FBA/gap-filling), chemical similarity (208K+ embeddings)
- Genome-guided design for organism-specific media formulation

**Related Projects:**
- **Depends on:** kg-microbe (knowledge graph foundation), MicroMediaParam (chemical mappings), eggnogtable (genome annotations), MATE-LLM (literature extraction)
- **Feeds into:** Media formulation recommendations, PFASCommunityAgents (consortium design)
- **Works with:** MicroGrowLink (complementary prediction approach)

---

#### MicroMediaParam
**[GitHub Repository](https://github.com/CultureBotAI/MicroMediaParam)** | Python

Comprehensive chemical compound knowledge graph mapping pipeline for microbial growth media analysis. Extracts chemical compounds from media compositions and maps them to knowledge graph entities with standardized chemical properties.

**Features:**
- Processes 23,181 chemical entries from 1,807 microbial growth media
- 78% ChEBI coverage (18,088 compounds mapped)
- Multi-database mapping to ChEBI, PubChem, and CAS-RN identifiers
- Intelligent hydrate parsing and molecular weight calculation
- Solution expansion for DSMZ solution references
- 99.99% chemical mapping accuracy

**Related Projects:**
- **Depends on:** CultureMech (chemical entity extraction)
- **Feeds into:** kg-microbe (standardized chemical data), MicroGrowAgents (chemical mappings), MicroGrowLink (knowledge graph integration)
- **Works with:** assay-metadata (compound identification)

---

#### CultureMech
**[Dedicated Page](/culturemech/)** | **[GitHub Repository](https://github.com/CultureBotAI/CultureMech)** | **[Web Interface](https://culturebotai.github.io/CultureMech/)** | CC0-1.0 License

Comprehensive collection of 10,000+ culture media recipes with chemical entity extraction and ontology grounding. Part of the X-Mech AI curation suite.

**→ See the [dedicated CultureMech page](/culturemech/) for full documentation, use cases, and examples.**

**Related Projects:**
- **Depends on:** Text-based media composition data
- **Feeds into:** MicroMediaParam (entity mapping), kg-microbe (chemical data integration), [MediaIngredientMech](/mediaingredientmech/) (ingredient curation)
- **Works with:** assay-metadata (standardized substrate processing)

### Specialized Research Pipelines

#### CMM-AI: Lanthanide Bioprocessing Data Pipeline
**[GitHub Repository](https://github.com/CultureBotAI/CMM-AI)** | Python

Automated data pipeline for lanthanide bioprocessing research, focusing on rare earth element-dependent biological processes in microorganisms. Integrates multiple biological databases to create comprehensive research datasets.

**Scientific Focus:**
- XoxF methanol dehydrogenase systems (lanthanide-dependent enzymes)
- Methylotrophic bacteria (Methylobacterium, Methylorubrum, Paracoccus)
- Environmental metal cycling and biogeochemistry
- Siderophore/lanthanophore transport mechanisms
- PQQ-dependent enzyme complexes

**Related Projects:**
- **Depends on:** kg-microbe (organism data), eggnogtable (functional annotations)
- **Feeds into:** Specialized lanthanide bioprocessing research
- **Works with:** MicroGrowAgents (media optimization for lanthanide-dependent organisms)

---

#### PFAS-AI: Machine Learning-Enabled PFAS Biodegradation Pipeline
**[GitHub Repository](https://github.com/CultureBotAI/PFAS-AI)** | Python

ML-enabled data pipeline for PFAS biodegradation research, focusing on identification and characterization of microorganisms capable of degrading per- and polyfluoroalkyl substances (PFAS).

**Research Objectives:**
- **ML-Powered Database** - Semantically-aware database using KG-Microbe platform to identify putative PFAS biodegradation genes, pathways, taxa, and environments
- **Intelligent Consortia Design** - Graph learning and LLMs to design optimized microbial consortia for PFAS remediation

**Scientific Focus:**
- C-F bond cleavage mechanisms (dehalogenases and defluorinases)
- Fluoride resistance systems
- Hydrocarbon degradation pathways
- Environmental context (AFFF-contaminated sites, groundwater, wastewater)

**Related Projects:**
- **Depends on:** kg-microbe (organism and gene identification)
- **Feeds into:** PFASCommunityAgents (consortium design)
- **Works with:** eggnogtable (functional gene annotations)

---

#### PFASCommunityAgents
**[GitHub Repository](https://github.com/CultureBotAI/PFASCommunityAgents)** | Python

Multi-agent system for designing optimized microbial consortia for PFAS biodegradation. Uses AI-powered reasoning to compose consortia with complementary metabolic capabilities and syntrophic relationships.

**Key Features:**
- Consortium composition optimization
- Syntrophic relationship prediction
- Environmental context-aware design
- Multi-species compatibility assessment

**Related Projects:**
- **Depends on:** PFAS-AI (candidate organism database), MicroGrowAgents (agent architecture), kg-microbe (organism relationships)
- **Feeds into:** PFAS remediation research and consortium cultivation
- **Works with:** MicroGrowAgents (media design for consortia)

### Data Processing & Analysis

#### assay-metadata: BacDive API Assay Metadata Extractor
**[GitHub Repository](https://github.com/CultureBotAI/assay-metadata)** | Python

Extracts API assay metadata from BacDive JSON data with comprehensive identifier mappings to CHEBI, EC, RHEA, and PubChem databases.

**Capabilities:**
- Parses 99,392 bacterial strain records from BacDive
- Extracts 17 unique API kit types (API zym, API 50CHac, etc.)
- Maps substrate codes to CHEBI and PubChem identifiers
- Maps enzyme EC numbers to RHEA reaction databases
- Generates consolidated JSON metadata files

**Related Projects:**
- **Depends on:** BacDive API data
- **Feeds into:** kg-microbe (phenotypic assay data integration)
- **Works with:** MicroMediaParam (compound identification), CultureMech (substrate processing)

---

#### eggnog_runner
**[GitHub Repository](https://github.com/CultureBotAI/eggnog_runner)** | Python

Automated pipeline for running EggNOG-mapper functional annotation at scale. Processes genome assemblies in batch to generate functional annotations for downstream analysis.

**Features:**
- Batch genome processing with parallel execution
- Automated EggNOG-mapper execution
- Output standardization and organization
- Error handling and retry logic

**Related Projects:**
- **Depends on:** kg-microbe (genome data), EggNOG-mapper tool
- **Feeds into:** eggnogtable (annotation post-processing)
- **Works with:** MicroGrowAgents GenomeFunctionAgent (functional predictions)

---

#### eggnogtable
**[GitHub Repository](https://github.com/CultureBotAI/eggnogtable)** | Python

Post-processing pipeline for EggNOG-mapper output into structured datasets. Extracts and organizes functional annotations including GO terms, EC numbers, and KEGG pathways.

**Features:**
- GO term extraction and organization
- EC number mapping
- KEGG pathway assignment
- Ontology term integration
- Structured dataset generation

**Related Projects:**
- **Depends on:** eggnog_runner (annotation output)
- **Feeds into:** MicroGrowAgents GenomeFunctionAgent (auxotrophy detection), kg-microbe (functional annotations), CMM-AI (enzyme identification)
- **Works with:** assay-metadata (enzyme EC number mapping)

---

#### microbe-rules: Machine Learning Models for Microbial Data
**[GitHub Repository](https://github.com/CultureBotAI/microbe-rules)** | Python

Research code repository containing machine learning models and analysis pipelines for binary classification and comparative modeling of microbial datasets.

**Features:**
- Binary classification models for microbial data
- Model comparison and evaluation frameworks
- Automated data preparation pipelines
- Reproducible research workflows

**Related Projects:**
- **Depends on:** kg-microbe (training data), various microbial datasets
- **Feeds into:** Model optimization research
- **Works with:** MicroGrowLink (model comparison), MicroGrowAgents (ML component evaluation)

### AI Agent Systems

#### MATE-LLM
**[GitHub Repository](https://github.com/CultureBotAI/MATE-LLM)** | Python

LLM-powered system for extracting structured microbial information from scientific literature. Automates the extraction of cultivation protocols, growth conditions, and microbial annotations from research papers.

**Key Features:**
- Entity extraction from scientific literature
- Automated cultivation protocol annotation
- Literature mining for growth conditions
- Knowledge graph integration preparation
- Structured data generation from unstructured text

**Related Projects:**
- **Depends on:** Scientific literature corpus, LLM APIs
- **Feeds into:** kg-microbe (literature-derived data), MicroGrowAgents LiteratureAgent (cultivation protocols)
- **Works with:** METPO ontology (standardized terminology)

### Web Services & APIs

#### MicroGrowLinkService
**[GitHub Repository](https://github.com/CultureBotAI/MicroGrowLinkService)** | Python | REST API

RESTful API service wrapper for MicroGrowLink prediction models. Provides HTTP endpoints for programmatic access to growth media predictions and enables integration with laboratory information management systems (LIMS).

**Key Features:**
- HTTP API endpoints for predictions
- Model serving infrastructure
- Batch prediction support
- LIMS integration capabilities
- Production deployment configuration

**Related Projects:**
- **Depends on:** MicroGrowLink (prediction models), kg-microbe (knowledge graph)
- **Feeds into:** External applications, LIMS integrations, web interfaces
- **Works with:** MicroGrowAgents (complementary API services)

---

## 🔬 Advanced Research Tools

#### neurosymbolreason - Neurosymbolic Analogy Reasoning
**[GitHub Repository](https://github.com/CultureBotAI/neurosymbolreason)** | Python

Neurosymbolic analogy reasoning on microbial knowledge graph embeddings to analyze relationships between microbial taxa and their physical growth preferences. Combines neural network embeddings with symbolic reasoning for cross-organism inference.

**Key Features:**
- Knowledge graph embedding analysis
- Analogy-based reasoning for growth preferences
- Taxonomic relationship exploration
- Novel organism growth condition inference

**Related Projects:**
- **Depends on:** kg-microbe (knowledge graph embeddings), taxonomic data
- **Feeds into:** MicroGrowAgents (AnalogyReasoningAgent), growth prediction pipelines
- **Works with:** MicroGrowLink (complementary prediction approach)

---

#### auto-term-catalog - Automated Term Extraction
**[GitHub Repository](https://github.com/CultureBotAI/auto-term-catalog)** | Python

Code for extracting AUTO terms from ontoGPT output. Processes ontology-based text mining results to create curated term catalogs for microbial cultivation research.

**Key Features:**
- OntoGPT output processing
- Automated term extraction and cataloging
- Integration with METPO ontology
- Standardized term generation

**Related Projects:**
- **Depends on:** OntoGPT output, METPO ontology
- **Feeds into:** kg-microbe (ontology terms), MATE-LLM (standardized vocabulary)
- **Works with:** Literature mining pipelines

---

## 🛠️ Developer Resources

#### culturebot-skills - Claude Code Skills
**[GitHub Repository](https://github.com/CultureBotAI/culturebot-skills)** | Skills/Configuration

Claude Code skills for CultureBot/KG-Microbe projects. Custom skills and workflows for AI-assisted development within the CultureBotAI ecosystem.

**What it provides:**
- Pre-configured Claude Code skills for common tasks
- Project-specific development workflows
- Integration helpers for CultureBotAI tools
- Best practices and code patterns

**Use Cases:**
- Automated code generation for kg-microbe integrations
- Data pipeline development assistance
- Documentation generation
- Testing and validation workflows

**Getting Started:**
```bash
# Install Claude Code skills
git clone https://github.com/CultureBotAI/culturebot-skills.git
# Follow setup instructions in repository README
```

---

## 📊 Datasets

### Curated Cultivation Database
Curated collection of cultivation protocols for diverse microorganisms based on reference sources and literature.

**Contents:**
- Growth media compositions
- Environmental conditions (temperature, pH, atmosphere)
- Cultivation methods and protocols
- Literature references

### Environmental Metadata Collection
Comprehensive dataset linking microorganisms to their natural habitats and environmental conditions.

## 🌐 Related Organizations & Resources

### Academic & Research Institutions
- [**ABPDU**](https://abpdu.lbl.gov/) - Advanced Biofuels and Bioproducts Process Development Unit
- [**BacDive**](https://bacdive.dsmz.de/) - Bacterial Diversity Metadatabase
- [**Cultivarium**](https://www.cultivarium.org/) - Global microbial cultivation platform
- [**JBEI**](https://www.jbei.org/) - Joint BioEnergy Institute
- [**JGI GOLD**](https://gold.jgi.doe.gov/) - Genomes Online Database
- [**KBase**](https://www.kbase.us/) - Systems Biology Knowledgebase
- [**NMDC**](https://microbiomedata.org/) - National Microbiome Data Collaborative
- [**Palsson Lab**](https://systemsbiology.ucsd.edu/) - UC San Diego Systems Biology Research Group

### Commercial Organizations
- [**Biolog**](https://www.biolog.com/) - Microbial identification and characterization systems
- [**Isolation Bio**](https://isolationbio.com/) - Microbial isolation and cultivation technology

## 📚 Documentation & Tutorials

### API Documentation
Comprehensive documentation for programmatic access to kg-microbe and related tools:
- Neo4j graph database interface  
- Python SDK usage examples
- Data schema specifications

### Tutorials
Coming soon!

### Example Notebooks
Jupyter notebooks demonstrating practical applications:
- Growth condition prediction workflows
- Literature mining pipelines
- Data visualization examples

## 🔗 Data Access & APIs

### Direct Downloads
- **Knowledge Graph Dumps** - Complete RDF/TTL files
- **Processed Datasets** - CSV/JSON formatted data tables
- **Ontology Files** - OWL/RDF ontology definitions

### API Endpoints
Coming soon

### Query Interfaces
Coming soon

## 📦 Software Packages

### Python Packages
Coming soon

## 🤝 Community & Collaboration

### Contributing
We welcome contributions from the research community:
- **Data contributions** - Share cultivation protocols and growth data
- **Software development** - Contribute to open source tools
- **Literature curation** - Help extract cultivation data from papers
- **Validation** - Test predictions against experimental results

### Discussion Forums
- **GitHub Discussions** - Technical questions and feature requests
- **Slack Community** - Real-time collaboration and support
- **Monthly Webinars** - Updates and community presentations

### Citation
If you use kg-microbe or other CultureBotAI resources in your research, please cite:

```
Santangelo, B.E., Hegde, H., Caufield, J.H., Reese, J., Kliegr, T., Hunter, L.E., 
Lozupone, C.A., Mungall, C.J., Joachimiak, M.P. (2025). KG-Microbe - Building 
Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. 
bioRxiv. https://doi.org/10.1101/2025.02.24.639989
```

---

## Support & Contact

For technical support, collaboration inquiries, or questions about our resources:

- **Email:** [MJoachimiak@lbl.gov](mailto:MJoachimiak@lbl.gov)
- **GitHub Issues:** [Report bugs or request features](https://github.com/CultureBotAI)
- **Documentation:** Comprehensive guides and API references
- **Community Forums:** Connect with other researchers and developers