---
layout: page
title: "Resources — KG-Microbe Knowledge Graph and AI Tools"
description: "Access KG-Microbe knowledge graph, METPO ontology, and AI tools for microbial cultivation developed by Dr. Marcin P. Joachimiak at CultureBotAI."
permalink: /resources/
---

# Resources & Tools — KG-Microbe Knowledge Graph and AI Tools

CultureBotAI led by Dr. Marcin P. Joachimiak develops and maintains various computational resources, databases, and tools for the microbial research community, including the comprehensive KG-Microbe knowledge graph.

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

---

#### microbe-rules: Machine Learning Models for Microbial Data
**[GitHub Repository](https://github.com/CultureBotAI/microbe-rules)** | Python

Research code repository containing machine learning models and analysis pipelines for binary classification and comparative modeling of microbial datasets.

**Features:**
- Binary classification models for microbial data
- Model comparison and evaluation frameworks
- Automated data preparation pipelines
- Reproducible research workflows


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