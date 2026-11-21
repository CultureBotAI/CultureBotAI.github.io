# Independent review of the six Group B sites

Root reviewed all 144 proposed verdicts on November 19, 2026,
America/Los_Angeles, in a separate read-only pass. The auditor was a different
agent. This record was written after that pass ended. The review compared the
24-criterion catalogue, complete proposed notes, deployment evidence, raw page
states and links, action receipts, export inventories, and follow-up evidence.
It did not independently visit every record or reassess scientific claims.

**All 144 final verdicts are accepted.** This includes the two corrections from
present to partial for MediaIngredientMech evidence and licence disclosure.
The DOI is present as text without the corresponding anchor; the missing licence
statements are demonstrated across browser, map and schema routes. These findings
are recorded in existing issue 888 and new issue 1548 respectively.

The reviewed sites are CultureMech, MediaIngredientMech, ProteinTraitsMech,
DUFMech, NaturalProductMech and CMMMech. Each review refers to the deployed revision
in `../group-b/proposals.json`; all before/after deployment pairs agree and have
successful statuses and served-date checks.

| Criterion | Independent checks and rubric distinctions |
| --- | --- |
| search | Identifier, label and unmatched query actions return the documented counts and linked records; ProteinTraitsMech waits for loaded shards. |
| facets | Actual property selections change results, combined queries retain selected controls, and reset clears them. |
| result_counts | Matching counts are distinguished from corpus totals, including zero results and CMMMech's current 713 materials. |
| sorting | Sort actions change leading rows, not only the selected control; ProteinTraitsMech's supplemental populated-result run supersedes its initial empty-shell sorts. CultureMech has no sort UI. |
| shareable_state | Query/facet/sort values survive both reload and cold URL navigation where offered; zero-result combinations remain valid when their controls restore. |
| full_catalogue | Complete manifests/indexes support the totals. ProteinTraitsMech's all-five-axis action loads 429,421 records across 7,158 pages. CultureMech's unlinked merged corpus remains partial. |
| record_pages | Stable sampled routes render scientific content; ProteinTraitsMech's cold MCSA, METPO and ECOD detail captures supersede the primary hash-navigation race. |
| term_links | Visible labels and actual resolver anchors were distinguished from plain identifiers, unavailable ECOD source links and missing MediaDive source links. |
| evidence | Record anchors were compared with displayed citations; MIM's plain-text Bergey DOI and NaturalProductMech's plain-text PMID/DOI content justify partial. |
| review_status | Record workflow states were distinguished from material kind, ecological meaning, counts or an unrelated growth-review report. |
| curation_history | Dated events and curators were checked in record content; missing events remain missing for NaturalProductMech. |
| source_link | Actual individual-file anchors are present for DUF, CMM, Protein and NaturalProduct records; plain source paths on Culture and MIM records remain partial. |
| domain_view | Loaded map/graph evidence, scientific diagrams and recorded projection coverage were checked; subset maps are not described as full-corpus maps. |
| cross_mech_links | Specific related-record links were distinguished from generic sibling navigation or search links; examples include Culture's pinned community record, MIM's GYPS recipe and anisomycin's AntibioticMech record. |
| corpus_stats | Landing counts agree with complete exports or manifests. CMM's 713 materials and 609 mechanisms update feature notes only. |
| category_browse | Distinct DUF/category and natural-product pathway routes are distinguished from facet-only categories. |
| suite_nav | Actual visible X-Mech directory anchors were checked in page observations. |
| downloads | Full record content was distinguished from listing fields and plotted points. DUF's complete record-bearing metadata was verified by the additional export receipt. |
| schema_docs | Rendered class/slot guides were distinguished from raw LinkML YAML; the old CMM schema URL remains a 404 probe, not a newly claimed working route. |
| license | Page disclosures were compared across routes and with recorded repository licences; missing MIM notices justify the downgrade. |
| build_provenance | Own build dates, revisions and corpus dates were distinguished from upstream release dates and undated digests. |
| theme_toggle | Persisted choices and applied page themes were compared, including Culture's growth report and Protein's landing/SLC10 limitations. |
| responsive | Fresh and resized 390px widths agree with reported overflows; populated Protein detail captures, not loading shells, support record-layout claims. |
| load_failure | Failed-request messages and recovery were checked. CMM's embedded data is not applicable; NaturalProduct sequence input can overwrite its failure state; Culture's optional map-link failure is surfaced on activation. |

## Questions resolved by additional evidence

CultureMech's map initially keeps its 22,764 embedded points when the optional
`map-record-links.json` request fails. That alone did not prove a silent user-facing
failure. The follow-up activates an actual SVG point with Enter, then verifies
a visible `role=status` error and Browse fallback. Restoring requests and reloading
lets the same point open its populated normalized recipe. The load-failure rating
therefore remains present. See
[`culturemech-review-followup.json.gz`](../group-b/culturemech-review-followup.json.gz).

DUFMech's original compact download receipt omitted the large metadata payload.
The follow-up verifies 8,296 metadata entries containing record objects; PF04149
contains three scoped causal graphs with evidence, seven history entries and six
review entries. It matches the original index hash. This supports a full-record
bulk export, rather than only a listing export. See
[`dufmech-review-followup.json.gz`](../group-b/dufmech-review-followup.json.gz).

All primary archives, exact deployment identities, feature locators and supporting
receipts are indexed in [`../group-b/evidence.json`](../group-b/evidence.json) and
the Group B publication indexes. These clarification questions did not establish
additional defects and did not change their ratings.
