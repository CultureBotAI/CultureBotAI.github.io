#!/usr/bin/env python3
"""Independently inspect TraitMech's pinned corpus and live feature behaviors.

Inputs: Nov 4 pinned checkout, central feature rubric, public Pages and deployment API.
Outputs: trait-skeptic-observations.json; supports Nov 4 refresh canary review.
2026-11-04. Read-only for source checkout and public services; no publishing.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import yaml
from playwright.sync_api import sync_playwright

BASE = 'https://culturebotai.github.io/TraitMech/'
PIN = 'c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6'
CHROME = '/Users/marcin/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   env={**__import__('os').environ, 'GIT_OPTIONAL_LOCKS': '0'})

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))

def finalize(args):
    """Create the compact verdict ledger from this reviewer's own observations."""
    raw = json.loads(args.output.read_text())
    assert raw.get('finished_at'), 'An incomplete browser run cannot be finalized'
    current = json.loads(Path('_fleet/data/site_features.json').read_text())
    pages = {p['route']: p for p in raw['pages']}
    before = current['mechs']['TraitMech']['features']
    defs = [
        ('search','present','pages/browse.html','label[for=record-query]; #record-count',
         '1 of 1130 records shown',
         'Browse searches all 1,130 records. METPO:1000801 and traitmech:000048 each return one linked record; aerobic respiration returns 14 linked matches.'),
        ('facets','present','pages/browse.html','#record-category; #record-kind; #facet-clear-btn',
         '1130 of 1130 records shown',
         'Category and Kind filters apply to the full corpus. Clear all filters restores all 1,130 records.'),
        ('result_counts','present','pages/browse.html?q=pathogen&category=ECOLOGY&kind=CLASS','#record-count',
         '8 of 1130 records shown',
         'The count updates with search and filters: pathogen gives nine matches; ECOLOGY and CLASS narrow that to eight of 1,130 records.'),
        ('sorting','present','pages/browse.html','#record-sort option',
         'Label (A–Z); Label (Z–A); Identifier (A–Z); Category; Kind; kg-microbe nodes (high–low); Synonyms (high–low)',
         'Browse sorts by label in either direction, identifier, category, kind, kg-microbe node count, or synonym count.'),
        ('shareable_state','present','pages/browse.html?q=pathogen&category=ECOLOGY&kind=CLASS&sort=label-desc','#record-filters after reload',
         '8 of 1130 records shown',
         'Search, category, kind and sort are encoded in the URL and restored on reload; pathogen with ECOLOGY and CLASS restores eight matches.'),
        ('full_catalogue','present','pages/browse.html','#record-table tbody tr td:first-child a',
         '1130 of 1130 records shown',
         'Browse contains 1,130 distinct linked record rows, matching the landing count and complete JSON export.'),
        ('record_pages','present','pages/traits/ecology/animal_pathogen.html','h1; source card',
         'data/traits/ecology/animal_pathogen.yaml',
         'Each of the 1,130 records has a stable page under pages/traits/<category>/<slug>.html. At the pin, 761 records contain causal graphs.'),
        ('term_links','partial','pages/traits/metabolism/aerobic_respiration.html','.xrefs',
         '<a href="https://amigo.geneontology.org/amigo/term/GO:0009060" rel="nofollow noreferrer"><code>GO:0009060</code></a>',
         'The Cross-references section now links GO:0009060 to Amigo, but shows no readable term label beside that CURIE. Main graph and parent terms have labels and links.'),
        ('evidence','present','pages/traits/metabolism/aerobic_respiration.html','Trait evidence; Edge evidence',
         'DOI:10.1146/annurev.biophys.27.1.329',
         'Trait and causal-edge citations on the checked record pages link to DOI or PMID sources and display supporting text.'),
        ('review_status','present','pages/traits/ecology/animal_pathogen.html','header; Identifier card',
         'METPO:1004002 · CLASS · REVIEWED',
         'Record headers and Identifier cards display curation status. The complete corpus includes REVIEWED, PROPOSED, SEEDED and DEPRECATED records.'),
        ('curation_history','present','pages/traits/ecology/animal_pathogen.html','Curation history',
         '2026-05-11T23:15:00-07:00 · CURATED_CAUSAL_GRAPH · claude',
         'Curation history shows dated actions, curator identifiers and change summaries; some records also link detailed curation-session sidecars.'),
        ('source_link','present','pages/traits/ecology/animal_pathogen.html','Source card',
         'View YAML on GitHub',
         'Record Source cards link the record’s own YAML on GitHub, its raw file and its edit page.'),
        ('domain_view','present','pages/map.html','#umap-plot svg circle',
         '1130 records loaded.',
         'Text, PaCMAP and graph-layout views each render 1,130 trait points; the sequence map renders 156 protein points. Sampled record pages render causal diagrams; 761 pinned records carry graphs.'),
        ('cross_mech_links','present','pages/traits/metabolism/wood_ljungdahl_pathway.html','Pathway context',
         'WikiPathways:WP5019',
         'Wood–Ljungdahl links to PathwayMech’s Acetogenesis record. Its context describes organism scope and retains the source revision.'),
        ('corpus_stats','present','pages/index.html','.stats',
         '1130\nTRAIT RECORDS\n10\nCATEGORIES\n100.0%\nEMBEDDED',
         'The landing shows 1,130 trait records, ten categories and 100.0% embedding coverage. It does not display the reviewed-record or causal-graph totals.'),
        ('category_browse','present','pages/browse.html','category tiles; linked category/ecology.html',
         'ECOLOGY',
         'Browse links ten category pages; ECOLOGY has 40 records and QUANTITATIVE_PROPERTY has seven.'),
        ('suite_nav','present','pages/index.html','a[href="https://culturebotai.github.io/mechs/"]',
         'All Mech projects',
         'All Mech projects links to the suite directory from the landing, Browse, categories, sampled records, all four visualizations and discussions.'),
        ('downloads','present','pages/index.html','Download traits.json link',
         'Download traits.json →',
         'The landing links the complete traits.json export, which returns all 1,130 records; maps also offer CSV exports.'),
        ('schema_docs','partial','pages/index.html','Schema / LinkML schema links',
         'https://github.com/CultureBotAI/TraitMech/blob/main/src/traitmech/schema/traitmech.yaml',
         'Navigation and footers now link the LinkML schema YAML directly. They do not link a rendered schema documentation page.'),
        ('license','present','pages/index.html','footer; LICENSE@pin',
         'Project data: CC BY 4.0 · code: BSD-3-Clause · third-party source terms apply',
         'The checked pages consistently state CC BY 4.0 data and BSD-3-Clause code, matching LICENSE-DATA and LICENSE-CODE.'),
        ('build_provenance','present','pages/browse.html','footer',
         'Corpus as of 2026-10-31 20:55 UTC',
         'The site states its corpus date; record pages state their record date, separately from the METPO source release.'),
        ('theme_toggle','present','pages/index.html','.theme-toggle; html[data-theme]',
         'dark',
         'Selecting dark on the landing persists across Browse, categories, sampled records, all four visualizations and discussions in the same browser context.'),
        ('responsive','partial','pages/map.html','document.documentElement.scrollWidth at viewport390',
         '553',
         'Text and sequence maps overflow on fresh 390px loads (553px document width), and after resizing from 1280px (793px). Landing, Browse, sampled records/categories, PaCMAP, graph layout and discussions fit.'),
        ('load_failure','present','pages/map.html','#map-status after aborting data JSON',
         'Map data could not be loaded. Retry, or use Browse to read the trait records.',
         'Aborted JSON requests in all four visualizations show an explicit unavailable/error state and Retry. Blocking discussions data.js shows Discussion counts unavailable, an error and Retry loading discussions.'),
    ]
    features = {}
    for key, status, route, locator, excerpt, note in defs:
        features[key] = {'status':status, 'note':note, 'url':BASE + route,
            'claim_locator': f'_fleet/data/site_features.json#/mechs/TraitMech/features/{key}',
            'prior_verbatim':before[key]['note'], 'evidence':{'url':BASE+route,'locator':locator,'excerpt':excerpt}}
    assert set(features) == set(current['catalogue']) and len(features) == 24
    dep = api('repos/CultureBotAI/TraitMech/deployments?environment=github-pages&per_page=1')[0]
    status = api(f"repos/CultureBotAI/TraitMech/deployments/{dep['id']}/statuses?per_page=1")[0]
    assert dep['id'] == raw['deployment']['id'] and dep['sha'] == PIN and status['state'] == 'success'
    raw['deployment_after'] = {k:dep[k] for k in ['id','sha','created_at']}
    raw['deployment_after']['state'] = status['state']
    with urllib.request.urlopen('https://culturebotai.github.io/PathwayMech/pages/records/WikiPathways_WP5019.html') as response:
        page = response.read().decode()
        raw['cross_mech_target'] = {'url':response.url,'status':response.status,'contains_Acetogenesis':'Acetogenesis' in page}
    tree = git(args.snapshot,'ls-tree','-r','--name-only',PIN).splitlines()
    raw['corpus']['static_record_pages'] = len([p for p in tree if p.startswith('pages/traits/') and p.endswith('.html')])
    assert raw['corpus']['static_record_pages'] == 1130
    for entry in raw['pages']:
        body = entry['main_text']
        if len(body) > 20000:
            entry['body_text_sha256'] = hashlib.sha256(body.encode()).hexdigest()
            entry['main_text'] = body[:10000] + '\n[long middle omitted; full DOM inspected by script]\n' + body[-5000:]
            entry['text_excerpted'] = True
        if entry['route'] == 'pages/browse.html':
            entry['links'] = [x for x in entry['links'] if '/pages/traits/' not in x['url']]
            entry['record_links_counted_separately'] = 1130
    args.output.write_text(json.dumps(raw,indent=2)+'\n')
    hand = [
        {'locators':['_fleet/audit_notes.json#/notes/TraitMech','resources.md section TraitMech - Microbial Ecophysiological Traits','_fleet/README.md sentence beginning contains 1,130 records'],
         'old_excerpts':['The README and corpus contain 748 records with causal graphs.', '427 are marked REVIEWED and 748 carry causal graphs.', 'contains 1,130 records with 100.0% embedding coverage and 748 graph-bearing records.'],
         'replacements':['The README and corpus contain 761 records with causal graphs.', '427 are marked REVIEWED and 761 carry causal graphs.', 'contains 1,130 records with 100.0% embedding coverage and 761 graph-bearing records.'], 'reason':'Causal-graph-bearing records rose to761; all1130 YAML records independently parsed.',
         'evidence':{'source':'README.md@'+PIN+':37','excerpt':'Across the corpus, 761 records currently carry causal graphs. The 50 deprecated'}},
        {'locators':['_fleet/mechs_template.md article[data-mech="TraitMech"]','_fleet/fleet_fragment.html MECHS.TraitMech','index.md suite count','resources.md TraitMech paragraph'],
         'action':'retain1130records/10categories/427reviewed and vocabulary chips',
         'evidence':{'source':'README.md@'+PIN+':29','excerpt':'| **TOTAL** | **427** | **615** | **50** | **761** | **1130** |'},'derived':raw['corpus']},
        {'locators':['_fleet/fleet_fragment.html MECHS.TraitMech.root'], 'action':'retain TraitRecord',
         'evidence':{'source':'src/traitmech/schema/traitmech.yaml@'+PIN+':65-66','excerpt':'  TraitRecord:\n    class_uri: traitmech:TraitRecord'},
         'qualification':'This schema does not declare tree_root; docs/SCHEMA.md names TraitRecord (root), and the validator explicitly selects TraitRecord.'},
        {'locators':['_fleet/fleet_fragment.html HUB TraitMech input','_fleet/mechs_template.md Explore TraitMech link'],
         'action':'retain DeepWalk input and embedding-view claims',
         'evidence':{'url':BASE+'pages/index.html','excerpt':'Interactive PaCMAP projections of full-corpus BGE-large text embeddings, ESM-2 protein sequence embeddings, and KG-Microbe deepwalk space.'}},
        {'locators':['_fleet/fleet_fragment.html XREFS PathwayMech→TraitMech','_fleet/mechs_template.md PathwayMech→TraitMech'],
         'action':'retain19links/17nodes/11records/15targets; repin current evidence locators',
         'derived_counts':raw['corpus']['pathway_link_counts'],
         'evidence':{'source':'data/traits/ecology/free_living.yaml@'+PIN+':66-75', 'excerpt':'    - corpus: PathwayMech\n      identifier: MetaCyc:P101-PWY\n      relation: PATHWAY_CONTEXT'}},
        {'locators':['_fleet/fleet_fragment.html XREFS CommunityMech→TraitMech','_fleet/mechs_template.md CommunityMech→TraitMech'],
         'action':'retain port and proposal-cohort separation claims',
         'evidence':{'source':'scripts/research_trait_edison.py@'+PIN+':7-8','excerpt':"response provenance. This is the TraitMech port of CommunityMech's\n``research_community_edison.py``."}},
        {'locators':['_fleet/fleet_fragment.html XREFS ProteinTraitsMech→TraitMech','_fleet/mechs_template.md ProteinTraitsMech→TraitMech'],
         'action':'retain catalogue/validator port and required-license claim',
         'evidence':{'source':'scripts/check_sources.py@'+PIN+':42','excerpt':'REQUIRED = ("url", "name", "source", "license", "status")'}},
        {'locators':['_fleet/fleet_fragment.html XREFS CultureMech→TraitMech and MediaIngredientMech→TraitMech','_fleet/mechs_template.md corresponding paired entries'],
         'action':'retain port provenance; broad writer-coverage wording requires fleet-wide writer audit rather than assuming from docstring',
         'evidence':{'source':'src/traitmech/validation/write_validated.py@'+PIN+':39-40','excerpt':"Ported from CultureMech's ``src/culturemech/validation/write_validated.py``\n(by way of MediaIngredientMech's ``write_validated_ingredient``). The"}},
        {'locators':['_fleet/mechs_template.md license bullet','_fleet/fleet_fragment.html MECHS.TraitMech.license','resources.md TraitMech license'],
         'action':'retain data CC BY4.0/code BSD3',
         'evidence':{'source':'LICENSE@'+PIN+':4-9','excerpt':'data exports, are licensed under Creative Commons Attribution 4.0\nInternational (CC-BY-4.0). See LICENSE-DATA.'}},
    ]
    review = {'reviewer':'independent skeptic','checked_at':now(),'pin':PIN,'deployed_revision':dep['sha'],
        'observation_file':str(args.output),'features':features,'hand_claims':hand,
        'rubric_disagreement':{'feature':'schema_docs','initial_auditor':'present','skeptic':'partial',
            'basis':'Direct schema YAML is available; documentation criterion and root-stated PR503 precedent require partial without a rendered documentation link.',
            'resolution':'Auditor agreed to partial; root accepted partial under the documentation criterion.'},
        'scope_limits':['Cross-references whose decisive evidence belongs to another Mech, and global orchestration claims, remain with the fleet-wide source audit; this canary does not independently clear those other corpora.',
            'Static page count verified from complete pinned Git tree;13 live routes exercised. This is not a crawl of all1130 HTTP record URLs.',
            'Search for absent rendered schema links uses all anchors on13 reviewed live routes and complete pinned Git tree; ignores cannot hide tracked site assets. No claim of absence from every untracked source file is made.'],
        'canary_assessment':'The independent procedure supports all24 verdicts, exact source pin and served deployment. Compact auditor ledger must preserve unique locators, verbatim old claims, evidence excerpts and in-place replacements before fanout.'}
    dest = args.output.with_name('trait-skeptic.json')
    dest.write_text(json.dumps(review,indent=2)+'\n')
    lines=['# TraitMech independent skeptic — 2026-11-04','',
        'Pinned and served revision: `'+PIN+'`. Deployment '+str(dep['id'])+' remained successful before and after the independent browser pass; Last-Modified follows deployment creation.',
        '', 'All 24 feature verdicts were independently exercised. Keep `term_links`, `schema_docs`, and `responsive` partial; the other 21 are present. The schema-source link is new, but is not rendered documentation.', '',
        '| Feature | Verdict | Proposed note |', '|---|---|---|']
    lines.extend('| '+k+' | '+v['status']+' | '+v['note']+' |' for k,v in features.items())
    lines += ['', 'Confirmed source changes: causal-graph-bearing records are761 (formerly748), while total1130, statuses427/615/50/38, categories10, and Pathway links19 on17nodes in11records to15targets remain correct.',
        '', 'Exact old claims, replacements, unique locators and evidence are in `trait-skeptic.json`; browser/source observations and helper provenance are retained beside it.', '', 'Scope: this canary independently verifies Trait-owned claims and13 representative live routes. Claims supported primarily by sibling repositories and global orchestration remain for the fleet-wide audit.']
    dest.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'verdicts':len(features),'report':str(dest),'deployment':dep['id']}))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=Path('/private/tmp/xmech-refresh-20261104-snapshot/mechs/TraitMech'))
    parser.add_argument('--output', type=Path, default=Path('_fleet/reviews/refresh-20261104/trait-skeptic-observations.json'))
    parser.add_argument('--finalize', action='store_true', help='Summarize completed observations and recheck deployment')
    args = parser.parse_args()
    if args.finalize:
        return finalize(args)
    assert git(args.snapshot, 'rev-parse', 'HEAD').strip() == PIN
    report = {'started_at': now(), 'pin': PIN, 'snapshot': str(args.snapshot)}
    files = git(args.snapshot, 'ls-tree', '-r', '--name-only', PIN, 'data/traits').splitlines()
    files = [p for p in files if p.endswith('.yaml')]
    statuses, categories, links, causal, prefixes = collections.Counter(), collections.Counter(), [], [], collections.Counter()
    import re
    for path in files:
        raw = git(args.snapshot, 'show', f'{PIN}:{path}')
        record = yaml.load(raw, Loader=yaml.CSafeLoader)
        statuses[record.get('mapping_status')] += 1
        categories[record.get('trait_category')] += 1
        for prefix in ['METPO', 'GO', 'NCBITaxon', 'CHEBI', 'UniProtKB', 'PATO']:
            if re.search(r'\b' + prefix + ':', raw):
                prefixes[prefix] += 1
        if record.get('causal_graphs'):
            causal.append(path)
        for graph in record.get('causal_graphs', []):
            for node in graph.get('nodes', []):
                for rel in node.get('related_records', []):
                    if rel.get('corpus') == 'PathwayMech':
                        links.append({'source': path, 'graph_id': graph.get('graph_id'), 'node_id': node.get('node_id'), **rel})
    report['corpus'] = {'records': len(files), 'statuses': statuses, 'categories': categories,
        'records_with_causal_graphs': len(causal), 'vocabulary_record_counts': prefixes,
        'pathway_links': links, 'pathway_link_counts': {'links': len(links),
        'nodes': len({(p['source'], p['graph_id'], p['node_id']) for p in links}),
        'records': len({p['source'] for p in links}), 'targets': len({p['identifier'] for p in links})}}
    source_needles = {
        'README.md': ['1,130', '761', 'BSD', 'CC BY', 'METPO', 'GapMind', 'GTDB'],
        'src/traitmech/schema/traitmech.yaml': ['TraitRecord:', 'class_uri: traitmech:TraitRecord', 'tree_root:', 'causal_graphs:', 'METPO:'],
        'LICENSE': ['BSD'], 'LICENSE-DATA': ['Creative Commons'],
        'scripts/research_trait_edison.py': ['CommunityMech', 'research_community_edison'],
        '.claude/skills/deep-research-trait/SKILL.md': ['CommunityMech'],
        '.claude/skills/metpo-proposal/SKILL.md': ['CommunityMech', 'placeholder'],
        'scripts/check_sources.py': ['ProteinTraitsMech', 'license', 'licence'],
        'download.yaml': ['ProteinTraitsMech'],
        'src/traitmech/validation/write_validated.py': ['CultureMech', 'MediaIngredientMech'],
        'src/traitmech/curate/curation_event.py': ['CultureMech', 'MediaIngredientMech'],
        'scripts/add_faprotax_synonyms.py': ['MediaIngredientMech', 'raw'],
        'justfile': ['qc:', 'sources-check'],
        'docs/SCHEMA.md': ['material', 'MediaIngredientMech'],
        'docs/PATHWAY_LINKS.md': ['19', '17', '11', '15', 'PATHWAY_CONTEXT'],
    }
    report['source_excerpts'] = []
    tree = set(git(args.snapshot, 'ls-tree', '-r', '--name-only', PIN).splitlines())
    for path, needles in source_needles.items():
        if path not in tree:
            report['source_excerpts'].append({'source': path + '@' + PIN, 'missing_from_git_tree': True})
            continue
        lines = git(args.snapshot, 'show', f'{PIN}:{path}').splitlines()
        report['source_excerpts'].append({'source': path + '@' + PIN, 'matches': [
            {'line': i + 1, 'excerpt': line} for i, line in enumerate(lines) if any(n.lower() in line.lower() for n in needles)]})
    deps = api('repos/CultureBotAI/TraitMech/deployments?environment=github-pages&per_page=1')
    dep = deps[0]
    status = api(f"repos/CultureBotAI/TraitMech/deployments/{dep['id']}/statuses?per_page=1")[0]
    report['deployment'] = {k: dep[k] for k in ['id', 'sha', 'created_at']}
    report['deployment']['status'] = {k: status[k] for k in ['state', 'created_at']}
    with urllib.request.urlopen(urllib.request.Request(BASE + 'pages/index.html', method='HEAD')) as response:
        report['deployment']['head'] = {'status': response.status, 'last_modified': response.headers.get('Last-Modified'), 'date': response.headers.get('Date')}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    save()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, color_scheme='light')
        page = ctx.new_page()
        def go(route):
            response = page.goto(BASE + route, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(300)
            return response
        go('pages/browse.html')
        report['browse'] = {'url': page.url, 'all_rows': page.locator('#record-table tbody tr').count(),
            'unique_record_links': len(set(page.locator('#record-table tbody tr td:first-child a').evaluate_all('(els)=>els.map(e=>e.href)'))),
            'sort_options': page.locator('#record-sort option').all_text_contents(),
            'category_links': page.locator('a[href^="category/"]').evaluate_all('(els)=>els.map(e=>({text:e.innerText,url:e.href}))'),
            'query_label': page.locator('label[for="record-query"]').inner_text()}
        queries = []
        for query in ['METPO:1000801', 'aerobic respiration', 'traitmech:000048', 'pathogen']:
            page.locator('#record-query').fill(query)
            queries.append({'query': query, 'count': page.locator('#record-count').inner_text(),
                'rows': page.locator('#record-table tbody tr:not([hidden])').all_text_contents(),
                'links': page.locator('#record-table tbody tr:not([hidden]) td:first-child a').evaluate_all('(els)=>els.map(e=>e.href)')})
        report['browse']['queries'] = queries
        page.locator('#record-category').select_option('ECOLOGY')
        page.locator('#record-kind').select_option('CLASS')
        page.locator('#record-sort').select_option('label-desc')
        report['browse']['filtered'] = {'url': page.url, 'count': page.locator('#record-count').inner_text(), 'rows': page.locator('#record-table tbody tr:not([hidden])').all_text_contents()}
        page.reload(wait_until='networkidle')
        report['browse']['restored'] = {'query': page.locator('#record-query').input_value(), 'category': page.locator('#record-category').input_value(),
            'kind': page.locator('#record-kind').input_value(), 'sort': page.locator('#record-sort').input_value(), 'count': page.locator('#record-count').inner_text()}
        page.locator('#facet-clear-btn').click()
        report['browse']['reset_count'] = page.locator('#record-count').inner_text()
        orders = {}
        for sort in ['label-asc', 'label-desc', 'id-asc', 'category', 'kind', 'kgm-desc', 'synonyms-desc']:
            page.locator('#record-sort').select_option(sort)
            orders[sort] = page.locator('#record-table tbody tr').evaluate_all('(els)=>els.slice(0,3).map(e=>e.innerText)')
        report['browse']['sorting_samples'] = orders
        go('pages/index.html')
        page.locator('.theme-toggle').click()
        report['theme_initial'] = page.locator('html').get_attribute('data-theme')
        report['pages'] = []
        routes = ['pages/index.html', 'pages/browse.html', 'pages/category/ecology.html',
            'pages/category/quantitative_property.html', 'pages/traits/metabolism/aerobic_respiration.html',
            'pages/traits/ecology/animal_pathogen.html', 'pages/traits/ecology/free_living.html',
            'pages/traits/metabolism/wood_ljungdahl_pathway.html', 'pages/map.html', 'pages/umap.html',
            'pages/sequence-map.html', 'pages/graph.html', 'app/discussions/']
        for route in routes:
            response = go(route)
            rec = {'route': route, 'url': page.url, 'status': response.status,
                'observed_at': now(), 'theme': page.locator('html').get_attribute('data-theme'),
                'title': page.title(), 'main_text': page.locator('body').inner_text(),
                'suite_links': page.locator('a[href="https://culturebotai.github.io/mechs/"]').count(),
                'links': page.locator('a').evaluate_all('(els)=>els.map(e=>({text:e.innerText,url:e.href}))'),
                'svg_counts': page.locator('svg').count(), 'circles': page.locator('svg circle').count(),
                'canvases': page.locator('canvas').count()}
            page.set_viewport_size({'width':390, 'height':844})
            page.wait_for_timeout(500)
            rec['resized_390'] = page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
            page.reload(wait_until='networkidle')
            page.wait_for_timeout(300)
            rec['fresh_390'] = page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
            if 'aerobic_respiration' in route:
                rec['xref_html'] = page.locator('.xrefs').inner_html()
                rec['graph_grounding_links'] = page.locator('.causal-graphs a').evaluate_all('(els)=>els.map(e=>({text:e.innerText,url:e.href}))')
            report['pages'].append(rec)
            page.set_viewport_size({'width':1280, 'height':900})
            save()
        report['bulk'] = {}
        response = ctx.request.get(BASE + 'pages/data/traits.json')
        data = response.json()
        report['bulk'] = {'url': response.url, 'status': response.status, 'type': type(data).__name__,
            'count': len(data), 'keys': list(data)[:10] if isinstance(data, dict) else None,
            'sha256': hashlib.sha256(response.body()).hexdigest()}
        report['failure_cases'] = []
        for route, pattern in [('pages/map.html','**/data/*.json'),('pages/umap.html','**/data/*.json'),
                               ('pages/sequence-map.html','**/data/*.json'),('pages/graph.html','**/data/*.json'),
                               ('app/discussions/','**/data.js')]:
            fail = ctx.new_page()
            fail.route(pattern, lambda route: route.abort())
            response = fail.goto(BASE + route, wait_until='networkidle', timeout=60000)
            fail.wait_for_timeout(500)
            report['failure_cases'].append({'url': fail.url, 'aborted': pattern, 'status': response.status,
                'text': fail.locator('body').inner_text(), 'buttons': fail.locator('button').all_text_contents()})
            fail.close()
            save()
        browser.close()
    assert git(args.snapshot, 'rev-parse', 'HEAD').strip() == PIN
    report['finished_at'] = now()
    save()
    print(json.dumps({'output': str(args.output), 'records':len(files), 'causal_records':len(causal),
                      'pathway_link_counts':report['corpus']['pathway_link_counts'], 'finished_at':report['finished_at']}))

if __name__ == '__main__':
    main()
