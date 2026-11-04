# AIMech website audit — 2026-11-04

Observed deployment `7ad7d92709e8816ab33bc8979d7187dec109a1ab`; corpus pin `7ad7d92709e8816ab33bc8979d7187dec109a1ab`.

| Feature | Verdict | Proposed note |
|---|---|---|
| search | present | AIMech:KernelPCA returns one linked concept and Adam returns 131 matches across the 1,929-record catalogue. |
| facets | present | Origin, concept kind and AIO branch filters have Reset. Curated selects 1,487 records and curated algorithms 1,047; Reset restores all 1,929. |
| result_counts | present | The matching count changes to one for AIMech:KernelPCA, 131 for Adam and zero for an unmatched query, separately from the 1,929 total. |
| sorting | present | The browser offers Concept name (A–Z), Concept name (Z–A), Curated claims (high–low), Evidence sources (high–low), Origin (Curated first), Identifier (A–Z). Changing each option reorders the displayed results. |
| shareable_state | present | Search, origin, kind, branch and sort are encoded in the URL; reload restores the exercised values and matching count. |
| full_catalogue | present | The complete browser and its machine-readable export cover 1,929 published records; sampled record links open successfully. |
| suite_nav | present | Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory. |
| record_pages | present | Browse links static curated/<name>.html and aio/<name>.html record pages; sampled Adam, KernelPCA and TrainingStrategy pages open. |
| term_links | present | Sampled accepted AIO mappings show names with linked CURIEs; AIO class pages link their ontology IRIs and labeled parent terms. |
| evidence | present | Sampled curated claims link source rows and primary evidence URLs; the landing distinguishes 5,149 claims from 3,269 evidence citations. |
| review_status | present | Sampled curated and imported class records show their workflow state in the record header. |
| curation_history | partial | Curated pages show curator, method/model and created/updated times, but do not present an event-by-event change list; AIO pages give import provenance. |
| source_link | present | Sampled records link their individual data/curated or data/aio YAML file on GitHub. |
| domain_view | present | The graph renders 1,949 nodes and 4,256 edges; the text map retains 1,259 concepts, a subset of the 1,929-record catalogue. |
| cross_mech_links | missing | Sampled record pages provide sibling navigation/search links rather than links to specific sibling-Mech records. |
| corpus_stats | present | The landing reports 1,929 concepts (1,487 curated and 442 AIO), 5,149 curated claims and 3,269 evidence citations. |
| category_browse | present | The landing links twelve curated-kind and eight AIO-branch subset pages, including 121 architectures and 61 biases. |
| downloads | partial | Linked index.json covers all 1,929 concepts as listing metadata with claim/source counts; it omits complete claims and evidence. Map data and per-record YAML sources are also linked. |
| schema_docs | partial | The reviewed site links LinkML YAML source files. The previously recorded pages/schema.html documentation URL returns 404. |
| license | partial | Footers display CC BY 4.0 / BSD-3-Clause data and BSD-3-Clause code, but do not clearly explain which data receives each license. |
| build_provenance | present | Page footers identify the project snapshot date 2026-10-24 and digest de5b593fee12, separately from upstream AIO import provenance. |
| theme_toggle | present | Dark selected on the landing persists through Browse, sampled records, and both graph and text-map views. |
| responsive | present | Reviewed landing, Browse, sampled records and visualizations fit a 390px viewport. |
| load_failure | not_applicable | Reviewed listings, records and visualizations embed their record data; no fetch or XHR data request was observed to abort. |

Exact prior claims, replacement text and reproducible observation locators are retained in the JSON ledger. Statuses remain proposals pending independent skepticism.
