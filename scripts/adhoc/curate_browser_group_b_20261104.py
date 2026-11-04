#!/usr/bin/env python3
"""Build reviewable 24-feature ledgers from independently collected Nov4 observations.
Inputs: completed group-B browser receipts and the existing catalogue. Outputs:
seven compact auditor ledgers/Markdown reports for the refresh PR. 2026-11-04.
No website source or catalogue is edited; every replacement remains a proposal.
"""
import json
import re
from pathlib import Path
from audit_browser_group_b_20261104 import GROUP, OUT, now
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')

def captured_path(name):
    """Full archived captures remain reproducible after PR evidence compaction."""
    archived=ARCHIVE/name
    return archived if archived.exists() else OUT/name

# Decisions below are human-reviewed against each captured page and action.
COUNTS={'CultureMech':15915,'MediaIngredientMech':2956,'CommunityMech':485,'ProteinTraitsMech':429421,'DUFMech':8296,'CMMMech':678,'AIMech':1929}
OVERRIDES={
'CultureMech':{
 'sorting':('missing','The recipe browser has no reader-facing sort selector, sort button or sortable table. Its facet lists are internally ordered, which does not provide record sorting.'),
 'full_catalogue':('partial','The main browser covers 15,915 normalized recipes. The landing also counts 6,325 merged recipes, whose separate pages/index.html listing is outside the main browser navigation.'),
 'record_pages':('present','Normalized and merged recipes have stable individual URLs; sampled normalized pages display composition, organisms and provenance.'),
 'term_links':('partial','Ingredient and organism terms have labels and resolver links, but mediadive.medium:1399 on recipe 000252 is shown as source link unavailable.'),
 'evidence':('partial','Sampled records link formal DOI references, but source URLs embedded in Notes remain plain text.'),
 'review_status':('missing','Sampled recipe pages do not state record curation or review status. The separate growth-evidence report does not provide a status for each recipe.'),
 'curation_history':('present','Recipe Provenance tables show timestamps, curators or scripts, actions and notes.'),
 'source_link':('partial','The source YAML path appears as plain text in sampled record footers rather than as a link to that file.'),
 'domain_view':('present','Text and chemically derived media maps and an ingredient map render interactive corpus views.'),
 'cross_mech_links':('present','Recipe 015438 links CommunityMech:000064 to the specific pinned Soybean_N_Fixation_sfSynCom.yaml record.'),
 'corpus_stats':('present','The landing shows 15,915 normalized recipes, 6,325 merged recipes and five populated categories.'),
 'category_browse':('partial','Categories are browser facets and headed sections on long indexes; the landing does not link separate category pages.'),
 'downloads':('partial','The landing links JSON and TSV indexes covering 15,915 normalized recipes, but these omit full compositions and record evidence; a complete bulk record export is not linked.'),
 'schema_docs':('present','The linked app/schema.html guide documents 49 classes and 33 enumerations, including MediaRecipe and growth-evidence structures.'),
 'license':('partial','The reviewed landing, schema and record footers identify BSD-3-Clause but do not consistently distinguish the project data license from the code license.'),
 'build_provenance':('missing','The reviewed landing, browser and recipe footers do not state a site build, deployment revision or dated corpus version; recipe curation dates describe individual events.'),
 'theme_toggle':('partial','Dark mode persists through the core browser, indexes, maps and records. The linked growth-evidence report has no toggle and does not adopt the saved choice.'),
 'responsive':('partial','Core reviewed pages and the normalized index fit 390px. The linked growth-evidence report still widens the document to 520px.'),
 'load_failure':('present','Blocking data.js shows Recipes could not be loaded and a retry control rather than a zero-record catalogue.')},
'MediaIngredientMech':{
 'record_pages':('present','Mapped, rejected and unmapped ingredients have stable record URLs; sampled NaCl, GYPS and glucose pages open with mapping, evidence and history sections.'),
 'term_links':('present','Sampled ingredient groundings display names with resolver links for ontology terms and component identities; local registry identities can remain plain text.'),
 'evidence':('present','NaCl and GYPS expose linked PMID, DOI and source-URL references in their evidence sections.'),
 'review_status':('present','Record headers state mapping status and quality. Runtime metadata reports 2,611 MAPPED, 262 UNMAPPED, 82 REJECTED and one AMBIGUOUS ingredient.'),
 'curation_history':('present','Sampled ingredient pages show Curation history tables with timestamp, curator, action and change details.'),
 'source_link':('partial','Sampled record footers name data/ingredients/...yaml as plain text; their anchors do not link that individual YAML source.'),
 'domain_view':('present','Text and chemical embedding maps render, and sampled records display role/partonomy diagrams. Embedding coverage is separate from the 2,956-record catalogue total.'),
 'cross_mech_links':('present','GYPS links CultureMech:002799 to its individual normalized recipe from the related-recipe and comparison-evidence sections.'),
 'corpus_stats':('present','Runtime landing tiles show 2,956 ingredients, 2,611 mapped and 88% coverage; the linked catalogue metadata distinguishes all four mapping statuses.'),
 'category_browse':('partial','The record index has identifier-prefix sections, while the main browser offers property filters; these do not form standalone category pages.'),
 'downloads':('partial','The landing links catalogue JSON and CSV covering all 2,956 ingredients, but they contain mapping/search fields rather than complete records with components, evidence and history.'),
 'schema_docs':('present','The visible schema reference links rendered class, slot, enum and type documentation, including schema/classes-IngredientRecord.html.'),
 'license':('present','The landing and sampled record footers distinguish CC BY 4.0 project data from BSD-3-Clause code.'),
 'build_provenance':('present','Generated timestamps and a linked build receipt identify the current record build, including NaCl at 2026-11-04T07:37:37+00:00.'),
 'theme_toggle':('present','Dark selected on the landing carries across the browser, record index, sampled ingredients, maps and schema documentation.'),
 'responsive':('present','The reviewed landing, browser, record index, ingredient pages, maps and valid schema pages fit a 390px viewport.'),
 'load_failure':('present','Blocking the catalogue request displays unavailable counters, Ingredients could not be loaded and a retry control.')},
'CommunityMech':{
 'search':('partial','Name and description searches work across 485 communities, but known record identifiers CommunityMech:000134 and CommunityMech:000139 return zero matches; the corresponding named records are present.'),
 'record_pages':('present','Published communities have individual communities/<slug>.html pages; four sampled records display taxonomy, interactions, environment and growth media.'),
 'term_links':('present','Sampled taxonomy and environmental sections show readable names beside NCBITaxon, ChEBI and ENVO resolver links.'),
 'evidence':('present','Sampled interaction evidence links PMID and DOI references with supporting text and evidence-type labels.'),
 'review_status':('missing','Record headers show ecological state and evidence labels, not an overall curation or review status.'),
 'curation_history':('missing','The sampled community pages do not display curation events, even though the repository retains provenance.'),
 'source_link':('present','Each sampled record footer now links its own kb/communities YAML file on GitHub.'),
 'domain_view':('present','Community pages render interaction diagrams, and text, taxonomic and sequence embedding views open as linked domain views.'),
 'cross_mech_links':('present','Copper Biomining links Standard 9K Medium directly to CultureMech normalized recipe 003277.'),
 'corpus_stats':('present','The landing and browser report 485 published communities across 16 categories. Repository isolate records are outside this published-community count.'),
 'category_browse':('partial','Category and ecological-state subsets are filters in the browser rather than separate category pages.'),
 'downloads':('partial','Linked communities.json and TSV cover all 485 communities as catalogue summaries; they omit the complete taxon and interaction evidence stored in individual records.'),
 'schema_docs':('present','The linked schema.html page documents the CommunityMech classes, slots and ontology groundings.'),
 'license':('partial','Reviewed landing and record footers say License: BSD-3-Clause without distinguishing the project data license from the code license.'),
 'build_provenance':('missing','Reviewed pages identify the generator and source corpus but do not give a build date, deployed commit or dated corpus version.'),
 'theme_toggle':('present','Dark mode chosen on the landing persists through the browser, maps, schema and four sampled records.'),
 'responsive':('present','The reviewed landing, browser, maps, schema and four records fit a 390px viewport.'),
 'load_failure':('not_applicable','Reviewed community pages and visualizations use embedded data; no fetch or XHR catalogue request was observed to abort.')},
'ProteinTraitsMech':{
 'facets':('present','Axis, source, category and status facets combine with text search. Selecting active sites gives 1,004 records and adding racemase gives nine; controls provide a facet reset.'),
 'full_catalogue':('present','The facet manifest totals 429,421 records in 73 shards; selecting all five axes exposes the full count through paginated results.'),
 'record_pages':('present','Cold browse.html#record=CURIE routes open individual record details, including MCSA:1, METPO:1000639 and ECOD:F.3755.3.1.364.'),
 'term_links':('partial','Labeled ontology and internal record links are available, but some primary identifiers such as ECOD:F.3755.3.1.364 explicitly lack a source-entry resolver.'),
 'evidence':('present','Reference-bearing record details link PMID and DOI evidence separately from database-source links.'),
 'review_status':('present','Record details and status facets expose SEEDED, PROPOSED and REVIEWED workflow states; the runtime manifest has 39,591 REVIEWED records.'),
 'curation_history':('present','Record details show dated curation actions, curators and change summaries, including the MCSA:1 curation event.'),
 'source_link':('present','Record detail views link the record’s individual YAML path on GitHub, separately from external database-entry links.'),
 'domain_view':('present','Record views provide sequences, annotations and causal diagrams where available. The corpus map covers 344,797 current records; protein and sequence maps show 68,657 and 12,705 proteins.'),
 'cross_mech_links':('missing','Checked record views link external databases and other ProteinTraitsMech records; their main sections do not link specific sibling-Mech or kg-microbe records.'),
 'corpus_stats':('present','Runtime statistics show 429,421 records: 118,338 structure, 147,149 sequence, 392 sequence/structure, 163,527 function and 15 evolution, across 63 categories and 34 source labels.'),
 'category_browse':('partial','Landing axis/category/source links select filters in the common browser rather than standalone category pages.'),
 'downloads':('partial','The browser links facet counts and listing shards for all 429,421 records; complete detail is fetched per record, and map CSVs contain plotted points rather than the full corpus records.'),
 'schema_docs':('present','The linked schema guide explains ProteinTraitRecord, enums and causal graph fields and links its LinkML source.'),
 'license':('partial','Core pages and maps distinguish CC BY 4.0 data from BSD-3-Clause code. The linked SLC10 pilot does not state both project licenses.'),
 'build_provenance':('partial','Core pages show upstream releases and retained map coverage but no site build date or deployed revision; the embedding date is explicitly unrecorded.'),
 'theme_toggle':('partial','The injected Browse toggle works, but the landing’s existing empty theme button does not respond. The linked SLC10 pilot has no theme toggle.'),
 'responsive':('partial','Core sampled routes fit 390px, but expanding all 63 category values widens the document to 400px.'),
 'load_failure':('present','Blocked catalogue requests produce an explicit index-load failure; map requests display unavailable/error states instead of presenting zero coverage.')},
'DUFMech':{
 'full_catalogue':('present','The complete index and catalogue contain 8,296 families. The browser provides numbered pagination and links individual family pages.'),
 'record_pages':('present','Family accessions have stable families/PFxxxxx.html pages; PF04149, PF02698 and PF18141 opened successfully.'),
 'term_links':('present','Sampled family grounding shows readable names with linked Pfam and InterPro identifiers.'),
 'evidence':('present','Family views link frozen source descriptions and citations. Curated mechanism evidence is distinguished from imported descriptions and unresolved source citations.'),
 'review_status':('present','Family headers and browser rows display curation status alongside seed classification and characterization tier.'),
 'curation_history':('present','The sampled family views show retained dated curation events and reviews with attribution and outcomes.'),
 'source_link':('present','Family pages link their individual YAML at the retained source revision, plus build-local YAML and JSON copies.'),
 'domain_view':('present','Family pages display domain tracks and causal diagrams where available; linked text and protein sequence maps provide corpus views.'),
 'cross_mech_links':('present','Sampled family pages link specific retained ProteinTraitsMech records, including Pfam:PF18141; the previous claim that PF18141 was outside the scan no longer applies.'),
 'corpus_stats':('present','The landing reports 8,296 families, 8,238 with InterPro IDs, 1,906 with structures and 8,242 with AlphaFold models; seed subsets total 1,796 EX_DUF, 373 historical DUFs and 6,127 unknown candidates.'),
 'category_browse':('present','The linked category index opens distinct paginated seed-status subsets.'),
 'downloads':('present','Sources & schema and the catalogue link the complete index.json export containing all 8,296 families and retained provenance.'),
 'schema_docs':('present','The linked schema.html guide documents family records, curation, evidence, history and enums, and provides the schema source.'),
 'license':('present','Reviewed footers distinguish CC BY 4.0 project data from BSD 3-Clause code and retain third-party terms.'),
 'build_provenance':('present','Footers identify the site build, retained corpus source revision and dated frozen upstream inputs.'),
 'theme_toggle':('present','The System/Light/Dark selector persists Dark across the reviewed landing, families, categories, schema, sources and maps.'),
 'responsive':('present','Reviewed landing, sampled families, category index, sources, schema and maps fit 390px; wide tables scroll within their containers.'),
 'load_failure':('present','Blocking catalogue.json visibly reports that interactive search is unavailable while retaining static rows and pagination.')},
'CMMMech':{
 'record_pages':('present','Browse and kind/process listings link stable materials/<slug>.html pages; cobalt and akaganeite opened successfully.'),
 'term_links':('present','Sampled material identifiers and mechanism terms show readable labels with ChEBI, taxon and protein/ontology resolver links.'),
 'evidence':('present','Sampled references link DOI or source URLs, and mechanism evidence points to the corresponding references.'),
 'review_status':('missing','Record headers show material kind and criticality; these and individual evidence labels do not state overall review status.'),
 'curation_history':('present','Sampled records include Curation History tables with timestamp, curator, action and summary.'),
 'source_link':('present','Record source lines link the individual data/records YAML on GitHub.'),
 'domain_view':('present','The mechanism graph renders 654 nodes and 970 edges; the text map retains 602 material points, a subset of the 678-record catalogue.'),
 'cross_mech_links':('missing','Record sections provide cross-Mech search links and site navigation, but the sampled pages do not link specific sibling records.'),
 'corpus_stats':('present','The landing reports 678 materials, 609 mechanisms, 500 materials with mechanisms and 90 designated critical materials across six kinds.'),
 'category_browse':('present','Landing cards link six material-kind and process listings. Kind totals are 66 elements, 427 minerals, 111 secondary resources, 36 commodities, 31 primary resources and seven mineral groups.'),
 'downloads':('partial','Linked index.json covers all 678 catalogue entries but contains listing metadata and mechanism counts, not full mechanism evidence; map exports and individual YAML links are also available.'),
 'schema_docs':('partial','Visible schema links open the LinkML YAML source. The previously recorded pages/schema.html documentation URL returns 404.'),
 'license':('present','Reviewed footers separately state CC BY 4.0 data and BSD-3-Clause code, consistent with the repository license policy.'),
 'build_provenance':('present','Footers now state 678 materials, 609 mechanisms, latest curation 2026-11-04 and corpus digest 0e188cbbc0a4.'),
 'theme_toggle':('present','Dark selected on the landing carries to Browse, kind, record, text-map and graph pages.'),
 'responsive':('partial','At 390px, cobalt widens the document to 597px and akaganeite to 669px; both overflow on fresh and resized views.'),
 'load_failure':('not_applicable','Reviewed listings, records and canvas visualizations embed their data; no fetch/XHR data request was observed to abort.')},
'AIMech':{
 'record_pages':('present','Browse links static curated/<name>.html and aio/<name>.html record pages; sampled Adam, KernelPCA and TrainingStrategy pages open.'),
 'term_links':('present','Sampled accepted AIO mappings show names with linked CURIEs; AIO class pages link their ontology IRIs and labeled parent terms.'),
 'evidence':('present','Sampled curated claims link source rows and primary evidence URLs; the landing distinguishes 5,149 claims from 3,269 evidence citations.'),
 'review_status':('present','Sampled curated and imported class records show their workflow state in the record header.'),
 'curation_history':('partial','Curated pages show curator, method/model and created/updated times, but do not present an event-by-event change list; AIO pages give import provenance.'),
 'source_link':('present','Sampled records link their individual data/curated or data/aio YAML file on GitHub.'),
 'domain_view':('present','The graph renders 1,949 nodes and 4,256 edges; the text map retains 1,259 concepts, a subset of the 1,929-record catalogue.'),
 'cross_mech_links':('missing','Sampled record pages provide sibling navigation/search links rather than links to specific sibling-Mech records.'),
 'corpus_stats':('present','The landing reports 1,929 concepts (1,487 curated and 442 AIO), 5,149 curated claims and 3,269 evidence citations.'),
 'category_browse':('present','The landing links twelve curated-kind and eight AIO-branch subset pages, including 121 architectures and 61 biases.'),
 'downloads':('partial','Linked index.json covers all 1,929 concepts as listing metadata with claim/source counts; it omits complete claims and evidence. Map data and per-record YAML sources are also linked.'),
 'schema_docs':('partial','The reviewed site links LinkML YAML source files. The previously recorded pages/schema.html documentation URL returns 404.'),
 'license':('partial','Footers display CC BY 4.0 / BSD-3-Clause data and BSD-3-Clause code, but do not clearly explain which data receives each license.'),
 'build_provenance':('present','Page footers identify the project snapshot date 2026-10-24 and digest de5b593fee12, separately from upstream AIO import provenance.'),
 'theme_toggle':('present','Dark selected on the landing persists through Browse, sampled records, and both graph and text-map views.'),
 'responsive':('present','Reviewed landing, Browse, sampled records and visualizations fit a 390px viewport.'),
 'load_failure':('not_applicable','Reviewed listings, records and visualizations embed their record data; no fetch or XHR data request was observed to abort.')}
}

