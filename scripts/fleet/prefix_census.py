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

from roots import ORDER, read_record, record_paths, revision, unchanged

# The same registry is written several ways across the fleet: TaxonMech uses
# lowercase bioregistry-style prefixes (gold:, bacdive:, img.taxon:), others the
# upper-case forms, and a few Mechs qualify a registry by entity (kegg.compound:,
# mediadive.medium:). Each spelling found in the records folds into one name
# here, so a registry is not counted under one spelling and dropped under
# another. The spellings added for #84 and #255 were measured by scanning every
# record at the #120 pins; all were missed before, 1.49 million GOLD and 556,160
# BacDive identifiers in TaxonMech among them. A spelling a Mech adopts later
# is not caught until someone looks again. Which new registries to count at all
# is a separate decision, still open on #84.
P="CHEBI|pubchem\\.compound|PubChem|METPO|ENVO|NCBITaxon|GO|PR|UniProtKB|UniProt|cas|CAS|MESH|mesh|OBI|PATO|UBERON|FOODON|MICRO|MicrO|OMP|ECO|RO|BFO|IAO|ARO|NCIT|RHEA|KEGG|EC|Pfam|PFAM|InterPro|IPR|MediaDive|mediadive\\.compound|KOMODO|BacDive|GTDB|IMG|GOLD|DSMZ|ATCC|drugbank|DrugBank|PDB|TCDB|SO|CL|GAZ|PO|BTO|EMDB|CHEMBL\\.COMPOUND|PMID|DOI|doi|PHIPO|NCBIfam|ComplexPortal|SNOMED|gold\\.ecosystem|bacdive\\.isolation_source|mibig|MIBiG|npatlas|NPAtlas|gold|bacdive|img\\.taxon|DSM|mediadive\\.medium|mediadive\\.solution|mediadive\\.ingredient|komodo\\.medium|pubchem\\.aid|pubchem|KEGG_REACTION|kegg\\.compound|kegg\\.drug|chembl|ec|ChEBI|RCSB_PDB|PubMed|PUBMED|SwissProt|swissprot|Swissprot|UNIPROT|TAXON|PDBe|pdbe|interpro|KEGG_PATHWAY|kegg\\.module|kegg\\.glycan|MeSH|PubChem_Compound"
rx=re.compile(r"\b("+P+r"):[A-Za-z0-9_.\-]+")
norm={"pubchem.compound":"PubChem","mesh":"MESH","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","mediadive.compound":"MediaDive","MicrO":"MICRO","cas":"CAS","drugbank":"DrugBank","doi":"DOI","CHEMBL.COMPOUND":"ChEMBL","gold.ecosystem":"GOLD","mibig":"MIBiG","npatlas":"NPAtlas","bacdive.isolation_source":"BacDive","gold":"GOLD","bacdive":"BacDive","img.taxon":"IMG","DSM":"DSMZ","mediadive.medium":"MediaDive","mediadive.solution":"MediaDive","mediadive.ingredient":"MediaDive","komodo.medium":"KOMODO","pubchem.aid":"PubChem","pubchem":"PubChem","KEGG_REACTION":"KEGG","kegg.compound":"KEGG","kegg.drug":"KEGG","chembl":"ChEMBL","ec":"EC","ChEBI":"CHEBI","RCSB_PDB":"PDB","PubMed":"PMID","PUBMED":"PMID","SwissProt":"UniProt","swissprot":"UniProt","Swissprot":"UniProt","UNIPROT":"UniProt","TAXON":"NCBITaxon","PDBe":"PDB","pdbe":"PDB","interpro":"InterPro","KEGG_PATHWAY":"KEGG","kegg.module":"KEGG","kegg.glycan":"KEGG","MeSH":"MESH","PubChem_Compound":"PubChem"}


def census():
    """Count prefix occurrences per Mech. Minutes of I/O over every record."""
    out={}; revisions={}
    for m in ORDER:
        pc=collections.Counter()
        paths=record_paths(m)
        # The revision is taken before the records are read and checked after,
        # so it names the tree that was actually counted (#122).
        revisions[m]=revision(m, paths)
        for f in paths:
            for p in rx.findall(read_record(f)): pc[norm.get(p,p)]+=1
        unchanged(m, revisions[m])
        out[m]={"files":len(paths),"prefixes":dict(pc.most_common())}
        print(m,len(paths),dict(pc.most_common(14)),flush=True)
    # The run date travels in the file, not on it: git does not preserve mtimes,
    # so a fresh clone would otherwise make the page claim the corpora were
    # counted on the day someone cloned it (CultureBotAI.github.io#74).
    out["_as_of"]=datetime.date.today().isoformat()
    # And the revision each corpus was read at, so the census can be checked
    # against mech_stats.json, which counts the same files (#85).
    out["_revisions"]=revisions
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
