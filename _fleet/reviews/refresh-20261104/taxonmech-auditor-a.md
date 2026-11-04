# TaxonMech browser audit — 2026-11-04

Pinned source `e0cc7c86ac2107242ab499db610737f5fcad1c9b`; latest successful deployment `7538952744` serves `b04590a7a416eb934f67e7c04416e37924f10ec8`. Last-Modified: Wed, 04 Nov 2026 05:47:18 GMT.

Exercised all 24 existing criteria across 9 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | present | Browse searches by identifier and label. NCBITaxon:2173: 32 of 626048 records match · page 1 of 1.; Methanobrevibacter smithii: 26 of 626048 records match · page 1 of 1.; NCBITaxon:562: 259 of 626048 records match · page 1 of 2.. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 626,048-record corpus. |
| sorting | present | The Browse sort control offers Default (corpus order); Taxon name (A–Z); Taxon name (Z–A); NCBI ID (numeric); Taxonomic rank; BacDive strains (high–low); GTDB mappings (high–low); Attesting sources (high–low). Changing order was exercised in the browser. |
| shareable_state | partial | Search and sort restore from the URL, but changing domain to Bacteria and rank to species does not encode those filters. Reload changes 553,073 matches back to all 626,048. |
| full_catalogue | present | The browser covers 626,048 records across 3,131 pages; Next was exercised to page 2. Domain and type-strain subsets provide additional entry points. |
| record_pages | present | Stable taxon.html?id=NCBITaxon:N routes open individual records, including Methanobrevibacter smithii and Escherichia coli, with paged strain details. |
| term_links | present | Sampled taxonomy sections show named NCBI lineage terms and resolver links for NCBI identifiers, LPSN entries and GTDB names. |
| evidence | present | Methanobrevibacter smithii links its LPSN DOI references and PMID:390357; strain details retain source links. |
| review_status | present | Sampled record headers and browse rows display SEEDED workflow status; the browser also exposes its Deprecated filter. |
| curation_history | present | Methanobrevibacter smithii shows a dated seed_from_sources event with curator, action, source list and change summary. |
| source_link | present | Sampled taxon views link their own data/taxa YAML in the repository. |
| domain_view | present | Record pages show labeled, linked taxonomy lineages. The separate corpus map renders 31,258 embedded taxa; it is a subset of the 626,048-record corpus. |
| cross_mech_links | partial | Sampled details retain kgmicrobe.strain identifiers as plain text. Suite and exploratory links do not provide direct links for those named cross-Mech records. |
| corpus_stats | present | The landing shows 626,048 taxa, 100,745 distinct strains and 20,648 taxa with a type strain. The live Archaea subset now contains 14,013 records. |
| category_browse | present | Landing links domain and type-strain listings. Archaea shows 14,013 records and the type-strain subset 20,648, with pagination. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | partial | The linked index.json.gz contains 626,048 catalogue rows, and its manifest records format and checksum. It is a browse index rather than full taxon records; individual pages link YAML, but no bulk complete-record export was linked. |
| schema_docs | partial | Visible Schema and LinkML schema links now open the annotated YAML source, while reviewed navigation lacks rendered schema documentation. |
| license | present | Sampled pages state CC BY 4.0 project data and BSD-3-Clause code, with upstream terms retained, consistent with the pinned license files. |
| build_provenance | partial | The footer now identifies corpus digest 959c8dfd8771 and 626,048 records, but provides no own build date or commit. Sources dates describe upstream snapshots. |
| theme_toggle | present | Selecting the theme on the landing persists across the sampled linked pages in the same browser context. |
| responsive | present | All sampled live routes fit a 390px viewport on both fresh load and resizing from 1280px; wide content stays within its own region. |
| load_failure | present | Blocking the search index preserves static pagination and says Search is unavailable. Blocked detail shards and corpus-map data display explicit load errors. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
