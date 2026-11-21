# Cross-site criterion review and arbitration

Root compared all sixteen proposed rows against the unchanged 24-criterion
catalogue after the independent passes. The decisions below apply to the final
table. `arbitration.json` preserves the differences from original auditor
proposals; the source observations remain immutable.

| Criterion | Consistent interpretation across sites |
| --- | --- |
| search | Known labels and identifiers must work; Habitat/Antibiotic caps and Community identifier misses remain partial even when other navigation reaches the records. |
| facets | Property filters must change the result set and offer recovery/reset, not just appear as controls. |
| result_counts | Matching counts and corpus totals are distinct; map subset totals do not replace browser totals. |
| sorting | Observed ordering changes support present. Culture, Cofactor and Assay expose no sort UI. |
| shareable_state | Cold/reloaded controls and counts support present; Taxon property loss and Cofactor/Assay query-only links remain partial. |
| full_catalogue | Complete indexes/manifests or source inventories establish coverage. A capped search does not imply a capped catalogue when category pagination works. Culture's unlinked merged corpus remains partial. |
| record_pages | Stable, populated detail routes qualify, including hash routes after deferred content has loaded. |
| term_links | Readable labels and resolver links are assessed separately from raw CURIEs or unavailable source resolvers. |
| evidence | A displayed citation must have the corresponding source link. MIM's component DOI remains partial despite other working DOI links. |
| review_status | Record workflow states qualify; relationship badges, record kinds and ecological states do not substitute for whole-record status. |
| curation_history | Dated, attributed events qualify; a single created/updated metadata block does not establish an event history. |
| source_link | Individual source-file links qualify; repository home links and plain source paths are partial. |
| domain_view | Scientific diagrams/maps qualify even when their explicitly labeled scope is a subset. CellStructure's unsupported point-activation wording was removed without changing this rating. |
| cross_mech_links | Specific record relationships qualify. Broken specific Taxon record handoffs make Community partial. Habitat names related taxa with search-only handoffs, supporting partial; Taxon offers only generic searches, supporting missing. Generic Explore searches do not invalidate Antibiotic's working WP5060 relationship; their broken route is filed. |
| corpus_stats | Current live-site counts are described without altering the separate corpus census or suggesting full scientific review. |
| category_browse | Linked category/subset routes qualify; facet-only subsets remain partial where the criterion requires browsing structure. |
| suite_nav | Visible links to the central suite directory qualify; sibling links alone do not. |
| downloads | Linked full-record bulk exports qualify; complete listing indexes or projection files alone are partial. DUF metadata contains all 8,296 full record objects. |
| schema_docs | Rendered guides/class references qualify; raw annotated YAML alone remains partial. |
| license | Both project data and code terms must be stated consistently across linked pages. Trait discussions, Habitat standalone map, MIM maps/schema and other omissions are treated alike. |
| build_provenance | Own build dates, commits or dated corpus versions qualify. Undated digests and upstream-only dates remain partial. |
| theme_toggle | The persisted choice must apply to the rendered page, not only a storage key/attribute. Community maps and Pathway's mixed CSS cascade are partial. |
| responsive | Fresh and resized 390px document widths reveal overflow; contained, keyboard-accessible table scrolling is not document overflow. |
| load_failure | Exercise the failing dependency's user action before judging silence: Culture's optional point-navigation error appears on activation. False zero results remain partial; embedded-only sites are not applicable. |

The final rating changes include six present-to-partial corrections: Community
cross-Mech links and theme; MediaIngredient evidence and licence; Trait licence;
Pathway theme. Taxon's generic sibling searches change from partial to missing,
for seven changes overall. The other 377 ratings retain their previous values after
revalidation, with notes updated to current observations. These are corrections
to the recorded assessment, not proof that each defect first appeared after the
previous audit. No rating is changed merely because a deployment is newer.

The additional Taxon correction and Habitat evidence clarification came from the
separate final PR review and are tracked in hub issue 628. See `pr-review.md`.

Review limitations remain explicit: representative record rendering and scientific
links, rather than every record and external citation; current browser observations,
rather than a full corpus refresh; no rating for the unpublished EdgeMech proposal.
