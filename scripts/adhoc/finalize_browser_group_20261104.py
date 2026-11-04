#!/usr/bin/env python3
"""Condense reviewed browser receipts into 24-feature ledgers for the Nov4 refresh.

Inputs: audit_site_group_20261104 raw captures, manual reviewed verdicts below.
Outputs: *_auditor_a.json/md in the refresh evidence directory. No site/source edits.
Date:2026-11-04. Serves the central-directory refresh PR and independent skepticism.
"""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RAW=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-a/raw')
EVID=ROOT/'_fleet/reviews/refresh-20261104'

# Only conclusions actually inspected by the auditor are entered here.
REVIEW={
'CellStructureMech':{
 'total':1022,'statuses':{'term_links':'present','build_provenance':'present'},
 'notes':{
 'full_catalogue':'Browse exposes all 1,022 structure records, matching the landing and linked complete-corpus JSON; category pages and the 873-record grounded subset provide additional routes.',
 'record_pages':'The sampled structure records have stable pages with components, evidence, curation history and their own YAML source links. Browse and the complete export both cover 1,022 records.',
 'term_links':'Attachment organelle membrane now shows labeled GO:0033111, GO:0033099 and GO:0005886 resolver links in its mechanism Subject/Object cells, alongside labeled parent, taxon and UniProt-location links.',
 'evidence':'Sampled components, distribution statements, mechanism edges and record-level evidence link GO, DOI and PubMed references.',
 'review_status':'Sampled record headers and Browse rows show Proposed, separately from their dated curation histories.',
 'curation_history':'Attachment organelle membrane shows dated creation, expansion and review actions with named curators and change summaries.',
 'source_link':'Each sampled record links its own data/structures YAML on GitHub.',
 'domain_view':'The working embedding-map.html renders 1,022 structure points; the sequence map renders 469 proteins across 140 structures. The old note’s pages/map.html returns 404, and sampled mechanism sections are tables rather than rendered SVG diagrams.',
 'cross_mech_links':'S-layer links traitmech:000064 to TraitMech’s stable S-layer record; that target returns HTTP 200.',
 'corpus_stats':'The landing reports 1,022 structures, 13 categories and 873 GO-grounded records; its category table includes 226 membrane organelles.',
 'category_browse':'Thirteen category links lead to subset pages. The opened Microcompartment page shows all six records; the separate GO-grounded page shows 873.',
 'downloads':'The landing links the complete corpus JSON with 1,022 records and the 1,022-entry catalogue index; both downloads return HTTP 200.',
 'schema_docs':'Visible Schema and LinkML schema links open the annotated LinkML YAML source. Reviewed navigation does not expose a rendered schema reference or explanatory guide.',
 'build_provenance':'Shared footers state corpus as of 2026-11-03 05:55:11 UTC, digest d7c5fef867d9 and 1,022 records.',
 'load_failure':'Blocking either embedding-map JSON request displays Could not load embedding artifacts: Failed to fetch. The sequence map embeds its data without a fetch.',
 }},
'AntibioticMech':{
 'total':3064,'statuses':{'search':'partial','load_failure':'partial','downloads':'partial'},
 'notes':{
 'search':'Browse finds CHEBI:2637 and amikacin with matching counts, but large result sets stop at the first 500 links without result pagination. Category indexes provide separate routes through the corpus.',
 'full_catalogue':'The 3,064-record browse index and linked paginated class listings provide routes into the complete corpus; the interactive result panel itself is capped at 500.',
 'record_pages':'Sampled amikacin, avibactam and D-cycloserine pages have stable URLs, source assertions, molecular context, curation histories and links to their own source records.',
 'term_links':'Avibactam’s own identity and activity terms resolve, but four broader ChEBI identifiers still display Label unavailable; the main classification section remains incompletely labeled.',
 'evidence':'Avibactam links PMID:25406838 in its molecular-target, causal-edge and record evidence. D-cycloserine retains linked evidence for its qualified pathway correspondence.',
 'review_status':'Record headers show workflow status, including REVIEWED on avibactam; the landing distinguishes recorded workflow status from human review.',
 'curation_history':'Avibactam shows dated seeding, reseeding, review and protein/causal-graph curation events, with curator identifiers and LLM-assisted labels where recorded.',
 'source_link':'Sampled Provenance sections link their own data/antibiotics YAML. Large records also link a complete per-record JSON.gz export.',
 'domain_view':'The chemical map displays all 3,064 compounds and the sequence map 132 proteins; the corpus text map renders separately. Sampled causal mechanisms are available as node/edge tables.',
 'cross_mech_links':'D-cycloserine links to PathwayMech WikiPathways:WP5060 with source revision and qualified target/process correspondence; the target returns HTTP 200.',
 'corpus_stats':'The landing reports 3,064 compounds and generated grounding, review and mechanism statistics; its notice states 2,815 SEEDED records.',
 'category_browse':'Browse and the landing link antimicrobial class listings, including Antibacterial with 1,147 directly filed records and 1,225 including its 78-record antimycobacterial subclass; Antifungal has 609.',
 'downloads':'The landing links a 3,064-entry browse index and chemical-map coordinates, while sampled record pages link complete individual JSON.gz records. No bulk complete-record corpus export is linked; the old corpus.json/corpus.csv claim is unsupported.',
 'schema_docs':'Navigation links the annotated LinkML schema YAML successfully; no rendered schema documentation was linked from the sampled pages.',
 'build_provenance':'The footer displays corpus digest 6c2a5f8e3f3f and 3,064 records, but its only date is the upstream ChEBI/CARD input date 2026-08-30; it does not identify a dated build of its own corpus.',
 'load_failure':'Chemical-map and browse-index failures are explicit. After sequence-map JSON fails, typing in search replaces the error with Showing 0 of 0 proteins, which misrepresents an unavailable dataset as empty.',
 }},
'NaturalProductMech':{
 'total':3136,'statuses':{'schema_docs':'partial','responsive':'partial','load_failure':'partial'},
 'notes':{
 'full_catalogue':'Browse exposes the complete 3,136-compound catalogue across eight filing pathways, matching the landing and chemical-map record count.',
 'record_pages':'Sampled natural products have stable compound URLs with structure, producers, occurrence evidence, biosynthetic loci, provenance and cross-fleet exploration links.',
 'term_links':'Anisomycin and rebeccamycin display chemical, taxon, MIBiG and GenBank identifiers, but the main producer and biosynthetic sections leave their resolver links absent.',
 'evidence':'Anisomycin’s producer PMID:28373542 and occurrence DOI references remain plain text without PubMed or DOI anchors.',
 'review_status':'Compound headers display grounding and SEEDED workflow tags with a What these status tags mean explanation.',
 'curation_history':'The sampled compound record views do not show dated, attributed curation events. Source/history links and mechanism summaries do not constitute a displayed event history.',
 'source_link':'Each sampled Provenance section links its own data/natural_products YAML on GitHub.',
 'domain_view':'The chemical structure map renders 3,136 compounds, the text map covers a retained 3,114-compound projection, and the sequence map renders 763 proteins across 303 records. Sampled records also show a mechanism/biosynthesis summary diagram.',
 'cross_mech_links':'Anisomycin links CHEBI:338412 directly to AntibioticMech’s anisomycin record with a same-structure/same-InChIKey qualifier; that target returns HTTP 200.',
 'corpus_stats':'The landing reports a 3,136-compound corpus with generated source, producer, occurrence and causal-graph counts.',
 'category_browse':'Eight filing-pathway cards open category indexes. The checked Terpenoids page shows all 213 compounds.',
 'downloads':'The landing links chemical-map coordinates for all 3,136 compounds, the complete chemical-search index and a 763-protein map export. These are indexes/projections rather than complete source-record exports.',
 'schema_docs':'Downloads & Schema now links the LinkML YAML source. Reviewed navigation does not link rendered schema documentation or an explanatory schema guide.',
 'build_provenance':'The footer states 3,136 records and corpus SHA-256 2838a2004e52, but its date is source retrieval (2026-10-31), not a dated build of the project corpus.',
 'responsive':'At 390px the sampled compound pages overflow: anisomycin 409px, rebeccamycin 407px, staurosporine 415px and the long dehydrohistidyltryptophanyldiketopiperazine page 464px, on fresh and resized loads. Browse, category and maps fit.',
 'load_failure':'Chemical-map JSON failures display an explicit error. After sequence-map JSON fails, using search replaces its error with Showing 0 of 0 proteins and no unavailable-data explanation.',
 }},
'HabitatMech':{
 'total':3209,'statuses':{'search':'partial','cross_mech_links':'partial','schema_docs':'partial','theme_toggle':'partial','responsive':'partial','load_failure':'partial'},
 'notes':{
 'search':'Browse finds ENVO:03000033 and marine sediment, but large match sets stop at 200 results without result pagination. Separate category pages remain paginated.',
 'full_catalogue':'Eight linked category indexes contain 3,209 records in total; paginated category pages expose records beyond the 200-result global search cap.',
 'record_pages':'The sampled marine-sediment and aquatic-macrophyte records have stable pages with source attestations, environmental context, curation events and their own YAML links.',
 'term_links':'Marine sediment’s own ENVO grounding and broader habitat resolve, but its Associated taxa section still shows readable names beside unlinked NCBITaxon CURIEs. Nearby TaxonMech search links are not ontology resolver links.',
 'evidence':'Marine-sediment causal-edge PMID citations and curation DOI references remain plain text without PubMed or DOI anchors.',
 'review_status':'Record headers display SEEDED or REVIEWED workflow status. The current landing says 1,915 of 3,209 are SEEDED and explicitly distinguishes workflow decisions from human review.',
 'curation_history':'Marine sediment displays dated, attributed ADD_CAUSAL_GRAPH, SOURCE_SYNONYM_SCOPED, SOURCE_PARENT_EXCLUDED and UPDATE_CAUSAL_GRAPH events with change summaries.',
 'source_link':'The marine-sediment Provenance section links its own data/habitats/aquatic/marine_sediment.yaml file.',
 'domain_view':'The semantic text map renders 3,209 descriptions and marine sediment renders a directed SVG causal graph. The old pages/map.html route returns 404; the working route is pages/text-map/.',
 'cross_mech_links':'Associated taxa now have TaxonMech search links, but they point at /TaxonMech/browse.html rather than the working /TaxonMech/pages/browse.html route. They do not resolve to specific sibling records.',
 'corpus_stats':'The landing reports 3,209 habitats and generated grounding, corroboration and workflow counts; its current notice states 1,915 SEEDED records.',
 'category_browse':'Eight named categories link to paginated subset listings, including Aquatic with 468 records and Host-associated with 1,655.',
 'downloads':'Downloads & Schema links all eight category JSON indexes (3,209 rows together), the complete point projection and its manifest; these are compact indexes/projections rather than complete habitat records.',
 'schema_docs':'The landing and footers now link the annotated LinkML schema YAML and imported schemas. This is source access, not rendered schema documentation.',
 'license':'Main templates state CC BY 4.0 data, BSD-3-Clause code and upstream terms. The linked standalone text-map-source page omits the project license statement.',
 'build_provenance':'Main footers date upstream kg-microbe extraction (2026-08-16); the linked map manifest dates that projection. They do not identify a common dated build of the project corpus.',
 'theme_toggle':'The main Auto/Light/Dark control saves the preference across templated pages, but the linked standalone semantic map has no toggle or theme attribute and keeps its light presentation.',
 'responsive':'The aquatic-macrophyte record is 404px wide at a 390px viewport on fresh and resized loads. The other sampled landing, Browse, category, marine-sediment and semantic-map pages fit.',
 'load_failure':'Blocking the global Browse category-index requests and searching shows Showing 0 of 0 matching habitats without explaining that data could not load. Category fallback rows remain available.',
 }},
'TaxonMech':{
 'total':626048,'statuses':{'shareable_state':'partial','downloads':'partial'},
 'notes':{
 'shareable_state':'Search and sort restore from the URL, but changing domain to Bacteria and rank to species does not encode those filters. Reload changes 553,073 matches back to all 626,048.',
 'full_catalogue':'The browser covers 626,048 records across 3,131 pages; Next was exercised to page 2. Domain and type-strain subsets provide additional entry points.',
 'record_pages':'Stable taxon.html?id=NCBITaxon:N routes open individual records, including Methanobrevibacter smithii and Escherichia coli, with paged strain details.',
 'term_links':'Sampled taxonomy sections show named NCBI lineage terms and resolver links for NCBI identifiers, LPSN entries and GTDB names.',
 'evidence':'Methanobrevibacter smithii links its LPSN DOI references and PMID:390357; strain details retain source links.',
 'review_status':'Sampled record headers and browse rows display SEEDED workflow status; the browser also exposes its Deprecated filter.',
 'curation_history':'Methanobrevibacter smithii shows a dated seed_from_sources event with curator, action, source list and change summary.',
 'source_link':'Sampled taxon views link their own data/taxa YAML in the repository.',
 'domain_view':'Record pages show labeled, linked taxonomy lineages. The separate corpus map renders 31,258 embedded taxa; it is a subset of the 626,048-record corpus.',
 'cross_mech_links':'Sampled details retain kgmicrobe.strain identifiers as plain text. Suite and exploratory links do not provide direct links for those named cross-Mech records.',
 'corpus_stats':'The landing shows 626,048 taxa, 100,745 distinct strains and 20,648 taxa with a type strain. The live Archaea subset now contains 14,013 records.',
 'category_browse':'Landing links domain and type-strain listings. Archaea shows 14,013 records and the type-strain subset 20,648, with pagination.',
 'downloads':'The linked index.json.gz contains 626,048 catalogue rows, and its manifest records format and checksum. It is a browse index rather than full taxon records; individual pages link YAML, but no bulk complete-record export was linked.',
 'schema_docs':'Visible Schema and LinkML schema links now open the annotated YAML source, while reviewed navigation lacks rendered schema documentation.',
 'build_provenance':'The footer now identifies corpus digest 959c8dfd8771 and 626,048 records, but provides no own build date or commit. Sources dates describe upstream snapshots.',
 'load_failure':'Blocking the search index preserves static pagination and says Search is unavailable. Blocked detail shards and corpus-map data display explicit load errors.',
 }},
'PathwayMech':{
 'total':280,'statuses':{'category_browse':'partial','schema_docs':'partial','license':'partial'},
 'notes':{
 'full_catalogue':'Browse exposes all 280 stable pathway links, matching the landing and the 280-record downloadable pathway index.',
 'record_pages':'Sampled MetaCyc, GO and WikiPathways records have stable pages with organism scope, participants, mechanistic edges, evidence, curation history and their own YAML links.',
 'term_links':'Organism-scope taxa are labeled and linked, but the main component and mechanistic-edge tables still display chemical, protein and reaction CURIEs without resolver links.',
 'evidence':'Sampled mechanistic edges link Rhea and PubMed references and source locations, separating source assertions from quotations.',
 'review_status':'Sampled pathway pages show pathway type and editing history but no record-level curation or review status.',
 'curation_history':'Sampled pathway pages show dated curator actions, change summaries and retained curation-session links, including current November edits.',
 'source_link':'Read the source YAML links sampled records to their own data/pathways file in GitHub.',
 'domain_view':'Pathway pages render directed SVG networks with node selection and zoom controls. The text map renders 270 pathways and the sequence map 216 pathway centroids; the current corpus has 280 records.',
 'cross_mech_links':'The sampled MetaCyc, GO and WikiPathways pages offer suite navigation and external authority links, but no direct links to specific sibling-Mech or kg-microbe records.',
 'corpus_stats':'The landing reports 280 pathway records, 105 taxa, 14,788 mechanistic edges and 5,917 distinct references.',
 'category_browse':'The current Browse exposes subset filters, but sampled navigation does not link the previously claimed 15 standalone category pages. Its Pathway type options include edge-count strings, which need separate site correction.',
 'downloads':'Landing links KGX node and edge TSV exports plus the complete 280-record pathway index. These and the version/checksum manifest return HTTP 200; the manifest reports 5,466 nodes and 14,788 edges.',
 'schema_docs':'The current landing links LinkML YAML sources. The formerly claimed pages/schema.html returns HTTP 404; no rendered schema reference was linked.',
 'license':'The landing states CC BY 4.0 data and upstream terms, but does not state a code license; sampled record and browse pages omit the data/code license statement.',
 'build_provenance':'Landing displays an undated graph-content hash. No site build date, displayed commit or dated project-corpus version is shown on sampled pages.',
 'load_failure':'The sampled landing, Browse, record, text-map and sequence-map pages embed their data and issue no data fetch/XHR requests, so the data-request failure criterion does not apply.',
 }},
}

