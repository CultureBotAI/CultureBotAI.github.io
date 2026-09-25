"""Count ontology-prefix occurrences in each Mech's canonical record directory (feeds the heatmap).

Run from the site root: `python3 scripts/fleet/prefix_census.py`. Reads the Mech
checkouts through scripts/fleet/roots.py (set MECHS_ROOT to relocate them); writes derived data under _fleet/data and assets/fleet. See
_fleet/README.md for the whole pipeline.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import collections
import datetime
import json
import re

from roots import ORDER, record_paths, revision

P="CHEBI|pubchem\\.compound|PubChem|METPO|ENVO|NCBITaxon|GO|PR|UniProtKB|UniProt|cas|CAS|MESH|mesh|OBI|PATO|UBERON|FOODON|MICRO|MicrO|OMP|ECO|RO|BFO|IAO|ARO|NCIT|RHEA|KEGG|EC|Pfam|PFAM|InterPro|IPR|MediaDive|mediadive\\.compound|KOMODO|BacDive|GTDB|IMG|GOLD|DSMZ|ATCC|drugbank|DrugBank|PDB|TCDB|SO|CL|GAZ|PO|BTO|EMDB|CHEMBL\\.COMPOUND|PMID|DOI|doi|PHIPO|NCBIfam|ComplexPortal|SNOMED|gold\\.ecosystem|bacdive\\.isolation_source|mibig|MIBiG|npatlas|NPAtlas"
rx=re.compile(r"\b("+P+r"):[A-Za-z0-9_.\-]+")
norm={"pubchem.compound":"PubChem","mesh":"MESH","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","mediadive.compound":"MediaDive","MicrO":"MICRO","cas":"CAS","drugbank":"DrugBank","doi":"DOI","CHEMBL.COMPOUND":"ChEMBL","gold.ecosystem":"GOLD","mibig":"MIBiG","npatlas":"NPAtlas","bacdive.isolation_source":"BacDive"}


def census():
    """Count prefix occurrences per Mech. Minutes of I/O over every record."""
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
    # The run date travels in the file, not on it: git does not preserve mtimes,
    # so a fresh clone would otherwise make the page claim the corpora were
    # counted on the day someone cloned it (CultureBotAI.github.io#74).
    out["_as_of"]=datetime.date.today().isoformat()
    # And the revision each corpus was read at, so the census can be checked
    # against mech_stats.json, which counts the same files (#85).
    out["_revisions"]={m: revision(m) for m in ORDER}
    return out


def main():
    # Build the document before opening the file. `json.dump(census(), open(...))`
    # happens to be safe because arguments evaluate left to right, so a scan that
    # exits takes the process down before the truncation — but write it the
    # idiomatic way, with the open first, and a missing checkout leaves the
    # committed census at zero bytes. census() exits for ordinary reasons:
    # roots.mech_root when a checkout is absent, record_paths when a glob matches
    # nothing, both deliberately fail-closed. Also closes the handle (#102).
    document = census()
    with open(DATA + "/prefix_census.json", "w") as handle:
        json.dump(document, handle, indent=1)


# Guarded so the module can be imported for P, rx and norm alone. Without this
# the scan ran at import time: reading the prefix list cost four minutes and
# overwrote the committed census with a partial refresh, which is why the three
# prefix lists could not be tested against each other (#95).
if __name__ == "__main__":
    main()
