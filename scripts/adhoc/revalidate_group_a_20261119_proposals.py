#!/usr/bin/env python3
"""Materialize reviewed Group A verdict proposals from retained Nov19 evidence.

Inputs: exact 24-feature catalogue and completed browser/coverage receipts.
Outputs: group-a/proposals.json; no upstream or shared table mutations.
These are auditor proposals for independent skeptical review, 2026-11-19.
"""
import json
import re
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '_fleet/reviews/site-features-20261119/group-a'

# Each entry was judged from the new receipt, not carried forward by date alone.
VERDICTS = {
    'HabitatMech': {
        'search': ('partial', 'Identifier ENVO:03000033 finds one habitat and marine sediment finds three. The water query reports 310 matches but exposes only 200 search results; the category listings are separate routes.', ['actions/search:ENVO:03000033', 'actions/search:marine sediment', 'actions/search:water']),
        'facets': ('present', 'The grounding filter reduces the water query from 310 to 86 matches. Keyboard activation of Reset filters restores the initial unfiltered category listing.', ['actions/facet:#browse-grounding', 'actions/keyboard_reset']),
        'result_counts': ('present', 'Counts change with identifier, label, unmatched-query and grounding-filter inputs; displayed results are distinguished from matching records when capped.', ['actions/search:water', 'actions/search:no-such-record-nov19-audit', 'actions/facet:#browse-grounding']),
        'sorting': ('present', 'All five sort choices were exercised with the water query; the leading habitat changed between assertions, ascending/descending name, and grounding orders.', ['actions/sort:assertions-asc', 'actions/sort:name-asc', 'actions/sort:name-desc', 'actions/sort:grounding-asc']),
        'shareable_state': ('present', 'The identifier query restores after reload. Combined water search, grounding=EXACT and grounding sort also restore the same controls and 86 matches.', ['actions/query_before_reload', 'actions/query_after_reload', 'actions/facets_before_reload', 'actions/facets_after_reload']),
        'full_catalogue': ('present', 'Eight linked category indexes contain 3,209 distinct habitat slugs. Category pages expose paginated listings beyond the separate 200-result global-search cap.', ['coverage.json#/habitat_categories', 'pages/https://culturebotai.github.io/HabitatMech/pages/category/host-associated.html']),
        'record_pages': ('present', 'Marine sediment and aquatic macrophyte-associated environment open at stable habitat URLs with source attestations, environmental context and their own YAML links.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/habitats/aquatic-macrophyte-associated-environment-habitatmech-bacdive-38260eea00.html']),
        'term_links': ('partial', 'Marine sediment links its ENVO identity, while the Associated taxa section displays names and NCBITaxon CURIEs without ontology-resolver anchors. TaxonMech exploration links do not replace those resolver links.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html']),
        'evidence': ('partial', 'Marine-sediment mechanistic-edge PMID references and curation DOI citations are displayed as plain text rather than PubMed/DOI links.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html']),
        'review_status': ('present', 'Record views show workflow status; the landing reports 1,301 REVIEWED records and explicitly distinguishes workflow status from human review.', ['pages/https://culturebotai.github.io/HabitatMech/pages/index.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html']),
        'curation_history': ('present', 'Marine sediment displays dated, attributed causal-graph creation/update and source-synonym/parent decisions, including the change explanations.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html']),
        'source_link': ('present', 'The sampled marine-sediment Provenance section links its own data/habitats/aquatic/marine_sediment.yaml source file.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html']),
        'domain_view': ('present', 'The semantic text map renders the 3,209-record projection, and the marine-sediment detail displays its directed causal graph.', ['pages/https://culturebotai.github.io/HabitatMech/pages/text-map/', 'pages/https://culturebotai.github.io/HabitatMech/pages/habitats/marine-sediment-envo-03000033.html', 'downloads/https://culturebotai.github.io/HabitatMech/pages/text-map-source/points.json']),
        'cross_mech_links': ('partial', 'Record exploration links to TaxonMech/browse.html and TraitMech/browse.html return HTTP 404; the correct browsers live under pages/. These handoffs do not resolve to specific sibling records.', ['link_checks/https://culturebotai.github.io/TaxonMech/browse.html?q=marine%20sediment', 'link_checks/https://culturebotai.github.io/TraitMech/browse.html?q=marine%20sediment']),
        'corpus_stats': ('present', 'The landing displays 3,209 habitats, 2,143 ontology-grounded records, 175 corroborated by at least two sources and 1,301 with REVIEWED workflow status.', ['pages/https://culturebotai.github.io/HabitatMech/pages/index.html']),
        'category_browse': ('present', 'Eight named category links lead to subset listings, including Aquatic with 468 records and Host-associated with 1,655.', ['pages/https://culturebotai.github.io/HabitatMech/pages/browse.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/category/aquatic.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/category/host-associated.html']),
        'suite_nav': ('present', 'All Mech projects links on the sampled templated landing, browse and record pages lead to the central suite directory, which returns HTTP 200.', ['pages/https://culturebotai.github.io/HabitatMech/pages/index.html', 'link_checks/https://culturebotai.github.io/mechs/']),
        'downloads': ('partial', 'The landing links all eight category JSON indexes and the complete semantic projection with its manifest. These retain 3,209 compact rows/points, rather than full habitat records.', ['downloads', 'coverage.json#/habitat_categories']),
        'schema_docs': ('partial', 'Visible schema links open the annotated LinkML YAML and imported schemas. The sampled navigation supplies schema source rather than a rendered schema reference.', ['link_checks/https://github.com/CultureBotAI/HabitatMech/blob/main/src/habitatmech/schema/habitatmech.yaml', 'pages/https://culturebotai.github.io/HabitatMech/pages/index.html']),
        'license': ('partial', 'Templated pages state CC BY 4.0 data, BSD-3-Clause code and retained upstream terms, matching deployed-revision license files. The linked standalone text-map-source page omits these project licenses.', ['licenses', 'pages/https://culturebotai.github.io/HabitatMech/pages/text-map-source/index.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/index.html']),
        'build_provenance': ('partial', 'Main footers date the upstream kg-microbe extraction. The linked manifest dates the semantic projection, but sampled main pages do not identify a dated build or commit of the habitat corpus.', ['pages/https://culturebotai.github.io/HabitatMech/pages/index.html', 'downloads/https://culturebotai.github.io/HabitatMech/pages/text-map-source/manifest.json']),
        'theme_toggle': ('partial', 'Dark mode selected on the landing persists across templated pages. The linked standalone semantic map retains its light presentation without a theme control or theme attribute.', ['pages/https://culturebotai.github.io/HabitatMech/pages/index.html', 'pages/https://culturebotai.github.io/HabitatMech/pages/text-map-source/index.html']),
        'responsive': ('partial', 'The aquatic-macrophyte record widens the document to 404px at a 390px viewport on fresh and resized loads. The other seven sampled routes fit.', ['pages/https://culturebotai.github.io/HabitatMech/pages/habitats/aquatic-macrophyte-associated-environment-habitatmech-bacdive-38260eea00.html']),
        'load_failure': ('partial', 'Blocking Browse category-index requests and searching reports Showing 0 of 0 matching habitats without an error. Removing the fault and reloading restores the one matching habitat.', ['failures/https://culturebotai.github.io/HabitatMech/pages/browse.html']),
    },
}


