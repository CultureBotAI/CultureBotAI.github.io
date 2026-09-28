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

# The rule (#271): every namespace named for or qualified by a counted registry
# folds into that registry. That covers case and alternate names (gold:, GOLD:;
# SwissProt:, UniProt:; TAXON:, NCBITaxon:; CAS-RN:, CAS:; TC:, TCDB:; MSH:, MESH:) and
# entity-qualified namespaces (kegg.compound:, gold.ecosystem:, gtdb.genome:,
# uniprot.location:, RHEA-COMP:), as gold.ecosystem and pubchem.compound always
# did. Reference and curator collections named for a registry are not its terms
# and stay out: GO_REF: and PO_REF: are literature-like (#84 lists GO_REF as a
# CITATION candidate), and GOC: is curator attribution, which #84 proposes never
# to count (#282). Mechs mix lowercase bioregistry spellings with upper-case ones,
# TaxonMech most heavily, so a registry was counted under one spelling and
# dropped under another (#279). The
# spellings here were measured by scanning every record at the #120 pins with a
# pattern that allows dots, underscores and hyphens (#255, #270); 1.49 million
# GOLD and 556,160 BacDive identifiers in TaxonMech were among those missed. A
# spelling a Mech adopts later is not caught until someone scans again. Which
# registries to count at all is the inclusion rule below (#84).
P="CHEBI|pubchem\\.compound|PubChem|METPO|ENVO|NCBITaxon|GO|PR|UniProtKB|UniProt|cas|CAS|MESH|mesh|OBI|PATO|UBERON|FOODON|MICRO|MicrO|OMP|ECO|RO|BFO|IAO|ARO|NCIT|RHEA|KEGG|EC|Pfam|PFAM|InterPro|IPR|MediaDive|mediadive\\.compound|KOMODO|BacDive|GTDB|IMG|GOLD|DSMZ|ATCC|drugbank|DrugBank|PDB|TCDB|SO|CL|GAZ|PO|BTO|EMDB|CHEMBL\\.COMPOUND|PMID|DOI|doi|PHIPO|NCBIfam|ComplexPortal|SNOMED|gold\\.ecosystem|bacdive\\.isolation_source|mibig|MIBiG|npatlas|NPAtlas|gold|bacdive|img\\.taxon|DSM|mediadive\\.medium|mediadive\\.solution|mediadive\\.ingredient|komodo\\.medium|pubchem\\.aid|pubchem|KEGG_REACTION|kegg\\.compound|kegg\\.drug|chembl|ec|ChEBI|RCSB_PDB|PubMed|PUBMED|SwissProt|swissprot|Swissprot|UNIPROT|TAXON|PDBe|pdbe|interpro|KEGG_PATHWAY|kegg\\.module|kegg\\.glycan|MeSH|PubChem_Compound|gtdb\\.genome|pdb\\.ligand|pdb\\-ccd|RHEA\\-COMP|CAS\\-RN|uniprot\\.location|uniprot\\.ptm|UniProtKB\\-KW|Swiss|TC|MSH"
norm={"pubchem.compound":"PubChem","mesh":"MESH","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","mediadive.compound":"MediaDive","MicrO":"MICRO","cas":"CAS","drugbank":"DrugBank","doi":"DOI","CHEMBL.COMPOUND":"ChEMBL","gold.ecosystem":"GOLD","mibig":"MIBiG","npatlas":"NPAtlas","bacdive.isolation_source":"BacDive","gold":"GOLD","bacdive":"BacDive","img.taxon":"IMG","DSM":"DSMZ","mediadive.medium":"MediaDive","mediadive.solution":"MediaDive","mediadive.ingredient":"MediaDive","komodo.medium":"KOMODO","pubchem.aid":"PubChem","pubchem":"PubChem","KEGG_REACTION":"KEGG","kegg.compound":"KEGG","kegg.drug":"KEGG","chembl":"ChEMBL","ec":"EC","ChEBI":"CHEBI","RCSB_PDB":"PDB","PubMed":"PMID","PUBMED":"PMID","SwissProt":"UniProt","swissprot":"UniProt","Swissprot":"UniProt","UNIPROT":"UniProt","TAXON":"NCBITaxon","PDBe":"PDB","pdbe":"PDB","interpro":"InterPro","KEGG_PATHWAY":"KEGG","kegg.module":"KEGG","kegg.glycan":"KEGG","MeSH":"MESH","PubChem_Compound":"PubChem","gtdb.genome":"GTDB","pdb.ligand":"PDB","pdb-ccd":"PDB","RHEA-COMP":"RHEA","CAS-RN":"CAS","uniprot.location":"UniProt","uniprot.ptm":"UniProt","UniProtKB-KW":"UniProt","Swiss":"UniProt","TC":"TCDB","MSH":"MESH"}

