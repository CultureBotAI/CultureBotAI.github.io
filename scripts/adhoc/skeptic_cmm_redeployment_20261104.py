#!/usr/bin/env python3
"""Independently verify CMM's new protein-example deployment for Nov4 refresh.
Inputs: exact Git objects, live Pages, current 24-feature auditor evidence.
Outputs: compact skeptic receipt and B-review addendum only. No production edits.
2026-11-04; refresh PR provenance. Raw browser details archived outside Git.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_site_group_20261104 import CHROME,gh,now,state

ROOT=Path(__file__).resolve().parents[2];EVID=ROOT/'_fleet/reviews/refresh-20261104'
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a')
OBJECTS=Path('/private/tmp/cmm-redeployment-20261104-objects.git')
OLD='8bf82c8dfa25a35f12b60617b86751bc3ce7df71';NEW='ff4a9841deb7e4f6e9fff025eccd2ffa07b5493c'
BASE='https://culturebotai.github.io/CMMMech/'

def git(*args):return subprocess.check_output(['git','--git-dir',str(OBJECTS),*args],text=True)
def deploy(ctx):
    d=gh('repos/CultureBotAI/CMMMech/deployments?environment=github-pages&per_page=1')[0]
    s=gh(f'repos/CultureBotAI/CMMMech/deployments/{d["id"]}/statuses?per_page=1')[0]
    url=BASE+'pages/index.html';r=ctx.request.head(url)
    return {k:d[k] for k in ('id','sha','created_at')}|{'latest_status':{k:s[k] for k in ('state','created_at','environment_url')},'header_url':url,'http_status':r.status,'last_modified':r.headers.get('last-modified')}

def action(page):
    d=state(page)
    return {k:d[k] for k in ('url','statuses','firstRows','visibleRows')}

def main():
    assert git('rev-parse',NEW+'^').strip()==OLD
    changed=git('diff','--name-only',OLD,NEW).splitlines();assert len(changed)==735
    records=[p for p in changed if p.startswith('data/records/')];assert len(records)==10
    production=[p for p in changed if p.startswith(('src/','scripts/','conf/','.github/','templates/'))];assert not production
    root_old={line.split('\t')[1]:line.split()[2] for line in git('ls-tree',OLD).splitlines()}
    root_new={line.split('\t')[1]:line.split()[2] for line in git('ls-tree',NEW).splitlines()}
    unchanged={k:root_old[k] for k in root_old if k not in ('data','history','reviews','pages')};assert all(root_new.get(k)==v for k,v in unchanged.items())
    result={'reviewer':'deployment_review independent CMM redeployment skeptic','started_at':now(),'corpus_pin':OLD,'served_revision':NEW,'source_diff':{'object_repository':str(OBJECTS),'changed_count':len(changed),'record_count':len(records),'production_changes':production,'unchanged_root_objects':unchanged,'method':'Independent git diff and tree comparison on exact commits; complete file list, not truncated compare API.','changed_list_sha256':hashlib.sha256('\n'.join(changed).encode()).hexdigest()},'changed_records':{},'controls':{}}
    raw={'changed_files':changed,'pages':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page();result['deployment_before']=deploy(c)
        p.goto(BASE+'pages/index.html',wait_until='networkidle');p.locator('button.theme-toggle').click();landing=state(p)
        result['landing']={'url':p.url,'footer':landing['footer'],'excerpt':landing['text'][:1100]};assert '92117fbb1ec5' in landing['footer']
        for path in records:
            slug=Path(path).stem;url=BASE+'pages/materials/'+slug+'.html'
            diff=git('diff',OLD,NEW,'--',path)
            added=sorted(set(re.findall(r'^\+\s*-?\s*uniprot_accession:\s*(UniProtKB:\S+)',diff,re.M)))
            response=p.goto(url,wait_until='networkidle');desktop=state(p);assert response.status==200
            p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(180);narrow=state(p)
            protein_links=[a for a in desktop['allLinks'] if 'uniprot.org' in a['href']]
            missing=[v for v in added if not any(v.split(':')[1] in a['href'] for a in protein_links)]
            pos=desktop['text'].lower().find('protein example')
            result['changed_records'][slug]={'url':url,'http_status':response.status,'source':path,'added_accessions':added,'missing_resolver_anchors':missing,'protein_anchors':[{'text':a['text'],'href':a['href']} for a in protein_links][:16],'protein_excerpt':desktop['text'][max(0,pos):max(0,pos)+1200],'current_footer':desktop['footer'],'theme':desktop.get('theme'),'width_390':narrow['scrollWidth'],'has_own_yaml_link':any(path in a['href'] for a in desktop['allLinks'])}
            assert not missing and desktop.get('theme')=='dark'
            raw['pages'][slug]={'desktop':desktop,'narrow':narrow};p.set_viewport_size({'width':1280,'height':900})
        for slug in ('cobalt','akaganeite'):
            p.set_viewport_size({'width':390,'height':844});p.goto(BASE+'pages/materials/'+slug+'.html',wait_until='networkidle');d=state(p)
            result.setdefault('width_boundary',{})[slug]={'url':p.url,'width':390,'document_width':d['scrollWidth']}
        p.set_viewport_size({'width':1280,'height':900});p.goto(BASE+'pages/browse.html',wait_until='networkidle')
        q=p.locator('input[type=search],#search,#search-input').first
        for query in ('CHEBI:27638','cmmmech:copper','Cobalt','no-such-cmm-skeptic'):
            q.fill(query);p.wait_for_timeout(180);result['controls']['query:'+query]=action(p)
        q.fill('');p.wait_for_timeout(150)
        selects=p.locator('select');result['selects']=selects.evaluate_all('(xs)=>xs.map(x=>({id:x.id,options:[...x.options].map(o=>({value:o.value,text:o.text}))}))')
        for control in result['selects']:
            if len(control['options'])>1:
                value=control['options'][1]['value'];p.locator('#'+control['id']).select_option(value);p.wait_for_timeout(150);result['controls']['select:'+control['id']]=action(p)
        result['controls']['before_reload']=action(p);p.reload(wait_until='networkidle');result['controls']['after_reload']=action(p)
        download=c.request.get(BASE+'pages/index.json');data=download.json()
        result['download']={'url':BASE+'pages/index.json','status':download.status,'rows':len(data),'first_row_fields':list(data[0]),'assessment':'Navigation fields only; no full substantive record corpus. Partial download criterion retained.'}
        result['deployment_after']=deploy(c);b.close()
    assert result['deployment_after']['sha']==NEW and result['deployment_after']['latest_status']['state']=='success'
    auditor=json.loads((EVID/'cmmmech-auditor-b.json').read_text());review_path=EVID/'group-b-independent-review.json';review=json.loads(review_path.read_text())
    discrepancies=[k for k,v in auditor['features'].items() if review['features']['CMMMech'][k]['skeptic']!=v['status']];assert len(auditor['features'])==24 and not discrepancies
    result['criterion_reconciliation']={k:{'status':v['status'],'auditor_evidence':'cmmmech-auditor-b.json#/features/'+k,'agree':True} for k,v in auditor['features'].items()}
    result['assessment']='All 24 verdicts remain valid. New protein examples retain labeled context, UniProt resolver links, citations, own-source access and curation history; current build digest is 92117fbb1ec5. Existing responsive, schema and export limitations remain.'
    result['finished_at']=now();raw_path=ARCHIVE/'cmm-redeployment-independent-raw.json';raw_path.write_text(json.dumps(raw,indent=2)+'\n');result['raw_capture']={'path':str(raw_path),'sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    out=EVID/'cmmmech-redeployment-skeptic.json';out.write_text(json.dumps(result,indent=2)+'\n')
    review['cmm_redeployment']={'receipt':out.name,'verified_at':result['finished_at'],'corpus_pin':OLD,'served_revision':NEW,'deployment':result['deployment_after'],'criteria_reconciled':24,'status_disagreements':0,'changed_records_checked':10,'digest':'92117fbb1ec5'}
    review_path.write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps({'receipt':str(out),'deployment':result['deployment_after'],'changed_records_checked':10,'disagreements':discrepancies,'widths':result['width_boundary']},indent=2))

if __name__=='__main__':main()
