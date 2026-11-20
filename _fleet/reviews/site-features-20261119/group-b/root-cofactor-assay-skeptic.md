# Independent CofactorMech and AssayMech verdict review

Reviewed on November 19, 2026, America/Los_Angeles, by the Group B auditor.
The independent pass was read-only: no site, proposal, script or receipt was
changed while reviewing. This ledger was recorded after that pass ended.

**Result: no findings among the 48 proposed verdicts.** The result applies to
the two proposed entries in `../root/proposals.json` and the captured deployment
revisions below. It is a review of retained evidence, not a second live audit or
an assurance about every possible interaction.

| Site | Successful deployment | Reviewed revision |
| --- | --- | --- |
| CofactorMech | 7785837174 | `1af737829b74a619610a7ee81972357d7fe178fd` |
| AssayMech | 7785702573 | `2c39f17bfcd940c15c6f10dfdc26b4ce2d6e734e` |

The primary archives are
[`cofactor-canary.json.gz`](../root/cofactor-canary.json.gz) and
[`assay-auditor.json.gz`](../root/assay-auditor.json.gz). The supplemental receipts
are [`cofactor-supplement.json`](../root/cofactor-supplement.json) and
[`assay-supplement.json`](../root/assay-supplement.json). JSON pointers below
refer to the uncompressed document in those archives; every row was checked
for both sites. Supplemental pointers apply to the corresponding supplement.

| Criterion | Both verdicts accepted | Evidence inspected |
| --- | --- | --- |
| search | present | `/actions`, identifier, complete label and unmatched queries |
| facets | present | `/actions/category`, Assay `/actions/record_kind`, `/actions/keyboard_reset` |
| result_counts | present | `/actions`, visible totals before and after queries, filters and reset |
| sorting | missing | `/pages/index.html`, all controls and column headings |
| shareable_state | partial | `/actions/url_after_search`, `/actions/reload_after_search`, `/actions/explicit_query_url` |
| full_catalogue | present | `/manifest`, `/pages`, `/source_records`, `/no_javascript` |
| record_pages | present | All 14 Cofactor and nine Assay record entries under `/pages` |
| term_links | partial | Biotin and Ax17 page body and links; source links do not substitute for term links |
| evidence | present | Every record's evidence content and corresponding source-reference anchors |
| review_status | missing | Record kinds and relationship badges distinguished from whole-record review status |
| curation_history | present | Every record's dated Curation provenance table and history source |
| source_link | present | Every record's pinned YAML link, downloaded source and `/asset_integrity` |
| domain_view | missing | All captured pages and available navigation; no visualization offered |
| cross_mech_links | present | Biotin's scoped sibling records and Ax17's CMM records, including revision and scope |
| corpus_stats | present | `/pages/index.html` counts reconciled to `/manifest` |
| category_browse | partial | Static category tiles and functioning selectors, no category routes in navigation |
| suite_nav | present | All captured pages' All Mech projects anchors |
| downloads | partial | Record YAML and manifest links, no full-record bulk download offered |
| schema_docs | partial | Linked raw LinkML source, no rendered class/slot documentation in captured artifact |
| license | present | All footers; supplement `/license` checks exact served and repository licence bytes |
| build_provenance | present | Page footer revisions/digests, `/manifest`, all 63 `/asset_integrity` entries |
| theme_toggle | missing | All controls and `/actions/system_dark` retain the light background |
| responsive | present | All 25 routes at resized 390px plus supplement `/cold_390`; wide tables remain inside labelled, keyboard-focusable scroll regions |
| load_failure | not_applicable | `/data_failure_probe`, `/no_javascript` and request inventories show static data, with working search when fetch/XHR is blocked |

The proposed numerical claims agree with the receipts: 14 and nine records;
15 and ten rendered routes; 36 and 27 manifest asset hashes without mismatches.
The licence statement is CC BY 4.0 for curated records and CC0 for original
code/schema, matching the source bytes. The missing and partial judgments were
retained despite working static pages: linked raw schemas, record-only downloads,
relationship-specific badges and query-only URLs do not meet broader criteria.

Audit helper behavior was inspected in
`scripts/adhoc/revalidate_small_sites_20261119.py` and
`scripts/adhoc/revalidate_root_proposals_20261119.py`, including actual control
actions, response hashes, fresh mobile contexts and the distinction between
static HTML and an untested failed client-side data request.
