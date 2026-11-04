# NaturalProductMech browser audit — 2026-11-04

Pinned source `b0fb4c22274771cd75308eaf5e209b584c12bcdf`; latest successful deployment `7457625249` serves `b0fb4c22274771cd75308eaf5e209b584c12bcdf`. Last-Modified: Sat, 31 Oct 2026 10:52:36 GMT.

Exercised all 24 existing criteria across 10 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | present | Browse searches by identifier and label. CHEBI:338412: 1 of 3136 compounds match; marneral: 1 of 3136 compounds match. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 3,136-record corpus. |
| sorting | present | The Browse sort control offers Compound name (A–Z); Compound name (Z–A); Causal producers (high–low); Gene clusters (high–low); Bioactivities (high–low); Identifier (A–Z). Changing order was exercised in the browser. |
| shareable_state | present | Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored. |
| full_catalogue | present | Browse exposes the complete 3,136-compound catalogue across eight filing pathways, matching the landing and chemical-map record count. |
| record_pages | present | Sampled natural products have stable compound URLs with structure, producers, occurrence evidence, biosynthetic loci, provenance and cross-fleet exploration links. |
| term_links | partial | Anisomycin and rebeccamycin display chemical, taxon, MIBiG and GenBank identifiers, but the main producer and biosynthetic sections leave their resolver links absent. |
| evidence | partial | Anisomycin’s producer PMID:28373542 and occurrence DOI references remain plain text without PubMed or DOI anchors. |
| review_status | present | Compound headers display grounding and SEEDED workflow tags with a What these status tags mean explanation. |
| curation_history | missing | The sampled compound record views do not show dated, attributed curation events. Source/history links and mechanism summaries do not constitute a displayed event history. |
| source_link | present | Each sampled Provenance section links its own data/natural_products YAML on GitHub. |
| domain_view | present | The chemical structure map renders 3,136 compounds, the text map covers a retained 3,114-compound projection, and the sequence map renders 763 proteins across 303 records. Sampled records also show a mechanism/biosynthesis summary diagram. |
| cross_mech_links | present | Anisomycin links CHEBI:338412 directly to AntibioticMech’s anisomycin record with a same-structure/same-InChIKey qualifier; that target returns HTTP 200. |
| corpus_stats | present | The landing reports a 3,136-compound corpus with generated source, producer, occurrence and causal-graph counts. |
| category_browse | present | Eight filing-pathway cards open category indexes. The checked Terpenoids page shows all 213 compounds. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | partial | The landing links chemical-map coordinates for all 3,136 compounds, the complete chemical-search index and a 763-protein map export. These are indexes/projections rather than complete source-record exports. |
| schema_docs | partial | Downloads & Schema now links the LinkML YAML source. Reviewed navigation does not link rendered schema documentation or an explanatory schema guide. |
| license | present | Sampled pages state CC BY 4.0 project data and BSD-3-Clause code, with upstream terms retained, consistent with the pinned license files. |
| build_provenance | partial | The footer states 3,136 records and corpus SHA-256 2838a2004e52, but its date is source retrieval (2026-10-31), not a dated build of the project corpus. |
| theme_toggle | present | Selecting the theme on the landing persists across the sampled linked pages in the same browser context. |
| responsive | partial | At 390px the sampled compound pages overflow: anisomycin 409px, rebeccamycin 407px, staurosporine 415px and the long dehydrohistidyltryptophanyldiketopiperazine page 464px, on fresh and resized loads. Browse, category and maps fit. |
| load_failure | partial | Chemical-map JSON failures display an explicit error. After sequence-map JSON fails, using search replaces its error with Showing 0 of 0 proteins and no unavailable-data explanation. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
