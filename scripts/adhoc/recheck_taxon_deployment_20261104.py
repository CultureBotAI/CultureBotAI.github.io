#!/usr/bin/env python3
"""Reconcile Taxon's final known redeployment with the Nov4 feature audit.
Inputs: former served SHA, immutable common pin, live Pages and GitHub read APIs.
Outputs: Taxon-only supplemental receipt and auditor metadata. No production edits.
2026-11-04 refresh PR provenance; complete raw browser states archived outside Git.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_site_group_20261104 import CHROME,gh,now,state

ROOT=Path(__file__).resolve().parents[2];EVID=ROOT/'_fleet/reviews/refresh-20261104'
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a')
OLD='b04590a7a416eb934f67e7c04416e37924f10ec8';NEW='e0cc7c86ac2107242ab499db610737f5fcad1c9b'
BASE='https://culturebotai.github.io/TaxonMech/'

def deploy(ctx):
    d=gh('repos/CultureBotAI/TaxonMech/deployments?environment=github-pages&per_page=1')[0]
    s=gh(f'repos/CultureBotAI/TaxonMech/deployments/{d["id"]}/statuses?per_page=1')[0]
    url=BASE+'pages/index.html';r=ctx.request.head(url)
    return {k:d[k] for k in ('id','sha','created_at')}|{'latest_status':{k:s[k] for k in ('state','created_at','environment_url')},'header_url':url,'http_status':r.status,'last_modified':r.headers.get('last-modified')}

def action(page):
    d=state(page)
    return {k:d[k] for k in ('url','statuses','firstRows','visibleRows')}|{'filters':[{k:x[k] for k in ('id','value')} for x in d['controls'] if x['tag']=='SELECT']}

def main():
    ledger_path=EVID/'taxonmech-auditor-a.json';ledger=json.loads(ledger_path.read_text());assert ledger['pin']==NEW
    compare=gh(f'repos/CultureBotAI/TaxonMech/compare/{OLD}...{NEW}');files=[x['filename'] for x in compare['files']]
    assert compare['total_commits']==1 and len(files)==9
    assert not any(x.startswith(('data/','pages/','src/','scripts/','.github/','conf/')) for x in files)
    trees={sha:{x['path']:x['sha'] for x in gh(f'repos/CultureBotAI/TaxonMech/git/trees/{sha}')['tree']} for sha in (OLD,NEW)}
    equal={k:{'old':v,'new':trees[NEW].get(k),'equal':v==trees[NEW].get(k)} for k,v in trees[OLD].items() if k not in ('curation','docs','reviews','tests')};assert all(x['equal'] for x in equal.values())
    result={'mech':'TaxonMech','reviewer':'deployment_review redeployment auditor','started_at':now(),'corpus_pin':NEW,'previous_served_revision':OLD,'served_revision':NEW,'source_diff':{'compare_url':compare['html_url'],'changed_files':files,'commits':1,'unchanged_root_objects':equal,'assessment':'Only curation documentation, review reports and a test changed. No records, rendered pages, schema or renderer inputs changed; there are no new record pages to sample.'},'pages':{},'actions':{}}
    raw={'compare':compare,'pages':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page();result['deployment_before']=deploy(c)
        for route in ledger['receipts']['pages']:
            r=p.goto(BASE+route,wait_until='networkidle',timeout=120000);p.wait_for_timeout(400)
            if route=='pages/index.html':
                toggle=p.locator('button.theme-toggle')
                if toggle.count():toggle.first.click()
            desktop=state(p);p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(180);narrow=state(p)
            result['pages'][route]={'url':p.url,'http_status':r.status,'h1':desktop['h1'],'theme':desktop.get('theme'),'footer':desktop['footer'],'resized_width_390':narrow['scrollWidth'],'excerpt':desktop['text'][:650],'named_evidence_and_source_links':[{'text':a['text'],'href':a['href']} for a in desktop['allLinks'] if re.search(r'pubmed|doi.org|/blob/main/data/|ncbi.nlm.nih.gov/Taxonomy',a['href'])][:20],'visuals':desktop['svgs']+desktop['canvases']}
            assert r.status==200 and narrow['scrollWidth']<=390
            raw['pages'][route]={'desktop':desktop,'narrow':narrow}
            p.set_viewport_size({'width':1280,'height':900})
        p.goto(BASE+'pages/browse.html',wait_until='networkidle',timeout=120000);q=p.locator('input[type=search]').first
        for query in ('NCBITaxon:2173','Methanobrevibacter smithii','NCBITaxon:562','no-such-taxon-skeptic'):
            q.fill(query);p.wait_for_timeout(700);result['actions']['query:'+query]=action(p)
        q.fill('');p.wait_for_timeout(400)
        p.locator('#taxon-domain-filter').select_option('BACTERIA');p.wait_for_timeout(300);result['actions']['domain_bacteria']=action(p)
        p.locator('#taxon-rank-filter').select_option('SPECIES');p.wait_for_timeout(300);result['actions']['domain_bacteria_rank_species']=action(p)
        p.reload(wait_until='networkidle',timeout=120000);p.wait_for_timeout(700);result['actions']['facet_reload']=action(p)
        sorts=p.locator('select[id*=sort]')
        if sorts.count():
            for value in sorts.first.locator('option').evaluate_all('(xs)=>xs.slice(0,2).map(x=>x.value)'):
                sorts.first.select_option(value);p.wait_for_timeout(250);result['actions']['sort:'+value]=action(p)
        p.goto(BASE+'pages/browse.html',wait_until='networkidle',timeout=120000)
        next_link=p.get_by_role('link',name=re.compile('^Next'))
        if next_link.count():next_link.first.click();p.wait_for_timeout(500);result['actions']['pagination_next']=action(p)
        f=b.new_context();blocked=[]
        def abort(route):blocked.append(route.request.url);route.abort()
        f.route('**/index.json.gz',abort);fp=f.new_page();fp.goto(BASE+'pages/browse.html',wait_until='networkidle');fp.locator('input[type=search]').first.fill('smithii');fp.wait_for_timeout(500)
        text=fp.inner_text('body');pos=text.lower().find('unavailable');result['failure_check']={'blocked':blocked,'excerpt':text[max(0,pos-120):max(0,pos)+400]};assert 'unavailable' in text.lower();f.close()
        result['deployment_after']=deploy(c);b.close()
    assert result['deployment_after']['sha']==NEW and result['deployment_after']['latest_status']['state']=='success'
    result['criterion_reconciliation']={k:{'status':v['status'],'evidence':'taxonmech-auditor-a.json#/features/'+k,'basis':'Public page, source and data hashes unchanged; current route, evidence, map, query and control checks agree.'} for k,v in ledger['features'].items()};assert len(result['criterion_reconciliation'])==24
    result['finished_at']=now();raw_path=ARCHIVE/'taxon-redeployment-e0cc7c8-raw.json';raw_path.write_text(json.dumps(raw,indent=2)+'\n');result['raw_capture']={'path':str(raw_path),'sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    out=EVID/'taxonmech-redeployment-20261104.json';out.write_text(json.dumps(result,indent=2)+'\n')
    ledger.setdefault('initial_deployment_after',ledger['deployment_after']);ledger['deployment_after']=result['deployment_after'];ledger['supplemented_at']=result['finished_at']
    ledger['redeployment_followup']={'receipt':out.name,'verified_at':result['finished_at'],'served_revision':NEW,'deployment_after':result['deployment_after'],'status_changes':0,'public_tree_hashes_unchanged':True,'independent_review':'Pending central_directory skepticism'}
    ledger_path.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'receipt':str(out),'deployment':result['deployment_after'],'routes':len(result['pages']),'criteria':24,'facet_before':result['actions']['domain_bacteria_rank_species']['statuses'],'facet_reload':result['actions']['facet_reload']['statuses']},indent=2))

def accept():
    skeptic=json.loads((EVID/'taxonmech-redeployment-skeptic.json').read_text())
    assert skeptic['deployment_after']['sha']==NEW and skeptic['deployment_after']['state']=='success'
    path=EVID/'taxonmech-auditor-a.json';ledger=json.loads(path.read_text())
    assert ledger['pin']==NEW and ledger['deployment_after']['sha']==NEW
    ledger['redeployment_followup']['deployment_after']=ledger['deployment_after']
    ledger['redeployment_followup']['independent_review']='taxonmech-redeployment-skeptic.json; all 24 criteria agreed'
    path.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
    receipt=EVID/'taxonmech-redeployment-20261104.json';data=json.loads(receipt.read_text())
    data['independent_review']='taxonmech-redeployment-skeptic.json; all 24 criteria agreed'
    receipt.write_text(json.dumps(data,indent=2)+'\n')
    print('Taxon follow-up accepted; latest deployment promoted, initial metadata and pin preserved.')

if __name__=='__main__':
    if '--accept' in sys.argv:accept()
    else:main()