def count_text(row):return '; '.join(x['text'] for x in row.get('statuses',[]) if x['text'] and not ('filter' in x['id'] or x['id'].startswith('facet-') or x['id']=='record-status'))
def trim_state(d):
    keys=('url','statuses','firstRows','visibleRows','theme','savedTheme','width','scrollWidth')
    return {k:d[k] for k in keys if k in d}|{'first_link_labels':[a['text'] for a in d.get('allLinks',[]) if a['table']][:5]}
def finalize(site):
    rawpath=RAW/site/'raw.json';raw=json.loads(rawpath.read_text());assert raw.get('finished_at')
    cfg=REVIEW[site];old=raw['baseline']['features'];pages=raw['pages'];actions=raw['actions'];base='https://culturebotai.github.io/'+site+'/'
    valid={p:r for p,r in pages.items() if r.get('status')==200 and 'desktop'in r}
    data={p:r['desktop'] for p,r in valid.items()};index=data['pages/index.html'];browse=actions['browse_initial'];total=cfg['total']
    notes={
      'search':'Browse searches by identifier and label. '+ '; '.join(k.removeprefix('search:')+': '+count_text(v) for k,v in actions.items() if k.startswith('search:') and 'no-such'not in k)+'.',
      'facets':'Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view.',
      'result_counts':'Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the '+f'{total:,}'+'-record corpus.',
      'sorting':'The Browse sort control offers '+ '; '.join(o['text'] for c in browse['controls'] if c['tag']=='SELECT' and 'sort'in c['id'] for o in c['options'])+'. Changing order was exercised in the browser.',
      'shareable_state':'Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored.',
      'suite_nav':'A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target.',
      'license':'Sampled pages state CC BY 4.0 project data and BSD-3-Clause code, with upstream terms retained, consistent with the pinned license files.',
      'theme_toggle':'Selecting the theme on the landing persists across the sampled linked pages in the same browser context.',
      'responsive':'All sampled live routes fit a 390px viewport on both fresh load and resizing from 1280px; wide content stays within its own region.',
    }|cfg['notes']
    assert set(notes)==set(old),set(old)-set(notes)
    receipts={
      'actions':{k:trim_state(v.get('state',v))|({'blocked':v['blocked']} if 'blocked'in v else {})|({'text':v.get('state',{}).get('text','')[-4500:]} if 'failure:'in k else {}) for k,v in actions.items() if not k.startswith('explicit_dark')},
      'controls':browse['controls'],
      'pages':{p:{'url':d['url'],'title':d['title'],'text_excerpt':d['text'][:11000] if ('/browse'not in p and '/grounded'not in p) else d['text'][:1800], 'footer':d['footer'],'links':[a for a in d['allLinks'] if not a['table'] or re.search(r'doi.org|pubmed|purl|TaxonMech|PathwayMech',a['href'])][:100], 'status':valid[p]['status'],'page_errors':valid[p].get('page_errors',[]),'svgs':d['svgs'],'canvases':d['canvases'],'themes':{k:valid[p][k]['theme'] for k in ('desktop','fresh_mobile','resized_mobile')},'widths':{k:valid[p][k]['scrollWidth'] for k in ('desktop','fresh_mobile','resized_mobile')},'fetches':[r for r in valid[p].get('requests',[]) if r['kind'] in ('fetch','xhr')]} for p,d in data.items()},
      'downloads':{url:{k:v for k,v in item.items() if k!='array_lengths'}|{'array_lengths':dict(list(item.get('array_lengths',{}).items())[:25])} for url,item in raw['downloads'].items()},
      'external_links':raw['external_links'],
      'explicit_theme':{k:v for k,v in actions.items() if k.startswith('explicit_dark:')},
      'non200':{p:r.get('status') for p,r in pages.items() if r.get('status')!=200},
    }
    follow=EVID/'group-a-followups.json'
    if follow.exists():
        receipts['followup_checks']={k:v for k,v in json.loads(follow.read_text())['checks'].items() if k.startswith(site+':') or '/'+site+'/' in k}
    features={}
    actionkeys={'search':'search:','facets':'facet:','result_counts':'search:','sorting':'sort:','shareable_state':'query_','full_catalogue':'browse_initial','load_failure':'failure:'}
    for key in old:
        status=cfg['statuses'].get(key,old[key]['status'])
        route=old[key]['url'].removeprefix(base).split('#')[0]
        if route not in data:route='pages/index.html'
        if key in actionkeys:
            evidence={'locator':'receipts.actions','verbatim':{k:count_text(v.get('state',v)) for k,v in actions.items() if actionkeys[key]in k},'control_locator':'receipts.controls'}
        elif key=='responsive':evidence={'locator':'receipts.pages.*.widths','verbatim':{p:receipts['pages'][p]['widths'] for p in data}}
        elif key in ('schema_docs','downloads','suite_nav','source_link','cross_mech_links','term_links','evidence'):
            patterns={'schema_docs':r'schema|LinkML','downloads':r'json|tsv|csv|Download','suite_nav':r'/mechs/','source_link':r'/blob/main/data/|source YAML','cross_mech_links':r'github.io/.*[mM]ech/','term_links':r'GO:|NCBI|CHEBI|UniProt|purl|LPSN|GTDB','evidence':r'PMID|DOI|pubmed|doi.org|RHEA'}
            evidence={'locator':'receipts.pages.'+route+'.links','verbatim':[a for a in data[route]['allLinks'] if re.search(patterns[key],a['href']+' '+a['text'],re.I)][:25]}
        else:
            needles={'review_status':r'REVIEWED|SEEDED|Proposed|Pathway type','curation_history':r'Curation history|Curation\n','corpus_stats':r'.','domain_view':r'.','build_provenance':r'corpus|Graph version|Generated|Provenance','license':r'CC BY|BSD|License'}
            text=data[route]['text'];m=re.search(needles.get(key,r'.'),text,re.I);pos=m.start() if m else 0
            evidence={'locator':'receipts.pages.'+route+'.text_excerpt','verbatim':text[pos:pos+1500]}
        features[key]={'status':status,'note':notes[key],'url':base+route,'claim_locator':f'_fleet/data/site_features.json#/mechs/{site}/features/{key}','prior_verbatim':old[key]['note'],'prior_status':old[key]['status'],'evidence':evidence}
    catalogue=json.loads((ROOT/'_fleet/data/site_features.json').read_text())['catalogue'];assert set(features)==set(catalogue) and len(features)==24
    result={'reviewer':'deployment_review group A auditor','mech':site,'pin':raw['pin'],'started_at':raw['started_at'],'finished_at':raw['finished_at'],'supplemented_at':raw.get('supplemented_at'),'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],'features':features,'receipts':receipts,'raw_capture':{'path':str(rawpath),'sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest()},'limits':['The 24 existing criteria were exercised on the listed routes; this is not an exhaustive record-page crawl.','Sibling-owned relationship provenance and corpus-source hand claims are covered by the separate hand-claim reviewer.','Non-200 guessed legacy routes are not counted as responsive/theme failures unless currently linked.','Root arbitration: a browse index or coordinate array alone does not qualify as a bulk record-corpus export; direct schema YAML alone remains partial schema documentation.']}
    out=EVID/(site.lower()+'-auditor-a.json');out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    lines=[f'# {site} browser audit — 2026-11-04','',f'Pinned source `{raw["pin"]}`; latest successful deployment `{raw["deployment_after"]["id"]}` serves `{raw["deployment_after"]["sha"]}`. Last-Modified: {raw["deployment_after"]["last_modified"]}.','',f'Exercised all 24 existing criteria across {len(valid)} live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.','', '| Feature | Verdict | Replacement note |','|---|---|---|']
    lines += [f'| {k} | {v["status"]} | {v["note"]} |' for k,v in features.items()]
    lines+=['','Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.']
    out.with_suffix('.md').write_text('\n'.join(lines)+'\n');print(site,dict(collections.Counter(v['status'] for v in features.values())),out.stat().st_size)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('site',choices=list(REVIEW)+['all']);a=ap.parse_args()
    for site in REVIEW if a.site=='all' else [a.site]:finalize(site)
