"""Assemble _fleet/data/fleet_data.json, the compact blob embedded in the page, from subsets_summary.json and prefix_census.json.

Run from the site root: `python3 scripts/fleet/build_data.py`. Reads the local Mech
checkouts named in MECH_ROOTS below (override with environment variables of the
same names); writes derived data under _fleet/data and assets/fleet. See
_fleet/README.md for the whole pipeline.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import json, os
S=DATA
sub=json.load(open(f"{S}/subsets_summary.json")); cen=json.load(open(f"{S}/prefix_census.json"))
ORDER=["HabitatMech","CommunityMech","TraitMech","CellStructureMech","ProteinTraitsMech","AntibioticMech","MediaIngredientMech","CultureMech"]
VOC=["CHEBI","NCBITaxon","GO","ENVO","METPO","ARO","UniProt","InterPro","Pfam","RHEA","PDB","PATO","UBERON","FOODON","BTO","GTDB","KEGG","CAS","PMID","DOI"]
edges=[]
for k,v in sub["edges"].items():
    a,b=k.split("|")
    if v["n"]==0: continue
    edges.append({"a":a,"b":b,"n":v["n"],"by":v["by"],"ex":v["ex"]})
heat={m:{v:cen[m]["prefixes"].get(v,0) for v in VOC} for m in ORDER}
cells={k.replace("|","--"):n for k,n in sub["cells"].items()}
json.dump({"order":ORDER,"voc":VOC,"heat":heat,"cells":cells,"vocab_edges":edges},open(f"{S}/fleet_data.json","w"),separators=(",",":"),ensure_ascii=False)
print(len(edges),"edges;",os.path.getsize(f"{S}/fleet_data.json"),"bytes")
for e in sorted(edges,key=lambda e:-e["n"])[:6]: print(e["a"],e["b"],e["n"],e["by"],[x["label"] for x in e["ex"]])