def reviewed_shared(mech):
    """Common judgments only for completed, individually inspected site receipts."""
    cfg = json.loads((ROOT / '_fleet/data/site_features.json').read_text())['mechs'][mech]
    pointer = lambda feature: ['pages/' + cfg['features'][feature]['url'].split('#')[0]]
    return {
        'facets': ('present', 'Property filters change the matching result count, and activating the reset control with the keyboard restores the unfiltered listing.', ['actions/facets_before_reload', 'actions/keyboard_reset']),
        'result_counts': ('present', 'The matching count changes with known identifier, known label, unmatched-query and property-filter inputs, separately from the corpus total.', ['actions']),
        'sorting': ('present', 'The available sort choices were exercised in the live browser; ascending and descending orders change the leading records.', ['actions']),
        'shareable_state': ('present', 'The query and exercised facet/sort state survive URL reload with the same controls and matching counts.', ['actions/query_before_reload', 'actions/query_after_reload', 'actions/facets_before_reload', 'actions/facets_after_reload']),
        'record_pages': ('present', 'Sampled populated records open at stable individual URLs and display their scientific sections and their own source-file links.', pointer('record_pages')),
        'evidence': ('present', 'Sampled record sections render citation identifiers as PubMed/DOI or source-reference anchors with associated evidence text. This judges linked rendering, not the scientific validity or external-service access policy of every citation.', pointer('evidence')),
        'review_status': ('present', 'Sampled record headers show the workflow status, separately from dated curation events.', pointer('review_status')),
        'curation_history': ('present', 'Sampled record views display dated curator actions and change summaries.', pointer('curation_history')),
        'source_link': ('present', 'Sampled record views link directly to their own YAML files in the repository.', pointer('source_link')),
        'suite_nav': ('present', 'Visible All Mech projects navigation on the sampled main pages links to the central X-Mech directory; its target responds successfully.', pointer('suite_nav') + ['link_checks/https://culturebotai.github.io/mechs/']),
        'schema_docs': ('partial', 'Sampled navigation links the annotated LinkML YAML source, rather than a rendered schema reference.', pointer('schema_docs')),
        'license': ('present', 'Sampled pages distinguish CC BY 4.0 project data, BSD-3-Clause code and retained upstream terms, consistent with license files read at the deployed revision.', pointer('license') + ['licenses']),
        'build_provenance': ('partial', 'Sampled pages show an undated corpus digest or upstream-source dates, without a build date, displayed commit or dated version of the project corpus.', pointer('build_provenance')),
        'theme_toggle': ('present', 'Dark mode chosen on the landing persists across the sampled browser, record and visualization pages in the same browser context.', ['pages']),
        'responsive': ('present', 'All sampled routes fit a 390px viewport on both fresh load and resizing from 1280px; retained states record document widths for every route.', ['pages']),
    }


