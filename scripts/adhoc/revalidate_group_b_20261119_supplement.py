#!/usr/bin/env python3
"""Resolve bounded Group B live audit questions, 2026-11-19.

Inputs: public sites and primary Group B receipts. Outputs: new supplement JSON
and screenshots in the owned evidence directory. Supports the feature-only PR.
Never modifies source sites, prior receipts, or shared catalogue data.
"""
import argparse
import json
from urllib.parse import quote
from revalidate_group_b_20261119 import (
    ROOT, OUT, CHROME, GROUP, now, deployment, capture, settle, dark, ACTION_JS,
)
from playwright.sync_api import sync_playwright

EXTRAS = {
 'CultureMech':['app/umap_graph.html'],
 'MediaIngredientMech':['ingredient_graph.html', 'records/ingredient/mapped/Bacteriocin_Isk_1.html', 'records/ingredient/mapped/BHI.html'],
 'ProteinTraitsMech':['browse.html#record='+quote(i,safe='') for i in ['MCSA:1','METPO:1000639','ECOD:F.3755.3.1.364']],
 'NaturalProductMech':['pages/terpenoids/index.html'],
 'DUFMech':['categories/ex_duf.html'],
 'CMMMech':[],
}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mech',required=True,choices=GROUP)
    args=parser.parse_args()
    config=json.loads((ROOT/'_fleet/data/site_features.json').read_text())['mechs'][args.mech]
    repo=config['repository'].rsplit('/',1)[-1]; base=f'https://culturebotai.github.io/{repo}/'
    dest=OUT/(args.mech.lower()+'-supplement.json')
    if dest.exists(): raise SystemExit('Refusing overwrite: '+str(dest))
    result={'mech':args.mech,'started_at':now(),'deployment_before':deployment(repo,config['site']),'pages':{},'checks':{}}
    def save(): dest.write_text(json.dumps(result,indent=2)+'\n')
    save()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        ctx=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=ctx.new_page(); page.set_default_timeout(15000)
        def visit(url,key=None):
            page.goto('about:blank')
            r=page.goto(url,wait_until='networkidle',timeout=90000)
            settle(page,args.mech)
            rec=capture(page)|{'http_status':r.status,'checked_at':now()}
            # Record identifiers must be present in actual detail content, not loading shells.
            if '#record=' in url:
                rec['populated_detail']=page.locator('#results .detail').inner_text()
            page.set_viewport_size({'width':390,'height':844}); settle(page,args.mech)
            rec['resized_390']=capture(page)
            page.reload(wait_until='networkidle',timeout=90000); settle(page,args.mech)
            rec['fresh_390']=capture(page)
            page.set_viewport_size({'width':1280,'height':900})
            result['pages'][key or url]=rec; save(); return rec
        if args.mech=='ProteinTraitsMech':
            visit(base+'browse.html'); dark(page); settle(page,args.mech)
            result['checks']['browse_toggle']=capture(page);save()
        else:
            visit(config['site']);dark(page);settle(page,args.mech)
        for path in EXTRAS[args.mech]:
            try: visit(base+path)
            except Exception as error: result['pages'][base+path]={'error':str(error)};save()
        if args.mech=='ProteinTraitsMech':
            visit(base); before=capture(page);dark(page);settle(page,args.mech)
            result['checks']['landing_toggle']={'before':before,'after':capture(page)}
            visit(base+'slc10.html');visit(base+'browse.html')
            page.set_viewport_size({'width':390,'height':844})
            page.get_by_role('button',name='Show all (63)',exact=True).click();settle(page,args.mech)
            result['checks']['expanded_categories_390']=capture(page)
            page.set_viewport_size({'width':1280,'height':900})
            # No active axis means all shards; force a nonempty broad search so the
            # fetch lifecycle completes before preserving the complete count.
            page.locator('#q').fill('');settle(page,args.mech)
            result['checks']['all_axes_catalogue']=page.evaluate(ACTION_JS);save()
        if args.mech=='NaturalProductMech':
            visit(base+'pages/browse.html')
            record_links = r'''() => {let a=[...document.querySelectorAll('a[href]')].filter(e=>/\/pages\/(alkaloids|amino_acids_and_peptides|carbohydrates|fatty_acids|polyketides|shikimates_and_phenylpropanoids|terpenoids|unclassified)\//.test(e.href)&&!e.href.endsWith('/index.html'));return {total:a.length,unique:new Set(a.map(e=>e.href)).size,first:a.filter(e=>e.getClientRects().length).slice(0,5).map(e=>({text:e.innerText,url:e.href}))};}'''
            result['checks']['complete_catalogue_links']=page.evaluate(record_links)
            result['checks']['sort_orders']={}
            for option in ['label-asc','label-desc','causal-desc','clusters-desc','bioactivity-desc','id-asc']:
                page.locator('#facet-sort').select_option(option);page.wait_for_timeout(300)
                result['checks']['sort_orders'][option]=page.evaluate(record_links)
            save()
            target=base+'pages/sequence-map.html';blocked=[]
            def block(route):
                if route.request.resource_type in ('fetch','xhr'):
                    blocked.append(route.request.url);route.abort()
                else:route.continue_()
            page.route('**/*',block);visit(target,'sequence_failure_before_input')
            fields=page.locator('input[type=search],input[type=text]')
            if fields.count():fields.first.fill('marneral');page.wait_for_timeout(300)
            result['checks']['sequence_failure_after_input']={'aborted':blocked,'capture':capture(page)}
            page.unroute('**/*',block);visit(target,'sequence_failure_recovered');save()
        # Read exact linked exports and public sibling/source anchors from sampled pages.
        links={}
        primary=json.loads((OUT/(args.mech.lower()+'.json')).read_text())
        for rec in [*primary['pages'].values(),*result['pages'].values()]:
            for link in rec.get('links',[]):
                url=link['url']
                if url.startswith(base) and url.endswith(('.json','.tsv','.csv')):
                    links[url]=link['text']
        result['checks']['linked_exports']={}
        for url,text in links.items():
            if len(result['checks']['linked_exports'])>=12:break
            try:
                r=ctx.request.get(url,timeout=60000);body=r.body()
                value={'text':text,'status':r.status,'bytes':len(body)}
                if r.ok and url.endswith('.json'):
                    obj=r.json();value['top_level_type']=type(obj).__name__
                    if isinstance(obj,list):value.update(count=len(obj),first_keys=list(obj[0]) if obj and isinstance(obj[0],dict) else None)
                    elif isinstance(obj,dict):
                        value['keys']=list(obj)
                        value['lists']={k:{'count':len(v),'first_keys':list(v[0]) if v and isinstance(v[0],dict) else None} for k,v in obj.items() if isinstance(v,list)}
                result['checks']['linked_exports'][url]=value
            except Exception as error:result['checks']['linked_exports'][url]={'error':str(error)}
            save()
        # A retained screenshot proves a loaded visual, not just an allocated canvas.
        mapurl=next((u for u in primary['pages'] if ('map.html' in u or 'umap.html' in u) and '#' not in u),None)
        if mapurl:
            page.goto(mapurl,wait_until='networkidle',timeout=90000);settle(page,args.mech)
            path=OUT/(args.mech.lower()+'-map.png');page.screenshot(path=str(path))
            result['checks']['map_screenshot']={'url':mapurl,'path':str(path.relative_to(ROOT))}
        browser.close()
    result['deployment_after']=deployment(repo,config['site'])
    assert result['deployment_before']['id']==result['deployment_after']['id']
    assert result['deployment_before']['sha']==result['deployment_after']['sha']
    result['finished_at']=now();result['complete']=True;save()
    print(json.dumps({'mech':args.mech,'path':str(dest.relative_to(ROOT)),'complete':True}))

if __name__=='__main__':main()
