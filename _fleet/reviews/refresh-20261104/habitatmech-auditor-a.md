# HabitatMech browser audit — 2026-11-04

Pinned source `13ae9f8a89e7b002257470e911453a6c7d38c0f5`; latest successful deployment `7541124068` serves `13ae9f8a89e7b002257470e911453a6c7d38c0f5`. Last-Modified: Wed, 04 Nov 2026 08:06:59 GMT.

Exercised all 24 existing criteria across 8 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | partial | Browse finds ENVO:03000033 and marine sediment, but large match sets stop at 200 results without result pagination. Separate category pages remain paginated. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 3,209-record corpus. |
| sorting | present | The Browse sort control offers Assertions / Records (high–low); Assertions / Records (low–high); Name (A–Z); Name (Z–A); Grounding status (A–Z). Changing order was exercised in the browser. |
| shareable_state | present | Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored. |
| full_catalogue | present | Eight linked category indexes contain 3,209 records in total; paginated category pages expose records beyond the 200-result global search cap. |
| record_pages | present | The sampled marine-sediment and aquatic-macrophyte records have stable pages with source attestations, environmental context, curation events and their own YAML links. |
| term_links | partial | Marine sediment’s own ENVO grounding and broader habitat resolve, but its Associated taxa section still shows readable names beside unlinked NCBITaxon CURIEs. Nearby TaxonMech search links are not ontology resolver links. |
| evidence | partial | Marine-sediment causal-edge PMID citations and curation DOI references remain plain text without PubMed or DOI anchors. |
| review_status | present | Record headers display SEEDED or REVIEWED workflow status. The current landing says 1,915 of 3,209 are SEEDED and explicitly distinguishes workflow decisions from human review. |
| curation_history | present | Marine sediment displays dated, attributed ADD_CAUSAL_GRAPH, SOURCE_SYNONYM_SCOPED, SOURCE_PARENT_EXCLUDED and UPDATE_CAUSAL_GRAPH events with change summaries. |
| source_link | present | The marine-sediment Provenance section links its own data/habitats/aquatic/marine_sediment.yaml file. |
| domain_view | present | The semantic text map renders 3,209 descriptions and marine sediment renders a directed SVG causal graph. The old pages/map.html route returns 404; the working route is pages/text-map/. |
| cross_mech_links | partial | Associated taxa now have TaxonMech search links, but they point at /TaxonMech/browse.html rather than the working /TaxonMech/pages/browse.html route. They do not resolve to specific sibling records. |
| corpus_stats | present | The landing reports 3,209 habitats and generated grounding, corroboration and workflow counts; its current notice states 1,915 SEEDED records. |
| category_browse | present | Eight named categories link to paginated subset listings, including Aquatic with 468 records and Host-associated with 1,655. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | partial | Downloads & Schema links all eight category JSON indexes (3,209 rows together), the complete point projection and its manifest; these are compact indexes/projections rather than complete habitat records. |
| schema_docs | partial | The landing and footers now link the annotated LinkML schema YAML and imported schemas. This is source access, not rendered schema documentation. |
| license | partial | Main templates state CC BY 4.0 data, BSD-3-Clause code and upstream terms. The linked standalone text-map-source page omits the project license statement. |
| build_provenance | partial | Main footers date upstream kg-microbe extraction (2026-08-16); the linked map manifest dates that projection. They do not identify a common dated build of the project corpus. |
| theme_toggle | partial | The main Auto/Light/Dark control saves the preference across templated pages, but the linked standalone semantic map has no toggle or theme attribute and keeps its light presentation. |
| responsive | partial | The aquatic-macrophyte record is 404px wide at a 390px viewport on fresh and resized loads. The other sampled landing, Browse, category, marine-sediment and semantic-map pages fit. |
| load_failure | partial | Blocking the global Browse category-index requests and searching shows Showing 0 of 0 matching habitats without explaining that data could not load. Category fallback rows remain available. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