VERDICTS['CommunityMech'] = reviewed_shared('CommunityMech') | {
    'search': ('partial', 'The full ANME-SRB community name finds one of 512 communities. Known identifiers CommunityMech:000134 and CommunityMech:000139 return zero matches despite their records being present.', ['actions/search:CommunityMech:000134', 'actions/search:CommunityMech:000139', 'actions/search:ANME-SRB Marine Methane Seep Consortium']),
    'shareable_state': ('present', 'The positive full-name query survives reload. The BIOTECHNOLOGY facet and category sort also restore the same controls and 99 matches.', ['followup-1.json#/actions/positive_query_before_reload', 'followup-1.json#/actions/positive_query_after_reload', 'actions/facets_before_reload', 'actions/facets_after_reload']),
    'full_catalogue': ('present', 'The live browser exposes 512 distinct community record links and its complete published JSON index contains 512 distinct record slugs; sampled individual pages open successfully.', ['pages/https://culturebotai.github.io/CommunityMech/browser.html', 'coverage.json#/downloads']),
    'term_links': ('present', 'Sampled taxonomy and environmental sections show readable organism, chemical and habitat labels alongside NCBITaxon, ChEBI and ENVO resolver links.', ['pages/https://culturebotai.github.io/CommunityMech/communities/Aalborg_East_Full_Scale_EBPR_Community.html']),
    'review_status': ('missing', 'The four sampled community views show ecological state and claim evidence, but no overall record curation/review status.', ['pages/https://culturebotai.github.io/CommunityMech/communities/ANME_SRB_Marine_Methane_Seep_Consortium.html', 'pages/https://culturebotai.github.io/CommunityMech/communities/Alseth_FourSpecies_Pathogen_Phage_Community.html']),
    'curation_history': ('missing', 'The four sampled community views do not display dated curator events or change histories.', ['pages/https://culturebotai.github.io/CommunityMech/communities/Aalborg_East_Full_Scale_EBPR_Community.html', 'pages/https://culturebotai.github.io/CommunityMech/communities/Copper_Biomining_Heap_Leach.html']),
    'domain_view': ('present', 'Community records render interaction diagrams and linked maps render populated views. The text map contains 458 communities and the sequence map 27 proteins; these are subsets, not complete coverage of the 512-community browser.', ['pages/https://culturebotai.github.io/CommunityMech/text_map.html', 'pages/https://culturebotai.github.io/CommunityMech/sequence_map.html', 'pages/https://culturebotai.github.io/CommunityMech/community_umap.html']),
    'cross_mech_links': ('partial', 'Copper Biomining links a working CultureMech normalized recipe, but sampled TaxonMech record handoffs and several sibling browser links return HTTP 404.', ['followup-1.json#/link_checks', 'link_checks/https://culturebotai.github.io/TaxonMech/taxa/NCBITaxon_2157.html', 'pages/https://culturebotai.github.io/CommunityMech/communities/Copper_Biomining_Heap_Leach.html']),
    'corpus_stats': ('present', 'The landing and browser display 512 published communities across 16 categories; repository isolate records are outside this published-community total.', ['pages/https://culturebotai.github.io/CommunityMech/', 'actions/initial']),
    'category_browse': ('partial', 'Category subsets are accessible as browser filters, rather than standalone category pages. Selecting BIOTECHNOLOGY shows 99 of 512 communities.', ['actions/facet:first_checkbox']),
    'downloads': ('partial', 'Linked JSON and TSV downloads cover all 512 communities as catalogue summaries, omitting the full taxonomy and interaction evidence of individual records.', ['downloads/https://culturebotai.github.io/CommunityMech/communities.json', 'downloads/https://culturebotai.github.io/CommunityMech/communities.tsv']),
    'schema_docs': ('present', 'The linked schema.html page renders a CommunityMech schema reference with classes, slots and ontology groundings.', ['pages/https://culturebotai.github.io/CommunityMech/schema.html']),
    'license': ('partial', 'Landing and record footers state License: BSD-3-Clause without distinguishing project data from code, although the deployed repository retains a separate CC BY 4.0 data license.', ['pages/https://culturebotai.github.io/CommunityMech/', 'pages/https://culturebotai.github.io/CommunityMech/communities/ANME_SRB_Marine_Methane_Seep_Consortium.html', 'licenses']),
    'build_provenance': ('missing', 'Sampled pages identify the generator and source corpus but do not display a build date, deployed commit or dated corpus version.', ['pages/https://culturebotai.github.io/CommunityMech/', 'pages/https://culturebotai.github.io/CommunityMech/communities/ANME_SRB_Marine_Methane_Seep_Consortium.html']),
    'theme_toggle': ('partial', 'Dark mode persists across the templated browser, records and taxonomic/network views. The linked text and sequence maps ignore the saved dark choice, have no toggle, and render a light background.', ['pages/https://culturebotai.github.io/CommunityMech/text_map.html', 'pages/https://culturebotai.github.io/CommunityMech/sequence_map.html', 'pages/https://culturebotai.github.io/CommunityMech/browser.html']),
    'responsive': ('partial', 'The schema page widens the document to 1,321px at a 390px viewport on fresh and resized loads; the other ten sampled routes fit.', ['pages/https://culturebotai.github.io/CommunityMech/schema.html']),
    'load_failure': ('not_applicable', 'The eleven sampled landing, browser, record, schema and visualization routes use embedded data; no fetch/XHR data request was observed. Blocking fetch/XHR while exercising browser search intercepted no request.', ['pages', 'failures/https://culturebotai.github.io/CommunityMech/browser.html']),
}

