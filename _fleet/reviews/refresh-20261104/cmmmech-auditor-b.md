# CMMMech deployment recheck — 2026-11-04

Corpus pin `8bf82c8dfa25a35f12b60617b86751bc3ce7df71` retained; served deployment `ff4a9841deb7e4f6e9fff025eccd2ffa07b5493c`.

- search: **present**. CHEBI:27638 and cmmmech:copper each return one linked material; Cobalt returns 23 of 678.
- facets: **present**. Kind, mechanism process and criticality filters have Clear filters. Element selects 66 records; adding bioleaching selects 15; reset restores all 678.
- result_counts: **present**. The count updates to one for identifier searches, 23 for Cobalt, 15 for bioleaching elements and zero for an unmatched query.
- sorting: **present**. The browser offers Material name (A–Z), Material name (Z–A), Mechanisms (high–low), Microbial agents (high–low), Material kind (A–Z), Criticality (critical first). Changing each option reorders the displayed results.
- shareable_state: **present**. Cobalt with element, bioleaching, criticality and sort selections reloads from its URL with all controls restored and one matching record.
- full_catalogue: **present**. The complete browser and its machine-readable export cover 678 published records; sampled record links open successfully.
- suite_nav: **present**. Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory.
- record_pages: **present**. Browse and kind/process listings link stable materials/<slug>.html pages; cobalt and akaganeite opened successfully.
- term_links: **present**. Sampled material identifiers and mechanism terms show readable labels with ChEBI, taxon and protein/ontology resolver links.
- evidence: **present**. Sampled references link DOI or source URLs, and mechanism evidence points to the corresponding references.
- review_status: **missing**. Record headers show material kind and criticality; these and individual evidence labels do not state overall review status.
- curation_history: **present**. Sampled records include Curation History tables with timestamp, curator, action and summary.
- source_link: **present**. Record source lines link the individual data/records YAML on GitHub.
- domain_view: **present**. The mechanism graph renders 654 nodes and 970 edges; the text map retains 602 material points, a subset of the 678-record catalogue.
- cross_mech_links: **missing**. Record sections provide cross-Mech search links and site navigation, but the sampled pages do not link specific sibling records.
- corpus_stats: **present**. The landing reports 678 materials, 609 mechanisms, 500 materials with mechanisms and 90 designated critical materials across six kinds.
- category_browse: **present**. Landing cards link six material-kind and process listings. Kind totals are 66 elements, 427 minerals, 111 secondary resources, 36 commodities, 31 primary resources and seven mineral groups.
- downloads: **partial**. Linked index.json covers all 678 catalogue entries but contains listing metadata and mechanism counts, not full mechanism evidence; map exports and individual YAML links are also available.
- schema_docs: **partial**. Visible schema links open the LinkML YAML source. The previously recorded pages/schema.html documentation URL returns 404.
- license: **present**. Reviewed footers separately state CC BY 4.0 data and BSD-3-Clause code, consistent with the repository license policy.
- build_provenance: **present**. Footers state 678 materials, 609 mechanisms, latest curation 2026-11-04 and corpus digest 92117fbb1ec5.
- theme_toggle: **present**. Dark selected on the landing carries to Browse, kind, record, text-map and graph pages.
- responsive: **partial**. At 390px, cobalt widens the document to 597px and akaganeite to 669px. The ten newly curated records reach 652–669px, including copper at 652px, on fresh and resized views.
- load_failure: **not_applicable**. Reviewed listings, records and canvas visualizations embed their data; no fetch/XHR data request was observed to abort.