CONTROL_NOTES={
 'CultureMech':{
  'search':'CultureMech:000252 returns one recipe and Halophilic medium returns four, with individual recipe links.',
  'facets':'The category facet selects 14,332 bacterial recipes; combining it with Halophilic medium leaves two. Clear All restores all 15,915.',
  'result_counts':'The live count distinguishes one identifier match, four label matches, two bacterial label matches and zero for an unmatched query.',
  'shareable_state':'Search and property filters restore from the URL: Halophilic medium with category=bacterial reloads with the same two recipes.'},
 'MediaIngredientMech':{
  'search':'UNMAPPED_0196 and table salt each return one linked ingredient; CHEBI:63895 returns two of the 2,956 records.',
  'facets':'Mapping status, ontology source and mapping quality filters combine with search. AMBIGUOUS gives one record; Clear search and filters restores all 2,956.',
  'result_counts':'Showing N of 2956 ingredients changes to one for UNMAPPED_0196, two for CHEBI:63895 and zero for an unmatched query.',
  'shareable_state':'Search, status, source, quality and sort values are encoded in query parameters and restore with the same matching count after reload.'},
 'CommunityMech':{
  'facets':'Category and ecological-state filters have Clear All. BIOTECHNOLOGY selects 96 of 485 communities; reset restores all 485.',
  'result_counts':'The live count shows three matches for ANME, one for its full community name and zero for the tested canonical identifiers and unmatched query.',
  'shareable_state':'The URL retains search, category and sort; the combined BIOTECHNOLOGY/name-search selection restores the same controls and zero-match state.'},
 'ProteinTraitsMech':{
  'search':'Searching cd05137 returns one linked record; homogentisate 1,2-dioxygenase returns 16 after the relevant shards finish loading.',
  'result_counts':'Matching results are shown separately from the 429,421-record total; the active-site category plus racemase gives nine and an unmatched query gives zero.',
  'shareable_state':'A cold #cat=STRUCT_ACTIVE_SITE&q=racemase URL and its reload restore the category and search with nine matching records.'},
 'DUFMech':{
  'search':'PF04149, IPR007278 and Domain of unknown function (DUF397) each return one linked family from the 8,296-family catalogue.',
  'facets':'Seed status, characterization and curation status filters combine with search; Clear search and filters restores all 8,296 families.',
  'result_counts':'The live count shows one of 8,296 for each tested identifier/label and zero for an unmatched query.',
  'shareable_state':'Query, seed status, characterization, curation status, sort and page are retained in the URL; the exercised combined filter state restores after reload.'},
 'CMMMech':{
  'search':'CHEBI:27638 and cmmmech:copper each return one linked material; Cobalt returns 23 of 678.',
  'facets':'Kind, mechanism process and criticality filters have Clear filters. Element selects 66 records; adding bioleaching selects 15; reset restores all 678.',
  'result_counts':'The count updates to one for identifier searches, 23 for Cobalt, 15 for bioleaching elements and zero for an unmatched query.',
  'shareable_state':'Cobalt with element, bioleaching, criticality and sort selections reloads from its URL with all controls restored and one matching record.'},
 'AIMech':{
  'search':'AIMech:KernelPCA returns one linked concept and Adam returns 131 matches across the 1,929-record catalogue.',
  'facets':'Origin, concept kind and AIO branch filters have Reset. Curated selects 1,487 records and curated algorithms 1,047; Reset restores all 1,929.',
  'result_counts':'The matching count changes to one for AIMech:KernelPCA, 131 for Adam and zero for an unmatched query, separately from the 1,929 total.',
  'shareable_state':'Search, origin, kind, branch and sort are encoded in the URL; reload restores the exercised values and matching count.'}}