VERDICTS['TaxonMech'] = reviewed_shared('TaxonMech') | {
    'search': ('present', 'NCBITaxon:2173 returns 32 matches and Methanobrevibacter smithii returns 26. NCBITaxon:562 returns 259 matches across two pages; the browser provides result pagination.', ['actions/search:NCBITaxon:2173', 'actions/search:Methanobrevibacter smithii', 'actions/search:NCBITaxon:562']),
    'shareable_state': ('partial', 'Search and sort restore, but domain/rank/source selectors are not retained in the URL. Reload changes the exercised 553,073-match filter selection back to all 626,048 records.', ['actions/query_after_reload', 'actions/facets_before_reload', 'actions/facets_after_reload']),
    'full_catalogue': ('present', 'The complete published index contains 626,048 unique identifiers and 626,048 unique taxon detail routes. Browse exposes 3,131 pages; clicking Next successfully opens page 2.', ['coverage.json#/downloads', 'actions/initial', 'actions/next_page']),
    'term_links': ('present', 'The sampled Methanobrevibacter record displays labeled NCBI lineage and organism identifiers, LPSN links and GTDB mappings with resolver anchors.', ['pages/https://culturebotai.github.io/TaxonMech/pages/taxon.html?id=NCBITaxon:2173']),
    'domain_view': ('present', 'Sampled records show named taxonomic lineages. The text embedding map renders 31,258 embedded taxa, explicitly a subset of the 626,048-record corpus.', ['pages/https://culturebotai.github.io/TaxonMech/pages/taxon.html?id=NCBITaxon:2173', 'pages/https://culturebotai.github.io/TaxonMech/pages/map.html']),
    'cross_mech_links': ('partial', 'Record exploration links include CommunityMech search, but the sampled CultureMech, HabitatMech, PathwayMech and NaturalProductMech browser handoffs use missing routes and return HTTP 404.', ['link_checks']),
    'corpus_stats': ('present', 'The landing displays 626,048 taxa, 100,745 distinct strains and 20,648 taxa with a type strain. The opened Archaea listing contains 14,013 taxa.', ['pages/https://culturebotai.github.io/TaxonMech/pages/index.html', 'pages/https://culturebotai.github.io/TaxonMech/pages/domain/archaea.html']),
    'category_browse': ('present', 'Linked domain and type-strain pages provide paginated subsets; the opened Archaea and type-strain listings contain 14,013 and 20,648 records.', ['pages/https://culturebotai.github.io/TaxonMech/pages/domain/archaea.html', 'pages/https://culturebotai.github.io/TaxonMech/pages/type-strains.html']),
    'downloads': ('partial', 'The linked compressed index contains all 626,048 catalogue rows and detail routes, with a separate format/checksum manifest. It is an index, rather than a bulk export of complete taxon records.', ['downloads/https://culturebotai.github.io/TaxonMech/pages/index.json.gz', 'downloads/https://culturebotai.github.io/TaxonMech/pages/index.json', 'coverage.json#/downloads']),
    'schema_docs': ('partial', 'Visible schema links identify annotated LinkML YAML, verified through the GitHub API at the deployed revision after the web UI rate-limited a request. Sampled navigation does not expose a rendered schema reference.', ['followup-1.json#/pinned_source_checks', 'pages/https://culturebotai.github.io/TaxonMech/pages/index.html']),
    'load_failure': ('present', 'Blocked search indexes report Search is unavailable while preserving static pagination. Blocked taxon-detail shards and embedding-map data show explicit load errors; removing each fault and reloading restores populated content.', ['failures']),
}

