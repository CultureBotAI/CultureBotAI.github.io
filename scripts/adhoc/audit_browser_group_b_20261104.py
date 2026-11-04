#!/usr/bin/env python3
"""Read-only browser audit for seven Mech sites in the Nov 4 fleet refresh.

Inputs: site_features.json, pinned snapshot revisions, public Pages/deployments.
Outputs: per-site browser observations and later compact reviewer verdicts.
2026-11-04; follows the completed TraitMech auditor/skeptic canary.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

CHROME='/Users/marcin/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'
OUT=Path('_fleet/reviews/refresh-20261104')
GROUP=['CultureMech','MediaIngredientMech','CommunityMech','ProteinTraitsMech','DUFMech','CMMMech','AIMech']
GROUP_A=['AntibioticMech','CellStructureMech','HabitatMech','NaturalProductMech','PathwayMech','TaxonMech']
EXTRAS={
 'CultureMech':['app/text_map.html','app/ingredient_umap.html','app/umap.html','pages/media_growth_review.html','pages/normalized/index.html','pages/index.html'],
 'MediaIngredientMech':['text_map.html','ingredient_umap.html','schema/classes-IngredientRecord.html'],
 'CommunityMech':['text_map.html','sequence_map.html','community_umap.html'],
 'ProteinTraitsMech':['map.html','map.html#proteins','map.html#sequences','slc10.html','schema.html'],
 'DUFMech':['map.html','sequence-map.html','categories.html','sources.html','schema.html'],
 'CMMMech':['pages/map.html','pages/graph.html','pages/schema.html'],
 'AIMech':['pages/map.html','pages/graph.html','pages/schema.html']}
EXTRAS.update({
 'AntibioticMech':['pages/map.html','pages/chemical-map.html'],
 'CellStructureMech':['pages/embedding-map.html','pages/sequence-map.html'],
 'HabitatMech':['pages/text-map/','pages/map.html'],
 'NaturalProductMech':['pages/map.html','pages/chemical-map.html'],
 'PathwayMech':['pages/map.html','pages/sequence-map.html','pages/schema.html'],
 'TaxonMech':['pages/map.html','pages/schema.html']})
PROFILES={
 'CultureMech':('#searchInput',['CultureMech:000252','Halophilic medium'],None,'.clear-filters'),
 'MediaIngredientMech':('#search',['UNMAPPED_0196','table salt','CHEBI:63895'],'#sort-by','#reset-filters'),
 'CommunityMech':('#search',['CommunityMech:000134','CommunityMech:000139','ANME-SRB Marine Methane Seep Consortium'],'#sort-by','#reset-all'),
 'ProteinTraitsMech':('#q',['cd05137','homogentisate 1,2-dioxygenase'],'#sort',None),
 'DUFMech':('#family-query',['PF04149','Domain of unknown function (DUF397)','IPR007278'],'#family-sort','#reset-families'),
 'CMMMech':('#record-query',['CHEBI:27638','cmmmech:copper','Cobalt'],'#record-sort','button[type="reset"]'),
 'AIMech':('#searchInput',['AIMech:KernelPCA','Adam'],'#sortSelect','#resetFilters')}
PROFILES.update({
 'AntibioticMech':('#q',['CHEBI:2637','rifampicin','antibiotic'],'#facet-sort','#browse-reset'),
 'CellStructureMech':('#record-query',['GO:0097589','MitoStore','cellstructuremech:insoluble_protein_deposit'],'#record-sort','button[type="reset"]'),
 'HabitatMech':('#browse-q',['ENVO:03000033','marine sediment','water'],'#browse-sort','#browse-reset'),
 'NaturalProductMech':('#browse-query',['CHEBI:338412','marneral'],'#facet-sort','button[type="reset"]'),
 'PathwayMech':('#pathway-query',['MetaCyc:PWY-6543','trehalose'],'#pathway-sort','button[type="reset"]'),
 'TaxonMech':('#taxon-query',['NCBITaxon:2173','Methanobrevibacter smithii','NCBITaxon:562'],'#taxon-sort','#taxon-reset')})
SELECT_FACETS={'MediaIngredientMech':['#filter-status','#filter-source','#filter-quality'],
 'DUFMech':['#seed-filter','#characterization-filter','#curation-filter'],
 'CMMMech':['#record-kind','#record-mechanism','#record-criticality'],
 'AIMech':['#originSelect','#kindSelect','#branchSelect'],
 'AntibioticMech':['#facet-class','#facet-grounding','#facet-status'],
 'CellStructureMech':['#record-category','#record-kind','#record-status'],
 'HabitatMech':['#browse-grounding'],
 'NaturalProductMech':['#facet-pathway','#facet-claim'],
 'PathwayMech':['#pathway-type','#pathway-taxon','#pathway-grounding'],
 'TaxonMech':['#taxon-domain-filter','#taxon-rank-filter','#taxon-source-filter']}
BULK={'CultureMech':['app/recipes.json'],'MediaIngredientMech':['all_ingredients.json','data/ingredients.json'],
      'CommunityMech':['communities.json'],'ProteinTraitsMech':['data/facets.json','data/map-coverage.json'],
      'DUFMech':['index.json','catalogue.json'],'CMMMech':['pages/index.json'],'AIMech':['pages/index.json']}

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def api(path): return json.loads(subprocess.check_output(['gh','api',path],text=True))
def deployment(repo,url):
    d=api(f'repos/CultureBotAI/{repo}/deployments?environment=github-pages&per_page=1')[0]
    s=api(f"repos/CultureBotAI/{repo}/deployments/{d['id']}/statuses?per_page=1")[0]
    with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=30) as r:
        result={k:d[k] for k in ['id','sha','created_at']}
        result.update(state=s['state'],status_created_at=s['created_at'],http_status=r.status,
                      last_modified=r.headers.get('Last-Modified'),header_date=r.headers.get('Date'))
    return result

SNAPSHOT_JS='''() => {
 const all=(s)=>Array.from(document.querySelectorAll(s));
 const visible=(e)=>e.getClientRects().length>0;
 const text=(e)=>(e.innerText||e.textContent||'').trim();
 const selector=(e)=>e.id?'#'+CSS.escape(e.id): e.name?e.tagName.toLowerCase()+'[name="'+e.name+'"]':null;
 let body=document.body.innerText;
 return {title:document.title,url:location.href,body:body.length>30000?body.slice(0,22000)+'\\n[MIDDLE OMITTED]\\n'+body.slice(-8000):body,
  body_length:body.length,headings:all('h1,h2,h3').map(text),
  input_count:all('input').length,
  inputs:all('input').slice(0,120).map(e=>({selector:selector(e),type:e.type,value:e.value,placeholder:e.placeholder,aria:e.getAttribute('aria-label'),checked:e.checked,visible:visible(e),dataset:{...e.dataset}})),
  labels:all('label').slice(0,120).map(e=>({for:e.htmlFor,text:text(e)})),
  selects:all('select').map(e=>({selector:selector(e),value:e.value,visible:visible(e),options:Array.from(e.options).map(o=>({value:o.value,text:o.text,disabled:o.disabled}))})),
  buttons:all('button').slice(0,100).map(e=>({selector:selector(e),text:text(e),aria:e.getAttribute('aria-label'),visible:visible(e)})),
  counts:all('[role="status"],[aria-live],[id*="count"],[id*="Count"],[id*="stats"],.stat,.metric').filter(visible).slice(0,50).map(e=>({id:e.id,cls:e.className,text:text(e).slice(0,300)})),
  links:all('a[href]').slice(0,300).map(e=>({text:text(e).slice(0,180),url:e.href})),
  link_total:all('a[href]').length,
  record_links:all('a[href]').filter(e=>/\\/(records|families|communities|traits|materials|curated|aio|normalized|media)\\/|#record=/.test(e.href)).map(e=>e.href),
  rows:all('tbody tr').length,visible_rows:all('tbody tr').filter(visible).length,
  first_rows:all('tbody tr').filter(visible).slice(0,3).map(text),
  svg:all('svg').length,circles:all('svg circle').length,canvas:all('canvas').length,
  theme:document.documentElement.getAttribute('data-theme'),saved_theme:localStorage.getItem('mech-theme'),
  theme_controls:all('[class*="theme"], [id*="theme"]').filter(e=>e.tagName==='BUTTON'||e.tagName==='SELECT').map(e=>({selector:selector(e),text:text(e),value:e.value})),
  width:innerWidth,scroll_width:document.documentElement.scrollWidth,
  suite_links:all('a[href="https://culturebotai.github.io/mechs/"]').filter(visible).length,
  footer:all('footer').map(text).join('\\n')}; }'''

def compact(s):
    # Preserve complete record-link cardinality and a reproducible hash without huge ledgers.
    links=s.pop('record_links',[])
    s['record_links_count']=len(links);s['unique_record_links']=len(set(links))
    s['record_links_sha256']=hashlib.sha256('\n'.join(sorted(set(links))).encode()).hexdigest()
    s['record_link_samples']=links[:4]+links[-3:]
    return s

ACTION_JS='''() => {
 const vis=e=>e.getClientRects().length>0;
 const all=s=>Array.from(document.querySelectorAll(s));
 return {url:location.href,body_start:document.body.innerText.slice(0,1800),body_end:document.body.innerText.slice(-1800),
 counts:all('[role="status"],[aria-live],[id*="count"],[id*="Count"],#results,#results-count,.results-count,.summary').filter(vis).map(e=>({id:e.id,text:e.innerText.slice(0,600)})).slice(0,20),
 controls:all('input[id],select').map(e=>({id:e.id,value:e.value})),
 checked:all('input[type=checkbox]:checked').map(e=>({value:e.value,dataset:{...e.dataset}})),
 rows:all('tbody tr').filter(vis).length,
 first_results:all('tbody tr,.recipe-card,.community-card,.ingredient-card,.record-card').filter(vis).slice(0,3).map(e=>e.innerText.slice(0,500)),
 width:innerWidth,scroll:document.documentElement.scrollWidth}; }'''

def summarize_json(data):
    if isinstance(data,list): return {'type':'list','count':len(data),'first':data[:1]}
    if not isinstance(data,dict): return {'type':type(data).__name__}
    out={'type':'dict','keys':list(data)}
    for k,v in data.items():
        if isinstance(v,(str,int,float,bool)) or v is None: out[k]=v
        elif isinstance(v,list): out[k]={'count':len(v)}
        elif k in ('counts','metadata','meta','coverage','stats','summary','provenance'):
            out[k]=v if len(json.dumps(v))<30000 else {'keys':list(v)[:30],'count':len(v),'omitted_large_payload':True}
        elif isinstance(v,dict):out[k]={'keys':list(v)[:30],'count':len(v)}
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mech',required=True,choices=GROUP+GROUP_A)
    ap.add_argument('--role',choices=['auditor','skeptic'],default='auditor')
    ap.add_argument('--discover',action='store_true')
    ap.add_argument('--actions-only',action='store_true',help='Re-exercise controls using an existing completed page capture')
    args=ap.parse_args()
    config=json.loads(Path('_fleet/data/site_features.json').read_text())['mechs'][args.mech]
    pins=json.loads(Path('/private/tmp/xmech-refresh-20261104-snapshot/revisions.json').read_text())['mechs'][args.mech]
    repo=config['repository'].rsplit('/',1)[-1]
    base='https://culturebotai.github.io/'+repo+'/'
    suffix='-browser-b' if args.role=='auditor' else '-skeptic-b-observations'
    outfile=OUT/(args.mech.lower()+suffix+('-discovery' if args.discover else '')+'.json')
    report={'mech':args.mech,'reviewer':'central_directory independent '+args.role,'started_at':now(),'pin':pins['sha'],
            'deployment_before':deployment(repo,config['site']),'pages':{},'actions':{}}
    if args.actions_only:
        report=json.loads(outfile.read_text())
        report['actions_followup_started_at']=now()
        report.pop('finished_at',None)
    def save():
        temp=outfile.with_suffix('.json.tmp')
        temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(outfile)
    save()
    urls=[config['site'],config['features']['search']['url']]
    if not args.discover:
        urls += [v['url'] for v in config['features'].values() if not urllib.parse.urlsplit(v['url']).path.endswith(('.json','.csv','.tsv','.yaml'))]
        urls += [base+p for p in EXTRAS[args.mech]]
    urls=list(dict.fromkeys(urls))
    if args.actions_only:urls=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        ctx=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=ctx.new_page();page.set_default_timeout(12000)
        requests=[];errors=[]
        page.on('request',lambda r: requests.append({'url':r.url,'type':r.resource_type}))
        page.on('pageerror',lambda e:errors.append(str(e)))
        for url in urls:
            requests.clear();errors.clear()
            try:
                response=page.goto(url,wait_until='networkidle',timeout=90000)
                page.wait_for_timeout(800)
                if url==config['site']:
                    toggles=page.locator('.theme-toggle')
                    if toggles.count():
                        toggles.first.click();page.wait_for_timeout(100)
                    elif page.locator('#theme-toggle').count():
                        page.locator('#theme-toggle').click()
                    elif page.locator('#theme-control').count():
                        page.locator('#theme-control').select_option('dark')
                    elif page.get_by_role('button',name='Dark',exact=True).count():
                        page.get_by_role('button',name='Dark',exact=True).click()
                observed=compact(page.evaluate(SNAPSHOT_JS))
                observed.update(http_status=response.status if response else None,checked_at=now(),requests=list(requests),errors=list(errors))
                report['pages'][url]=observed
                if not args.discover:
                    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
                    observed['resized_390']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                    page.reload(wait_until='networkidle',timeout=90000);page.wait_for_timeout(300)
                    observed['fresh_390']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                    page.set_viewport_size({'width':1280,'height':900})
            except Exception as e:
                report['pages'][url]={'error':str(e),'checked_at':now(),'requests':list(requests)}
            save()
        if not args.discover:
            browse=config['features']['search']['url'].split('#')[0].split('?')[0]
            query,queries,sort,reset=PROFILES[args.mech]
            def action(name,fn):
                try:
                    fn();page.wait_for_timeout(700)
                    if args.mech=='ProteinTraitsMech':
                        page.wait_for_function("!document.getElementById('results')?.innerText.match(/Loading .*shards|Loading records/i)",timeout=120000)
                        page.wait_for_timeout(200)
                    report['actions'][name]=page.evaluate(ACTION_JS)
                except Exception as error:report['actions'][name]={'error':str(error)}
                save()
            page.goto(browse,wait_until='networkidle',timeout=90000);page.wait_for_timeout(500)
            for q in queries+['no-such-record-nov4-audit']:
                action('query:'+q,lambda q=q:page.locator(query).fill(q))
            action('clear_query',lambda:page.locator(query).fill(''))
            if sort:
                opts=page.locator(sort+' option').evaluate_all('(els)=>els.map(e=>e.value)')
                for opt in opts:
                    action('sort:'+opt,lambda opt=opt:page.locator(sort).select_option(opt))
            else:
                report['actions']['sorting_absence']={'selects':page.locator('select').count(),'sort_buttons':page.get_by_role('button',name=__import__('re').compile('sort',__import__('re').I)).count()}
            # Exercise property facets through actual visible controls.
            if args.mech in SELECT_FACETS:
                selectors=SELECT_FACETS[args.mech]
                for sel in selectors:
                    values=page.locator(sel+' option').evaluate_all('(els)=>els.filter(e=>!e.disabled).map(e=>e.value)')
                    if len(values)>1:action('facet:'+sel,lambda sel=sel,v=values[1]:page.locator(sel).select_option(v))
                action('combined_query',lambda:page.locator(query).fill(queries[-1]))
                action('restored',lambda:page.reload(wait_until='networkidle'))
                action('reset',lambda:page.locator(reset).first.click())
            elif args.mech in ['CultureMech','CommunityMech']:
                checkbox=page.locator('input[type=checkbox]:visible').first
                action('facet:first',lambda:checkbox.check())
                action('combined_query',lambda:page.locator(query).fill(queries[-1]))
                action('restored',lambda:page.reload(wait_until='networkidle'))
                action('reset',lambda:page.locator(reset).first.click())
            else:
                action('expand_axes',lambda:page.get_by_role('button',name='Show all (5)',exact=True).click())
                for value in ['FUNCTION','STRUCTURE','SEQUENCE','SEQUENCE_STRUCTURE','EVOLUTION']:
                    action('axis:'+value,lambda value=value:page.locator('input[data-facet="axis"][value="'+value+'"]').check())
                action('active_site_cold',lambda:page.goto(browse+'#cat=STRUCT_ACTIVE_SITE',wait_until='networkidle'))
                action('active_site_query',lambda:page.locator(query).fill('racemase'))
                action('restored',lambda:page.reload(wait_until='networkidle'))
                action('active_site_reviewed',lambda:page.goto(browse+'#cat=STRUCT_ACTIVE_SITE&sta=REVIEWED',wait_until='networkidle'))
                page.set_viewport_size({'width':390,'height':844})
                show=page.get_by_role('button',name=__import__('re').compile(r'Show all \(63\)'))
                action('mobile_expanded_categories',lambda:show.click())
                page.set_viewport_size({'width':1280,'height':900})
            report['failure_cases']={}
            candidates={browse}
            for url,rec in report['pages'].items():
                if any(r['type'] in ('fetch','xhr') for r in rec.get('requests',[])) and any(x in url for x in ('map','graph','browser','browse')):
                    candidates.add(url)
            for url in sorted(candidates):
                failed=[]
                def block(route):
                    r=route.request
                    if r.resource_type in ('fetch','xhr') or r.url.endswith('/data.js'):
                        failed.append(r.url);route.abort()
                    else:route.continue_()
                test=ctx.new_page();test.route('**/*',block)
                try:
                    test.goto(url,wait_until='networkidle',timeout=90000);test.wait_for_timeout(500)
                    report['failure_cases'][url]={'aborted':failed,'state':compact(test.evaluate(SNAPSHOT_JS))}
                except Exception as error:report['failure_cases'][url]={'error':str(error),'aborted':failed}
                test.close();save()
            report['bulk']={}
            for path in BULK.get(args.mech,[]):
                try:
                    response=ctx.request.get(base+path,timeout=90000)
                    item={'http_status':response.status,'bytes':len(response.body()),'sha256':hashlib.sha256(response.body()).hexdigest()}
                    if response.ok:item['data']=summarize_json(response.json())
                    report['bulk'][base+path]=item
                except Exception as error:report['bulk'][base+path]={'error':str(error)}
                save()
        browser.close()
    report['deployment_after']=deployment(repo,config['site'])
    report['finished_at']=now()
    save()
    print(json.dumps({'mech':args.mech,'pages':len(urls),'output':str(outfile),'finished_at':report['finished_at']}))

if __name__=='__main__': main()
