---
layout: page
title: Resources
permalink: /resources/
---

# Resources & Tools

CultureBotAI develops and maintains various computational resources, databases, and tools for the microbial research community.

## 🧬 kg-microbe: Microbial Knowledge Graph

### Overview
[kg-microbe](https://github.com/Knowledge-Graph-Hub/kg-microbe) is our flagship resource - a comprehensive knowledge graph that integrates diverse microbial data sources to enable AI-driven insights and predictions.

**📄 [Read the Preprint](https://www.biorxiv.org/content/10.1101/2025.02.24.639989v1)** - bioRxiv publication detailing kg-microbe development and applications.

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
- **KEGG** - Metabolic pathways and enzyme information
- **Environmental ontologies** - Habitat and growth condition data
- **Literature sources** - Manually curated cultivation data

### Applications
- **Growth condition prediction** for uncultured organisms
- **Media optimization** using metabolic network analysis
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

# Download latest knowledge graph
make download
```

## 🔧 Computational Tools

### CultureBot Predictor
AI-powered tool for predicting optimal growth conditions for target microorganisms.

**Features:**
- Machine learning models trained on kg-microbe data
- Growth condition recommendations
- Media composition suggestions
- Confidence scoring for predictions

### Cultivation Protocol Generator
Automated generation of cultivation protocols based on organism characteristics and environmental preferences.

### Culture Monitoring Dashboard
Real-time monitoring and analysis platform for automated culture systems.

## 📊 Datasets

### Curated Cultivation Database
Manually curated collection of successful cultivation protocols for diverse microorganisms.

**Contents:**
- Growth media compositions
- Environmental conditions (temperature, pH, atmosphere)
- Cultivation methods and protocols
- Success rates and optimization notes
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
- REST API endpoints
- GraphQL query interface  
- Python SDK usage examples
- Data schema specifications

### Tutorials
Step-by-step guides for common use cases:
- **"Predicting Growth Conditions"** - Using kg-microbe for cultivation planning
- **"Media Optimization"** - Computational approaches to media design
- **"Integration Workflows"** - Connecting kg-microbe with laboratory systems
- **"Knowledge Graph Querying"** - Advanced SPARQL and Cypher queries

### Example Notebooks
Jupyter notebooks demonstrating practical applications:
- Growth condition prediction workflows
- Metabolic network analysis
- Literature mining pipelines
- Data visualization examples

## 🔗 Data Access & APIs

### Direct Downloads
- **Knowledge Graph Dumps** - Complete RDF/TTL files
- **Processed Datasets** - CSV/JSON formatted data tables
- **Ontology Files** - OWL/RDF ontology definitions

### API Endpoints
```
# Base API URL
https://api.culturebotai.github.io/v1/

# Example endpoints
/organisms/{taxid}        # Organism information
/growth-conditions/{taxid} # Growth condition data  
/media/{organism_id}      # Media recommendations
/predict                  # Growth prediction service
```

### Query Interfaces
- **SPARQL Endpoint** - Semantic queries over RDF data
- **GraphQL API** - Flexible graph-based queries
- **REST API** - Standard HTTP-based access

## 📦 Software Packages

### Python Packages
```bash
pip install kg-microbe           # Core knowledge graph utilities
pip install culturebot-predict  # Growth prediction models
pip install microbe-media       # Media optimization tools
```

### R Packages
```r
devtools::install_github("CultureBotAI/kg-microbe-r")
devtools::install_github("CultureBotAI/growth-predictor-r")
```

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
Joachimiak, M.P. et al. (2025). kg-microbe: A comprehensive knowledge graph 
for microbial cultivation and AI-driven growth prediction. bioRxiv. 
https://doi.org/10.1101/2025.02.24.639989
```

---

## Support & Contact

For technical support, collaboration inquiries, or questions about our resources:

- **Email:** [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- **GitHub Issues:** [Report bugs or request features](https://github.com/CultureBotAI)
- **Documentation:** Comprehensive guides and API references
- **Community Forums:** Connect with other researchers and developers