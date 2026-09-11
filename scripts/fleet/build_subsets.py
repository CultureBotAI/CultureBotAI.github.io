"""Build the shared-term index per Mech pair and the per-Mech, per-vocabulary record lists (assets/fleet/edges, assets/fleet/cells) plus subsets_summary.json.

Run from the site root: `python3 scripts/fleet/build_subsets.py`. Reads the Mech
checkouts through scripts/fleet/roots.py (set MECHS_ROOT to relocate them); writes derived data under _fleet/data and assets/fleet. See
_fleet/README.md for the whole pipeline.
"""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "_fleet", "data")
import collections
import glob
import itertools
import json
import re
import urllib.parse

from roots import CITATION, ORDER, mech_root, record_paths

OUT=os.path.join(REPO,"assets","fleet")
GH="https://github.com/CultureBotAI/"; SITE="https://culturebotai.github.io/"
# Where each Mech publishes one record. Five serve a page per record; the
# ProteinTraitsMech browser routes by hash; CultureMech and MediaIngredientMech
# do not deploy per-record pages, so their links open the source file on GitHub.
SITE_BASE={
 # NaturalProductMech publishes no site yet, so its records link to the source file.
 "NaturalProductMech": GH+"NaturalProductMech/blob/main/data/natural_products/",
 "HabitatMech": SITE+"HabitatMech/pages/habitats/",
 "CommunityMech": SITE+"CommunityMech/communities/",
 "TraitMech": SITE+"TraitMech/pages/traits/",
 "CellStructureMech": SITE+"CellStructureMech/pages/structures/",
 "ProteinTraitsMech": SITE+"proteintraitsmech/browse.html#record=",
 "AntibioticMech": SITE+"AntibioticMech/pages/",
 "MediaIngredientMech": GH+"MediaIngredientMech/blob/main/data/ingredients/",
 "CultureMech": GH+"CultureMech/blob/main/data/merge_yaml/merged/",
}
MECHS={name: dict(root=mech_root(name), base=SITE_BASE[name]) for name in ORDER}
PREF=["CHEBI","NCBITaxon","GO","ENVO","METPO","ARO","UniProt","InterPro","Pfam","PATO","UBERON","FOODON","KEGG","CAS","RHEA","PDB","BTO","GTDB","MIBiG","NPAtlas","DOI"]
NORM={"mibig":"MIBiG","npatlas":"NPAtlas","UniProtKB":"UniProt","PFAM":"Pfam","IPR":"InterPro","cas":"CAS","doi":"DOI","MeSH":"MESH"}
rx=re.compile(r"\b(CHEBI|NCBITaxon|GO|ENVO|METPO|ARO|UniProtKB|UniProt|InterPro|IPR|Pfam|PFAM|PATO|UBERON|FOODON|KEGG|CAS|cas|RHEA|PDB|BTO|GTDB|mibig|MIBiG|npatlas|NPAtlas|DOI|doi):([A-Za-z0-9_.\-/()]+)")
STRICT=re.compile(r"^\s*(?:-\s*)?(?:id|identifier|term|term_id|ontology_id|curie|taxon_id|taxon|organism)\s*:\s*['\"]?(CHEBI|NCBITaxon|GO|ENVO|METPO|ARO|UniProtKB|UniProt|InterPro|IPR|Pfam|PFAM|PATO|UBERON|FOODON|KEGG|CAS|cas):([A-Za-z0-9_.\-]+)['\"]?\s*$")
strict=collections.defaultdict(collections.Counter)
LAB=re.compile(r"^\s*(?:-\s*)?(?:label|name|term_label|preferred_label|preferred_term|taxon_label|organism_label|ontology_label)\s*:\s*(.+?)\s*$")
AUTH={"MIBiG":["NaturalProductMech"],"NPAtlas":["NaturalProductMech"],"CHEBI":["MediaIngredientMech","AntibioticMech","CultureMech"],"NCBITaxon":["HabitatMech","CommunityMech","TraitMech"],"GO":["CellStructureMech","CommunityMech","TraitMech"],"METPO":["TraitMech"],"ARO":["AntibioticMech"],"ENVO":["HabitatMech","CommunityMech","MediaIngredientMech"],"UBERON":["HabitatMech","MediaIngredientMech","CultureMech"],"FOODON":["HabitatMech","MediaIngredientMech","CultureMech"],"UniProt":["CellStructureMech","TraitMech"],"InterPro":["TraitMech"],"Pfam":["CellStructureMech"],"KEGG":["CultureMech"],"PATO":["TraitMech"],"CAS":["MediaIngredientMech"],"DOI":[]}
def unq(v):
    v=v.strip()
    while len(v)>=2 and v[0]==v[-1] and v[0] in "'\"": v=v[1:-1].strip()
    return v.replace("''","'")
