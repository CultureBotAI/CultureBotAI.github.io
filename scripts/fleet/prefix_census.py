"""Count ontology-prefix occurrences in each Mech's canonical record directory (feeds the heatmap).

Run from the site root: `python3 scripts/fleet/prefix_census.py`. Reads the local Mech
checkouts named in MECH_ROOTS below (override with environment variables of the
same names); writes derived data under _fleet/data and assets/fleet. See
_fleet/README.md for the whole pipeline.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import re, glob, json, os, collections
K=os.environ.get("KG_MICROBE_ROOT","/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe"); O=os.environ.get("ONTOLOGY_ROOT","/Users/marcin/Documents/VIMSS/ontology")  # MECH_ROOTS
MECHS={
 "CultureMech":[f"{K}/CultureMech/data/merge_yaml/merged/*.yaml"],
 "MediaIngredientMech":[f"{K}/MediaIngredientMech/data/ingredients/**/*.yaml"],
 "CommunityMech":[f"{K}/CommunityMech/CommunityMech/kb/communities/*.yaml",f"{K}/CommunityMech/CommunityMech/data/isolates/*.yaml"],
 "AntibioticMech":[f"{K}/AntibioticMech/data/antibiotics/**/*.yaml"],
 "TraitMech":[f"{K}/TraitMech/data/traits/**/*.yaml"],
 "ProteinTraitsMech":[f"{O}/ProteinTraitsMech/data/traits/**/*.yaml"],
 "CellStructureMech":[f"{K}/CellStructureMech/data/structures/**/*.yaml"],
 "HabitatMech":[f"{O}/HabitatMech/data/habitats/**/*.yaml"],
}
P="CHEBI|pubchem\\.compound|PubChem|METPO|ENVO|NCBITaxon|GO|PR|UniProtKB|UniProt|cas|CAS|MESH|mesh|OBI|PATO|UBERON|FOODON|MICRO|MicrO|OMP|ECO|RO|BFO|IAO|ARO|NCIT|RHEA|KEGG|EC|Pfam|PFAM|InterPro|IPR|MediaDive|mediadive\\.compound|KOMODO|BacDive|GTDB|IMG|GOLD|DSMZ|ATCC|drugbank|DrugBank|PDB|TCDB|SO|CL|GAZ|PO|BTO|EMDB|CHEMBL\\.COMPOUND|PMID|DOI|doi|PHIPO|NCBIfam|ComplexPortal|SNOMED|gold\\.ecosystem|bacdive\\.isolation_source"
rx=re.compile(r"\b("+P+r"):[A-Za-z0-9_.\-]+")
norm={"pubchem.compound":"PubChem","mesh":"MESH","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","mediadive.compound":"MediaDive","MicrO":"MICRO","cas":"CAS","drugbank":"DrugBank","doi":"DOI","CHEMBL.COMPOUND":"ChEMBL","gold.ecosystem":"GOLD","bacdive.isolation_source":"BacDive"}
out={}
for m,globs in MECHS.items():
    pc=collections.Counter(); n=0
    for g in globs:
        for f in glob.glob(g,recursive=True):
            n+=1
            try: txt=open(f,encoding="utf-8",errors="ignore").read()
            except Exception: continue
            for p in rx.findall(txt): pc[norm.get(p,p)]+=1
    out[m]={"files":n,"prefixes":dict(pc.most_common())}
    print(m,n,dict(pc.most_common(14)),flush=True)
json.dump(out,open(DATA+"/prefix_census.json","w"),indent=1)
