#!/usr/bin/env python3
"""Independently check CultureMech's concurrent deployment for the Nov4 refresh.
Inputs: GitHub read-only deployment/compare APIs, live schema/browser, prior audit.
Outputs: compact skeptic receipt and B-review deployment addendum. No site changes.
2026-11-04; central directory refresh PR provenance.
"""
import hashlib
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_site_group_20261104 import CHROME,gh,now

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/'_fleet/reviews/refresh-20261104'
OLD='a74dd489720c9df96cc073ffd11568d407d3c06c'
NEW='09f908802989670d2cc799f75f67cf56f7834178'
BASE='https://culturebotai.github.io/CultureMech/'

def deploy(ctx):
    d=gh('repos/CultureBotAI/CultureMech/deployments?environment=github-pages&per_page=1')[0]
    s=gh(f'repos/CultureBotAI/CultureMech/deployments/{d["id"]}/statuses?per_page=1')[0]
    r=ctx.request.head(BASE+'app/')
    return {k:d[k] for k in ('id','sha','created_at')}|{'latest_status':{k:s[k] for k in ('state','created_at','environment_url')},'header_url':BASE+'app/','http_status':r.status,'last_modified':r.headers.get('last-modified')}

def main():
    result={'reviewer':'deployment_review independent redeployment skeptic','started_at':now(),'corpus_pin':OLD,'served_revision':NEW}
    compare=gh(f'repos/CultureBotAI/CultureMech/compare/{OLD}...{NEW}')
    filenames=[x['filename'] for x in compare['files']]
    archive=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a/culture-redeployment-compare.json')
    archive.write_text(json.dumps(compare,indent=2)+'\n')
    result['source_diff']={'compare_url':compare['html_url'],'commits':compare['total_commits'],'changed_files':filenames,'changed_recipe_data':[x for x in filenames if x.startswith(('data/','normalized_yaml/','merged_yaml/'))],'changed_page_renderers':[x for x in filenames if re.search(r'(render|generate.*page|build.*site|app/|templates/|\.github/workflows)',x)],'assessment':'Schema, causal-graph validation/writer and KGX-export infrastructure changed. Recipe data and page renderers are outside the diff. The schema document is regenerated from changed source.','raw':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    assert compare['total_commits']==1 and not result['source_diff']['changed_recipe_data'] and not result['source_diff']['changed_page_renderers']
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME);c=b.new_context(viewport={'width':1280,'height':900});p=c.new_page()
        result['deployment_before']=deploy(c)
        r=p.goto(BASE+'app/schema.html',wait_until='networkidle');text=p.inner_text('body')
        counts=re.search(r'(\d+) classes\s*·\s*(\d+) enums',text)
        assert counts and counts.groups()==('51','34')
        result['schema']={'url':p.url,'status':r.status,'verbatim_counts':counts.group(0),'classes':51,'enums':34,'new_terms_present':{term:term in text for term in ('CausalEdge','CausalTerm','CausalPredicateEnum')},'excerpt':text[:640],'locator':'body schema count summary and generated class/enum sections'}
        p.goto(BASE+'app/browser.html',wait_until='networkidle');p.wait_for_timeout(600)
        result['browser']={'sort_selects':p.locator('select').count(),'sort_buttons':p.get_by_role('button',name=re.compile('sort',re.I)).count(),'queries':{}}
        for query in ('CultureMech:000252','Halophilic medium','no-such-record-nov4-skeptic'):
            p.locator('#searchInput').fill(query);p.wait_for_timeout(500)
            result['browser']['queries'][query]={'url':p.url,'verbatim_count':p.locator('#resultsCount').inner_text()}
        p.locator('#searchInput').fill('Halophilic medium');p.locator('input[data-facet="category"][data-value="bacterial"]').check();p.wait_for_timeout(500)
        result['browser']['combined']={'url':p.url,'verbatim_count':p.locator('#resultsCount').inner_text()}
        p.reload(wait_until='networkidle');p.wait_for_timeout(500)
        result['browser']['reload']={'url':p.url,'verbatim_count':p.locator('#resultsCount').inner_text(),'query':p.locator('#searchInput').input_value()}
        result['deployment_after']=deploy(c);b.close()
    assert result['deployment_after']['sha']==NEW and result['deployment_after']['id']==7545180210
    assert result['deployment_after']['latest_status']['state']=='success'
    current=json.loads((EVID/'culturemech-auditor-b.json').read_text())
    review_path=EVID/'group-b-independent-review.json';review=json.loads(review_path.read_text())
    disagreements=[k for k,v in current['features'].items() if review['features']['CultureMech'][k]['skeptic']!=v['status']]
    assert len(current['features'])==24 and not disagreements
    result['criterion_comparison']={'criteria':24,'status_disagreements':disagreements,'only_note_change':'schema_docs count 49 classes / 33 enums becomes 51 classes / 34 enums','auditor_supplement':'culturemech-redeployment-20261104.json','decision':'Prior feature verdicts remain valid for this served revision. Schema docs remain present.'}
    result['finished_at']=now()
    path=EVID/'culturemech-redeployment-skeptic.json';path.write_text(json.dumps(result,indent=2)+'\n')
    review['culture_redeployment']={'receipt':path.name,'verified_at':result['finished_at'],'corpus_pin':OLD,'served_revision':NEW,'deployment':result['deployment_after'],'schema_classes':51,'schema_enums':34,'criteria_reconciled':24,'status_disagreements':0}
    review_path.write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps({'receipt':str(path),'deployment':result['deployment_after'],'schema':result['schema']['verbatim_counts'],'browser':result['browser'],'status_disagreements':disagreements},indent=2))

if __name__=='__main__':main()
