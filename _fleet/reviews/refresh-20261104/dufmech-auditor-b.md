# DUFMech website audit — 2026-11-04

Observed deployment `aa7d08bcf3a9a03879d06cffd075bc083d29788f`; corpus pin `aa7d08bcf3a9a03879d06cffd075bc083d29788f`.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | present | PF04149, IPR007278 and Domain of unknown function (DUF397) each return one linked family from the 8,296-family catalogue. |
| facets | present | Seed status, characterization and curation status filters combine with search; Clear search and filters restores all 8,296 families. |
| result_counts | present | The live count shows one of 8,296 for each tested identifier/label and zero for an unmatched query. |
| sorting | present | The browser offers Proteins: high to low, Proteins: low to high, Pfam accession, Family name: A to Z, Structures: high to low. Changing each option reorders the displayed results. |
| shareable_state | present | Query, seed status, characterization, curation status, sort and page are retained in the URL; the exercised combined filter state restores after reload. |
| full_catalogue | present | The complete index and catalogue contain 8,296 families. The browser provides numbered pagination and links individual family pages. |
| suite_nav | present | Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory. |
| record_pages | present | Family accessions have stable families/PFxxxxx.html pages; PF04149, PF02698 and PF18141 opened successfully. |
| term_links | present | Sampled family grounding shows readable names with linked Pfam and InterPro identifiers. |
| evidence | present | Family views link frozen source descriptions and citations. Curated mechanism evidence is distinguished from imported descriptions and unresolved source citations. |
| review_status | present | Family headers and browser rows display curation status alongside seed classification and characterization tier. |
| curation_history | present | The sampled family views show retained dated curation events and reviews with attribution and outcomes. |
| source_link | present | Family pages link their individual YAML at the retained source revision, plus build-local YAML and JSON copies. |
| domain_view | present | Family pages display domain tracks and causal diagrams where available; linked text and protein sequence maps provide corpus views. |
| cross_mech_links | present | Sampled family pages link specific retained ProteinTraitsMech records, including Pfam:PF18141; the previous claim that PF18141 was outside the scan no longer applies. |
| corpus_stats | present | The landing reports 8,296 families, 8,238 with InterPro IDs, 1,906 with structures and 8,242 with AlphaFold models; seed subsets total 1,796 EX_DUF, 373 historical DUFs and 6,127 unknown candidates. |
| category_browse | present | The linked category index opens distinct paginated seed-status subsets. |
| downloads | present | Sources & schema and the catalogue link the complete index.json export containing all 8,296 families and retained provenance. |
| schema_docs | present | The linked schema.html guide documents family records, curation, evidence, history and enums, and provides the schema source. |
| license | present | Reviewed footers distinguish CC BY 4.0 project data from BSD 3-Clause code and retain third-party terms. |
| build_provenance | present | Footers identify the site build, retained corpus source revision and dated frozen upstream inputs. |
| theme_toggle | present | The System/Light/Dark selector persists Dark across the reviewed landing, families, categories, schema, sources and maps. |
| responsive | present | Reviewed landing, sampled families, category index, sources, schema and maps fit 390px; wide tables scroll within their containers. |
| load_failure | present | Blocking catalogue.json visibly reports that interactive search is unavailable while retaining static rows and pagination. |

Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.
