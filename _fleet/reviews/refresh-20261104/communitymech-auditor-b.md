# CommunityMech website audit — 2026-11-04

Observed deployment `88314cf16ca1db9580d379babd4ec808e334d898`; corpus pin `a4e963e5bebc49fa7a9908ac441d003e3ad4a817`.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | partial | Name and description searches work across 485 communities, but known record identifiers CommunityMech:000134 and CommunityMech:000139 return zero matches; the corresponding named records are present. |
| facets | present | Category and ecological-state filters have Clear All. BIOTECHNOLOGY selects 96 of 485 communities; reset restores all 485. |
| result_counts | present | The live count shows three matches for ANME, one for its full community name and zero for the tested canonical identifiers and unmatched query. |
| sorting | present | The browser offers Name (A → Z), Name (Z → A), Members (Most → Fewest), Members (Fewest → Most), Category (A → Z). Changing each option reorders the displayed results. |
| shareable_state | present | The URL retains search, category and sort; the combined BIOTECHNOLOGY/name-search selection restores the same controls and zero-match state. |
| full_catalogue | present | The complete browser and its machine-readable export cover 485 published records; sampled record links open successfully. |
| suite_nav | present | Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory. |
| record_pages | present | Published communities have individual communities/<slug>.html pages; four sampled records display taxonomy, interactions, environment and growth media. |
| term_links | present | Sampled taxonomy and environmental sections show readable names beside NCBITaxon, ChEBI and ENVO resolver links. |
| evidence | present | Sampled interaction evidence links PMID and DOI references with supporting text and evidence-type labels. |
| review_status | missing | Record headers show ecological state and evidence labels, not an overall curation or review status. |
| curation_history | missing | The sampled community pages do not display curation events, even though the repository retains provenance. |
| source_link | present | Each sampled record footer now links its own kb/communities YAML file on GitHub. |
| domain_view | present | Community pages render interaction diagrams, and text, taxonomic and sequence embedding views open as linked domain views. |
| cross_mech_links | present | Copper Biomining links Standard 9K Medium directly to CultureMech normalized recipe 003277. |
| corpus_stats | present | The landing and browser report 485 published communities across 16 categories. Repository isolate records are outside this published-community count. |
| category_browse | partial | Category and ecological-state subsets are filters in the browser rather than separate category pages. |
| downloads | partial | Linked communities.json and TSV cover all 485 communities as catalogue summaries; they omit the complete taxon and interaction evidence stored in individual records. |
| schema_docs | present | The linked schema.html page documents the CommunityMech classes, slots and ontology groundings. |
| license | partial | Reviewed landing and record footers say License: BSD-3-Clause without distinguishing the project data license from the code license. |
| build_provenance | missing | Reviewed pages identify the generator and source corpus but do not give a build date, deployed commit or dated corpus version. |
| theme_toggle | present | Dark mode chosen on the landing persists through the browser, maps, schema and four sampled records. |
| responsive | present | The reviewed landing, browser, maps, schema and four records fit a 390px viewport. |
| load_failure | not_applicable | Reviewed community pages and visualizations use embedded data; no fetch or XHR catalogue request was observed to abort. |

Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.
