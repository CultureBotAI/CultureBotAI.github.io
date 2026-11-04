#!/usr/bin/env python3
"""Exercise the existing 24-feature rubric on six Mech Pages sites, 2026-11-04.

Inputs: pinned Nov4 snapshot, site_features.json baseline and live Pages.
Outputs: raw receipts/screenshots in /private/tmp/xmech-refresh-20261104-browser-evidence/group-a/raw;
compact reviewed evidence is finalized separately in this repository.
Serves the central X-Mech refresh PR; read-only toward sources and GitHub.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
SNAP=Path('/private/tmp/xmech-refresh-20261104-snapshot/mechs')
RAW=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a/raw')
CHROME='/Users/marcin/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'
CONFIG={
 'CellStructureMech':{'queries':['GO:0097589','MitoStore','cellstructuremech:insoluble_protein_deposit'],'extra':['pages/map.html','pages/sequence-map.html','pages/grounded.html','pages/category/microcompartment.html']},
 'AntibioticMech':{'queries':['CHEBI:2637','amikacin'],'extra':['pages/map.html','pages/sequence-map.html','pages/chemical-map.html','pages/antibacterial/index.html']},
 'NaturalProductMech':{'queries':['CHEBI:338412','marneral'],'extra':['pages/map.html','pages/sequence-map.html','pages/chemical-map.html','pages/terpenoids/index.html']},
 'HabitatMech':{'queries':['ENVO:03000033','marine sediment'],'extra':['pages/map.html','pages/text-map/','pages/text-map-source/index.html','pages/category/host-associated.html']},
 'TaxonMech':{'queries':['NCBITaxon:2173','Methanobrevibacter smithii','NCBITaxon:562'],'extra':['pages/map.html','pages/type-strains.html','pages/domain/archaea.html']},
 'PathwayMech':{'queries':['MetaCyc:PWY-6543','trehalose'],'extra':['pages/map.html','pages/sequence-map.html','pages/records/WikiPathways_WP5019.html','pages/records/MetaCyc_GLYCOLYSIS.html']},
}

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],text=True))
def state(page):
    return page.evaluate('''()=>({url:location.href,title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
      theme:document.documentElement.dataset.theme,savedTheme:localStorage.getItem('mech-theme'),
      h1:document.querySelector('h1')?.innerText, text:document.body.innerText.slice(0,65000),
      footer:[...document.querySelectorAll('footer')].map(x=>x.innerText).join('\\n'),
      statuses:[...document.querySelectorAll('[role=status], [id*=count], [id*=status]')].filter(x=>x.offsetParent!==null).map(x=>({id:x.id,text:x.innerText.slice(0,1200)})),
      controls:[...document.querySelectorAll('input,select,button')].map(x=>({tag:x.tagName,id:x.id,type:x.type,text:x.innerText.slice(0,900),label:x.getAttribute('aria-label'),value:x.value,disabled:x.disabled,options:x.tagName==='SELECT'?[...x.options].map(o=>({text:o.text,value:o.value})):null})),
      rows:document.querySelectorAll('tbody tr').length,visibleRows:[...document.querySelectorAll('tbody tr')].filter(x=>!x.hidden&&x.offsetParent!==null).length,
      firstRows:[...document.querySelectorAll('tbody tr')].filter(x=>!x.hidden&&x.offsetParent!==null).slice(0,3).map(x=>x.innerText.slice(0,1000)),
      allLinks:[...document.querySelectorAll('a[href]')].map(x=>({text:(x.innerText||x.textContent||'').slice(0,250),href:typeof x.href==='string'?x.href:x.href.baseVal,table:!!x.closest('tbody')})),
      svgs:[...document.querySelectorAll('svg')].map(x=>({id:x.id,classes:x.getAttribute('class'),width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height,circles:x.querySelectorAll('circle').length,paths:x.querySelectorAll('path').length,rects:x.querySelectorAll('rect').length})),
      canvases:[...document.querySelectorAll('canvas')].map(x=>({width:x.width,height:x.height,displayWidth:x.getBoundingClientRect().width})),
      iframes:[...document.querySelectorAll('iframe')].map(x=>x.src)})''')

def run(site):
    cfg=CONFIG[site]; dest=RAW/site;dest.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ROOT/'_fleet/data/site_features.json').read_text())['mechs'][site]
    source=json.loads((ROOT/'_fleet/reviews/refresh-20261104/source-excerpts-fleet.json').read_text())[site]
    pin=source['sha'];repo=SNAP/site
    assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==pin
    base='https://culturebotai.github.io/'+site+'/'
    out={'site':site,'pin':pin,'started_at':now(),'baseline':baseline,'pages':{},'actions':{},'downloads':{},'external_links':[]}
    output=dest/'raw.json'
    def save():output.write_text(json.dumps(out,indent=2)+'\n')
    def deploy(ctx):
        d=gh(f'repos/CultureBotAI/{site}/deployments?environment=github-pages&per_page=1')[0]
        s=gh(f'repos/CultureBotAI/{site}/deployments/{d["id"]}/statuses?per_page=1')[0]
        response=ctx.request.head(base+'pages/index.html')
        return {k:d[k] for k in ('id','sha','created_at')}|{'latest_status':{k:s[k] for k in ('state','created_at','environment_url')},'last_modified':response.headers.get('last-modified')}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME)
        ctx=browser.new_context(viewport={'width':1280,'height':900})
        out['deployment_before']=deploy(ctx)
        routes=['pages/index.html','pages/browse.html']
        for feature in baseline['features'].values():
            u=feature['url'].removeprefix(base).split('#')[0]
            if not u.startswith('http') and not re.search(r'\.(json|gz|tsv)$',u):routes.append(u)
        routes+=cfg['extra'];routes=list(dict.fromkeys(routes))
        for route in routes:
            page=ctx.new_page();errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:requests.append({'url':r.url,'status':r.status,'kind':r.request.resource_type}))
            try:
                response=page.goto(base+route,wait_until='networkidle',timeout=120000);page.wait_for_timeout(700)
                if route=='pages/index.html':
                    toggle=page.locator('button.theme-toggle,button[aria-label*="dark" i],button[aria-label*="theme" i]')
                    if toggle.count():toggle.first.click()
                row={'status':response.status,'desktop':state(page)}
                # Capture a real render, with raw screenshots kept outside Git.
                page.screenshot(path=str(dest/(re.sub(r'[^a-zA-Z0-9]+','_',route)+'.png')),full_page=False)
                page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(400)
                row['resized_mobile']=state(page)
                narrow=browser.new_context(viewport={'width':390,'height':844});np=narrow.new_page()
                np.goto(base+route,wait_until='networkidle',timeout=120000);np.wait_for_timeout(500)
                row['fresh_mobile']=state(np);narrow.close()
                row['page_errors']=errors;row['requests']=requests;out['pages'][route]=row
            except Exception as exc:out['pages'][route]={'error':str(exc),'page_errors':errors,'requests':requests}
            page.close();save();print(site+' PAGE '+route,flush=True)
        page=ctx.new_page();page.goto(base+'pages/browse.html',wait_until='networkidle',timeout=120000);page.wait_for_timeout(800)
        out['actions']['browse_initial']=state(page)
        search=page.locator('input[type=search]')
        if not search.count():search=page.locator('input[name=q],input[id*=query]')
        if search.count():
            for q in cfg['queries']+['no-such-record-canary-20261104']:
                search.first.fill(q);page.wait_for_timeout(900);out['actions']['search:'+q]=state(page)
            search.first.fill(cfg['queries'][0]);page.wait_for_timeout(700)
            out['actions']['query_before_reload']=state(page)
            page.reload(wait_until='networkidle',timeout=120000);page.wait_for_timeout(700)
            out['actions']['query_after_reload']=state(page)
            search.first.fill('');page.wait_for_timeout(600)
        facets=page.locator('select:not([id*=sort])')
        for i in range(min(facets.count(),2)):
            options=facets.nth(i).locator('option').evaluate_all('(xs)=>xs.map(x=>({value:x.value,text:x.text}))')
            values=[x for x in options if x['value']]
            if values:
                facets.nth(i).select_option(values[0]['value']);page.wait_for_timeout(500)
                out['actions']['facet:'+str(i)]=state(page)
        sort=page.locator('select[id*=sort]')
        if sort.count():
            options=sort.first.locator('option').evaluate_all('(xs)=>xs.map(x=>x.value)')
            for value in options[:2]:
                sort.first.select_option(value);page.wait_for_timeout(500);out['actions']['sort:'+value]=state(page)
        out['actions']['before_reload']=state(page);page.reload(wait_until='networkidle',timeout=120000);page.wait_for_timeout(700);out['actions']['after_reload']=state(page)
        clear=page.get_by_role('button',name=re.compile(r'^(Clear( all)?( filters)?|Reset( filters)?|Clear search and filters)$',re.I))
        if clear.count():
            clear.first.focus();page.keyboard.press('Enter');page.wait_for_timeout(600);out['actions']['keyboard_reset']=state(page)
        else:out['actions']['reset_absent']={'controls':state(page)['controls']}
        # Exercise actual next-page control if available, including static navigation.
        next_control=page.get_by_role('link',name=re.compile(r'^Next',re.I))
        if not next_control.count():next_control=page.get_by_role('button',name=re.compile(r'^Next',re.I))
        if next_control.count() and next_control.first.is_enabled():
            next_control.first.click();page.wait_for_timeout(900);out['actions']['next_page']=state(page)
        page.close();save()
        for route,row in out['pages'].items():
            if 'desktop' not in row or row['status']!=200:continue
            data_urls=list(dict.fromkeys(r['url'] for r in row['requests'] if r['kind'] in ('fetch','xhr') and ('.json' in r['url'] or '.tsv' in r['url'])))
            for target in data_urls[:3]:
                failed=browser.new_context(viewport={'width':1280,'height':900});failed.route(target,lambda r:r.abort());fp=failed.new_page()
                try:
                    fp.goto(base+route,wait_until='networkidle',timeout=120000);fp.wait_for_timeout(500)
                    # Category data is lazy: typing triggers the fetch failure path.
                    inp=fp.locator('input[type=search]')
                    if inp.count():inp.first.fill(cfg['queries'][0]);fp.wait_for_timeout(700)
                    fail={'target':target,'state':state(fp)}
                    retry=fp.get_by_role('button',name=re.compile(r'retry|try again',re.I))
                    failed.unroute(target)
                    if retry.count():retry.first.click();fp.wait_for_timeout(1000);fail['recovered']=state(fp)
                    out['actions']['failure:'+route+':'+target]=fail
                except Exception as exc:out['actions']['failure:'+route+':'+target]={'error':str(exc)}
                failed.close();save()
        all_links=[a|{'from':route} for route,row in out['pages'].items() if 'desktop'in row for a in row['desktop']['allLinks'] if not a['table']]
        seen=set()
        for link in all_links:
            url=link['href']
            if url in seen:continue
            download=re.search(r'\.(json|json.gz|tsv|csv)(\?|$)',url) and url.startswith(base)
            schema=re.search(r'schema|LinkML',link['text'],re.I)
            sibling='culturebotai.github.io/'in url and not url.startswith(base) and '/pages/'in url
            if download or schema or sibling:
                seen.add(url)
                try:
                    r=ctx.request.get(url,timeout=90000);item=link|{'status':r.status}
                    if download:
                        body=r.body();item['bytes']=len(body);item['sha256']=hashlib.sha256(body).hexdigest()
                        if '.json' in url:
                            if body[:2]==b'\x1f\x8b':body=gzip.decompress(body)
                            j=json.loads(body);item['kind']=type(j).__name__;item['length']=len(j)
                            if isinstance(j,dict):item['keys']=list(j)[:25];item['array_lengths']={k:len(v) for k,v in j.items() if isinstance(v,list)}
                        else:item['header']=body[:400].decode(errors='replace');item['lines']=body.count(b'\n')
                        out['downloads'][url]=item
                    else:out['external_links'].append(item)
                except Exception as exc:out['external_links'].append(link|{'error':str(exc)})
                save()
        out['deployment_after']=deploy(ctx);browser.close()
    out['finished_at']=now();save();print(output,flush=True)

def summarize(site):
    raw=json.loads((RAW/site/'raw.json').read_text())
    compact={'site':site,'deployment':raw.get('deployment_after'),'finished_at':raw.get('finished_at'),'pages':{},'actions':{},'downloads':raw['downloads'],'external_links':raw['external_links']}
    for path,row in raw['pages'].items():
        if 'desktop' not in row:compact['pages'][path]=row;continue
        d=row['desktop'];compact['pages'][path]={'status':row['status'],'h1':d['h1'],'theme':d['theme'],'widths':{m:row[m]['scrollWidth'] for m in ('desktop','fresh_mobile','resized_mobile')},'statuses':d['statuses'],'footer':d['footer'],'svgs':d['svgs'],'canvases':d['canvases'],'links':[a for a in d['allLinks'] if not a['table']][:80],'text':d['text'][:7000] if '/browse'not in path else d['text'][:1700]}
    for key,row in raw['actions'].items():
        d=row.get('state',row)
        compact['actions'][key]={k:d[k] for k in ('url','statuses','firstRows','visibleRows','controls') if k in d}
        if key.startswith('failure:'):compact['actions'][key]['text']=d.get('text','')[:2500]
    output=RAW/site/'summary.json';output.write_text(json.dumps(compact,indent=2)+'\n');print(output)

def inspect(site, section):
    raw=json.loads((RAW/site/'raw.json').read_text())
    for row in raw['downloads'].values():
        if len(row.get('array_lengths',{}))>30:row['array_lengths']={'omitted_entries':len(row['array_lengths'])}
    if section=='overview':
        print(json.dumps({'finished':raw.get('finished_at'),'deployment':raw.get('deployment_after'),'pages':{p:{'status':r.get('status'),'error':r.get('error'),'widths':{m:r[m]['scrollWidth'] for m in ('desktop','fresh_mobile','resized_mobile') if m in r},'theme':r.get('desktop',{}).get('theme'),'svg':r.get('desktop',{}).get('svgs'),'canvas':r.get('desktop',{}).get('canvases'),'statuses':r.get('desktop',{}).get('statuses'),'footer':r.get('desktop',{}).get('footer')} for p,r in raw['pages'].items()},'actions':{k:{x:v.get('state',v).get(x) for x in ('url','statuses','firstRows','visibleRows')} for k,v in raw['actions'].items()},'downloads':raw['downloads'],'external_links':raw['external_links']},indent=2))
    elif section=='controls':print(json.dumps(raw['actions']['browse_initial']['controls'],indent=2))
    elif section=='downloads':print(json.dumps(raw['downloads'],indent=2))
    elif section=='links':print(json.dumps({p:[a for a in r['desktop']['allLinks'] if not a['table']] for p,r in raw['pages'].items() if 'desktop'in r},indent=2))
    elif section.startswith('action:'):print(json.dumps(raw['actions'][section.removeprefix('action:')],indent=2))
    elif section=='actions':
        print(json.dumps({k:{x:v.get('state',v).get(x) for x in ('url','statuses')}|({'blocked':v['blocked']} if 'blocked'in v else {})|({'failure_text':v.get('state',{}).get('text','')[-2200:]} if 'failure:'in k else {}) for k,v in raw['actions'].items()},indent=2))
    elif section=='themes':print(json.dumps({k:v for k,v in raw['actions'].items() if k.startswith('explicit_dark:')},indent=2))
    elif section.startswith('text:'):print(raw['pages'][section.removeprefix('text:')]['desktop']['text'])
    elif section.startswith('terms:'):print(json.dumps([a for a in raw['pages'][section.removeprefix('terms:')]['desktop']['allLinks'] if re.search(r'pubmed|doi.org|CHEBI|NCBI|geneontology|uniprot|ebi.ac.uk|genbank',a['href'],re.I)],indent=2))
    else:
        row=raw['pages'][section]['desktop']
        print(row['text'])
        print(json.dumps([a for a in row['allLinks'] if a['table'] or re.search('pubmed|doi.org|CHEBI|NCBI|geneontology|schema|Mech/',a['href'])],indent=2))

def supplement(site):
    """Extend earlier completed receipts with explicit query reload and map inspection."""
    output=RAW/site/'raw.json';raw=json.loads(output.read_text());assert raw.get('finished_at')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME);ctx=browser.new_context(viewport={'width':1280,'height':900});page=ctx.new_page()
        page.goto('https://culturebotai.github.io/'+site+'/pages/browse.html',wait_until='networkidle',timeout=120000)
        search=page.locator('input[type=search]');search.first.fill(CONFIG[site]['queries'][0]);page.wait_for_timeout(1000)
        raw['actions']['query_before_reload']=state(page);page.reload(wait_until='networkidle',timeout=120000);page.wait_for_timeout(1000)
        raw['actions']['query_after_reload']=state(page)
        base='https://culturebotai.github.io/'+site+'/'
        page.goto(base+'pages/index.html',wait_until='networkidle')
        toggle=page.locator('button.theme-toggle,button[aria-label*="dark" i],button[aria-label*="theme" i]')
        if toggle.count():
            for _ in range(3):
                if page.evaluate("document.documentElement.dataset.theme")=='dark':break
                toggle.first.click();page.wait_for_timeout(200)
            raw['actions']['explicit_dark_landing']=state(page)
            for route,row in raw['pages'].items():
                if row.get('status')!=200:continue
                page.goto(base+route,wait_until='networkidle',timeout=120000);page.wait_for_timeout(300)
                raw['actions']['explicit_dark:'+route]={'theme':page.evaluate("document.documentElement.dataset.theme"),'savedTheme':page.evaluate("localStorage.getItem('mech-theme')"),'bodyBackground':page.evaluate("getComputedStyle(document.body).backgroundColor"),'toggle_count':page.locator('button.theme-toggle,button[aria-label*="dark" i],button[aria-label*="theme" i]').count()}
        # Most category and corpus search indexes fetch lazily after typing.
        for route,row in raw['pages'].items():
            if row.get('status')!=200 or not (re.search(r'browse|category/|map',route)):continue
            failed=browser.new_context();blocked=[]
            def abort(request):blocked.append(request.request.url);request.abort()
            failed.route('**/*.json*',abort);fp=failed.new_page()
            fp.goto(base+route,wait_until='networkidle',timeout=120000);fp.wait_for_timeout(300)
            search=fp.locator('input[type=search]')
            if search.count():search.first.fill(CONFIG[site]['queries'][0]);fp.wait_for_timeout(1200)
            raw['actions']['lazy_failure:'+route]={'blocked':blocked,'state':state(fp)}
            failed.close()
        browser.close()
    raw['supplemented_at']=now();output.write_text(json.dumps(raw,indent=2)+'\n');print('query reload supplemented '+site)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('site',choices=CONFIG);ap.add_argument('--summary',action='store_true');ap.add_argument('--inspect');ap.add_argument('--supplement',action='store_true');a=ap.parse_args()
    inspect(a.site,a.inspect) if a.inspect else supplement(a.site) if a.supplement else summarize(a.site) if a.summary else run(a.site)
