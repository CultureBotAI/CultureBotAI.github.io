"""Count ontology-prefix occurrences in each Mech's canonical record directory (feeds the heatmap).

Run from the site root: `python3 scripts/fleet/prefix_census.py`. Reads the Mech
checkouts through scripts/fleet/roots.py (set MECHS_ROOT to relocate them); writes derived data under _fleet/data and assets/fleet. See
_fleet/README.md for the whole pipeline.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import collections
import json
import re

from roots import ORDER, record_paths

P="CHEBI|pubchem\\.compound|PubChem|METPO|ENVO|NCBITaxon|GO|PR|UniProtKB|UniProt|cas|CAS|MESH|mesh|OBI|PATO|UBERON|FOODON|MICRO|MicrO|OMP|ECO|RO|BFO|IAO|ARO|NCIT|RHEA|KEGG|EC|Pfam|PFAM|InterPro|IPR|MediaDive|mediadive\\.compound|KOMODO|BacDive|GTDB|IMG|GOLD|DSMZ|ATCC|drugbank|DrugBank|PDB|TCDB|SO|CL|GAZ|PO|BTO|EMDB|CHEMBL\\.COMPOUND|PMID|DOI|doi|PHIPO|NCBIfam|ComplexPortal|SNOMED|gold\\.ecosystem|bacdive\\.isolation_source|mibig|MIBiG|npatlas|NPAtlas"
rx=re.compile(r"\b("+P+r"):[A-Za-z0-9_.\-]+")
norm={"pubchem.compound":"PubChem","mesh":"MESH","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","mediadive.compound":"MediaDive","MicrO":"MICRO","cas":"CAS","drugbank":"DrugBank","doi":"DOI","CHEMBL.COMPOUND":"ChEMBL","gold.ecosystem":"GOLD","mibig":"MIBiG","npatlas":"NPAtlas","bacdive.isolation_source":"BacDive"}
out={}
for m in ORDER:
    pc=collections.Counter(); n=0
    for f in record_paths(m):
            n+=1
            try: txt=open(f,encoding="utf-8",errors="ignore").read()
            except Exception: continue
            for p in rx.findall(txt): pc[norm.get(p,p)]+=1
    out[m]={"files":n,"prefixes":dict(pc.most_common())}
    print(m,n,dict(pc.most_common(14)),flush=True)
json.dump(out,open(DATA+"/prefix_census.json","w"),indent=1)
