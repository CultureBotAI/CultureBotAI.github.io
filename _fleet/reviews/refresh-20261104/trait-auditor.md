# TraitMech auditor — 2026-11-04

Pin `c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6`. Real Chromium browser run 2026-11-04T11:39:02.785879+00:00 to 2026-11-04T11:40:49.143267+00:00.

Deployment7544029987 remained successful at the exact pin before and after the run. Latest status2026-11-04T10:51:27Z; Last-Modified Wed,04Nov2026 10:51:17GMT.

All24features exercised.21present,3partial: term_links,schema_docs,responsive. JSON contains every action/result receipt, proposed replacement and pinned source excerpt.

| Feature | Verdict | Observation |
|---|---|---|
| search | present | Browse searches all 1,130 records: METPO:1004002 and traitmech:000616 each return one linked record; bipolar mating system returns two. |
| facets | present | Browse provides Category and Kind selectors plus Clear filters. Combining pathogen, ECOLOGY and CLASS gives eight records; reset restores all 1,130. |
| result_counts | present | The count responds to search and property filters: identifiers give 1 of 1,130 records shown; pathogen plus ECOLOGY and CLASS gives 8 of 1,130. |
| sorting | present | Browse offers label, identifier, category, kind, kg-microbe node-count and synonym-count ordering. Reversing label order changes the first row from 2,3-butanediol fermentation to Zorya type III system. |
| shareable_state | present | Search, category and kind are written to the URL. Reloading ?q=pathogen&category=ECOLOGY&kind=CLASS restores the controls and eight matches. |
| full_catalogue | present | Browse exposes 1,130 distinct record links, matching the landing total and all 1,130 record HTML paths at the pin. |
| record_pages | present | All 1,130 traits have static pages under pages/traits/<category>/<slug>.html. Sampled pages show overview, grounding, curation and source sections; 761 source records carry causal graphs. |
| term_links | partial | Record identifiers have readable labels and resolver links. Aerobic respiration links GO:0009060 in Cross-references, but that whole section still lacks a readable term label. |
| evidence | present | Animal pathogen and aerobic respiration link their trait and causal-edge DOI citations and display supporting text. |
| review_status | present | Record headers and Identifier cards show workflow status, including REVIEWED on animal pathogen; the complete corpus retains all four mapping statuses. |
| curation_history | present | Sampled record pages display dated curation events, attributed curators and change summaries. |
| source_link | present | Record Source cards link View YAML on GitHub, Raw YAML and Edit on GitHub for the record’s own data/traits YAML. |
| domain_view | present | Sampled record pages render causal SVG diagrams; 761 source records carry causal graphs. PaCMAP, text and graph-layout maps each render 1,130 traits, and the sequence map renders 156 associated proteins. These source counts do not imply that every graph was visually inspected. |
| cross_mech_links | present | Wood–Ljungdahl’s Pathway context links to PathwayMech WikiPathways:WP5019. The target returns HTTP 200; the trait page retains organism scope and the target revision. |
| corpus_stats | present | The landing page shows 1,130 trait records, 10 categories and 100.0% embedding coverage. Reviewed and causal-graph totals are corpus-source statistics, not landing tiles. |
| category_browse | present | Browse links ten category pages with counts; the opened ECOLOGY page contains 40 records and QUANTITATIVE_PROPERTY contains seven. |
| suite_nav | present | All Mech projects links the landing, Browse, sampled categories and records, all four maps and the discussions index to the suite directory. |
| downloads | present | The site links Download traits.json, a complete 1,130-record bulk JSON export. Downloaded map exports contain 1,130 traits or 156 proteins as labeled. |
| schema_docs | partial | Visible Schema and LinkML schema links open the annotated LinkML YAML source successfully. They provide source access; the reviewed navigation does not link rendered schema documentation or the explanatory schema guide. |
| license | present | Sampled page footers state CC BY 4.0 project data and BSD-3-Clause code, with third-party source terms retained; these match the pinned license files. |
| build_provenance | present | Landing, Browse and map footers give a dated version of the project corpus, alongside the METPO baseline and record count. |
| theme_toggle | present | Selecting dark on the landing persists through Browse, two categories, three records, all four maps and the discussions index in the same browser context. |
| responsive | partial | At 390px, the text and sequence maps overflow: 553px document width on fresh load and 793px after resizing from 1280px. The other ten sampled routes, including PaCMAP and graph layout, fit 390px. |
| load_failure | present | Aborted JSON requests produce explicit map failure messages and Retry; retry after restoring requests recovers 1,130 traits or 156 proteins. Aborting discussion data produces Discussion counts unavailable and a retry prompt. |

## Hand-claim corrections

- Causal graphs:748→761 in audit_notes and resources;1,130total,427reviewed,615proposed,50deprecated,38seeded unchanged.
- Feature notes: ecology40; combined-filter8; correct sort options; landing counts only1,130/10/100%; linked but unlabeled GOxref; working schema-source link; current map overflow measurements.
- PathwayContext remains19links/17nodes/11records/15targets.
- Remove “nearly every TraitMech write script goes through them” unless the fleet audit supplies a current writer denominator. Adoption itself is supported by module docstrings.
- Relationship claims owned by sibling repositories remain pending their respective audits.

## Limits

This is a current24-feature browser audit, not a new34-feature audit or exhaustive rendering of1,130records. Raw capture is outside the repository; committed receipts preserve the meaningful evidence. No central source data, original checkout,GitHub objects or commits were changed.