# The inclusion rule (#84, decided 2026-09-28; stated in roots.py beside
# CITATION): count every external identifier namespace a record cites --
# ontologies, databases and registries -- folded to one name per registry, with
# every culture collection folded into one entry and literature counted under
# roots.CITATION. Never count a Mech's own ids, another Mech's, kg-microbe's,
# metamodel prefixes (skos, biolink, rdf, rdfs, xref), curator attribution (GOC,
# POC, PATOC, MITRE) or provenance (sqlite, sha256, url, dataset row hashes).
# The namespaces below were classified from every CURIE-shaped token in every
# record at the 2026-09-28 refresh's pins, with sample ids read for each; the
# rest of what that scan finds is chemical names, serotypes (O157:H7), strain
# designations (Bacteroides sp. CAG:1060) and ratios that only look like
# prefixes. Each entry is the counted name, then the spellings that fold into it.
ADDED = {
    # Protein domain, family, structure, pathway and function resources, and
    # the ontologies ProteinTraitsMech and others cite beside them.
    "CATH": ["CATH"], "CDD": ["CDD"], "PROSITE": ["PROSITE", "Prosite"],
    "ECOD": ["ECOD"], "SCOP": ["SCOP"], "PANTHER": ["PANTHER"],
    "AlphaFoldDB": ["AlphaFoldDB"], "OrthoDB": ["OrthoDB"], "IEDB": ["IEDB"],
    "SMART": ["SMART"], "TED": ["TED"], "HAMAP": ["HAMAP"], "MCSA": ["MCSA"],
    "Reactome": ["Reactome"], "MetaCyc": ["MetaCyc", "metacyc.compound"],
    "COG": ["COG"], "PRINTS": ["PRINTS"], "OMA": ["OMA"], "CAZy": ["CAZy"],
    "MEROPS": ["MEROPS", "MEROPS_fam"], "OPM": ["OPM"], "RESID": ["RESID"],
    "Unimod": ["Unimod"], "SFLD": ["SFLD"], "ELM": ["ELM"], "RepeatsDB": ["RepeatsDB"],
    "UniPathway": ["UniPathway", "Unipathway"], "DeltaMass": ["DeltaMass"],
    "UM-BBD": ["UM-BBD_reactionID", "UM-BBD_pathwayID", "UM-BBD_enzymeID", "umbbd.compound"],
    "VZ": ["VZ"], "RNAcentral": ["RNAcentral"], "CORUM": ["CORUM"],
    "IUPHAR": ["IUPHAR_GPCR", "IUPHAR_RECEPTOR"], "IntAct": ["Intact"],
    "OMIM": ["OMIM"], "ZFIN": ["ZFIN"], "CryoETDataPortal": ["CryoETDataPortal"],
    "MI": ["MI"], "MOD": ["MOD"], "NIF_Subcellular": ["NIF_Subcellular"],
    "IDPO": ["IDPO"], "GNO": ["GNO"], "UO": ["UO"], "MA": ["MA"], "MP": ["MP"],
    "FMA": ["FMA"], "ZFA": ["ZFA"], "FBbt": ["FBbt"], "XAO": ["XAO"],
    "WBbt": ["WBbt"], "HAO": ["HAO"], "CEPH": ["CEPH"],
    # Rhea's generic and polymer compounds, cited as GENERIC: and POLYMER:
    # beside RHEA-COMP:, fold into Rhea as RHEA-COMP does.
    "RHEA": ["GENERIC", "POLYMER"],
    # Strain, genome and sequence registries.
    "StrainInfo": ["straininfo.strain", "straininfo.deposit"],
    "ncbi.assembly": ["ncbi.assembly"], "patric": ["patric"], "biosample": ["biosample"],
    "bioproject": ["bioproject"], "INSDC": ["INSDC"], "genbank": ["genbank"],
    "NCBI_Nuccore": ["NCBI_Nuccore"], "NCBI_Protein": ["NCBI_Protein"], "SRA": ["SRA"],
    "LPSN": ["lpsn"], "atb.assembly": ["atb.assembly"], "ena.analysis": ["ena.analysis"],
    # Chemical and natural-product registries.
    "UNII": ["UNII"], "reaxys": ["reaxys"], "beilstein": ["beilstein"],
    "gmelin": ["gmelin"], "drugcentral": ["drugcentral"], "knapsack": ["knapsack"],
    "HMDB": ["hmdb"], "LINCS": ["lincs.smallmolecule"], "ChemSpider": ["chemspider"],
    "ppdb": ["ppdb"], "bpdb": ["bpdb"], "pesticides": ["pesticides"],
    "LIPIDMAPS": ["lipidmaps"], "FooDB": ["foodb.compound"], "vsdb": ["vsdb"],
    "CyanoMetDB": ["cyanometdb"], "LOTUS": ["lotus"], "molbase": ["molbase"],
    "YMDB": ["ymdb"], "ECMDB": ["ecmdb"], "GlyTouCan": ["glytoucan"], "GlyGen": ["glygen"],
    "PHI-base": ["PHIG"],
    # Culture-media databases.
    "TOGO": ["TOGO"], "MEDIADB": ["MEDIADB"],
    # Literature and other citable works: counted, and listed in roots.CITATION.
    "ISBN": ["ISBN"], "GO_REF": ["GO_REF"], "PO_REF": ["PO_REF"], "WB_REF": ["WB_REF"],
    "patent": ["patent"], "Wikipedia": ["Wikipedia", "wikipedia.en", "WIKIPEDIA", "WikiPedia"],
    "PMCID": ["PMCID", "PMC"], "ISSN": ["ISSN"], "JSTOR": ["JSTOR"], "OSTI": ["OSTI"],
    "Zenodo": ["Zenodo"], "GitHub": ["GITHUB", "github"], "PNNLDH": ["PNNLDH"],
}
# Every culture collection counts as one entry (#84): ATCC and DSMZ, which the
# census counted separately before, and the collections TaxonMech cites in
# source_strain_identifiers, CultureMech in media references (CCAP, UTEX, JCM's
# medium list), with the spellings each uses.
COLLECTIONS = ["ATCC", "DSMZ", "DSM", "JCM", "jcm.grmd", "NBRC", "NCTC", "CGMCC", "CCUG",
               "KCTC", "LMG", "NRRL", "KACC", "CCM", "NCIMB", "CECT", "NCPPB", "CFBP", "KMM",
               "CIP", "KCCM", "VKM", "CCTCC", "BCRC", "MTCC", "ICMP", "NCDO", "YIM", "VTT",
               "NCFB", "HAMBI", "NCIB", "NCCB", "SGSC", "TBRC", "CPCC", "NCIM", "IAM", "PCC",
               "CCOS", "RIMD", "IBSBF", "CCAP", "UTEX"]
ADDED["CultureCollection"] = COLLECTIONS
_have = set(P.replace("\\", "").split("|"))
P += "".join("|" + re.escape(sp) for sps in ADDED.values() for sp in sps if sp not in _have)
norm.update({sp: name for name, sps in ADDED.items() for sp in sps if sp != name})
norm.update({"DSM": "CultureCollection"})
# The lookahead skips every position not followed by a colon within LOOKAHEAD
# prefix characters before trying the alternation. It changes no match, since
# no alternative is that long (a test holds the bound), and it keeps the census
# near its old running time: with #84's 270 alternatives, the bare alternation
# took three times as long over the same records.
LOOKAHEAD=40
rx=re.compile(r"\b(?=[\w.\-]{1,%d}:)("%LOOKAHEAD+P+r"):[A-Za-z0-9_.\-]+")


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
