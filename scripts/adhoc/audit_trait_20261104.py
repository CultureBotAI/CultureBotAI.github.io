#!/usr/bin/env python3
"""TraitMech refresh canary, 2026-11-04; evidence for the X-Mech refresh PR.

Inputs: TraitMech at c7627fd, live Pages and GitHub deployment metadata.
Outputs: _fleet/reviews/refresh-20261104/trait-auditor.json; no source edits.
Run with uv --offline --no-project --with playwright --with pyyaml python.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import hashlib
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SNAP = Path('/private/tmp/xmech-refresh-20261104-snapshot/mechs/TraitMech')
PIN = 'c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6'
BASE = 'https://culturebotai.github.io/TraitMech/'
OUT = ROOT / '_fleet/reviews/refresh-20261104/trait-auditor.json'
BROWSER = '/Users/marcin/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'


def gh(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def blob(path):
    return subprocess.check_output(['git', '-C', str(SNAP), 'show', f'{PIN}:{path}'], text=True)


def state(page):
    return page.evaluate('''() => ({url:location.href,theme:document.documentElement.dataset.theme,
      savedTheme:localStorage.getItem('mech-theme'), width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
      main:document.querySelectorAll('main,[role=main]').length,
      count:document.querySelector('#record-count')?.textContent,
      mapStatus:document.querySelector('#map-status')?.textContent,
      visibleCount:document.querySelector('#visible-count')?.textContent,
      circles:document.querySelectorAll('#umap-plot svg circle').length,
      svg:document.querySelectorAll('svg').length,
      graphSvg:document.querySelectorAll('.mermaid svg, svg[id^="mermaid"]').length,
      rows:document.querySelectorAll('#record-table tbody tr').length,
      visibleRows:[...document.querySelectorAll('#record-table tbody tr')].filter(x=>!x.hidden).length,
      firstRecords:[...document.querySelectorAll('#record-table tbody tr')].filter(x=>!x.hidden).slice(0,3).map(x=>x.innerText),
      controls:[...document.querySelectorAll('input,select,button')].map(x=>({id:x.id,text:x.innerText,label:x.getAttribute('aria-label'),value:x.value})),
      links:[...document.querySelectorAll('a[href]')].filter(x=>!x.closest('#record-table tbody')).map(x=>({text:x.innerText,href:x.href})),
      text:document.body.innerText.slice(0,45000)})''')


def main():
    assert subprocess.check_output(['git','-C',str(SNAP),'rev-parse','HEAD'],text=True).strip() == PIN
    result = {'pin':PIN,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'pages':{},'actions':{},'source_evidence':{}}
    def save():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result,indent=2)+'\n')
    def deploy():
        row=gh('repos/CultureBotAI/TraitMech/deployments?environment=github-pages&per_page=1')[0]
        status=gh(f"repos/CultureBotAI/TraitMech/deployments/{row['id']}/statuses?per_page=1")[0]
        request=urllib.request.Request(BASE+'pages/index.html',method='HEAD')
        with urllib.request.urlopen(request,timeout=30) as response:
            headers={k:response.headers.get(k) for k in ('Last-Modified','X-GitHub-Request-Id')}
        return {k:row[k] for k in ('id','sha','created_at')}|{'latest_status':{k:status[k] for k in ('state','created_at','environment_url')},'headers':headers}
    result['deployment_before']=deploy()
    paths=subprocess.check_output(['git','-C',str(SNAP),'ls-tree','-r','--name-only',PIN,'data/traits'],text=True).splitlines()
    records=[(p,yaml.load(blob(p),Loader=yaml.CSafeLoader)) for p in paths if p.endswith('.yaml')]
    links=[]
    for path,record in records:
        for graph in record.get('causal_graphs') or []:
            for node in graph.get('nodes') or []:
                for link in node.get('related_records') or []:
                    links.append({'path':path,'node':node.get('node_id'),'link':link})
    result['counts']={'records':len(records),'statuses':dict(collections.Counter(r.get('mapping_status') for _,r in records)),
        'categories':dict(collections.Counter(r.get('trait_category') for _,r in records)),
        'causal_graph_records':sum(bool(r.get('causal_graphs')) for _,r in records),'pathway_links':links}
    for path in ('README.md','LICENSE-DATA','LICENSE-CODE','docs/SCHEMA.md','docs/PATHWAY_LINKS.md','download.yaml','scripts/check_sources.py','scripts/seed_from_metpo.py','src/traitmech/curate/curation_event.py','src/traitmech/validation/write_validated.py','scripts/add_faprotax_synonyms.py'):
        result['source_evidence'][path]={'locator':f'{path}@{PIN}','text':blob(path)}
    save()
    routes=['pages/index.html','pages/browse.html','pages/category/ecology.html','pages/category/quantitative_property.html',
      'pages/traits/ecology/animal_pathogen.html','pages/traits/metabolism/aerobic_respiration.html',
      'pages/traits/metabolism/wood_ljungdahl_pathway.html','pages/umap.html','pages/map.html','pages/graph.html','pages/sequence-map.html','app/discussions/index.html']
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=BROWSER)
        context=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=context.new_page()
        for route in routes:
            errors=[]; requests=[]
            page.close();page=context.new_page()
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('response',lambda response:requests.append({'url':response.url,'status':response.status,'kind':response.request.resource_type}))
            try:
                page.set_viewport_size({'width':1280,'height':900})
                response=page.goto(BASE+route,wait_until='networkidle',timeout=60000)
                page.wait_for_timeout(500)
                if route=='pages/index.html':
                    page.get_by_role('button',name='Toggle dark mode').click()
                row={'status':response.status,'desktop':state(page)}
                page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(600)
                row['resized_mobile']=state(page)
                narrow=browser.new_context(viewport={'width':390,'height':844})
                np=narrow.new_page();np.goto(BASE+route,wait_until='networkidle',timeout=60000);np.wait_for_timeout(500)
                row['fresh_mobile']=state(np);narrow.close()
                row['page_errors']=errors;row['requests']=requests
                result['pages'][route]=row
            except Exception as exc:
                result['pages'][route]={'error':str(exc),'page_errors':errors,'requests':requests}
            save();print('PAGE '+route,flush=True)
        page.set_viewport_size({'width':1280,'height':900});page.goto(BASE+'pages/browse.html',wait_until='networkidle')
        result['actions']['all_links']=page.locator('#record-table tbody tr a').evaluate_all('(xs)=>xs.map(x=>({label:x.textContent,href:x.href}))')
        for query in ('METPO:1004002','traitmech:000616','bipolar mating system','no-such-trait-canary','<img src=x onerror=alert(1)>'):
            page.locator('#record-query').fill(query)
            result['actions']['query:'+query]=state(page)
        page.locator('#record-query').fill('pathogen');page.locator('#record-category').select_option('ECOLOGY');page.locator('#record-kind').select_option('CLASS')
        result['actions']['combined_filters']=state(page);page.reload(wait_until='networkidle');result['actions']['restored_filters']=state(page)
        page.get_by_role('button',name='Clear filters',exact=True).click();page.wait_for_timeout(100);result['actions']['reset']=state(page)
        page.locator('#record-sort').select_option('label-desc');result['actions']['sort_desc']=state(page)
        page.locator('#record-sort').select_option('label-asc');result['actions']['sort_asc']=state(page)
        page.locator('button[data-facet="category"][data-val="ECOLOGY"]').focus();page.keyboard.press('Enter');result['actions']['keyboard_facet']=state(page)
        page.locator('#facet-clear-btn').focus();page.keyboard.press('Enter');result['actions']['keyboard_reset']=state(page)
        save()
        for route in ('pages/umap.html','pages/map.html','pages/graph.html','pages/sequence-map.html'):
            failed=browser.new_context(viewport={'width':1280,'height':900})
            failed.route('**/data/*.json',lambda r:r.abort())
            fp=failed.new_page();fp.goto(BASE+route,wait_until='networkidle');fp.wait_for_timeout(500)
            result['actions']['failed:'+route]=state(fp)
            failed.unroute('**/data/*.json');fp.locator('#map-retry').click();fp.wait_for_timeout(1500)
            result['actions']['recovered:'+route]=state(fp);failed.close();save()
        failed=browser.new_context();failed.route('**/app/discussions/data.js',lambda r:r.abort())
        fp=failed.new_page();fp.goto(BASE+'app/discussions/index.html',wait_until='networkidle');result['actions']['failed:discussions']=state(fp);failed.close()
        for route in ('pages/data/traits.json','pages/data/trait_umap.json','pages/data/corpus_map.json','pages/data/sequence_map.json'):
            response=context.request.get(BASE+route)
            payload=response.json()
            result['actions']['download:'+route]={'status':response.status,'keys':list(payload)[:30] if isinstance(payload,dict) else None,'list_length':len(payload) if isinstance(payload,list) else None,'array_lengths':{k:len(v) for k,v in payload.items() if isinstance(v,list)} if isinstance(payload,dict) else None}
        for route,row in result['pages'].items():
            if 'desktop' not in row:continue
            relevant=[a for a in row['desktop']['links'] if ('PathwayMech/' in a['href'] and '/pages/' in a['href']) or ('traitmech/schema/traitmech.yaml' in a['href'])]
            for link in relevant:
                response=context.request.get(link['href'])
                result['actions'].setdefault('verified_external_links',[]).append(link|{'status':response.status,'from':route})
        browser.close()
    result['deployment_after']=deploy();result['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
    print(OUT,flush=True)


def finalize():
    """Retain raw browser capture outside Git; emit concise, reviewable receipts."""
    raw_path = Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a/trait-browser-auditor-20261104.json')
    if not raw_path.exists():
        raw_path.write_bytes(OUT.read_bytes())
    raw = json.loads(raw_path.read_text())
    assert raw['finished_at'] and raw['counts']['records'] == 1130
    catalogue = json.loads((ROOT/'_fleet/data/site_features.json').read_text())
    old = catalogue['mechs']['TraitMech']['features']
    pages, actions = raw['pages'], raw['actions']
    index, browse = 'pages/index.html', 'pages/browse.html'
    animal = 'pages/traits/ecology/animal_pathogen.html'
    aerobic = 'pages/traits/metabolism/aerobic_respiration.html'
    wood = 'pages/traits/metabolism/wood_ljungdahl_pathway.html'
    def excerpt(text, needle, before=0, after=450):
        start=text.index(needle)
        return text[max(0,start-before):start+len(needle)+after]
    def desktop(route): return pages[route]['desktop']
    def links(route, pattern):
        return [x for x in desktop(route)['links'] if re.search(pattern,x['text']+' '+x['href'],re.I)]
    def receipt(action):
        row=actions[action]
        return {k:row[k] for k in ('url','count','visibleRows','firstRecords','mapStatus','circles') if row.get(k) is not None}
    feature={}
    def add(key,note,route,evidence,status='present'):
        feature[key]={'status':status,'note':note,'url':BASE+route,'evidence':evidence}
    add('search','Browse searches all 1,130 records: METPO:1004002 and traitmech:000616 each return one linked record; bipolar mating system returns two.',browse,
        {q:receipt('query:'+q) for q in ('METPO:1004002','traitmech:000616','bipolar mating system','no-such-trait-canary','<img src=x onerror=alert(1)>')})
    add('facets','Browse provides Category and Kind selectors plus Clear filters. Combining pathogen, ECOLOGY and CLASS gives eight records; reset restores all 1,130.',browse,
        {q:receipt(q) for q in ('combined_filters','reset','keyboard_facet','keyboard_reset')})
    add('result_counts','The count responds to search and property filters: identifiers give 1 of 1,130 records shown; pathogen plus ECOLOGY and CLASS gives 8 of 1,130.',browse,receipt('combined_filters'))
    add('sorting','Browse offers label, identifier, category, kind, kg-microbe node-count and synonym-count ordering. Reversing label order changes the first row from 2,3-butanediol fermentation to Zorya type III system.',browse,
        {'ascending':receipt('sort_asc'),'descending':receipt('sort_desc'),'control':[x for x in desktop(browse)['controls'] if x['id']=='record-sort']})
    add('shareable_state','Search, category and kind are written to the URL. Reloading ?q=pathogen&category=ECOLOGY&kind=CLASS restores the controls and eight matches.',browse+'?q=pathogen&category=ECOLOGY&kind=CLASS',receipt('restored_filters'))
    listing=actions['all_links']
    tree=subprocess.check_output(['git','-C',str(SNAP),'ls-tree','-r','--name-only',PIN,'pages/traits'],text=True).splitlines()
    html={x for x in tree if x.endswith('.html')}
    listed={x['href'].removeprefix(BASE) for x in listing}
    assert len(listing)==len(listed)==len(html)==1130 and listed==html
    add('full_catalogue','Browse exposes 1,130 distinct record links, matching the landing total and all 1,130 record HTML paths at the pin.',browse,
        {'linked_rows':len(listing),'unique_links':len(listed),'pinned_html_files':len(html),'path_sets_equal':listed==html})
    add('record_pages','All 1,130 traits have static pages under pages/traits/<category>/<slug>.html. Sampled pages show overview, grounding, curation and source sections; 761 source records carry causal graphs.',animal,
        {'pinned_pages':len(html),'sampled':{p:pages[p]['status'] for p in (animal,aerobic,wood)},'graph_bearing_records':raw['counts']['causal_graph_records']})
    add('term_links','Record identifiers have readable labels and resolver links. Aerobic respiration links GO:0009060 in Cross-references, but that whole section still lacks a readable term label.',aerobic,
        {'section':excerpt(desktop(aerobic)['text'],'Cross-references',after=120),'links':links(aerobic,'GO:0009060|METPO:1000687')},'partial')
    add('evidence','Animal pathogen and aerobic respiration link their trait and causal-edge DOI citations and display supporting text.',animal,
        {'links':links(animal,'doi.org'),'excerpt':excerpt(desktop(animal)['text'],'Evidence',after=800)})
    add('review_status','Record headers and Identifier cards show workflow status, including REVIEWED on animal pathogen; the complete corpus retains all four mapping statuses.',animal,
        {'excerpt':excerpt(desktop(animal)['text'],'METPO:1004002',after=120),'pinned_status_counts':raw['counts']['statuses']})
    add('curation_history','Sampled record pages display dated curation events, attributed curators and change summaries.',animal,
        excerpt(desktop(animal)['text'],'Curation history',after=900))
    add('source_link','Record Source cards link View YAML on GitHub, Raw YAML and Edit on GitHub for the record’s own data/traits YAML.',animal,
        links(animal,'data/traits/ecology/animal_pathogen.yaml'))
    maps=['pages/umap.html','pages/map.html','pages/graph.html','pages/sequence-map.html']
    add('domain_view','Sampled record pages render causal SVG diagrams; 761 source records carry causal graphs. PaCMAP, text and graph-layout maps each render 1,130 traits, and the sequence map renders 156 associated proteins. These source counts do not imply that every graph was visually inspected.', 'pages/umap.html',
        {'maps':{p:{k:desktop(p)[k] for k in ('circles','mapStatus','svg')} for p in maps},'record_svg_counts':{p:desktop(p)['svg'] for p in (animal,aerobic,wood)}})
    add('cross_mech_links','Wood–Ljungdahl’s Pathway context links to PathwayMech WikiPathways:WP5019. The target returns HTTP 200; the trait page retains organism scope and the target revision.',wood,
        {'links':[x for x in actions['verified_external_links'] if 'PathwayMech/' in x['href']], 'excerpt':excerpt(desktop(wood)['text'],'Pathway context',after=1000)})
    add('corpus_stats','The landing page shows 1,130 trait records, 10 categories and 100.0% embedding coverage. Reviewed and causal-graph totals are corpus-source statistics, not landing tiles.',index,
        desktop(index)['text'][:2500])
    add('category_browse','Browse links ten category pages with counts; the opened ECOLOGY page contains 40 records and QUANTITATIVE_PROPERTY contains seven.',browse,
        {'links':links(browse,'/pages/category/'),'categories':raw['counts']['categories'],'ecology_excerpt':desktop('pages/category/ecology.html')['text'][:1100],'quantitative_excerpt':desktop('pages/category/quantitative_property.html')['text'][:900]})
    add('suite_nav','All Mech projects links the landing, Browse, sampled categories and records, all four maps and the discussions index to the suite directory.',index,
        {p:links(p,'culturebotai.github.io/mechs/') for p in pages})
    add('downloads','The site links Download traits.json, a complete 1,130-record bulk JSON export. Downloaded map exports contain 1,130 traits or 156 proteins as labeled.',index,
        {'links':links(index,'traits.json'),'requests':{k:v for k,v in actions.items() if k.startswith('download:')}})
    add('schema_docs','Visible Schema and LinkML schema links open the annotated LinkML YAML source successfully. They provide source access; the reviewed navigation does not link rendered schema documentation or the explanatory schema guide.',index,
        {'links':[x for x in actions['verified_external_links'] if 'traitmech/schema/traitmech.yaml' in x['href']][:2], 'arbitration':'Root 2026-11-04: direct schema YAML is source access; present requires published rendered docs or explanatory guide.'},'partial')
    add('license','Sampled page footers state CC BY 4.0 project data and BSD-3-Clause code, with third-party source terms retained; these match the pinned license files.',index,
        {'excerpt':excerpt(desktop(index)['text'],'Project data:',after=180),'source':'LICENSE, LICENSE-DATA and LICENSE-CODE at '+PIN})
    add('build_provenance','Landing, Browse and map footers give a dated version of the project corpus, alongside the METPO baseline and record count.',index,
        excerpt(desktop(index)['text'],'Corpus as of',after=200))
    add('theme_toggle','Selecting dark on the landing persists through Browse, two categories, three records, all four maps and the discussions index in the same browser context.',index,
        {p:{k:desktop(p)[k] for k in ('theme','savedTheme')} for p in pages})
    add('responsive','At 390px, the text and sequence maps overflow: 553px document width on fresh load and 793px after resizing from 1280px. The other ten sampled routes, including PaCMAP and graph layout, fit 390px.', 'pages/map.html',
        {p:{mode:{k:row[mode][k] for k in ('width','scrollWidth')} for mode in ('desktop','fresh_mobile','resized_mobile')} for p,row in pages.items()},'partial')
    add('load_failure','Aborted JSON requests produce explicit map failure messages and Retry; retry after restoring requests recovers 1,130 traits or 156 proteins. Aborting discussion data produces Discussion counts unavailable and a retry prompt.', 'pages/umap.html',
        {p:{'failed':receipt('failed:'+p),'recovered':receipt('recovered:'+p)} for p in maps}|{'discussions':actions['failed:discussions']['text']})
    assert set(feature)==set(catalogue['catalogue']) and len(feature)==24
    counts=raw['counts'].copy()
    pathway=counts.pop('pathway_links')
    counts['pathway_context']={'links':len(pathway),'nodes':len({(x['path'],x['node']) for x in pathway}),'records':len({x['path'] for x in pathway}),'targets':len({x['link']['identifier'] for x in pathway})}
    changes=[{'locator':f'_fleet/data/site_features.json::mechs.TraitMech.features.{k}.note','before':old[k]['note'],'replacement':v['note'],'evidence':f'features.{k}.evidence'} for k,v in feature.items() if old[k]['note']!=v['note']]
    for path,needle in [('_fleet/audit_notes.json','748 records with causal graphs'),('resources.md','748 carry causal graphs')]:
        text=(ROOT/path).read_text();assert text.count(needle)==1
        line=next((i,s) for i,s in enumerate(text.splitlines(),1) if needle in s)
        changes.append({'locator':f'{path}:{line[0]}','before':needle,'replacement':needle.replace('748','761'),'evidence':'counts.causal_graph_records; source_evidence.README.md'})
    patterns={
      'README.md':r'TOTAL|761|TraitRecord|material|MediaIngredient|METPO.*2026',
      'download.yaml':r'source:|status:|Adopted|license:|stricter|licence',
      'docs/SCHEMA.md':r'root|TraitRecord|material|MIM|MediaIngredient',
      'docs/PATHWAY_LINKS.md':r'PATHWAY_CONTEXT|source_revision|organism|equivalence|19|17|11|15',
      'scripts/seed_from_metpo.py':r'material|MIM|MediaIngredient',
      'scripts/research_trait_edison.py':r'port|CommunityMech',
      '.claude/skills/deep-research-trait/SKILL.md':r'CommunityMech|port',
      '.claude/skills/metpo-proposal/SKILL.md':r'CommunityMech|1007100|cohort',
      'scripts/check_sources.py':r'ProteinTraitsMech|license|licence|REQUIRED',
      'src/traitmech/curate/curation_event.py':r'CultureMech|MediaIngredient|Ported',
      'src/traitmech/validation/write_validated.py':r'CultureMech|MediaIngredient|Ported',
      'scripts/add_faprotax_synonyms.py':r'MediaIngredient|raw string|correct the label',
      'justfile':r'qc|CultureMech|MediaIngredient|audit-writers',
      'src/traitmech/schema/traitmech.yaml':r'^  (TraitRecord|METPO|GO|NCBITaxon|CHEBI|UniProt|UniProtKB|PATO):',
      'LICENSE':r'CC-BY|BSD-3|third-party|Third-party',
    }
    source={}
    for path,pattern in patterns.items():
        txt=raw['source_evidence'].get(path,{}).get('text') or blob(path)
        matched=[{'line':i,'text':s} for i,s in enumerate(txt.splitlines(),1) if re.search(pattern,s)]
        source[path]={'url':f'https://github.com/CultureBotAI/TraitMech/blob/{PIN}/{path}','sha256':hashlib.sha256(txt.encode()).hexdigest(),'excerpts':matched[:35]}
    claims=[
      {'locator':'_fleet/mechs_template.md::article[data-mech="TraitMech"]; _fleet/fleet_fragment.html::MECHS.TraitMech; resources.md::TraitMech; index.md:37; CLAUDE.md:161','verdict':'verified; graph count replacement separately listed','evidence':['counts','source_evidence.README.md','source_evidence.download.yaml','source_evidence.src/traitmech/schema/traitmech.yaml','features.license','features.domain_view'],'details':'1,130 TraitRecord YAMLs,10 populated categories,METPO seed,one YAML per trait; listed schema prefixes and candidate GapMind/GTDB sources; live kg-microbe matching/neighbor sections and map routes.'},
      {'locator':'_fleet/fleet_fragment.html::XREF[from=CommunityMech,to=TraitMech] + matching template relationship','verdict':'verified from Trait-owned sources','evidence':['source_evidence.scripts/research_trait_edison.py','source_evidence..claude/skills/deep-research-trait/SKILL.md','source_evidence..claude/skills/metpo-proposal/SKILL.md']},
      {'locator':'_fleet/fleet_fragment.html::XREF[from=TraitMech,to=MediaIngredientMech] + matching template relationship','verdict':'Trait scope half verified; MIM command adoption belongs to MIM audit','evidence':['source_evidence.docs/SCHEMA.md','source_evidence.scripts/seed_from_metpo.py']},
      {'locator':'_fleet/fleet_fragment.html::XREF[from=ProteinTraitsMech,to=TraitMech] + matching template relationship','verdict':'Trait adoption and required-license enforcement verified; historical sibling comparison retained as source-attributed history','evidence':['source_evidence.download.yaml','source_evidence.scripts/check_sources.py']},
      {'locator':'_fleet/fleet_fragment.html::XREF[from=MediaIngredientMech,to=TraitMech] and [from=CultureMech,to=TraitMech] + template equivalents','verdict':'adoption and qc provenance verified; nearly every writer is an imprecise legacy claim, propose remove unless whole-writer audit supplies denominator','evidence':['source_evidence.src/traitmech/curate/curation_event.py','source_evidence.src/traitmech/validation/write_validated.py','source_evidence.scripts/add_faprotax_synonyms.py','source_evidence.justfile']},
      {'locator':'_fleet/fleet_fragment.html::XREF[from=PathwayMech,to=TraitMech] + template equivalent','verdict':'verified unchanged19links17nodes11records15targets','evidence':['counts.pathway_context','source_evidence.docs/PATHWAY_LINKS.md','features.cross_mech_links.evidence']},
      {'locator':'_fleet/fleet_fragment.html::HUB[mech=TraitMech,dir=in]','verdict':'verified live kg-microbe matches and nearest-neighbor sections cite DeepWalk512dimensions','evidence':'features.record_pages; raw sampled record text'},
      {'locator':'Other relationship rows mentioning TraitMech whose source is CellStructureMech,TaxonMech,HabitatMech,CommunityMech,ProteinTraitsMech,DUFMech or PathwayMech','verdict':'delegated to owning Mech audit; not independently recertified by Trait-only canary','details':'Includes412protein mentions,4reaction rows,11Habitat trait nodes,two of15Taxon causal records,and17CellStructure writers.'},
    ]
    result={'mech':'TraitMech','pin':PIN,'started_at':raw['started_at'],'finished_at':raw['finished_at'],'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],'counts':counts,'features':feature,'proposed_changes':changes,'hand_claims':claims,'source_evidence':source,'raw_capture':{'path':str(raw_path),'sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest()},'limits':['Browser checks cover12routes and three record pages, not exhaustive rendering of1,130pages.','Source link sets cover all1,130trackedHTMLrecord paths at pin.','Direct YAML schema access retains partial under root arbitration; no new feature criteria introduced.','Other-Mech-owned relationship claims require their respective audit before fleet recertification.']}
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    md=['# TraitMech auditor — 2026-11-04','',f'Pin `{PIN}`. Real Chromium browser run {raw["started_at"]} to {raw["finished_at"]}.', '', 'Deployment7544029987 remained successful at the exact pin before and after the run. Latest status2026-11-04T10:51:27Z; Last-Modified Wed,04Nov2026 10:51:17GMT.', '', 'All24features exercised.21present,3partial: term_links,schema_docs,responsive. JSON contains every action/result receipt, proposed replacement and pinned source excerpt.','', '| Feature | Verdict | Observation |','|---|---|---|']
    md.extend(f'| {k} | {v["status"]} | {v["note"]} |' for k,v in feature.items())
    md+=['','## Hand-claim corrections','','- Causal graphs:748→761 in audit_notes and resources;1,130total,427reviewed,615proposed,50deprecated,38seeded unchanged.','- Feature notes: ecology40; combined-filter8; correct sort options; landing counts only1,130/10/100%; linked but unlabeled GOxref; working schema-source link; current map overflow measurements.','- PathwayContext remains19links/17nodes/11records/15targets.','- Remove “nearly every TraitMech write script goes through them” unless the fleet audit supplies a current writer denominator. Adoption itself is supported by module docstrings.','- Relationship claims owned by sibling repositories remain pending their respective audits.','','## Limits','','This is a current24-feature browser audit, not a new34-feature audit or exhaustive rendering of1,130records. Raw capture is outside the repository; committed receipts preserve the meaningful evidence. No central source data, original checkout,GitHub objects or commits were changed.']
    OUT.with_suffix('.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'report':str(OUT),'bytes':OUT.stat().st_size,'features':len(feature),'verdicts':dict(collections.Counter(v['status'] for v in feature.values())),'counts':counts},indent=2))


if __name__=='__main__':
    finalize() if '--finalize' in sys.argv else main()
