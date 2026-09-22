"""Assemble _fleet/data/fleet_data.json, the compact blob embedded in the page, from subsets_summary.json and prefix_census.json.

Run from the site root: `python3 scripts/fleet/build_data.py`, after the two
scanning passes. Reads no checkout: its inputs are the JSON those passes wrote
under _fleet/data, and its output goes back there. See _fleet/README.md for the
whole pipeline.

Everything below the constants sits behind main(), so VOC can be imported and
checked against the other two prefix lists without reading or writing any data
(#97). Before that, importing this module loaded both JSON inputs and rewrote
fleet_data.json, so the test that pins the three lists to each other had to
parse VOC out of the source text instead.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roots import CITATION, ORDER

S=DATA
VOC=["CHEBI","NCBITaxon","GO","ENVO","METPO","ARO","UniProt","InterPro","Pfam","RHEA","PDB","PATO","UBERON","FOODON","BTO","GTDB","KEGG","CAS","MIBiG","NPAtlas","PMID","DOI"]


def build(sub, cen):
    """The blob the page embeds, from the two scanning passes' output."""
    edges=[]
    for k,v in sub["edges"].items():
        a,b=k.split("|")
        if v["n"]==0: continue
        edges.append({"a":a,"b":b,"n":v["n"],"by":v["by"],"ex":v["ex"]})
    heat={m:{v:cen[m]["prefixes"].get(v,0) for v in VOC} for m in ORDER}
    cells={k.replace("|","--"):n for k,n in sub["cells"].items()}

    # Heatmap columns run left to right from the most widely shared vocabulary to
    # the least: first by how many Mechs ground anything in it, then, for the many
    # ties at nine and at one, by the total records citing it across the fleet.
    # Name last so the order is stable when a vocabulary appears in no records.
    def reach(v): return sum(1 for m in ORDER if heat[m][v])
    def records(v): return sum(cells.get(f"{m}--{v}",0) for m in ORDER)
    # CITATION comes from roots.py, the same list build_subsets.py uses to decide
    # which prefixes get no record lists. Those two have to agree: a citation
    # prefix would sort to the far left on Mech count with nothing to break the
    # tie, which is what the pin exists to prevent.
    VOC_ORDER=sorted((v for v in VOC if v not in CITATION),key=lambda v:(-reach(v),-records(v),v))+[v for v in CITATION if v in VOC]
    for v in VOC_ORDER: print(f"  {v:<10} {reach(v)} mechs {records(v):>9,} records")

    return {"order":ORDER,"voc":VOC_ORDER,"heat":heat,"cells":cells,"vocab_edges":edges}


def main():
    sub=json.load(open(f"{S}/subsets_summary.json")); cen=json.load(open(f"{S}/prefix_census.json"))
    document=build(sub, cen)
    with open(f"{S}/fleet_data.json","w") as handle:
        json.dump(document,handle,separators=(",",":"),ensure_ascii=False)
    edges=document["vocab_edges"]
    print(len(edges),"edges;",os.path.getsize(f"{S}/fleet_data.json"),"bytes")
    for e in sorted(edges,key=lambda e:-e["n"])[:6]: print(e["a"],e["b"],e["n"],e["by"],[x["label"] for x in e["ex"]])


if __name__ == "__main__":
    main()