VERDICTS['PathwayMech'] = reviewed_shared('PathwayMech') | {
    'search': ('present', 'MetaCyc:PWY-6543 finds one pathway and trehalose finds three of the 283 published pathways; all matches have directly reachable record links.', ['actions/search:MetaCyc:PWY-6543', 'actions/search:trehalose']),
    'full_catalogue': ('present', 'Browse contains 283 distinct stable record links, matching the complete downloadable index with 283 distinct identifiers and detail URLs.', ['pages/https://culturebotai.github.io/PathwayMech/pages/browse.html', 'coverage.json#/downloads']),
    'term_links': ('partial', 'Organism-scope taxa are labeled and linked, but the main component and mechanistic-edge tables display chemical, protein and reaction identifiers without resolver anchors.', ['pages/https://culturebotai.github.io/PathwayMech/pages/records/MetaCyc_PWY-6543.html']),
    'review_status': ('missing', 'The sampled MetaCyc, GO and actinorhodin pathway pages display pathway type and curation history, but no overall record curation/review status.', ['pages/https://culturebotai.github.io/PathwayMech/pages/records/MetaCyc_PWY-6543.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/records/MIBiG_BGC0000194.html']),
    'domain_view': ('present', 'Populated pathway pages render directed SVG networks. The text map renders 270 pathways and the sequence map 216 pathway centroids; both are subsets of the current 283-record corpus.', ['pages/https://culturebotai.github.io/PathwayMech/pages/records/MetaCyc_PWY-6543.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/map.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/sequence-map.html']),
    'cross_mech_links': ('missing', 'The sampled MetaCyc, GO and actinorhodin pages provide suite navigation and external source-authority links, but no direct links to specific sibling-Mech or kg-microbe records.', ['pages/https://culturebotai.github.io/PathwayMech/pages/records/MetaCyc_PWY-6543.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/records/GO_0036040.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/records/MIBiG_BGC0000194.html']),
    'corpus_stats': ('present', 'The landing reports 283 pathway records, 105 taxa, 14,841 mechanistic edges and 5,927 distinct references.', ['pages/https://culturebotai.github.io/PathwayMech/pages/index.html']),
    'category_browse': ('partial', 'Subset selection is provided by Browse filters; sampled navigation does not expose standalone class pages. The Pathway class selector currently labels classes using mechanistic-edge counts.', ['pages/https://culturebotai.github.io/PathwayMech/pages/browse.html', 'actions/facet:#pathway-type']),
    'downloads': ('present', 'The landing links KGX node/edge TSV exports and a complete 283-record pathway index. All downloads succeed; the checksum manifest identifies 5,476 nodes and 14,841 edges.', ['downloads', 'coverage.json#/downloads']),
    'license': ('partial', 'The landing states CC BY 4.0 data and retained upstream terms, but does not state the code license. Sampled browse and record views omit the data/code license statement.', ['pages/https://culturebotai.github.io/PathwayMech/pages/index.html', 'pages/https://culturebotai.github.io/PathwayMech/pages/browse.html', 'licenses']),
    'load_failure': ('not_applicable', 'The eight sampled landing, browse, record, text-map and sequence-map routes embed their data; no fetch/XHR data request was observed. Blocking those request types while searching intercepted nothing.', ['pages', 'failures/https://culturebotai.github.io/PathwayMech/pages/browse.html']),
}

