#!/usr/bin/env python3
"""Resolve specific group-B browser audit challenges; no source/site mutations.
Inputs: public pages and completed Nov4 browser receipts. Outputs: supplemental
receipts and compacted original captures; supports fleet refresh PR. 2026-11-04.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_browser_group_b_20261104 import CHROME, OUT, SNAPSHOT_JS, compact, deployment, now

def main():
    # Remove unnecessarily retained full external metadata; content hashes remain.
    for f in OUT.glob('*-browser-b.json'):
        data=json.loads(f.read_text())
        for item in data.get('bulk',{}).values():
            for key,value in list(item.get('data',{}).items()):
                if isinstance(value,dict) and len(json.dumps(value))>30000:
                    item['data'][key]={'count':len(value),'keys':list(value)[:30],'omitted_large_payload':True}
        tmp=f.with_suffix('.json.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(f)
    report={'reviewer':'central_directory group B auditor','started_at':now(),'pages':{},'checks':{}}
    dest=OUT/'group-b-supplement.json'
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        context=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=context.new_page()
        def capture(url,wait=None):
            page.goto('about:blank')
            response=page.goto(url,wait_until='networkidle',timeout=90000)
            if wait:page.wait_for_selector(wait,timeout=60000)
            page.wait_for_timeout(1500)
            rec=compact(page.evaluate(SNAPSHOT_JS));rec.update(http_status=response.status,checked_at=now())
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
            rec['fresh_390']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            page.set_viewport_size({'width':1280,'height':900})
            report['pages'][url]=rec
            dest.write_text(json.dumps(report,indent=2)+'\n')
            return rec
        base='https://culturebotai.github.io/proteintraitsmech/'
        for rid in ['MCSA:1','METPO:1000639','ECOD:F.3755.3.1.364']:
            from urllib.parse import quote
            capture(base+'browse.html#record='+quote(rid,safe=''), '#results .detail, #results h1, #results h2')
        capture(base+'browse.html')
        page.locator('.theme-toggle').click();page.wait_for_timeout(100)
        report['checks']['protein_browse_toggle']={'theme':page.locator('html').get_attribute('data-theme'),'saved':page.evaluate('localStorage.getItem("mech-theme")')}
        capture(base)
        before=page.locator('html').get_attribute('data-theme')
        page.locator('#theme-toggle').click();page.wait_for_timeout(100)
        report['checks']['protein_landing_toggle']={'before':before,'after':page.locator('html').get_attribute('data-theme'),'text':page.locator('#theme-toggle').inner_text()}
        capture(base+'slc10.html')
        capture(base+'schema.html')
        capture(base+'browse.html')
        page.set_viewport_size({'width':390,'height':844})
        page.get_by_role('button',name='Show all (63)',exact=True).click()
        page.wait_for_timeout(300)
        report['checks']['protein_expanded_categories']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,text:document.getElementById("facets").innerText})')
        page.set_viewport_size({'width':1280,'height':900})
        response=context.request.get(base+'data/map-coverage.json')
        report['checks']['protein_map_coverage']={'url':response.url,'status':response.status,'data':response.json()}
        capture('https://culturebotai.github.io/MediaIngredientMech/schema/classes-IngredientRecord.html')
        # Open actual downloadable and sibling-record anchors, never invented routes.
        for mech,needles in [('MediaIngredientMech',['.json','.csv']),('CommunityMech',['.json','.tsv'])]:
            data=json.loads((OUT/(mech.lower()+'-browser-b.json')).read_text())
            landing=next(v for u,v in data['pages'].items() if u.endswith('/'+mech+'/'))
            report['checks'][mech+'_download_links']=[]
            for link in landing['links']:
                if any(link['url'].endswith(ext) for ext in needles):
                    r=context.request.get(link['url'],timeout=60000)
                    report['checks'][mech+'_download_links'].append({'url':link['url'],'text':link['text'],'status':r.status,'bytes':len(r.body())})
        report['deployment_after']={}
        for mech in ['ProteinTraitsMech','MediaIngredientMech']:
            repo='proteintraitsmech' if mech=='ProteinTraitsMech' else mech
            report['deployment_after'][mech]=deployment(repo,'https://culturebotai.github.io/'+repo+'/')
        browser.close()
    report['finished_at']=now();dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(dest),'finished_at':report['finished_at']}))

if __name__=='__main__':main()
