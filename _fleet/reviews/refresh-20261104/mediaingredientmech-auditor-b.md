# MediaIngredientMech website audit — 2026-11-04

Observed deployment `b538ec76094e0d2d0667e5c3bd2455b24deceded`; corpus pin `0874614ea8a2a939c82707d19056b2208606c1b7`.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | present | UNMAPPED_0196 and table salt each return one linked ingredient; CHEBI:63895 returns two of the 2,956 records. |
| facets | present | Mapping status, ontology source and mapping quality filters combine with search. AMBIGUOUS gives one record; Clear search and filters restores all 2,956. |
| result_counts | present | Showing N of 2956 ingredients changes to one for UNMAPPED_0196, two for CHEBI:63895 and zero for an unmatched query. |
| sorting | present | The browser offers Default Order, Name (A → Z), Name (Z → A), Media Count (Most → Least), Occurrences (Most → Least), Synonyms (Most → Least). Changing each option reorders the displayed results. |
| shareable_state | present | Search, status, source, quality and sort values are encoded in query parameters and restore with the same matching count after reload. |
| full_catalogue | present | The complete browser and its machine-readable export cover 2,956 published records; sampled record links open successfully. |
| suite_nav | present | Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory. |
| record_pages | present | Mapped, rejected and unmapped ingredients have stable record URLs; sampled NaCl, GYPS and glucose pages open with mapping, evidence and history sections. |
| term_links | present | Sampled ingredient groundings display names with resolver links for ontology terms and component identities; local registry identities can remain plain text. |
| evidence | present | NaCl and GYPS expose linked PMID, DOI and source-URL references in their evidence sections. |
| review_status | present | Record headers state mapping status and quality. Runtime metadata reports 2,611 MAPPED, 262 UNMAPPED, 82 REJECTED and one AMBIGUOUS ingredient. |
| curation_history | present | Sampled ingredient pages show Curation history tables with timestamp, curator, action and change details. |
| source_link | partial | Sampled record footers name data/ingredients/...yaml as plain text; their anchors do not link that individual YAML source. |
| domain_view | present | Text and chemical embedding maps render, and sampled records display role/partonomy diagrams. Embedding coverage is separate from the 2,956-record catalogue total. |
| cross_mech_links | present | GYPS links CultureMech:002799 to its individual normalized recipe from the related-recipe and comparison-evidence sections. |
| corpus_stats | present | Runtime landing tiles show 2,956 ingredients, 2,611 mapped and 88% coverage; the linked catalogue metadata distinguishes all four mapping statuses. |
| category_browse | partial | The record index has identifier-prefix sections, while the main browser offers property filters; these do not form standalone category pages. |
| downloads | partial | The landing links catalogue JSON and CSV covering all 2,956 ingredients, but they contain mapping/search fields rather than complete records with components, evidence and history. |
| schema_docs | present | The visible schema reference links rendered class, slot, enum and type documentation, including schema/classes-IngredientRecord.html. |
| license | present | The landing and sampled record footers distinguish CC BY 4.0 project data from BSD-3-Clause code. |
| build_provenance | present | Generated timestamps and a linked build receipt identify the current record build, including NaCl at 2026-11-04T07:37:37+00:00. |
| theme_toggle | present | Dark selected on the landing carries across the browser, record index, sampled ingredients, maps and schema documentation. |
| responsive | present | The reviewed landing, browser, record index, ingredient pages, maps and valid schema pages fit a 390px viewport. |
| load_failure | present | Blocking the catalogue request displays unavailable counters, Ingredients could not be loaded and a retry control. |

Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.