for _mech,_notes in CONTROL_NOTES.items():
    OVERRIDES[_mech].update({key:('present',note) for key,note in _notes.items()})

def main():
    baseline=json.loads(Path('_fleet/data/site_features.json').read_text())
    supplement_path=captured_path('group-b-supplement.json')
    supplement=json.loads(supplement_path.read_text()) if supplement_path.exists() else {}
    rows={}
    for mech in GROUP:
        path=captured_path(mech.lower()+'-browser-b.json');raw=json.loads(path.read_text())
        assert raw.get('finished_at'), mech+' unfinished'
        for url,value in supplement.get('pages',{}).items():
            if '/'+('proteintraitsmech' if mech=='ProteinTraitsMech' else mech)+'/' in url:
                raw['pages'][url]=value
        if mech=='ProteinTraitsMech':
            follow_path=captured_path('protein-query-followup.json')
            if follow_path.exists():
                follow=json.loads(follow_path.read_text())
                if follow.get('finished_at'):
                    raw['actions'].update(follow['checks'])
        if mech in supplement.get('deployment_after',{}):
            raw['deployment_after']=supplement['deployment_after'][mech]
            raw['finished_at']=supplement['finished_at']
        orig=baseline['mechs'][mech];count=COUNTS[mech];n=f'{count:,}'
        browse=orig['features']['search']['url'].split('#')[0].split('?')[0]
        bp=raw['pages'].get(browse,{})
        sorts=[o['text'] for s in bp.get('selects',[]) if s.get('selector') and 'sort' in s['selector'].lower() for o in s['options']]
        defaults={
          'search':('present',f'The labeled browser searches the {n}-record catalogue by known identifier and label; tested matches are counted and link to records.'),
          'facets':('present',f'Property filters operate on the {n}-record browser and provide a reset; combined selections and reset were exercised.'),
          'result_counts':('present',f'The matching count changes with identifier/label searches and property filters, separately from the {n}-record total.'),
          'sorting':('present','The browser offers '+', '.join(sorts)+'. Changing each option reorders the displayed results.'),
          'shareable_state':('present','Search, property-filter and available sort selections are retained in the URL and restore on reload.'),
          'full_catalogue':('present',f'The complete browser and its machine-readable export cover {n} published records; sampled record links open successfully.'),
          'suite_nav':('present','Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory.')}
        notes={**defaults,**OVERRIDES[mech]}
        assert set(notes)==set(baseline['catalogue']), (mech,set(baseline['catalogue'])-set(notes))
        features={}
        for key,(status,note) in notes.items():
            old=orig['features'][key];url=old['url']
            if key=='schema_docs' and mech in ['CMMMech','AIMech']:
                url=orig['site']
            if key=='downloads' and mech=='MediaIngredientMech':url='https://culturebotai.github.io/MediaIngredientMech/'
            page=raw['pages'].get(url) or bp
            evidence={'capture_file':str(path),'capture_locator':'pages['+repr(url)+']',
              'url':url,'headings':page.get('headings',[])[:25],'footer_excerpt':page.get('footer',''),
              'relevant_links':[l for l in page.get('links',[]) if re.search('schema|github|doi.org|pubmed|mechs/|json|csv|tsv',l['url'],re.I)][:25]}
            if key in ['search','facets','result_counts','sorting','shareable_state']:
                evidence={'url':browse,'capture_file':str(path),'capture_locator':'actions','actions':{k:{f:v.get(f) for f in ['url','counts','controls','checked','rows','first_results','error']} for k,v in raw['actions'].items() if (key=='search' and k.startswith('query:')) or (key=='sorting' and k.startswith('sort')) or (key in ['facets','result_counts','shareable_state'] and k in ['combined_query','restored','reset','facet:first','active_site_query','active_site_reviewed'])}}
            elif key=='responsive':evidence={'url':url,'capture_file':str(path),'capture_locator':'pages[*].fresh_390 / resized_390','widths':{u:{'fresh':v.get('fresh_390'),'resized':v.get('resized_390')} for u,v in raw['pages'].items() if v.get('http_status') in (200,None)}}
            elif key=='theme_toggle':evidence={'url':url,'capture_file':str(path),'capture_locator':'pages[*].theme / saved_theme','themes':{u:{'theme':v.get('theme'),'saved':v.get('saved_theme')} for u,v in raw['pages'].items() if v.get('http_status') in (200,None)}}
            elif key=='load_failure':evidence={'url':url,'capture_file':str(path),'capture_locator':'failure_cases','cases':{u:{'aborted':v.get('aborted',[]),'excerpt':v.get('state',{}).get('body','')[:1800]} for u,v in raw.get('failure_cases',{}).items()}}
            elif key=='downloads':evidence['bulk']=raw.get('bulk',{})
            elif key in ['corpus_stats','domain_view']:
                evidence['excerpt']=page.get('body','')[:1700]
            features[key]={'status':status,'note':note,'url':url,'evidence':evidence}
            if key=='downloads':features[key]['evidence']['field_inventory']='group-b-bulk-inventory.json::'+mech
            if mech=='ProteinTraitsMech' and key in ['theme_toggle','responsive','record_pages','curation_history','domain_view','evidence','source_link','term_links']:
                features[key]['evidence']['supplement']=str(supplement_path)
                if key in ['theme_toggle','responsive']:
                    features[key]['evidence']['checks']={k:v for k,v in supplement.get('checks',{}).items() if k.startswith('protein_')}
        changes=[{'locator':f'_fleet/data/site_features.json::mechs.{mech}.features.{k}',
                  'before':orig['features'][k],'replacement':{x:v[x] for x in ['status','note','url']},
                  'evidence':'features.'+k+'.evidence'} for k,v in features.items()]
        ledger={'mech':mech,'reviewer':'central_directory group B auditor','pin':raw['pin'],
          'started_at':raw['started_at'],'finished_at':raw['finished_at'],'deployment_before':raw['deployment_before'],
          'deployment_after':raw['deployment_after'],'features':features,'proposed_changes':changes,
          'limits':['Representative route audit, not an HTTP crawl of every record. Complete counts are listing/export counts where stated.',
                    'Independent skeptic must verify all changed verdicts before editor applies them.',
                    'Supplemental cold-route, theme, download and schema evidence is recorded in group-b-supplement.json.']}
        dest=OUT/(mech.lower()+'-auditor-b.json');dest.write_text(json.dumps(ledger,indent=2)+'\n')
        from email.utils import parsedate_to_datetime
        from datetime import datetime
        dep=raw['deployment_after']
        assert dep['state']=='success' and parsedate_to_datetime(dep['last_modified']) >= datetime.fromisoformat(dep['created_at'].replace('Z','+00:00')), mech+' deployment proof incomplete'
        rows[mech]={'site':orig['site'],'repository':orig['repository'],'deployed_revision':dep['sha'],
          'checked_on':'2026-11-04','scope':'All 24 catalogue features re-exercised on the served site, with representative records, control actions, narrow views and request-failure checks; corpus pin and served deployment remain distinct.',
          'features':{k:{x:v[x] for x in ['status','note','url']} for k,v in features.items()}}
        lines=['# '+mech+' website audit — 2026-11-04','',f"Observed deployment `{raw['deployment_after']['sha']}`; corpus pin `{raw['pin']}`.",'','| Feature | Verdict | Proposed note |','|---|---|---|']
        lines += ['| '+k+' | '+v['status']+' | '+v['note'].replace('|','/')+' |' for k,v in features.items()]
        lines += ['','Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.']
        dest.with_suffix('.md').write_text('\n'.join(lines)+'\n')
        print(mech, len(features), str(dest))
    (OUT/'group-b-proposed-rows.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
