"""Assemble _fleet/data/fleet_data.json, the compact blob embedded in the page, from subsets_summary.json and prefix_census.json.

Run from the site root: `python3 scripts/fleet/build_data.py`, after the two
scanning passes. Reads no checkout: its inputs are the JSON those passes wrote
under _fleet/data, and its output goes back there. See _fleet/README.md for the
whole pipeline.

Importing this module performs no file I/O (#97). The heatmap includes every
vocabulary present in the dated census; the separately built record lists and
shared-term edges cover the prefixes indexed by build_subsets.py.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roots import CITATION, ORDER

S=DATA
def vocabularies(census):
    """Every counted namespace in the measured Mechs, without scan metadata."""
    return {prefix for mech in ORDER for prefix in census[mech]["prefixes"]}


def build(sub, cen):
    """The blob the page embeds, from the two scanning passes' output."""
    edges=[]
    for k,v in sub["edges"].items():
        a,b=k.split("|")
        if v["n"]==0: continue
        edges.append({"a":a,"b":b,"n":v["n"],"by":v["by"],"ex":v["ex"]})
    voc=vocabularies(cen)
    heat={m:{v:cen[m]["prefixes"].get(v,0) for v in sorted(voc)} for m in ORDER}
    cells={k.replace("|","--"):n for k,n in sub["cells"].items()}

    # Heatmap columns run left to right from the most widely shared vocabulary to
    # the least: first by how many Mechs ground anything in it, then, for the many
    # ties, by total occurrences across the fleet. Unlike record-list totals,
    # occurrence counts are available for every vocabulary in this census.
    # Name last so the order is stable for equal counts.
    def reach(v): return sum(1 for m in ORDER if heat[m][v])
    def occurrences(v): return sum(heat[m][v] for m in ORDER)
    # CITATION comes from roots.py, the same list build_subsets.py uses to decide
    # which prefixes get no record lists. Keep citable works together at the
    # right, after the ontology, database and registry vocabularies.
    VOC_ORDER=sorted((v for v in voc if v not in CITATION),key=lambda v:(-reach(v),-occurrences(v),v))+[v for v in CITATION if v in voc]
    for v in VOC_ORDER: print(f"  {v:<18} {reach(v)} mechs {occurrences(v):>9,} occurrences")

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