# HabitatMech publishes one page per record; the slug is matched against these.
hab_pages=set(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(mech_root("HabitatMech"),"pages","habitats","*.html")))
if not hab_pages:
    raise SystemExit("HabitatMech: no pages under pages/habitats; record links would silently be dropped")
hab_by_suffix=collections.defaultdict(list)
for n in hab_pages:
    parts=n.split("-")
    for k in range(1,len(parts)): hab_by_suffix["-".join(parts[k:])].append(n)
hab_collisions=[]
def simple_slug(text):
    return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",text.lower())).strip("-")
def slug_for(m, f, doc_id, doc_label=""):
    root=MECHS[m]["root"]; rel=os.path.relpath(f, root)
    if m=="HabitatMech":
        if not doc_id: return None
        flat=simple_slug(doc_id)
        cands=[n for n in hab_by_suffix.get(flat,[]) if n.endswith("-"+flat) or n==flat]
        if len(cands)==1: return urllib.parse.quote(cands[0]+".html")
        exact=simple_slug(doc_label)+"-"+flat
        if exact in hab_pages: return urllib.parse.quote(exact+".html")
        pref=[n for n in cands if n.startswith(simple_slug(doc_label)[:24])]
        if len(pref)==1: return urllib.parse.quote(pref[0]+".html")
        hab_collisions.append((doc_id,doc_label,cands)); return None
    if m=="CommunityMech": return urllib.parse.quote(os.path.basename(rel)[:-5]+".html")
    if m=="TraitMech": return urllib.parse.quote(rel[len("data/traits/"):-5]+".html")
    if m=="CellStructureMech": return urllib.parse.quote(rel[len("data/structures/"):-5]+".html")
    if m=="AntibioticMech": return urllib.parse.quote(rel[len("data/antibiotics/"):-5]+".html")
    if m=="ProteinTraitsMech": return urllib.parse.quote(doc_id or "", safe="")
    if m=="MediaIngredientMech": return urllib.parse.quote(rel[len("data/ingredients/"):])
    if m=="NaturalProductMech": return urllib.parse.quote(rel[len("data/natural_products/"):])
    if m=="CultureMech": return urllib.parse.quote(rel[len("data/merge_yaml/merged/"):])
    return None
def scan(m, keep=None, cap_cell=300):
    """Return per-mech index: term -> [(slug,label)], prefix -> (count, first refs), term labels votes."""
    cfg=MECHS[m]; root=cfg["root"]; terms=collections.defaultdict(list); cells=collections.defaultdict(lambda:[0,[]]); votes=collections.defaultdict(collections.Counter); nfiles=0; nolink=0
    for f in record_paths(m):
        try: txt=open(f,encoding="utf-8",errors="ignore").read()
        except Exception: continue
        nfiles+=1
        head=txt[:4000]
        mid=re.search(r"^(?:identifier|id)\s*:\s*(\S+)",head,flags=re.M); doc_id=mid.group(1).strip("'\"") if mid else ""
        ml=re.search(r"^(?:label|preferred_term|display_name|title|name)\s*:\s*(.+)$",head,flags=re.M); doc_label=unq(ml.group(1)) if ml else os.path.basename(f)[:-5]
        slug=slug_for(m,f,doc_id,doc_label)
        if slug is None: nolink+=1; continue
        assert re.fullmatch(r"[A-Za-z0-9_.~%\-/]+",slug), (m,slug)
        found=set()
        for p,i in rx.findall(txt):
            p=NORM.get(p,p)
            if p not in PREF: continue
            found.add(p+":"+i)
        if keep is not None: found_terms=found & keep
        else: found_terms=found
        for t in found_terms: terms[t].append((slug,doc_label))
        for p in {t.split(":")[0] for t in found}:
            c=cells[p]; c[0]+=1
            if len(c[1])<cap_cell: c[1].append((slug,doc_label))
        # label votes: strict structural form from every Mech, relaxed form from authoritative Mechs
        lines=txt.split("\n")
        for j,l in enumerate(lines):
            ms=STRICT.match(l)
            if ms:
                p,i=ms.group(1),ms.group(2); p=NORM.get(p,p); t=p+":"+i
                for k in (j+1,j+2):
                    if k<len(lines):
                        ml2=LAB.match(lines[k])
                        if ml2:
                            v=unq(ml2.group(1))
                            if v and not v.startswith("http") and "#" not in v: strict[t][v]+=1
                            break
        if any(m in AUTH.get(p,[]) for p in PREF):
            for j,l in enumerate(lines):
                for p,i in rx.findall(l):
                    p=NORM.get(p,p)
                    if m not in AUTH.get(p,[]): continue
                    t=p+":"+i
                    mm=re.search(re.escape(t)+r"\s*\((.+?)\)",l)
                    if mm: votes[t][mm.group(1).strip()]+=1; continue
                    for k in (j,j+1):
                        if k<len(lines):
                            ml2=LAB.match(lines[k])
                            if ml2:
                                v=unq(ml2.group(1))
                                if v and not v.startswith("http") and "#" not in v: votes[t][v]+=1
                                break
    print(m,"files",nfiles,"unlinked",nolink,"terms",len(terms),flush=True)
    return dict(terms=terms,cells=cells,votes=votes)
