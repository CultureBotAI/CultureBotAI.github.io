# CellStructureMech browser audit — 2026-11-04

Pinned source `6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc`; latest successful deployment `7543581273` serves `6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc`. Last-Modified: Wed, 04 Nov 2026 10:24:05 GMT.

Exercised all 24 existing criteria across 10 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | present | Browse searches by identifier and label. GO:0097589: 1 of 1022 records shown; MitoStore: 1 of 1022 records shown; cellstructuremech:insoluble_protein_deposit: 1 of 1022 records shown. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 1,022-record corpus. |
| sorting | present | The Browse sort control offers Label (A–Z); Label (Z–A); Identifier (A–Z); Category; Kind; Mapping status. Changing order was exercised in the browser. |
| shareable_state | present | Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored. |
| full_catalogue | present | Browse exposes all 1,022 structure records, matching the landing and linked complete-corpus JSON; category pages and the 873-record grounded subset provide additional routes. |
| record_pages | present | The sampled structure records have stable pages with components, evidence, curation history and their own YAML source links. Browse and the complete export both cover 1,022 records. |
| term_links | present | Attachment organelle membrane now shows labeled GO:0033111, GO:0033099 and GO:0005886 resolver links in its mechanism Subject/Object cells, alongside labeled parent, taxon and UniProt-location links. |
| evidence | present | Sampled components, distribution statements, mechanism edges and record-level evidence link GO, DOI and PubMed references. |
| review_status | present | Sampled record headers and Browse rows show Proposed, separately from their dated curation histories. |
| curation_history | present | Attachment organelle membrane shows dated creation, expansion and review actions with named curators and change summaries. |
| source_link | present | Each sampled record links its own data/structures YAML on GitHub. |
| domain_view | present | The working embedding-map.html renders 1,022 structure points; the sequence map renders 469 proteins across 140 structures. The old note’s pages/map.html returns 404, and sampled mechanism sections are tables rather than rendered SVG diagrams. |
| cross_mech_links | present | S-layer links traitmech:000064 to TraitMech’s stable S-layer record; that target returns HTTP 200. |
| corpus_stats | present | The landing reports 1,022 structures, 13 categories and 873 GO-grounded records; its category table includes 226 membrane organelles. |
| category_browse | present | Thirteen category links lead to subset pages. The opened Microcompartment page shows all six records; the separate GO-grounded page shows 873. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | present | The landing links the complete corpus JSON with 1,022 records and the 1,022-entry catalogue index; both downloads return HTTP 200. |
| schema_docs | partial | Visible Schema and LinkML schema links open the annotated LinkML YAML source. Reviewed navigation does not expose a rendered schema reference or explanatory guide. |
| license | present | Sampled pages state CC BY 4.0 project data and BSD-3-Clause code, with upstream terms retained, consistent with the pinned license files. |
| build_provenance | present | Shared footers state corpus as of 2026-11-03 05:55:11 UTC, digest d7c5fef867d9 and 1,022 records. |
| theme_toggle | present | Selecting the theme on the landing persists across the sampled linked pages in the same browser context. |
| responsive | present | All sampled live routes fit a 390px viewport on both fresh load and resizing from 1280px; wide content stays within its own region. |
| load_failure | present | Blocking either embedding-map JSON request displays Could not load embedding artifacts: Failed to fetch. The sequence map embeds its data without a fetch. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
