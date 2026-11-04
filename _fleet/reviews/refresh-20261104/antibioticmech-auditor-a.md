# AntibioticMech browser audit — 2026-11-04

Pinned source `47746980c7f56e7d9a37ebb7eb4d475d3a7ea6e5`; latest successful deployment `7538651315` serves `47746980c7f56e7d9a37ebb7eb4d475d3a7ea6e5`. Last-Modified: Wed, 04 Nov 2026 05:22:46 GMT.

Exercised all 24 existing criteria across 8 live routes. Detailed actions, old claims, unique locators and replacement notes are in the adjacent JSON.

| Feature | Verdict | Replacement note |
|---|---|---|
| search | partial | Browse finds CHEBI:2637 and amikacin with matching counts, but large result sets stop at the first 500 links without result pagination. Category indexes provide separate routes through the corpus. |
| facets | present | Property filters and a reset are available in Browse. Exercised filters changed the matching counts; activating reset by keyboard restored the unfiltered view. |
| result_counts | present | Matching counts respond to identifier, label, unmatched-query and property-filter changes, separately from the 3,064-record corpus. |
| sorting | present | The Browse sort control offers Compound name (A–Z); Compound name (Z–A); Antimicrobial class (A–Z); Structural class (A–Z); Curation status (REVIEWED first); Grounding status (EXACT first). Changing order was exercised in the browser. |
| shareable_state | present | Identifier search and the exercised property-filter/sort state survive URL reload, with matching counts and controls restored. |
| full_catalogue | present | The 3,064-record browse index and linked paginated class listings provide routes into the complete corpus; the interactive result panel itself is capped at 500. |
| record_pages | present | Sampled amikacin, avibactam and D-cycloserine pages have stable URLs, source assertions, molecular context, curation histories and links to their own source records. |
| term_links | partial | Avibactam’s own identity and activity terms resolve, but four broader ChEBI identifiers still display Label unavailable; the main classification section remains incompletely labeled. |
| evidence | present | Avibactam links PMID:25406838 in its molecular-target, causal-edge and record evidence. D-cycloserine retains linked evidence for its qualified pathway correspondence. |
| review_status | present | Record headers show workflow status, including REVIEWED on avibactam; the landing distinguishes recorded workflow status from human review. |
| curation_history | present | Avibactam shows dated seeding, reseeding, review and protein/causal-graph curation events, with curator identifiers and LLM-assisted labels where recorded. |
| source_link | present | Sampled Provenance sections link their own data/antibiotics YAML. Large records also link a complete per-record JSON.gz export. |
| domain_view | present | The chemical map displays all 3,064 compounds and the sequence map 132 proteins; the corpus text map renders separately. Sampled causal mechanisms are available as node/edge tables. |
| cross_mech_links | present | D-cycloserine links to PathwayMech WikiPathways:WP5060 with source revision and qualified target/process correspondence; the target returns HTTP 200. |
| corpus_stats | present | The landing reports 3,064 compounds and generated grounding, review and mechanism statistics; its notice states 2,815 SEEDED records. |
| category_browse | present | Browse and the landing link antimicrobial class listings, including Antibacterial with 1,147 directly filed records and 1,225 including its 78-record antimycobacterial subclass; Antifungal has 609. |
| suite_nav | present | A visible suite-directory link appears on the sampled main site pages; the evidence lists each checked route and its target. |
| downloads | partial | The landing links a 3,064-entry browse index and chemical-map coordinates, while sampled record pages link complete individual JSON.gz records. No bulk complete-record corpus export is linked; the old corpus.json/corpus.csv claim is unsupported. |
| schema_docs | partial | Navigation links the annotated LinkML schema YAML successfully; no rendered schema documentation was linked from the sampled pages. |
| license | present | Sampled pages state CC BY 4.0 project data and BSD-3-Clause code, with upstream terms retained, consistent with the pinned license files. |
| build_provenance | partial | The footer displays corpus digest 6c2a5f8e3f3f and 3,064 records, but its only date is the upstream ChEBI/CARD input date 2026-08-30; it does not identify a dated build of its own corpus. |
| theme_toggle | present | Selecting the theme on the landing persists across the sampled linked pages in the same browser context. |
| responsive | present | All sampled live routes fit a 390px viewport on both fresh load and resizing from 1280px; wide content stays within its own region. |
| load_failure | partial | Chemical-map and browse-index failures are explicit. After sequence-map JSON fails, typing in search replaces the error with Showing 0 of 0 proteins, which misrepresents an unavailable dataset as empty. |

Raw captures and screenshots remain under /private/tmp; meaningful receipts are retained here. No source data or site templates were edited.
