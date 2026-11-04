#!/usr/bin/env python3
"""Archive detailed auditor captures and retain compact feature-audit receipts.

Inputs: group A audited ledgers and independent B challenge captures.
Outputs: preserved raw copies under /private/tmp and smaller JSON receipts in
_fleet/reviews/refresh-20261104. Serves the Nov4 refresh PR, 2026-11-04.
No site/source data or GitHub objects are changed.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/'_fleet/reviews/refresh-20261104'
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a')
SITES=('cellstructuremech','antibioticmech','naturalproductmech','habitatmech','taxonmech','pathwaymech')

def shrink(value,key=''):
    if isinstance(value,dict):
        # DOM record/source anchors need their readable text and resolved URL.
        if 'href' in value and 'text' in value:
            return {k:value[k] for k in ('text','href')}
        return {k:shrink(v,k) for k,v in value.items()}
    if isinstance(value,list):
        if key in ('controls','options') and len(value)>20:
            return {'total_count':len(value),'first_20':[shrink(v) for v in value[:20]]}
        if key in ('allLinks','links'):
            # Preserve distinct anchors while removing duplicated nav/footer copies.
            rows=[];seen=set()
            for v in value:
                ident=json.dumps(v,sort_keys=True)
                if ident not in seen:seen.add(ident);rows.append(shrink(v))
            return rows[:35]
        if key=='firstRows':return [shrink(v) for v in value[:3]]
        return [shrink(v) for v in value]
    if isinstance(value,str):
        limit=1800 if key=='text_excerpt' else 1300 if key=='text' else None
        if limit and len(value)>limit:return value[:limit]+'\n[Excerpt; complete capture archived.]'
    return value

def archive(path):
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    target=ARCHIVE/path.name
    if not target.exists():shutil.copy2(path,target)
    return target

def state_excerpt(value):
    if not isinstance(value,dict):return value
    keys=('url','status','width','scrollWidth','theme','savedTheme','h1','result_text','blocked','before','error','status','text')
    result={k:shrink(v,k) for k,v in value.items() if k in keys}
    if 'statuses' in value:
        result['statuses']=[{'id':x.get('id'),'text':x.get('text','')[:250]} for x in value['statuses'] if x.get('text')][:8]
    if 'state' in value:result['state']=state_excerpt(value['state'])
    if 'after' in value:result['after']=state_excerpt(value['after'])
    if 'selects' in value or 'sortNodes' in value:
        result.update({k:value[k] for k in ('selects','sortNodes') if k in value})
    return result

def run():
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    previous_raw=Path('/private/tmp/mech-browser-group-20261104')
    destination=ARCHIVE/'raw'
    if previous_raw.exists() and not destination.exists():shutil.move(str(previous_raw),str(destination))
    previous_trait=Path('/private/tmp/trait-browser-auditor-20261104.json')
    trait_destination=ARCHIVE/previous_trait.name
    if previous_trait.exists() and not trait_destination.exists():shutil.move(str(previous_trait),str(trait_destination))
    for name in [x+'-auditor-a.json' for x in SITES]+['group-a-followups.json','group-b-skeptic-challenges.json']:
        path=EVID/name;raw=archive(path);data=json.loads(raw.read_text())
        if 'features' in data:
            # Feature verdicts, exact old/replacement claims and per-criterion evidence
            # are the primary record; only duplicated contextual receipts shrink.
            receipts=data['receipts']
            receipts['actions']={k:state_excerpt(v) for k,v in receipts['actions'].items()}
            receipts['pages']={p:{k:v for k,v in row.items() if k in ('url','status','footer','widths','themes','fetches','page_errors')} for p,row in receipts['pages'].items()}
            receipts['followup_checks']={k:state_excerpt(v) for k,v in receipts.get('followup_checks',{}).items()}
            receipts['controls']=shrink(receipts['controls'],'controls')
            # Evidence verbatim remains inside each feature; contextual DOM locator
            # is explicitly redirected to the preserved detailed capture.
            for feature in data['features'].values():
                locator=feature['evidence'].get('locator','')
                if locator.startswith('receipts.pages.') and not locator.endswith('.widths'):
                    feature['evidence']['locator']='Archived detailed capture '+str(raw)+'; original receipt locator: '+locator
            capture=data['raw_capture']
            capture['path']=capture['path'].replace('/private/tmp/mech-browser-group-20261104',str(destination))
            assert hashlib.sha256(Path(capture['path']).read_bytes()).hexdigest()==capture['sha256']
        else:
            data={'started_at':data.get('started_at'),'finished_at':data.get('finished_at'),'checks':{k:state_excerpt(v) for k,v in data['checks'].items()}}
        data['detailed_capture']={'path':str(raw),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'bytes':raw.stat().st_size}
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
        assert path.stat().st_size>0
        print(name,raw.stat().st_size,'->',path.stat().st_size)
    trait=EVID/'trait-auditor.json'
    data=json.loads(trait.read_text());data['raw_capture']['path']=str(trait_destination)
    assert hashlib.sha256(trait_destination.read_bytes()).hexdigest()==data['raw_capture']['sha256']
    trait.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

def verify():
    catalogue=json.loads((ROOT/'_fleet/data/site_features.json').read_text())['catalogue']
    for name in [x+'-auditor-a.json' for x in SITES]+['trait-auditor.json']:
        data=json.loads((EVID/name).read_text())
        assert len(data['features'])==24 and set(data['features'])==set(catalogue)
        raw=data['raw_capture'];assert hashlib.sha256(Path(raw['path']).read_bytes()).hexdigest()==raw['sha256']
        detail=data.get('detailed_capture')
        if detail:assert hashlib.sha256(Path(detail['path']).read_bytes()).hexdigest()==detail['sha256']
        print(name,'24 criteria; archived evidence hashes verified')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inventory',action='store_true');ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:verify()
    elif args.inventory:
        for site in SITES:
            data=json.loads((EVID/(site+'-auditor-a.json')).read_text())
            print(site,{k:len(json.dumps(v)) for k,v in data['receipts'].items()})
    else:run()
