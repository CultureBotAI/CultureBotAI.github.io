# ProteinTraitsMech website audit — 2026-11-04

Observed deployment `568e78869fb08b86849d13f6a23b3a32ec27cd08`; corpus pin `fa794e90b67bdafe7972f48c1288e0c939c53eea`.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | present | Searching cd05137 returns one linked record; homogentisate 1,2-dioxygenase returns 16 after the relevant shards finish loading. |
| facets | present | Axis, source, category and status facets combine with text search. Selecting active sites gives 1,004 records and adding racemase gives nine; controls provide a facet reset. |
| result_counts | present | Matching results are shown separately from the 429,421-record total; the active-site category plus racemase gives nine and an unmatched query gives zero. |
| sorting | present | The browser offers Identifier (A–Z), Label (A–Z), Label (Z–A), Axis & category, Source. Changing each option reorders the displayed results. |
| shareable_state | present | A cold #cat=STRUCT_ACTIVE_SITE&q=racemase URL and its reload restore the category and search with nine matching records. |
| full_catalogue | present | The facet manifest totals 429,421 records in 73 shards; selecting all five axes exposes the full count through paginated results. |
| suite_nav | present | Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory. |
| record_pages | present | Cold browse.html#record=CURIE routes open individual record details, including MCSA:1, METPO:1000639 and ECOD:F.3755.3.1.364. |
| term_links | partial | Labeled ontology and internal record links are available, but some primary identifiers such as ECOD:F.3755.3.1.364 explicitly lack a source-entry resolver. |
| evidence | present | Reference-bearing record details link PMID and DOI evidence separately from database-source links. |
| review_status | present | Record details and status facets expose SEEDED, PROPOSED and REVIEWED workflow states; the runtime manifest has 39,591 REVIEWED records. |
| curation_history | present | Record details show dated curation actions, curators and change summaries, including the MCSA:1 curation event. |
| source_link | present | Record detail views link the record’s individual YAML path on GitHub, separately from external database-entry links. |
| domain_view | present | Record views provide sequences, annotations and causal diagrams where available. The corpus map covers 344,797 current records; protein and sequence maps show 68,657 and 12,705 proteins. |
| cross_mech_links | missing | Checked record views link external databases and other ProteinTraitsMech records; their main sections do not link specific sibling-Mech or kg-microbe records. |
| corpus_stats | present | Runtime statistics show 429,421 records: 118,338 structure, 147,149 sequence, 392 sequence/structure, 163,527 function and 15 evolution, across 63 categories and 34 source labels. |
| category_browse | partial | Landing axis/category/source links select filters in the common browser rather than standalone category pages. |
| downloads | partial | The browser links facet counts and listing shards for all 429,421 records; complete detail is fetched per record, and map CSVs contain plotted points rather than the full corpus records. |
| schema_docs | present | The linked schema guide explains ProteinTraitRecord, enums and causal graph fields and links its LinkML source. |
| license | partial | Core pages and maps distinguish CC BY 4.0 data from BSD-3-Clause code. The linked SLC10 pilot does not state both project licenses. |
| build_provenance | partial | Core pages show upstream releases and retained map coverage but no site build date or deployed revision; the embedding date is explicitly unrecorded. |
| theme_toggle | partial | The injected Browse toggle works, but the landing’s existing empty theme button does not respond. The linked SLC10 pilot has no theme toggle. |
| responsive | partial | Core sampled routes fit 390px, but expanding all 63 category values widens the document to 400px. |
| load_failure | present | Blocked catalogue requests produce an explicit index-load failure; map requests display unavailable/error states instead of presenting zero coverage. |

Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.
