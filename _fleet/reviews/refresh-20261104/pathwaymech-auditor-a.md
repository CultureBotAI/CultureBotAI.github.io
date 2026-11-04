# PathwayMech browser audit — 2026-11-04

Pinned source `bc9795173651f6b032afcdd7270228392dd5ff99`; latest successful deployment `7542706097` serves `bc9795173651f6b032afcdd7270228392dd5ff99`. Last-Modified: Wed, 04 Nov 2026 09:33:03 GMT.

Exercised all 24 existing criteria across 8 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | present | Browse searches by identifier and label. MetaCyc:PWY-6543: 1 of 280 pathways match; trehalose: 3 of 280 pathways match. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 280-record corpus. |
| sorting | present | The Browse sort control offers Pathway name (A–Z); Pathway name (Z–A); Mechanistic edges (high–low); Mechanistic edges (low–high); Identifier (A–Z); Pathway class (A–Z). Changing order was exercised in the browser. |
| shareable_state | present | Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored. |
| full_catalogue | present | Browse exposes all 280 stable pathway links, matching the landing and the 280-record downloadable pathway index. |
| record_pages | present | Sampled MetaCyc, GO and WikiPathways records have stable pages with organism scope, participants, mechanistic edges, evidence, curation history and their own YAML links. |
| term_links | partial | Organism-scope taxa are labeled and linked, but the main component and mechanistic-edge tables still display chemical, protein and reaction CURIEs without resolver links. |
| evidence | present | Sampled mechanistic edges link Rhea and PubMed references and source locations, separating source assertions from quotations. |
| review_status | missing | Sampled pathway pages show pathway type and editing history but no record-level curation or review status. |
| curation_history | present | Sampled pathway pages show dated curator actions, change summaries and retained curation-session links, including current November edits. |
| source_link | present | Read the source YAML links sampled records to their own data/pathways file in GitHub. |
| domain_view | present | Pathway pages render directed SVG networks with node selection and zoom controls. The text map renders 270 pathways and the sequence map 216 pathway centroids; the current corpus has 280 records. |
| cross_mech_links | missing | The sampled MetaCyc, GO and WikiPathways pages offer suite navigation and external authority links, but no direct links to specific sibling-Mech or kg-microbe records. |
| corpus_stats | present | The landing reports 280 pathway records, 105 taxa, 14,788 mechanistic edges and 5,917 distinct references. |
| category_browse | partial | The current Browse exposes subset filters, but sampled navigation does not link the previously claimed 15 standalone category pages. Its Pathway type options include edge-count strings, which need separate site correction. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | present | Landing links KGX node and edge TSV exports plus the complete 280-record pathway index. These and the version/checksum manifest return HTTP 200; the manifest reports 5,466 nodes and 14,788 edges. |
| schema_docs | partial | The current landing links LinkML YAML sources. The formerly claimed pages/schema.html returns HTTP 404; no rendered schema reference was linked. |
| license | partial | The landing states CC BY 4.0 data and upstream terms, but does not state a code license; sampled record and browse pages omit the data/code license statement. |
| build_provenance | partial | Landing displays an undated graph-content hash. No site build date, displayed commit or dated project-corpus version is shown on sampled pages. |
| theme_toggle | present | Selecting the theme on the landing persists across the sampled linked pages in the same browser context. |
| responsive | present | All sampled live routes fit a 390px viewport on both fresh load and resizing from 1280px; wide content stays within its own region. |
| load_failure | not_applicable | The sampled landing, Browse, record, text-map and sequence-map pages embed their data and issue no data fetch/XHR requests, so the data-request failure criterion does not apply. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
