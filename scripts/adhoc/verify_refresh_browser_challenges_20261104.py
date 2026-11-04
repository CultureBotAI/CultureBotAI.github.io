#!/usr/bin/env python3
"""Independent targeted browser challenges from Nov4 reciprocal site review.
Inputs: public sites and existing pinned audit receipts. Output: additional compact
evidence for settled queries, failure-state overwrites and links. 2026-11-04.
"""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_browser_group_b_20261104 import CHROME,OUT,ACTION_JS,now,deployment

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--protein',action='store_true');args=ap.parse_args()
    report={'reviewer':'central_directory independent challenge','started_at':now(),'checks':{}}
    dest=OUT/('protein-query-followup.json' if args.protein else 'group-a-skeptic-challenges.json')
    def save():dest.write_text(json.dumps(report,indent=2)+'\n')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        ctx=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=ctx.new_page()
        if args.protein:
            url='https://culturebotai.github.io/proteintraitsmech/browse.html'
            page.goto(url,wait_until='networkidle',timeout=90000)
            def state():
                page.wait_for_timeout(1000)
                page.wait_for_function("!document.getElementById('results').innerText.match(/Loading .*shards|Loading records/i)",timeout=120000)
                return page.evaluate(ACTION_JS)
            for q in ['cd05137','homogentisate 1,2-dioxygenase','no-such-record-nov4-audit']:
                page.locator('#q').fill(q);report['checks']['query:'+q]=state();save()
            page.goto('about:blank');page.goto(url+'#cat=STRUCT_ACTIVE_SITE&q=racemase',wait_until='networkidle',timeout=90000)
            report['checks']['cold_active_site_racemase']=state()
            page.reload(wait_until='networkidle');report['checks']['restored']=state()
            report['deployment_after']=deployment('proteintraitsmech',url)
        else:
            for mech in ['AntibioticMech','HabitatMech']:
                url=f'https://culturebotai.github.io/{mech}/pages/browse.html'
                page.goto(url,wait_until='networkidle',timeout=90000)
                page.locator('input[type=search],input[type=text]').first.fill('a')
                page.wait_for_timeout(1500)
                report['checks'][mech+'_broad_search']=page.evaluate(ACTION_JS)
                save()
            failed=ctx.new_page();blocked=[]
            def fail_index(route):blocked.append(route.request.url);route.abort()
            failed.route('**/category/*.json',fail_index)
            failed.goto('https://culturebotai.github.io/HabitatMech/pages/browse.html',wait_until='networkidle')
            failed.wait_for_timeout(500)
            failed.locator('input[type=search],input[type=text]').first.fill('water')
            failed.wait_for_timeout(500)
            report['checks']['Habitat_failed_search']={'blocked':blocked,'state':failed.evaluate(ACTION_JS)}
            failed.close();save()
            for mech in ['AntibioticMech','NaturalProductMech']:
                test=ctx.new_page();blocked=[]
                def abort(route):blocked.append(route.request.url);route.abort()
                test.route('**/*sequence*.json',abort)
                url=f'https://culturebotai.github.io/{mech}/pages/sequence-map.html'
                test.goto(url,wait_until='networkidle',timeout=90000);test.wait_for_timeout(300)
                before=test.locator('body').inner_text()
                inputs=test.locator('input[type=search],input[type=text]')
                inputs.first.fill('protein');test.wait_for_timeout(300)
                report['checks'][mech+'_failed_sequence_search']={'url':url,'blocked':blocked,'before':before,'after':test.locator('body').inner_text()}
                test.close();save()
            url='https://culturebotai.github.io/HabitatMech/pages/index.html'
            page.goto(url,wait_until='networkidle')
            for i in range(3):
                if page.locator('html').get_attribute('data-theme')=='dark':break
                page.locator('.theme-toggle').click()
            report['checks']['Habitat_dark_selected']={'url':url,'theme':page.locator('html').get_attribute('data-theme')}
            page.goto('https://culturebotai.github.io/HabitatMech/pages/text-map-source/index.html',wait_until='networkidle')
            report['checks']['Habitat_map_dark']={'url':page.url,'theme':page.locator('html').get_attribute('data-theme'),'toggle_count':page.locator('.theme-toggle').count(),'background':page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')}
            target='https://culturebotai.github.io/TaxonMech/browse.html?q=Sulfurimonas'
            r=ctx.request.get(target);report['checks']['Habitat_Taxon_target']={'url':target,'status':r.status}
            # Validate linked CellStructure complete-corpus contents, not only its index.
            url='https://culturebotai.github.io/CellStructureMech/pages/index.html'
            page.goto(url,wait_until='networkidle')
            links=page.locator('a[href]').evaluate_all('(es)=>es.map(e=>({url:e.href,text:e.innerText}))')
            report['checks']['Cell_downloads']=[]
            for link in links:
                if link['url'].endswith('.json') and 'cellstructuremech' in link['url'].lower():
                    r=ctx.request.get(link['url']);data=r.json()
                    item={'url':link['url'],'text':link['text'],'status':r.status,'type':type(data).__name__}
                    if isinstance(data,list):item.update(count=len(data),first_fields=list(data[0]) if data else [])
                    elif isinstance(data,dict):item.update(keys=list(data),sample_fields={k:list(v[0]) if v and isinstance(v[0],dict) else len(v) for k,v in data.items() if isinstance(v,list)})
                    report['checks']['Cell_downloads'].append(item)
            report['checks']['Pathway_downloads']=[]
            for name in ['downloads/manifest.json','pathway_index.json','downloads/nodes.tsv','downloads/edges.tsv']:
                url='https://culturebotai.github.io/PathwayMech/pages/'+name
                r=ctx.request.get(url);item={'url':url,'status':r.status}
                if name.endswith('.json'):
                    data=r.json()
                    if isinstance(data,list):item.update(count=len(data),first_record=data[0])
                    else:item['data']=data
                else:item['header_and_first_row']=r.text().splitlines()[:2]
                report['checks']['Pathway_downloads'].append(item)
            report['deployment_after']={m:deployment(m,f'https://culturebotai.github.io/{m}/pages/index.html') for m in ['AntibioticMech','NaturalProductMech','HabitatMech','CellStructureMech']}
        browser.close()
    report['finished_at']=now();save();print(dest)

if __name__=='__main__':main()
