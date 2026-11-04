#!/usr/bin/env python3
"""Archive group-B raw captures and retain concise fleet-refresh review evidence.
Inputs: completed Nov4 browser/auditor/skeptic reports owned by central_directory.
Outputs: hash-verified raw archive outside Git plus compact committed ledgers.
Requested by the root editor for this refresh PR, 2026-11-04. No source edits.
"""
import hashlib,json,shutil
from pathlib import Path

OUT=Path('_fleet/reviews/refresh-20261104')
DEST=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
B=['culturemech','mediaingredientmech','communitymech','proteintraitsmech','dufmech','cmmmech','aimech']
A=['cellstructuremech','antibioticmech','naturalproductmech','habitatmech','taxonmech','pathwaymech']
MANIFEST=OUT/'group-b-evidence-archive.json'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def copy_verified(path):
    dest=DEST/path.name
    if dest.exists():
        if digest(dest)!=digest(path):
            dest=DEST/(path.stem+'-'+digest(path)[:12]+path.suffix)
    if not dest.exists():shutil.copy2(path,dest)
    assert digest(path)==digest(dest) and path.stat().st_size==dest.stat().st_size
    return {'original':str(path),'archive':str(dest),'sha256':digest(dest),'bytes':dest.stat().st_size}

def rewrite(value,mapping):
    if isinstance(value,str):
        for old,new in mapping.items():
            value=value.replace(old,new)
        return value
    if isinstance(value,list):return [rewrite(x,mapping) for x in value]
    if isinstance(value,dict):return {k:rewrite(v,mapping) for k,v in value.items()}
    return value

def small_action(v):
    return {k:v[k] for k in ['url','counts','controls','checked','rows','first_results','error'] if k in v}

def small_page(v):
    keep=['url','http_status','checked_at','title','headings','footer','counts','theme','saved_theme','fresh_390','resized_390','record_links_count','unique_record_links','record_links_sha256','canvas','svg','body_excerpt','field_excerpts','selected_links','sorts_and_facets']
    p={k:v[k] for k in keep if k in v}
    p['body_excerpt']=p.get('body_excerpt',v.get('body',''))[:900]
    if 'field_excerpts' in p:p['field_excerpts']=p['field_excerpts'][:22]
    if 'selected_links' in p:p['selected_links']=p['selected_links'][:22]
    elif 'links' in v:
        p['selected_links']=[x for x in v['links'] if isinstance(x.get('url'),str) and any(t in x['url'] for t in ['github','doi.org','pubmed','schema','/mechs/'])][:16]
    if 'sorts_and_facets' in p:
        for entry in p['sorts_and_facets']:
            options=entry.get('options',[])
            if len(options)>12 and 'sort' not in entry.get('selector','').lower():
                entry['option_count']=len(options);entry['options']=options[:6]
    return p

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    prior=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'files':[]}
    entries=prior['files'];mapping={e['original']:e['archive'] for e in entries if e.get('raw_removed')}
    raw_names=[m+'-browser-b'+suffix+'.json' for m in B for suffix in ['', '-discovery']]
    raw_names += [m+'-skeptic-b-observations.json' for m in A]+['trait-skeptic-observations.json']
    for name in raw_names:
        p=OUT/name
        if not p.exists():continue
        e=copy_verified(p);e['raw_removed']=True
        mapping[str(p)]=e['archive'];entries.append(e)
        p.unlink() # full identical bytes have been verified in the requested archive
    compact_names=[m+'-auditor-b.json' for m in B]+[m+'-skeptic-b.json' for m in A]
    compact_names += ['group-b-supplement.json','group-a-skeptic-challenges.json','protein-query-followup.json','trait-skeptic.json']
    for name in compact_names:
        p=OUT/name;d=json.loads(p.read_text())
        if d.get('evidence_compacted'):continue
        e=copy_verified(p);entries.append(e)
        d=rewrite(d,mapping)
        if name.endswith('-skeptic-b.json'):
            d['receipts']['pages']={u:small_page(v) for u,v in d['receipts']['pages'].items()}
        elif name.endswith('-auditor-b.json'):
            shared={};seen={}
            for key,f in d['features'].items():
                evidence=f['evidence']
                if 'actions' in evidence:evidence['actions']={k:small_action(v) for k,v in evidence['actions'].items()}
                if 'bulk' in evidence:
                    evidence.pop('bulk');evidence['field_inventory']='group-b-bulk-inventory.json::'+d['mech']
                evidence.pop('checks',None)
                encoded=json.dumps(evidence,sort_keys=True)
                ref=seen.get(encoded)
                if ref is None:ref=key;seen[encoded]=ref;shared[ref]=evidence
                f['evidence']={'locator':'receipts.'+ref,'url':f['url']}
            d['receipts']=shared
            d['independent_review']='group-b-independent-review.json'
        elif name=='group-b-supplement.json':
            d['pages']={u:small_page(v) for u,v in d['pages'].items()}
        elif name=='group-a-skeptic-challenges.json':
            for key,v in d['checks'].items():
                if 'broad_search' in key:d['checks'][key]=small_action(v)
                if key=='Habitat_failed_search':v['state']=small_action(v['state'])
                if key.endswith('failed_sequence_search'):
                    for field in ['before','after']:
                        v[field]=[line for line in v[field].splitlines() if any(t in line for t in ['could not','Failed to fetch','Showing 0 of 0','0 matching'])]
                if key=='Pathway_downloads':
                    for item in v:
                        data=item.get('data',{})
                        if 'records' in data:
                            records=data.pop('records');data['record_count']=len(records);data['first_record']=records[0]
        elif name=='protein-query-followup.json':d['checks']={k:small_action(v) for k,v in d['checks'].items()}
        d['evidence_compacted']={'full_capture':e['archive'],'sha256':e['sha256'],'bytes':e['bytes']}
        p.write_text(json.dumps(d,indent=2)+'\n')
    # Trait canary's raw capture field can be a bare filename, so rewrite it explicitly.
    p=OUT/'trait-skeptic.json';d=json.loads(p.read_text())
    if 'observation_file' in d:d['observation_file']=str(DEST/'trait-skeptic-observations.json')
    p.write_text(json.dumps(d,indent=2)+'\n')
    MANIFEST.write_text(json.dumps({'purpose':'Verified local raw archive; concise ledgers remain committed.','files':entries},indent=2)+'\n')
    assert all(Path(e['archive']).stat().st_size==e['bytes'] and digest(Path(e['archive']))==e['sha256'] for e in entries)
    print(json.dumps({'archived_files':len(entries),'archived_bytes':sum(e['bytes'] for e in entries),'raw_removed':sum(bool(e.get('raw_removed')) for e in entries)}))

if __name__=='__main__':main()
