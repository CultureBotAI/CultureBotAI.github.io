#!/usr/bin/env python3
"""Targeted independent challenges and own-audit followups for Nov4 Pages refresh.

Inputs: live Pages and captured group-A receipts. Outputs: compact browser receipts
under _fleet/reviews/refresh-20261104; no source changes or GitHub writes. 2026-11-04.
"""
import argparse
import hashlib
import gzip
import json
import re
import subprocess
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_site_group_20261104 import CHROME,ROOT,RAW,now,state

def small(page):
    d=state(page)
    return {k:d[k] for k in ('url','h1','width','scrollWidth','theme','savedTheme','statuses','controls','firstRows','svgs','canvases')}|{'text':d['text'][:6500],'links':d['allLinks'][:50]}

def own():
    result={'started_at':now(),'checks':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page()
        for site in ('AntibioticMech','HabitatMech'):
            base='https://culturebotai.github.io/'+site+'/'
            p.goto(base+'pages/browse.html',wait_until='networkidle');p.locator('input[type=search]').first.fill('a');p.wait_for_timeout(1000)
            result['checks'][site+':broad_search']=small(p)
            route='pages/class/antibacterial.html' if site=='AntibioticMech' else 'pages/category/host-associated.html'
            response=p.goto(base+route,wait_until='networkidle');result['checks'][site+':category']={'status':response.status,'state':small(p)}
            page2=p.get_by_role('link',name='2',exact=True)
            if page2.count():page2.first.click();p.wait_for_timeout(500);result['checks'][site+':category_page2']=small(p)
            f=b.new_context();blocked=[]
            def abort(r):blocked.append(r.request.url);r.abort()
            f.route('**/*.json*',abort);fp=f.new_page();fp.goto(base+route,wait_until='networkidle')
            q=fp.locator('input[data-index]')
            if q.count():q.first.fill('a');fp.wait_for_timeout(1000)
            result['checks'][site+':category_failure']={'blocked':blocked,'state':small(fp)};f.close()
        for url in ('https://culturebotai.github.io/TaxonMech/browse.html?q=verrucosispora_maris','https://culturebotai.github.io/PathwayMech/pages/downloads/manifest.json'):
            r=p.goto(url,wait_until='networkidle');result['checks'][url]={'status':r.status,'url':p.url,'text':p.inner_text('body')[:900]}
        p.goto('https://culturebotai.github.io/PathwayMech/pages/browse.html',wait_until='networkidle')
        for v in ('label-asc','label-desc'):
            p.locator('select[id*=sort]').select_option(v);p.wait_for_timeout(300)
            result['checks']['PathwayMech:sort:'+v]=small(p)
        for site in ('AntibioticMech','NaturalProductMech'):
            f=b.new_context();f.route('**/data/sequence_map.json',lambda r:r.abort());fp=f.new_page();fp.goto('https://culturebotai.github.io/'+site+'/pages/sequence-map.html',wait_until='networkidle');fp.wait_for_timeout(400)
            result['checks'][site+':sequence_initial_failure']=small(fp);fp.locator('input[type=search]').first.fill('a');fp.wait_for_timeout(500);result['checks'][site+':sequence_failure_after_typing']=small(fp);f.close()
        b.close()
    result['finished_at']=now();out=ROOT/'_fleet/reviews/refresh-20261104/group-a-followups.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out)

def skeptic():
    result={'started_at':now(),'checks':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page()
        # Choose the other auditor's observed URLs, then independently operate the DOM.
        for site in ('CultureMech','MediaIngredientMech','CommunityMech','ProteinTraitsMech','CMMMech','AIMech','DUFMech'):
            raw=json.loads((ROOT/f'_fleet/reviews/refresh-20261104/{site.lower()}-browser-b.json').read_text())
            urls=list(raw['pages']); home=urls[0]
            browse=next((x for x in urls if 'browse' in x or '/app/browser' in x),None)
            if browse is None:browse=home
            for url in dict.fromkeys([home,browse]):
                response=p.goto(url,wait_until='networkidle',timeout=120000);p.wait_for_timeout(500)
                result['checks'][site+':'+url]={'status':response.status,'state':small(p)}
            if site=='CultureMech':
                result['checks']['CultureMech:sort_controls']=p.evaluate("()=>({selects:[...document.querySelectorAll('select')].map(x=>x.outerHTML),sortNodes:[...document.querySelectorAll('[aria-sort],[data-sort],button,th')].filter(x=>/sort/i.test(x.textContent+' '+x.getAttribute('aria-label'))).map(x=>x.outerHTML)})")
            if site=='CommunityMech':
                q=p.locator('input[type=search],#search-input,#search')
                if q.count():
                    for s in ('CommunityMech:000134','CommunityMech:000139','methylotroph'):
                        q.first.fill(s);p.wait_for_timeout(600);result['checks'][site+':search:'+s]=small(p)
            if site=='ProteinTraitsMech':
                p.goto(home,wait_until='networkidle');t=p.locator('.theme-toggle');before=small(p)
                if t.count():t.first.click();p.wait_for_timeout(300)
                result['checks'][site+':home_toggle']={'before':{k:before[k] for k in ('theme','savedTheme')},'after':small(p)}
            if site in ('CMMMech','AIMech'):
                url='https://culturebotai.github.io/'+site+'/pages/schema.html';r=p.goto(url,wait_until='networkidle');result['checks'][site+':schema_html']={'status':r.status,'text':p.inner_text('body')[:400]}
            if site=='CMMMech':
                for url in [x for x in urls if re.search(r'cobalt|akaganeite',x)]:
                    p.set_viewport_size({'width':390,'height':844});r=p.goto(url,wait_until='networkidle');result['checks'][site+':narrow:'+url]={'status':r.status,'state':small(p)}
                p.set_viewport_size({'width':1280,'height':900})
            if site=='AIMech':
                for url in [x for x in urls if '/map.' in x]:
                    r=p.goto(url,wait_until='networkidle');result['checks'][site+':map']={'status':r.status,'state':small(p)}
        b.close()
    result['finished_at']=now();out=ROOT/'_fleet/reviews/refresh-20261104/group-b-skeptic-challenges.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out)

def inspect(site):
    review=json.loads((ROOT/f'_fleet/reviews/refresh-20261104/{site.lower()}-auditor-b.json').read_text())
    for key,row in review['features'].items():print(key,row['status'],row['note'])

def protein():
    result={'started_at':now(),'checks':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME)
        p=b.new_page(viewport={'width':1280,'height':900})
        p.goto('https://culturebotai.github.io/proteintraitsmech/browse.html',wait_until='networkidle',timeout=120000)
        for q in ('cd05137','homogentisate 1,2-dioxygenase','no-such-record-nov4-audit'):
            p.locator('#q').fill(q);p.wait_for_timeout(1000)
            p.wait_for_function("()=>{const t=document.querySelector('#results')?.innerText;return t && !/Loading .*shards|Loading records/i.test(t)}",timeout=120000)
            p.wait_for_timeout(500)
            result['checks'][q]={'url':p.url,'result_text':p.locator('#results').inner_text()[:2000], 'record_links':p.locator('#results a[href]').evaluate_all('(xs)=>xs.slice(0,20).map(x=>({text:x.textContent,href:x.href}))')}
        b.close()
    result['finished_at']=now()
    out=ROOT/'_fleet/reviews/refresh-20261104/protein-search-independent.json'
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def exports():
    import yaml
    output={'checked_at':now()}
    snapshot=Path('/private/tmp/xmech-refresh-20261104-snapshot/mechs/DUFMech')
    pin=subprocess.check_output(['git','-C',str(snapshot),'rev-parse','HEAD'],text=True).strip()
    source_bytes=subprocess.check_output(['git','-C',str(snapshot),'show',pin+':data/families/PF04149.yaml'])
    native=yaml.safe_load(source_bytes)
    url='https://culturebotai.github.io/DUFMech/index.json'
    with urllib.request.urlopen(url,timeout=120) as response:body=response.read()
    obj=json.loads(body);record=obj['metadata']['PF04149']['record']
    output['DUFMech']={'url':url,'sha256':hashlib.sha256(body).hexdigest(),'pin':pin,'native_path':'data/families/PF04149.yaml','native_sha256':hashlib.sha256(source_bytes).hexdigest(),'families':len(obj['families']),'metadata_records':len(obj['metadata']),'entries_with_embedded_record':sum(isinstance(v.get('record'),dict) for v in obj['metadata'].values()),'record_fields':list(record),'native_fields':list(native),'native_record_equal':native==record,'native_field_differences':[k for k in native if native[k]!=record.get(k)],'graph_count':len(record['causal_graphs']),'curation_event_count':len(record['curation_events'])}
    url='https://culturebotai.github.io/TaxonMech/pages/index.json.gz'
    with urllib.request.urlopen(url,timeout=120) as response:body=response.read()
    obj=json.loads(gzip.decompress(body) if body[:2]==b'\x1f\x8b' else body)
    if not isinstance(obj,list):
        raise ValueError('Unexpected taxon index shape: '+str(type(obj)))
    output['TaxonMech']={'url':url,'sha256':hashlib.sha256(body).hexdigest(),'rows':len(obj),'first_row':obj[0],'fields':list(obj[0]),'interpretation':'Catalogue rows contain browse fields, not full taxon source records with nested assertions, source evidence and history.'}
    dest=ROOT/'_fleet/reviews/refresh-20261104/downloads-independent.json'
    dest.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))

