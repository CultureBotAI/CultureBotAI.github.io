"""Assemble the page's compact data from census, graph and full-cell summaries.

Run from the site root: `python3 scripts/fleet/build_data.py`, after the three
scanning passes. Reads no checkout: its inputs are the JSON those passes wrote
under _fleet/data, and its output goes back there. See _fleet/README.md for the
whole pipeline.

Importing this module performs no file I/O (#97). The heatmap includes every
vocabulary present in the dated census. Record lists cover every populated
cell; shared-term edges retain the prefixes indexed by build_subsets.py.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roots import CITATION, ORDER
from build_subsets import PREF

S=DATA
def vocabularies(census):
    """Every counted namespace in the measured Mechs, without scan metadata."""
    return {prefix for mech in ORDER for prefix in census[mech]["prefixes"]}


def build(sub, cen, cell_summary):
    """The blob the page embeds, refusing incomplete or mixed cell snapshots."""
    pins=cen.get("_revisions", {})
    if set(pins) != set(ORDER) or sub.get("_revisions") != pins or cell_summary.get("_revisions") != pins:
        raise ValueError("Census, graph and cell source revisions must agree for every Mech")
    expected={m+"|"+v:n for m in ORDER for v,n in cen[m]["prefixes"].items() if n}
    summaries=cell_summary["cells"]
    if set(summaries) != set(expected):
        raise ValueError("Record lists must cover every populated census cell exactly")
    for key,row in summaries.items():
        m,v=key.split("|")
        if type(row.get("occurrences")) is not int or row["occurrences"] != expected[key]:
            raise ValueError(f"Cell occurrences must match the census: {key}")
        if type(row.get("records")) is not int or not 0 < row["records"] <= min(row["occurrences"],cen[m]["files"]):
            raise ValueError(f"Invalid matching-record count: {key}")
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise ValueError(f"Missing cell asset hash: {key}")
    edges=[]
    for k,v in sub["edges"].items():
        a,b=k.split("|")
        if v["n"]==0: continue
        edges.append({"a":a,"b":b,"n":v["n"],"by":v["by"],"ex":v["ex"]})
    voc=vocabularies(cen)
    heat={m:{v:cen[m]["prefixes"].get(v,0) for v in sorted(voc)} for m in ORDER}
    cells={k.replace("|","--"):row["records"] for k,row in summaries.items()}

    # DOI and PMID lead; every remaining column runs from the most widely used
    # vocabulary to the least: first by how many Mechs ground anything in it,
    # then by total occurrences across the fleet. Unlike record-list totals,
    # occurrence counts are available for every vocabulary in this census.
    # Name last so the order is stable for equal counts.
    def reach(v): return sum(1 for m in ORDER if heat[m][v])
    def occurrences(v): return sum(heat[m][v] for m in ORDER)
    leading=[v for v in ("DOI", "PMID") if v in voc]
    VOC_ORDER=leading+sorted(voc-set(leading),key=lambda v:(-reach(v),-occurrences(v),v))
    for v in VOC_ORDER: print(f"  {v:<18} {reach(v)} mechs {occurrences(v):>9,} occurrences")

    # Header filters preserve the old graph-index coverage, independently of
    # the newly complete record lists. Merely mentioning a vocabulary in an
    # unlinked census record does not add a graph filter.
    indexed={key.split("|")[1] for key,n in sub["cells"].items() if n}
    indexed.update(p for edge in edges for p,n in edge["by"].items() if n)
    indexed_voc=sorted(indexed & set(PREF) & voc - set(CITATION))
    return {"order":ORDER,"voc":VOC_ORDER,"heat":heat,"cells":cells,
            "indexed_voc":indexed_voc,"vocab_edges":edges}


def main():
    sub=json.load(open(f"{S}/subsets_summary.json")); cen=json.load(open(f"{S}/prefix_census.json"))
    cell_summary=json.load(open(f"{S}/cells_summary.json"))
    document=build(sub, cen, cell_summary)
    with open(f"{S}/fleet_data.json","w") as handle:
        json.dump(document,handle,separators=(",",":"),ensure_ascii=False)
    edges=document["vocab_edges"]
    print(len(edges),"edges;",os.path.getsize(f"{S}/fleet_data.json"),"bytes")
    for e in sorted(edges,key=lambda e:-e["n"])[:6]: print(e["a"],e["b"],e["n"],e["by"],[x["label"] for x in e["ex"]])


if __name__ == "__main__":
    main()
