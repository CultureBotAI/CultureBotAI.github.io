# TraitMech independent skeptic — 2026-11-04

Pinned and served revision: `c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6`. Deployment 7544029987 remained successful before and after the independent browser pass; Last-Modified follows deployment creation.

All 24 feature verdicts were independently exercised. Keep `term_links`, `schema_docs`, and `responsive` partial; the other 21 are present. The schema-source link is new, but is not rendered documentation.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | present | Browse searches all 1,130 records. METPO:1000801 and traitmech:000048 each return one linked record; aerobic respiration returns 14 linked matches. |
| facets | present | Category and Kind filters apply to the full corpus. Clear all filters restores all 1,130 records. |
| result_counts | present | The count updates with search and filters: pathogen gives nine matches; ECOLOGY and CLASS narrow that to eight of 1,130 records. |
| sorting | present | Browse sorts by label in either direction, identifier, category, kind, kg-microbe node count, or synonym count. |
| shareable_state | present | Search, category, kind and sort are encoded in the URL and restored on reload; pathogen with ECOLOGY and CLASS restores eight matches. |
| full_catalogue | present | Browse contains 1,130 distinct linked record rows, matching the landing count and complete JSON export. |
| record_pages | present | Each of the 1,130 records has a stable page under pages/traits/<category>/<slug>.html. At the pin, 761 records contain causal graphs. |
| term_links | partial | The Cross-references section now links GO:0009060 to Amigo, but shows no readable term label beside that CURIE. Main graph and parent terms have labels and links. |
| evidence | present | Trait and causal-edge citations on the checked record pages link to DOI or PMID sources and display supporting text. |
| review_status | present | Record headers and Identifier cards display curation status. The complete corpus includes REVIEWED, PROPOSED, SEEDED and DEPRECATED records. |
| curation_history | present | Curation history shows dated actions, curator identifiers and change summaries; some records also link detailed curation-session sidecars. |
| source_link | present | Record Source cards link the record’s own YAML on GitHub, its raw file and its edit page. |
| domain_view | present | Text, PaCMAP and graph-layout views each render 1,130 trait points; the sequence map renders 156 protein points. Sampled record pages render causal diagrams; 761 pinned records carry graphs. |
| cross_mech_links | present | Wood–Ljungdahl links to PathwayMech’s Acetogenesis record. Its context describes organism scope and retains the source revision. |
| corpus_stats | present | The landing shows 1,130 trait records, ten categories and 100.0% embedding coverage. It does not display the reviewed-record or causal-graph totals. |
| category_browse | present | Browse links ten category pages; ECOLOGY has 40 records and QUANTITATIVE_PROPERTY has seven. |
| suite_nav | present | All Mech projects links to the suite directory from the landing, Browse, categories, sampled records, all four visualizations and discussions. |
| downloads | present | The landing links the complete traits.json export, which returns all 1,130 records; maps also offer CSV exports. |
| schema_docs | partial | Navigation and footers now link the LinkML schema YAML directly. They do not link a rendered schema documentation page. |
| license | present | The checked pages consistently state CC BY 4.0 data and BSD-3-Clause code, matching LICENSE-DATA and LICENSE-CODE. |
| build_provenance | present | The site states its corpus date; record pages state their record date, separately from the METPO source release. |
| theme_toggle | present | Selecting dark on the landing persists across Browse, categories, sampled records, all four visualizations and discussions in the same browser context. |
| responsive | partial | Text and sequence maps overflow on fresh 390px loads (553px document width), and after resizing from 1280px (793px). Landing, Browse, sampled records/categories, PaCMAP, graph layout and discussions fit. |
| load_failure | present | Aborted JSON requests in all four visualizations show an explicit unavailable/error state and Retry. Blocking discussions data.js shows Discussion counts unavailable, an error and Retry loading discussions. |

Confirmed source changes: causal-graph-bearing records are761 (formerly748), while total1130, statuses427/615/50/38, categories10, and Pathway links19 on17nodes in11records to15targets remain correct.

Exact old claims, replacements, unique locators and evidence are in `trait-skeptic.json`; browser/source observations and helper provenance are retained beside it.

Scope: this canary independently verifies Trait-owned claims and13 representative live routes. Claims supported primarily by sibling repositories and global orchestration remain for the fleet-wide audit.