def compact():
    out=ROOT/'_fleet/reviews/refresh-20261104/group-b-skeptic-challenges.json';raw=out.read_bytes()
    backup=Path('/private/tmp/group-b-skeptic-challenges-full-20261104.json')
    if not backup.exists():backup.write_bytes(raw)
    data=json.loads(backup.read_text())
    def walk(obj):
        if isinstance(obj,dict):
            if 'options' in obj and isinstance(obj['options'],list) and len(obj['options'])>20:
                obj['option_count']=len(obj['options']);obj['options']=obj['options'][:20]
            if 'controls' in obj and isinstance(obj['controls'],list) and len(obj['controls'])>30:
                obj['control_count']=len(obj['controls']);obj['controls']=obj['controls'][:30]
            for val in obj.values():walk(val)
        elif isinstance(obj,list):
            for val in obj:walk(val)
    walk(data);data['raw_capture']=str(backup);out.write_text(json.dumps(data,indent=2)+'\n');print(out.stat().st_size)

def verdicts():
    # Independent decisions after reading all 168 feature notes, raw action
    # receipts, and the live counterchecks above. Unlisted criteria are present.
    decisions={
      'CultureMech':{'missing':['sorting','review_status','build_provenance'],'partial':['full_catalogue','term_links','evidence','source_link','category_browse','downloads','license','theme_toggle','responsive']},
      'MediaIngredientMech':{'partial':['source_link','category_browse','downloads']},
      'CommunityMech':{'partial':['search','category_browse','downloads','license'],'missing':['review_status','curation_history','build_provenance'],'not_applicable':['load_failure']},
      'ProteinTraitsMech':{'partial':['term_links','category_browse','downloads','license','build_provenance','theme_toggle','responsive'],'missing':['cross_mech_links']},
      'DUFMech':{},
      'CMMMech':{'partial':['downloads','schema_docs','responsive'],'missing':['review_status','cross_mech_links'],'not_applicable':['load_failure']},
      'AIMech':{'partial':['curation_history','downloads','schema_docs','license'],'missing':['cross_mech_links'],'not_applicable':['load_failure']},
    }
    keys=list(json.loads((ROOT/'_fleet/data/site_features.json').read_text())['catalogue']);assert len(keys)==24
    bulk=json.loads((ROOT/'_fleet/reviews/refresh-20261104/group-b-bulk-inventory.json').read_text())
    duf=bulk['DUFMech']['structure']['metadata'];assert duf['records']==8296
    assert {'causal_graphs','curation_events','provenance','source_url'}<=set(duf['PF04149']['record'])
    review={'reviewer':'deployment_review independent skeptic of group B','checked_at':now(),'method':'Read each of 168 criterion verdicts against captured live-page and action evidence, inspected the browser helper, and independently re-exercised the challenged behaviors in Chromium.','challenges':'group-b-skeptic-challenges.json','features':{},'disagreements':[],'full_export_check':{'evidence':'group-b-bulk-inventory.json#/DUFMech/structure/metadata','metadata_records':duf['records'],'sample_complete_record_fields':list(duf['PF04149']['record']),'decision':'Present: exported metadata includes full source records, curation events and provenance in addition to browsing rows.'},'limits':['This independently re-exercises challenged behaviors, not every previously captured action.','Root arbitration requires full record serialization for present downloads and rendered schema docs/guide for present schema_docs.']}
    actual=json.loads((ROOT/'_fleet/reviews/refresh-20261104/downloads-independent.json').read_text())['DUFMech']
    assert actual['native_record_equal'] and actual['entries_with_embedded_record']==8296
    review['full_export_check']['native_comparison']={'evidence':'downloads-independent.json#/DUFMech','native_record_equal':True,'embedded_records':8296,'sample_graphs':3,'sample_curation_events':7}
    protein=json.loads((ROOT/'_fleet/reviews/refresh-20261104/protein-search-independent.json').read_text())
    review['protein_search_check']={'evidence':'protein-search-independent.json','settled_result_headers':{k:v['result_text'].splitlines()[0] for k,v in protein['checks'].items()}}
    review['limits'][1]='Root arbitration requires substantive scientific record-corpus exports; navigation-only indexes remain partial. Rendered schema docs or a guide are required for present schema_docs.'
    for site,overrides in decisions.items():
        report_path=ROOT/f'_fleet/reviews/refresh-20261104/{site.lower()}-auditor-b.json'
        report=json.loads(report_path.read_text());assert set(report['features'])==set(keys)
        verdict={key:'present' for key in keys}
        for status,subset in overrides.items():
            for key in subset:verdict[key]=status
        review['features'][site]={key:{'skeptic':status,'auditor':report['features'][key]['status'],'agree':status==report['features'][key]['status'],'reviewed_evidence':str(report_path.relative_to(ROOT))+'#/features/'+key+'/evidence'} for key,status in verdict.items()}
        for key,status in verdict.items():
            if status!=report['features'][key]['status']:review['disagreements'].append({'site':site,'feature':key,'skeptic':status,'auditor':report['features'][key]['status']})
    out=ROOT/'_fleet/reviews/refresh-20261104/group-b-independent-review.json';out.write_text(json.dumps(review,indent=2)+'\n')
    md=['# Group B independent review — 2026-11-04','', 'Reviewed all 24 existing criteria for each of the seven assigned sites (168 verdicts). Independently re-exercised the main challenged behaviors in Chromium; the adjacent JSON maps every criterion to its reviewed evidence.','', 'Confirmed browser findings: CultureMech has no record-sort control; CommunityMech known identifiers return zero; ProteinTraitsMech’s landing toggle remains inert; CMMMech material pages overflow at 597px and 669px; CMMMech and AIMech schema.html return 404 while navigation exposes schema source.','', f'Status disagreements: {len(review["disagreements"])}. Download serialization checks follow the root arbiter’s common rule. DUF’s exported metadata has 8,296 records, with full record fields including causal graphs, curation events and provenance.','', 'The helper and raw-capture hash/location preserve provenance; no site source data or GitHub objects were changed.']
    out.with_suffix('.md').write_text('\n'.join(md)+'\n');print(json.dumps(review['disagreements']))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['own','skeptic','inspect','compact','verdicts','protein','exports']);ap.add_argument('--site');a=ap.parse_args()
    {'own':own,'skeptic':skeptic,'inspect':lambda:inspect(a.site),'compact':compact,'verdicts':verdicts,'protein':protein,'exports':exports}[a.mode]()