VERDICTS['CellStructureMech'] = reviewed_shared('CellStructureMech') | {
    'search': ('present', 'GO:0097589, the label MitoStore and the local insoluble-protein-deposit identifier each return one record. The complete listing contains all 1,022 structures.', ['actions/search:GO:0097589', 'actions/search:MitoStore', 'actions/search:cellstructuremech:insoluble_protein_deposit']),
    'full_catalogue': ('present', 'Browse exposes all 1,022 records. The complete corpus and index downloads each contain 1,022 unique identifiers; the index supplies 1,022 distinct stable detail routes.', ['actions/initial', 'coverage.json#/downloads']),
    'term_links': ('present', 'The attachment-organelle membrane view labels and links its GO identity, structural parents, UniProt location and taxonomy terms; the populated archaellum and S-layer pages provide corresponding resolver links.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/structures/appendage/attachment_organelle_membrane.html', 'pages/https://culturebotai.github.io/CellStructureMech/pages/structures/appendage/archaeal_type_flagellum.html']),
    'domain_view': ('present', 'The text map renders all 1,022 structures. The sequence map renders 469 proteins associated with 140 structures and clicking a point opens its linked structure context.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/embedding-map.html', 'pages/https://culturebotai.github.io/CellStructureMech/pages/sequence-map.html']),
    'cross_mech_links': ('present', 'The S-layer record links directly to the corresponding TraitMech S-layer trait page, which returns HTTP 200.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/structures/envelope/s_layer.html', 'link_checks/https://culturebotai.github.io/TraitMech/pages/traits/morphology/s_layer.html']),
    'corpus_stats': ('present', 'The landing reports 1,022 structures, 13 categories and 873 GO-grounded records, with counts for each category.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/index.html']),
    'category_browse': ('present', 'Thirteen named category routes and a GO-grounded subset are linked from the landing. The microcompartment and grounded listings open with populated record links.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/grounded.html', 'pages/https://culturebotai.github.io/CellStructureMech/pages/category/microcompartment.html']),
    'downloads': ('present', 'The linked complete corpus JSON contains 1,022 full records, with a separate 1,022-record catalogue index; both download successfully and have retained byte hashes.', ['downloads', 'coverage.json#/downloads']),
    'schema_docs': ('partial', 'The linked annotated LinkML YAML is verified at the deployed revision through the GitHub API after a web-UI rate limit; sampled navigation does not expose a rendered schema reference.', ['followup-1.json#/pinned_source_checks']),
    'build_provenance': ('present', 'Main pages display the corpus date 2026-11-03 05:55:11 UTC, digest d7c5fef867d9, record count and generation script.', ['pages/https://culturebotai.github.io/CellStructureMech/pages/index.html']),
    'load_failure': ('present', 'Blocking both text-map artifacts produces Could not load embedding artifacts: Failed to fetch. Removing the fault and reloading restores 1,022 structures; the main browser uses embedded data.', ['failures/https://culturebotai.github.io/CellStructureMech/pages/embedding-map.html']),
}

