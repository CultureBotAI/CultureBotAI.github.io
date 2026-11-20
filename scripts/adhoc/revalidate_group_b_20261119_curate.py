#!/usr/bin/env python3
"""Produce reviewed Group B feature proposals from Nov19 live receipts.

Inputs: retained primary/supplement/controls JSON and explicit reviewed notes.
Outputs: proposals.json and evidence.json under the owned Group B directory.
Serves the November 19 feature-only PR; does not edit the shared catalogue.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'_fleet/reviews/site-features-20261119/group-b'
NOTES={
 'DUFMech':{
 'search':'present|PF04149, IPR007278 and Domain of unknown function (DUF397) each return one linked family from 8,296.',
 'facets':'present|Seed, characterization and curation filters combine with search; the exercised selections give 1,796 then 127 families, and reset restores 8,296.',
 'result_counts':'present|Matching counts change between one, zero, filtered subsets and the separate 8,296-family total.',
 'sorting':'present|Protein count, accession, family name and structure-count sorts change the leading family rows.',
 'shareable_state':'present|A cold URL and reload preserve search, seed, characterization, curation and sort selections; reset clears them.',
 'full_catalogue':'present|The complete catalogue and family index each contain 8,296 families; the listing exposes 166 numbered pages and individual family links.',
 'record_pages':'present|PF04149, PF02698 and PF18141 have stable, populated families/PFxxxxx.html pages.',
 'term_links':'present|Sampled family grounding displays readable Pfam and InterPro labels with resolver links.',
 'evidence':'present|Sampled family pages link source descriptions and references, distinguishing imported provenance from curated functional evidence.',
 'review_status':'present|Family headers and browser rows distinguish curation status, seed status and characterization.',
 'curation_history':'present|PF04149 displays dated, attributed curation events and retained review outcomes; uncurated samples explicitly disclose missing events.',
 'source_link':'present|Sampled family pages link their individual YAML at a retained source revision and offer build-local YAML/JSON copies.',
 'domain_view':'present|Family domain tracks and causal content accompany loaded text and sequence maps; the maps show 8,296 families and 634 proteins respectively.',
 'cross_mech_links':'present|Sampled family pages link specific retained ProteinTraitsMech records, including PF04149 and PF02698.',
 'corpus_stats':'present|Landing counts show 8,296 families, 8,238 with InterPro IDs, 1,906 with structures and 8,242 with AlphaFold models.',
 'category_browse':'present|The category index links distinct paginated seed-status subsets: 1,796 former DUFs, 373 historical DUFs and 6,127 unknown candidates.',
 'suite_nav':'present|Visible All Mech projects links appear on the reviewed landing, families, categories, schema, sources and maps.',
 'downloads':'present|The linked index.json export contains all 8,296 families with retained metadata and provenance; individual family exports are also linked.',
 'schema_docs':'present|Sources links the rendered family-schema guide describing records, evidence, curation and history.',
 'license':'present|Reviewed footers distinguish CC BY 4.0 project data and BSD 3-Clause code, with third-party terms retained.',
 'build_provenance':'present|Reviewed footers identify site build c8350f3d911e6c4b, corpus source ea54567e804a and dated frozen inputs.',
 'theme_toggle':'present|The System/Light/Dark selector carries Dark through reviewed family, category, schema, source and map routes.',
 'responsive':'present|All nine reviewed routes fit 390px on resized and fresh loads; sampled screenshots confirm readable wrapped navigation.',
 'load_failure':'present|Blocked catalogue data visibly falls back to a static paginated catalogue with an unavailable-search explanation; blocked map data shows an error, and reload recovers.'},
 'CultureMech':{
 'search':'present|CultureMech:000252 returns one linked recipe and Halophilic medium returns four from 15,915 normalized recipes.',
 'facets':'present|The bacterial category selects 14,332 recipes, combined Halophilic medium search leaves two, and Clear All restores 15,915.',
 'result_counts':'present|The count changes to one identifier match, four label matches, two category/label matches and zero for an unmatched query.',
 'sorting':'missing|The main browser has no reader-facing record sort selector, sort button or sortable table.',
 'shareable_state':'present|Cold navigation and reload restore the Halophilic medium search plus bacterial category with the same two recipes.',
 'full_catalogue':'partial|The main browser and linked export cover 15,915 normalized recipes. The landing also counts 6,325 merged recipes, whose separate pages/index.html is not linked from its navigation.',
 'record_pages':'present|Sampled normalized recipes have stable pages with composition, organisms and provenance; normalized and merged indexes expose individual record links.',
 'term_links':'partial|Ingredients and organisms have labeled resolver links, but recipe 000252 still displays mediadive.medium:1399 as source link unavailable.',
 'evidence':'partial|Sampled recipes link formal DOI references while source URLs embedded in Notes remain plain text.',
 'review_status':'missing|Sampled recipe pages do not state an overall curation or review status; the separate growth-evidence report is not a per-record workflow status.',
 'curation_history':'present|Recipe Provenance tables display timestamps, curators or scripts, actions and notes.',
 'source_link':'partial|Sampled record footers name their individual YAML path as plain text and link the repository rather than that file.',
 'domain_view':'present|Loaded text, media and ingredient maps provide corpus views; retained coordinate coverage is distinguished from current recipe counts.',
 'cross_mech_links':'present|Recipe 015438 links CommunityMech:000064 directly to the retained Soybean_N_Fixation_sfSynCom.yaml record.',
 'corpus_stats':'present|The landing displays 15,915 normalized records, 6,325 merged records and five populated categories.',
 'category_browse':'partial|Categories are main-browser facets and headed index sections; the landing does not link separate category pages.',
 'suite_nav':'present|Visible suite-directory links appear in reviewed core navigation and record footers.',
 'downloads':'partial|Linked JSON/TSV indexes cover 15,915 normalized recipes but omit full composition and evidence; complete bulk records are not linked.',
 'schema_docs':'present|The linked app/schema.html guide documents MediaRecipe, growth-evidence classes and enumerations.',
 'license':'partial|Reviewed core footers state BSD-3-Clause without separately identifying project data and code licenses; the growth-review and maps omit that distinction.',
 'build_provenance':'missing|Reviewed core pages identify generators and recipe provenance but do not state a site build date, deployment revision or dated project-corpus version.',
 'theme_toggle':'partial|Dark persists through core browser, indexes, maps and records; the linked growth-evidence report has no toggle and ignores the saved choice.',
 'responsive':'partial|Core reviewed routes fit 390px, but pages/media_growth_review.html remains 520px wide on both fresh and resized loads.',
 'load_failure':'present|Blocking browser data.js shows Recipes could not be loaded with a retry control; unblocking and reloading restores 15,915 recipes.'},
 'MediaIngredientMech':{
 'search':'present|UNMAPPED_0196 and table salt each return one linked ingredient; CHEBI:63895 returns two from 2,956.',
 'facets':'present|Status, ontology source and mapping quality combine with search; AMBIGUOUS selects one record and reset restores all 2,956.',
 'result_counts':'present|The matching count changes to one, two, zero and filtered subsets separately from the 2,956-ingredient total.',
 'sorting':'present|Name ascending/descending, media count, occurrence count and synonym count reorder the leading records.',
 'shareable_state':'present|Cold URL navigation and reload preserve the exercised query, mapping status, source, quality and sort selections.',
 'full_catalogue':'present|The browser, record index and linked data/ingredients.json cover 2,956 ingredients with individual record links.',
 'record_pages':'present|NaCl, GYPS and rejected glucose have stable, populated individual record pages with mapping, evidence and history.',
 'term_links':'present|Sampled grounding and component sections show readable labels beside ontology resolver links; local registry identities remain literal identifiers.',
 'evidence':'partial|PMID and DOI links work in sampled sections, but GYPS material-component evidence leaves Bergey doi:10.1002/9781118960608.gbm00618 as plain text (existing issue 888).',
 'review_status':'present|Record headers expose mapping status and quality; runtime metadata distinguishes 2,611 MAPPED, 262 UNMAPPED, 82 REJECTED and one AMBIGUOUS record.',
 'curation_history':'present|Sampled records show dated curation events with curator, action, resulting status and change details.',
 'source_link':'partial|Sampled record footers name individual data/ingredients YAML paths but do not link those files.',
 'domain_view':'present|The text and KG embedding views load 2,872 and 2,337 plotted ingredients; these are explicit subsets of the 2,956-record catalogue.',
 'cross_mech_links':'present|GYPS links CultureMech:002799 directly to the corresponding normalized recipe.',
 'corpus_stats':'present|Landing tiles show 2,956 ingredients, 2,611 mapped and 88% coverage, matching runtime catalogue metadata.',
 'category_browse':'partial|Identifier-prefix sections and browser facets expose subsets without standalone linked category pages.',
 'suite_nav':'present|Visible All Mech projects links appear on reviewed landing, browser, records, maps and schema routes.',
 'downloads':'partial|Linked catalogue JSON/CSV covers all 2,956 ingredients but contains search/mapping fields, not complete evidence, component and history records.',
 'schema_docs':'present|The visible schema index links rendered class, slot, enum and type documentation, including IngredientRecord.',
 'license':'partial|Landing and sampled record pages distinguish CC BY 4.0 data and BSD-3-Clause code, but browser, maps and schema pages omit these statements; the record index states only CC BY 4.0.',
 'build_provenance':'present|The record index and individual records display generated timestamps on 2026-11-17 and link a SHA-256 build receipt.',
 'theme_toggle':'present|Dark selected on the landing carries through the reviewed browser, record index, ingredients, maps and schema documentation.',
 'responsive':'present|Reviewed landing, browser, record index, ingredient pages, maps and schema documentation fit 390px on fresh and resized loads.',
 'load_failure':'present|Blocking catalogue or KG-map JSON displays an explicit error with retry; ordinary reload after unblocking restores data.'},
 'CMMMech':{
 'search':'present|CHEBI:27638 returns one linked cobalt record and Cobalt returns 24 of the current 713 materials.',
 'facets':'present|Kind, mechanism and criticality filters combine with search; elements give 66, adding bioleaching gives 15, and reset restores 713.',
 'result_counts':'present|Matching counts update for identifier, label, unmatched query and property filters separately from 713 total materials.',
 'sorting':'present|Name, mechanism count, organism count, kind and criticality sorts reorder the visible material cards.',
 'shareable_state':'present|Cold navigation and reload restore the combined Cobalt query, element/bioleaching/criticality facets and sort with one match.',
 'full_catalogue':'present|Browse and linked index.json cover 713 materials; record cards link individual pages and kind listings expose subsets.',
 'record_pages':'present|Cobalt and akaganeite open stable, populated materials/<slug>.html pages with mechanisms, references and curation history.',
 'term_links':'present|Sampled material identities and mechanism terms display readable labels with chemical, taxon and protein resolver links.',
 'evidence':'present|Sampled reference sections link DOI/source URLs and mechanism evidence points to those reference records.',
 'review_status':'missing|Record headings show material kind and criticality, but do not display an overall record-review status.',
 'curation_history':'present|Sampled material pages display Curation History tables with timestamps, curators, actions and summaries.',
 'source_link':'present|Sampled source lines link each record’s individual data/records YAML on GitHub.',
 'domain_view':'present|The linked mechanism network and retained material embedding map render with populated counts; records include causal content where supplied.',
 'cross_mech_links':'missing|Sampled records expose sibling-site navigation and searches but do not link specific sibling records in their main sections.',
 'corpus_stats':'present|The landing now reports 713 materials and 609 mechanisms, with generated material-kind and criticality counts.',
 'category_browse':'present|Landing cards link material-kind and process subset pages; the Minerals listing opens populated records.',
 'suite_nav':'present|Visible All Mech projects links appear on reviewed landing, browse, kind, record and visualization pages.',
 'downloads':'partial|Linked index.json contains all 713 listing summaries and mechanism counts; full mechanism evidence remains in per-record source files.',
 'schema_docs':'partial|Visible schema links open LinkML YAML source; pages/schema.html still returns 404 rather than rendered schema documentation.',
 'license':'present|Reviewed generated footers separately state CC BY 4.0 data and BSD-3-Clause code, consistent with repository license files.',
 'build_provenance':'present|Generated footers identify 713 materials, 609 mechanisms, latest curation 2026-11-11 and corpus digest ca4e8e5f93ec.',
 'theme_toggle':'present|Dark selected on the landing carries to browse, kind, record, map and graph pages.',
 'responsive':'partial|At 390px cobalt and akaganeite widen the document to 597px and 669px respectively on fresh and resized loads; main listing/maps fit.',
 'load_failure':'not_applicable|Reviewed listings, records and visualizations embed their data; no fetch/XHR catalogue dependency was observed.'},
}

NOTES.update({
 'ProteinTraitsMech':{
 'search':'present|After record shards load, cd05137 returns one linked record and homogentisate 1,2-dioxygenase returns 16 from the 429,421-record corpus.',
 'facets':'present|Axis, source, category and status facets combine with search. Active-site category plus racemase gives nine; Clear all resets the facet controls.',
 'result_counts':'present|Matching counts change for identifier/label queries, zero-match input and active-site filters, separately from the 429,421-record total.',
 'sorting':'present|Identifier, label ascending/descending, axis/category and source options reorder populated search results.',
 'shareable_state':'present|A cold cat=STRUCT_ACTIVE_SITE&q=racemase hash route and reload restore the category, search and nine matches.',
 'full_catalogue':'present|The manifest totals 429,421 records across 73 shards; selecting all five axes loads the complete total into paginated results.',
 'record_pages':'present|Cold record hash routes open populated MCSA:1, METPO:1000639 and ECOD:F.3755.3.1.364 details; explicit waits exclude loading shells.',
 'term_links':'partial|Record details show labeled ontology/internal links, but the ECOD record explicitly states that its source-entry resolver is unavailable.',
 'evidence':'present|Populated MCSA, METPO and ECOD details link PMID evidence; MCSA notes and causal evidence are separately displayed from database sources.',
 'review_status':'present|Details and status facets expose SEEDED, PROPOSED and REVIEWED states; the manifest reports 39,591 REVIEWED records.',
 'curation_history':'present|Populated MCSA:1 details show the dated edison-causal-graphs event, action and change summary.',
 'source_link':'present|Populated record details link their individual repository YAML source files.',
 'domain_view':'present|Loaded corpus, protein and sequence maps accompany record annotations/causal content. The corpus map explicitly covers 344,797 of 429,421 current records.',
 'cross_mech_links':'missing|Sampled populated details link external databases and internal traits rather than specific sibling-Mech records.',
 'corpus_stats':'present|The landing/manifest report 429,421 records across five axes, 63 categories and 34 source labels.',
 'category_browse':'partial|Landing axis/category/source links lead to filters in the common browser rather than standalone category pages.',
 'suite_nav':'present|Visible suite-directory links appear on the reviewed landing, browser, populated records, schema and maps.',
 'downloads':'partial|Linked facet counts and listing shards cover the catalogue, while complete details load per record; map CSV exports contain plotted points rather than full corpus records.',
 'schema_docs':'present|The linked schema guide explains ProteinTraitRecord, enumerations and causal graph fields and links LinkML source.',
 'license':'partial|Core pages and maps distinguish CC BY 4.0 data and BSD-3-Clause code; the linked SLC10 pilot omits the two project-license statements.',
 'build_provenance':'partial|Core pages expose upstream releases and retained map coverage but no site build date or deployment revision; the embedding date is explicitly unrecorded.',
 'theme_toggle':'partial|Browse toggles and carries Dark, but clicking the landing’s existing theme button does not change its saved Dark state; SLC10 ignores that choice.',
 'responsive':'partial|Sampled core and populated record routes fit 390px; expanding all 63 category values widens the document to 400px.',
 'load_failure':'present|Blocked facet/map requests show explicit failures and retry controls; unblocking and reloading restores populated content.'},
 'NaturalProductMech':{
 'search':'present|CHEBI:338412 and marneral each find one linked compound from the full 3,136-record catalogue.',
 'facets':'present|Filing-pathway and claim filters combine with search; alkaloids selects 512, adding causal-producer coverage gives 141, and reset restores 3,136.',
 'result_counts':'present|Matching counts update for identifiers, labels, zero-match input and property filters, separately from 3,136 total compounds.',
 'sorting':'present|All six options change leading linked records: name ascending/descending, causal producers, gene clusters, bioactivities and identifier.',
 'shareable_state':'present|Cold navigation and reload restore the exercised query, pathway, claim and sort controls with the same matching count.',
 'full_catalogue':'present|Browse contains 3,136 unique individual compound links, matching the displayed corpus total and complete chemical-map export.',
 'record_pages':'present|Four sampled compound URLs open populated structure, producer, occurrence, biosynthetic and provenance sections.',
 'term_links':'partial|Sampled producer and biosynthetic sections display taxon, MIBiG and GenBank identifiers as plain text rather than labeled resolver links.',
 'evidence':'partial|Anisomycin’s PMID:28373542 and occurrence DOI references remain plain text, with no PubMed or DOI anchors.',
 'review_status':'present|Sampled compound headers display grounding and SEEDED workflow tags with an explanatory disclosure.',
 'curation_history':'missing|Sampled compound pages expose source/provenance links but do not display dated, attributed curation events.',
 'source_link':'present|Each sampled Provenance section links its individual data/natural_products YAML source.',
 'domain_view':'present|Loaded chemical, text and sequence maps show 3,136 compounds, 3,114 retained text points and 763 proteins respectively; coverage scopes are disclosed.',
 'cross_mech_links':'present|Anisomycin directly links the specific CHEBI:338412 AntibioticMech compound page with a same-structure qualifier.',
 'corpus_stats':'present|The landing displays 3,136 compounds and generated source, producer, occurrence and causal-graph counts.',
 'category_browse':'present|Eight filing-pathway cards link subset indexes; the Terpenoids page opens its 213-compound listing.',
 'suite_nav':'present|Visible All Mech projects links appear on reviewed landing, browse, category, compounds and map pages.',
 'downloads':'partial|Linked exports cover all 3,136 chemical-map entries, chemical-search values and 763 sequence-map proteins, but omit complete source-record evidence.',
 'schema_docs':'partial|Downloads & Schema links the raw LinkML YAML source; reviewed navigation does not link rendered documentation or a schema guide.',
 'license':'present|Reviewed generated footers distinguish CC BY 4.0 project data and BSD-3-Clause code with upstream terms retained, matching repository licenses.',
 'build_provenance':'partial|The footer gives 3,136 records and corpus digest 2838a2004e52, but its dated source retrieval is upstream provenance rather than a dated project build.',
 'theme_toggle':'present|Dark selected on the landing carries across reviewed browse, category, compound and map routes.',
 'responsive':'partial|At 390px, anisomycin, rebeccamycin, staurosporine and the long diketopiperazine page overflow to 409, 407, 415 and 464px respectively on fresh/resized loads; browse/category/maps fit.',
 'load_failure':'partial|Blocked map JSON initially shows an explicit error, but typing in the failed sequence-map search replaces it with Showing 0 of 0 proteins; reload after unblocking recovers.'},
})

def main():
    baseline=json.loads((ROOT/'_fleet/data/site_features.json').read_text())
    proposals={};evidence={}
    for mech,notes in NOTES.items():
        assert set(notes)==set(baseline['catalogue']),mech
        old=baseline['mechs'][mech]
        primary=OUT/(mech.lower()+'.json');raw=json.loads(primary.read_text())
        assert raw['complete'],mech
        supplements=[]
        for suffix in ['-supplement','-controls','-review-followup']:
            path=OUT/(mech.lower()+suffix+'.json')
            if path.exists():
                doc=json.loads(path.read_text());assert doc['complete'],str(path)
                assert path.with_suffix('.json.gz').exists(),str(path)
                supplements.append(str(path.with_suffix('.json.gz').relative_to(ROOT)))
        features={};feature_evidence={}
        for key,value in notes.items():
            status,note=value.split('|',1);url=old['features'][key]['url']
            if key=='evidence' and mech=='MediaIngredientMech':url='https://culturebotai.github.io/MediaIngredientMech/records/ingredient/mapped/GYPS.html'
            if key=='schema_docs' and mech=='CMMMech':url=old['site']
            features[key]={'status':status,'note':note,'url':url}
            locator=f'pages[{url!r}]'
            if key in ['search','facets','result_counts','sorting','shareable_state']:locator='actions (query:, facet:, sort:, cold_url, reload_state, reset)'
            if key in ['theme_toggle','responsive']:locator='pages[*].after_theme_toggle / theme / resized_390 / fresh_390'
            if key=='load_failure':locator='failure_cases[*].aborted / failed / recovered'
            if key=='downloads':locator='bulk + pages[*].links (linked exports, distinct from probe URLs)'
            if key=='license':locator='licenses + pages[*].body / footer'
            feature_evidence[key]={'primary':str(primary.with_suffix('.json.gz').relative_to(ROOT)),'locator':locator,'supplements':supplements,'url':url}
            if mech=='CultureMech' and key=='load_failure':
                feature_evidence[key]['review_followup']='_fleet/reviews/site-features-20261119/group-b/culturemech-review-followup.json.gz#/blocked_point_activation'
            if mech=='DUFMech' and key=='downloads':
                feature_evidence[key]['review_followup']='_fleet/reviews/site-features-20261119/group-b/dufmech-review-followup.json.gz#/full_export'
        dep=raw['deployment_after']
        proposals[mech]={'site':old['site'],'repository':old['repository'],'deployed_revision':dep['sha'],'checked_on':'2026-11-19',
            'scope':'All 24 criteria revalidated on representative live routes and controls with mobile, theme, deployment and failed-request checks. Complete-catalogue counts describe listing/export coverage, not an HTTP crawl of every record. Evidence: _fleet/reviews/site-features-20261119/group-b/evidence.json. Corpus pins are unchanged.',
            'features':features}
        evidence[mech]={'deployment_before':raw['deployment_before'],'deployment_after':dep,'features':feature_evidence,
                       'limits':['Representative record and navigation review, not an exhaustive scientific-content or every-record HTTP audit.','Probe-only 404 URLs do not establish broken site links; linked downloads are checked separately.']}
    (OUT/'proposals.json').write_text(json.dumps(proposals,indent=2)+'\n')
    (OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({'rows':list(proposals),'features':sum(len(p['features']) for p in proposals.values())}))

if __name__=='__main__':main()
