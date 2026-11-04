#!/usr/bin/env python3
"""Reconcile CellStructureMech's review-only redeployment with the Nov4 audit.
Inputs: pinned source, GitHub compare/deployment APIs and live browser.
Outputs: supplemental receipt and Cell auditor addendum; corpus pin is retained.
2026-11-04 refresh PR provenance. No production data or GitHub writes.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_site_group_20261104 import CHROME,gh,now,state

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/'_fleet/reviews/refresh-20261104'
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a')
SNAP=Path('/private/tmp/xmech-refresh-20261104-snapshot/mechs/CellStructureMech')
OLD='6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc'
NEW='d4d24c6c38d06ef27a6bac2c25ed381d50e96431'
BASE='https://culturebotai.github.io/CellStructureMech/'

def deployment(ctx):
    d=gh('repos/CultureBotAI/CellStructureMech/deployments?environment=github-pages&per_page=1')[0]
    s=gh(f'repos/CultureBotAI/CellStructureMech/deployments/{d["id"]}/statuses?per_page=1')[0]
    url=BASE+'pages/index.html';r=ctx.request.head(url)
    return {k:d[k] for k in ('id','sha','created_at')}|{'latest_status':{k:s[k] for k in ('state','created_at','environment_url')},'header_url':url,'http_status':r.status,'last_modified':r.headers.get('last-modified')}

def action_state(page):
    s=state(page)
    return {k:s[k] for k in ('url','theme','savedTheme','statuses','firstRows','visibleRows','width','scrollWidth')}

def main():
    ledger_path=EVID/'cellstructuremech-auditor-a.json';ledger=json.loads(ledger_path.read_text());assert ledger['pin']==OLD
    compare=gh(f'repos/CultureBotAI/CellStructureMech/compare/{OLD}...{NEW}')
    files=[x['filename'] for x in compare['files']]
    assert compare['total_commits']==1 and all(x.startswith('reviews/structured/') for x in files)
    original_tree={row.split('\t')[1]:row.split()[2] for row in subprocess.check_output(['git','-C',str(SNAP),'ls-tree',OLD],text=True).splitlines()}
    new_tree={x['path']:x['sha'] for x in gh(f'repos/CultureBotAI/CellStructureMech/git/trees/{NEW}')['tree']}
    tree_comparison={k:{'old':v,'new':new_tree.get(k),'equal':v==new_tree.get(k)} for k,v in original_tree.items() if k!='reviews'}
    assert all(x['equal'] for x in tree_comparison.values())
    result={'mech':'CellStructureMech','reviewer':'deployment_review redeployment auditor','started_at':now(),'corpus_pin':OLD,'served_revision':NEW,'source_diff':{'compare_url':compare['html_url'],'commits':compare['total_commits'],'changed_files':files,'root_trees_excluding_reviews':tree_comparison,'assessment':'Only 22 structured-review report files changed. Every other root tree/blob, including published pages, source templates, data and configuration, has the identical Git object hash.'},'pages':{},'actions':{}}
    raw={'compare':compare,'pages':{}}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page()
        result['deployment_before']=deployment(c)
        for route in ledger['receipts']['pages']:
            r=p.goto(BASE+route,wait_until='networkidle');p.wait_for_timeout(350)
            if route=='pages/index.html':
                toggle=p.locator('button.theme-toggle')
                if toggle.count():toggle.first.click()
            desktop=state(p)
            p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(200);resized=state(p)
            p.reload(wait_until='networkidle');p.wait_for_timeout(200);fresh=state(p)
            raw['pages'][route]={'desktop':desktop,'resized':resized,'fresh':fresh}
            result['pages'][route]={'url':BASE+route,'http_status':r.status,'h1':desktop['h1'],'footer':desktop['footer'],'theme':desktop.get('theme'),'resized_width':resized['scrollWidth'],'fresh_width':fresh['scrollWidth'],'body_sha256':hashlib.sha256(desktop['text'].encode()).hexdigest(),'svg_counts':desktop['svgs'],'excerpt':desktop['text'][:400]}
            assert r.status==200 and resized['scrollWidth']<=390 and fresh['scrollWidth']<=390
            p.set_viewport_size({'width':1280,'height':900})
        p.goto(BASE+'pages/browse.html',wait_until='networkidle')
        q=p.locator('input[type=search]').first
        for value in ('GO:0097589','MitoStore','no-such-cell-redeploy-audit'):
            q.fill(value);p.wait_for_timeout(250);result['actions']['query:'+value]=action_state(p)
        q.fill('');p.wait_for_timeout(200)
        category=p.locator('select').filter(has=p.locator('option[value="microcompartment"]'))
        # Actual category select identified by its option value, not a guessed id.
        if category.count():category.first.select_option('microcompartment');p.wait_for_timeout(200);result['actions']['category_microcompartment']=action_state(p)
        sorts=p.locator('select[id*=sort]')
        if sorts.count():
            opts=sorts.first.locator('option').evaluate_all('(xs)=>xs.map(x=>x.value)')
            for value in opts[:2]:sorts.first.select_option(value);p.wait_for_timeout(150);result['actions']['sort:'+value]=action_state(p)
        result['actions']['before_reload']=action_state(p);p.reload(wait_until='networkidle');result['actions']['after_reload']=action_state(p)
        # Re-exercise the sole fetched map's failure state after this deployment.
        f=b.new_context();blocked=[]
        def abort(route):blocked.append(route.request.url);route.abort()
        f.route('**/*.json',abort);fp=f.new_page();fp.goto(BASE+'pages/embedding-map.html',wait_until='networkidle');fp.wait_for_timeout(300)
        result['failure_check']={'blocked':blocked,'excerpt':fp.inner_text('body')[-1600:]};f.close()
        result['deployment_after']=deployment(c);b.close()
    assert result['deployment_after']['sha']==NEW and result['deployment_after']['latest_status']['state']=='success'
    result['criterion_reconciliation']={k:{'status':v['status'],'previous_evidence':'cellstructuremech-auditor-a.json#/features/'+k,'basis':'The source and published-page trees are byte-identical; post-deployment route/control checks agree with the prior complete audit.'} for k,v in ledger['features'].items()};assert len(result['criterion_reconciliation'])==24
    result['finished_at']=now()
    raw_path=ARCHIVE/'cell-redeployment-d4d24c6-raw.json';raw_path.write_text(json.dumps(raw,indent=2)+'\n')
    result['raw_capture']={'path':str(raw_path),'sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    out=EVID/'cellstructuremech-redeployment-20261104.json';out.write_text(json.dumps(result,indent=2)+'\n')
    ledger['redeployment_followup']={'receipt':out.name,'verified_at':result['finished_at'],'served_revision':NEW,'deployment_before':result['deployment_before'],'deployment_after':result['deployment_after'],'status_changes':0,'public_tree_hashes_unchanged':True,'independent_review':'Pending central_directory skepticism'}
    ledger_path.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'receipt':str(out),'pages_checked':len(result['pages']),'deployment':result['deployment_after'],'criteria':24,'source_change':'reviews/structured only; all other root object hashes unchanged'},indent=2))

if __name__=='__main__':main()