VERDICTS['AntibioticMech'] = reviewed_shared('AntibioticMech') | {
    'search': ('partial', 'CHEBI:2637 and rifampicin each find one compound. The antibiotic query has 553 matches but shows only the first 500 without search pagination; class listings provide a separate navigation route.', ['actions/search:CHEBI:2637', 'actions/search:rifampicin', 'actions/search:antibiotic']),
    'full_catalogue': ('present', 'The complete browse index contains 3,125 distinct record slugs and the chemical-map download contains 3,125 distinct identifiers and detail paths. Linked class listings provide pagination; opening antibacterial page 2 succeeds with 300 records.', ['coverage.json#/downloads', 'followup-1.json#/actions/category_first', 'followup-1.json#/actions/category_next']),
    'term_links': ('partial', 'Avibactam links its ChEBI identity and broader-compound CURIEs, but all four entries in its Classification section display Label unavailable instead of readable names.', ['pages/https://culturebotai.github.io/AntibioticMech/pages/antibacterial/avibactam.html']),
    'domain_view': ('present', 'The chemical map renders 3,125 structures; populated compound views display chemical properties and causal mechanisms. The sequence map renders a subset of 132 proteins across 71 compounds, and a separate text map is available.', ['pages/https://culturebotai.github.io/AntibioticMech/pages/chemical-map.html', 'pages/https://culturebotai.github.io/AntibioticMech/pages/sequence-map.html', 'pages/https://culturebotai.github.io/AntibioticMech/pages/map.html']),
    'cross_mech_links': ('partial', 'D-cycloserine links a working specific PathwayMech WP5060 record. The sampled MediaIngredientMech/app.html exploration links return HTTP 404, so cross-project navigation is inconsistent.', ['link_checks/https://culturebotai.github.io/PathwayMech/pages/records/WikiPathways_WP5060.html', 'link_checks/https://culturebotai.github.io/MediaIngredientMech/app.html?q=amikacin']),
    'corpus_stats': ('present', 'The landing reports 3,125 compounds, 2,782 ontology-grounded records, 281 merged ChEBI/ARO records and 174 with REVIEWED workflow status, plus mechanism coverage counts.', ['pages/https://culturebotai.github.io/AntibioticMech/pages/index.html']),
    'category_browse': ('present', 'The landing links antimicrobial-class listings. The antibacterial listing opens and its page-2 link loads a further 300 compound rows.', ['pages/https://culturebotai.github.io/AntibioticMech/pages/index.html', 'followup-1.json#/actions/category_first', 'followup-1.json#/actions/category_next']),
    'downloads': ('partial', 'Linked downloads include the 3,125-row browse index, the complete chemical-map data and lazy per-record JSON for sampled compounds, rather than a bulk full-record corpus export.', ['downloads', 'coverage.json#/downloads']),
    'responsive': ('present', 'The eight valid main/browser/detail/map routes fit 390px on fresh and resized loads. The actual linked antibacterial category pagination also fits 390px; a guessed unlinked category URL returned a retained 404 and is excluded from feature judgments.', ['pages', 'followup-1.json#/actions/category_resized_390', 'followup-1.json#/actions/category_fresh_390']),
    'load_failure': ('partial', 'Browse and the chemical map retain explicit fetch-error messages. On the sequence map, typing after a blocked JSON load replaces the error with Showing 0 of 0 proteins. Removing faults and reloading restores loaded data totals.', ['failures/https://culturebotai.github.io/AntibioticMech/pages/browse.html', 'failures/https://culturebotai.github.io/AntibioticMech/pages/chemical-map.html', 'failures/https://culturebotai.github.io/AntibioticMech/pages/sequence-map.html']),
}