idx={}
for m in ORDER:
    if m=="ProteinTraitsMech": continue
    idx[m]=scan(m)
union=set().union(*[set(idx[m]["terms"]) for m in idx])
idx["ProteinTraitsMech"]=scan("ProteinTraitsMech",keep=union)
# labels
labels={}
allterms=set().union(*[set(idx[m]["terms"]) for m in ORDER])
for t in allterms:
    p=t.split(":")[0]
    c=strict.get(t)
    if c:
        l,n=c.most_common(1)[0]
        if n/sum(c.values())>=0.6 and l.count("'")%2==0: labels[t]=l; continue
    for a in AUTH.get(p,[]):
        c=idx[a]["votes"].get(t)
        if c:
            l,n=c.most_common(1)[0]
            if n/sum(c.values())>=0.6 and l.count("'")%2==0: labels[t]=l; break
os.makedirs(f"{OUT}/edges",exist_ok=True); os.makedirs(f"{OUT}/cells",exist_ok=True)
summary={"edges":{},"cells":{}}
for a,b in itertools.combinations(ORDER,2):
    shared=set(idx[a]["terms"])&set(idx[b]["terms"])
    shared={t for t in shared if t.split(":")[0]!="DOI" or True}
    if not shared: continue
    rows=[]
    for t in shared:
        ra=idx[a]["terms"][t]; rb=idx[b]["terms"][t]
        rows.append({"id":t,"l":labels.get(t,""),"na":len(ra),"nb":len(rb),"a":ra[:6],"b":rb[:6]})
    rows.sort(key=lambda r:(-(min(r["na"],r["nb"])),-(r["na"]+r["nb"]),r["id"]))
    byp=collections.Counter(t.split(":")[0] for t in shared)
    doc={"a":a,"b":b,"base":{a:MECHS[a]["base"],b:MECHS[b]["base"]},"n":len(shared),"by":dict(byp.most_common()),"terms":rows}
    fn=f"{a}--{b}.json"; json.dump(doc,open(f"{OUT}/edges/{fn}","w"),separators=(",",":"),ensure_ascii=False)
    summary["edges"][f"{a}|{b}"]={"n":len(shared),"by":dict(byp.most_common()),"ex":[{"id":r["id"],"label":r["l"]} for r in rows if r["l"] and r["id"].split(":")[0]!="DOI"][:3]}
    print("edge",a,b,len(shared),os.path.getsize(f"{OUT}/edges/{fn}")//1024,"KB")
for m in ORDER:
    for p,(n,refs) in idx[m]["cells"].items():
        if p in CITATION: continue
        fn=f"{m}--{p}.json"
        json.dump({"mech":m,"prefix":p,"base":MECHS[m]["base"],"total":n,"records":refs},open(f"{OUT}/cells/{fn}","w"),separators=(",",":"),ensure_ascii=False)
        summary["cells"][f"{m}|{p}"]=n
json.dump(summary,open(DATA+"/subsets_summary.json","w"),indent=1)
print("labels resolved",len(labels),"of",len(allterms)); print("habitat pages unresolved (no link emitted):",len(hab_collisions), hab_collisions[:3]); print("done; total size KB:", sum(os.path.getsize(f) for f in glob.glob(f"{OUT}/**/*.json",recursive=True))//1024)