def evidence_pointer(folder, value):
    """Emit resolvable RFC 6901 pointers into lossless published archives."""
    if re.match(r'[^/]+\.json#/', value):
        filename, pointer = value.split('#', 1)
        tokens = pointer.lstrip('/').split('/')
        if filename != 'coverage.json':
            filename += '.gz'
    else:
        filename = 'raw.json.gz'
        tokens = value.split('/', 1)
    escaped = '/' + '/'.join(token.replace('~', '~0').replace('/', '~1') for token in tokens)
    path = folder / filename
    body = gzip.decompress(path.read_bytes()) if filename.endswith('.gz') else path.read_bytes()
    node = json.loads(body)
    for token in tokens:
        node = node[int(token)] if isinstance(node, list) else node[token]
    return str(path.relative_to(ROOT)) + '#' + escaped


def main():
    catalogue = json.loads((ROOT / '_fleet/data/site_features.json').read_text())
    proposals = {}
    for mech, decisions in VERDICTS.items():
        attempt = {'HabitatMech': 'audit-3', 'PathwayMech': 'audit-2', 'CellStructureMech': 'audit-2'}.get(mech, 'audit-1')
        folder = BASE / mech / attempt
        raw = json.loads((folder / 'raw.json').read_text())
        assert raw.get('finished_at') and raw.get('deployment_stable'), mech
        assert set(decisions) == set(catalogue['catalogue']), mech
        entry = catalogue['mechs'][mech]
        prefix = str(folder.relative_to(ROOT))
        features = {}
        for key, (status, note, pointers) in decisions.items():
            evidence = [evidence_pointer(folder, p) for p in pointers]
            features[key] = {'status': status, 'note': note, 'url': entry['features'][key]['url'], 'evidence': evidence}
        proposals[mech] = {'site': entry['site'], 'repository': entry['repository'], 'deployed_revision': raw['deployment_after']['sha'],
            'checked_on': '2026-11-19', 'scope': 'Current live Chrome/Playwright audit of all 24 criteria, with retained page states/screenshots, identifier and label search, facets/sort/reset and URL reload, fresh and resized 390px checks, cross-page theme checks, fault injection and reload recovery, sampled populated details, and separate complete-index coverage proofs. Exact successful deployment and served Last-Modified were verified before and after. Corpus pins are unchanged. Auditor proposals await independent skeptical review.', 'features': features}
    target = BASE / 'proposals.json'
    target.write_text(json.dumps(proposals, indent=2) + '\n')
    print(target)


if __name__ == '__main__':
    main()
