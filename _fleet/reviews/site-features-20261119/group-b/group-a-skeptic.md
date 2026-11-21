# Independent Group A verdict review

Reviewed November 19, 2026, America/Los_Angeles, by the Group B auditor.
This was a read-only pass over all 144 proposed verdicts, their retained
receipts, the exact 24 catalogue criteria and the collection helpers. No
proposal, helper or evidence file was edited during the pass. This ledger was
written after the pass ended.

Reviewed proposal: `../group-a/proposals.json`, SHA-256
`e4d6610e73e814b8660d52db78c2f4f0d61605ca499a7a3128d2de472c628bfb`.

## Findings

1. **P2 — AntibioticMech cross-Mech rating applies a different scope.** The
   proposed `partial` rests on generic name-search exploration links such as
   `MediaIngredientMech/app.html?q=amikacin`. The rendered footer explicitly
   calls these “Explore across X-Mech”; they do not identify a specific target
   record. D-cycloserine separately links the specific PathwayMech WP5060 record,
   and the recorded target response is HTTP 200. The same criterion accepts
   working specific-record links in CultureMech, MediaIngredientMech and
   NaturalProductMech without treating unrelated generic search shortcuts as
   record links. Retain `present` for the specific-record feature and track the
   broken exploration routes separately. Root recorded the arbitration with
   the native AntibioticMech issue 1374.
   Evidence: [Antibiotic raw archive](../group-a/AntibioticMech/audit-1/raw.json.gz),
   `/link_checks/https:~1~1culturebotai.github.io~1PathwayMech~1pages~1records~1WikiPathways_WP5060.html`,
   and `/pages/https:~1~1culturebotai.github.io~1AntibioticMech~1pages~1antibacterial~1amikacin.html/desktop/all_links`.

2. **P3 — CellStructureMech overstates a tested map action.** The proposed
   domain-view note says that clicking a point opens its linked structure
   context. The helper clicks the canvas centre, and both the desktop and
   subsequent pointer snapshots already show the same default
   `UniProtKB:A0A0H3C8I9` / RNP-body context. The auditor confirmed that no
   separate targeted point-activation receipt exists. The populated map and
   context support `present`; describe the linked context without claiming
   this action was demonstrated. Root filed the wording finding in hub issue
   626.
   Evidence: [CellStructure raw archive](../group-a/CellStructureMech/audit-2/raw.json.gz),
   `/pages/https:~1~1culturebotai.github.io~1CellStructureMech~1pages~1sequence-map.html/desktop`
   and the same page's `/map_after_pointer`.

3. **P2 — PathwayMech saves dark mode without applying it to the page body.**
   All eight desktop page receipts have `theme=dark` and `saved_theme=dark`,
   while their body background remains `rgb(248, 250, 252)`, identical to fresh
   light contexts. The sequence-map screenshot shows a light page around dark
   plot panels and dark legend text. Read-only inspection of the public
   `pages/style.css` confirmed the cause: lines 1–22 define/use
   `--background` and `--text` for the body; manual `data-theme` rules around
   lines 168–192 instead change `--bg` and `--fg`. The manual choice therefore
   affects some regions while principal page colors follow the operating
   system. Change `theme_toggle` from `present` to `partial`, keeping persistence
   distinct from successful visual application. Root confirmed the stylesheet
   mismatch and filed PathwayMech issue 809.
   Evidence: [Pathway raw archive](../group-a/PathwayMech/audit-2/raw.json.gz),
   `/pages/*/desktop/{theme,saved_theme,background}` compared with
   `/pages/*/fresh_390/background`; retained
   `PathwayMech_pages_sequence_map_html-desktop.png` in the same attempt folder;
   [public stylesheet](https://culturebotai.github.io/PathwayMech/pages/style.css).

## Scope and receipts

Only the final accepted attempts were used. Earlier attempts were not treated
as current evidence. Each primary gzip archive decompressed successfully.
Each proposal revision agrees with the same successful deployment before and
after its audit, with a valid served Last-Modified header.

| Site | Accepted primary archive | Deployment | Reviewed revision |
| --- | --- | --- | --- |
| HabitatMech | [audit-3/raw.json.gz](../group-a/HabitatMech/audit-3/raw.json.gz) | 7722826796 | `61edb3d0ae912e8f041378e669928051fbbd509e` |
| CommunityMech | [audit-1/raw.json.gz](../group-a/CommunityMech/audit-1/raw.json.gz) | 7797876073 | `6097f1ad3d47424b3cc092fc24cdb869aee5b539` |
| TaxonMech | [audit-1/raw.json.gz](../group-a/TaxonMech/audit-1/raw.json.gz) | 7848764604 | `112cd752949da0fbb18cdfdeb1663b5dc5514c8f` |
| PathwayMech | [audit-2/raw.json.gz](../group-a/PathwayMech/audit-2/raw.json.gz) | 7845573945 | `d2f73822d650851193ce541d68c8ebd8ffac4907` |
| CellStructureMech | [audit-2/raw.json.gz](../group-a/CellStructureMech/audit-2/raw.json.gz) | 7722453069 | `7a5ef9e01fe8e8bc44f649d94b61b4b2bab5ef2b` |
| AntibioticMech | [audit-1/raw.json.gz](../group-a/AntibioticMech/audit-1/raw.json.gz) | 7723164727 | `6ec4c26ca0b650f895b4e3d7d642e5d9eb22dda7` |

Each attempt's `coverage.json` supplies complete download inventories;
`publication.json` records archived receipt hashes. Additional evidence comes
from the corresponding `followup-1.json.gz` for CommunityMech's positive search
reload and CultureMech link, TaxonMech and CellStructureMech's pinned schema
checks, and AntibioticMech's actual linked category pagination. The guessed,
unlinked Antibiotic `pages/antibacterial/index.html` 404 is excluded.

The six full-catalogue claims reconcile to complete listing/export inventories:
3,209 Habitat slugs; 512 Community slugs; 626,048 Taxon identifiers and routes;
283 Pathway identifiers and routes; 1,022 CellStructure identifiers and routes;
3,125 Antibiotic identifiers and routes. Pagination/linked categories provide
routes beyond capped global search. This is coverage evidence plus sampled
populated record pages, not an HTTP crawl of every record.

## All-criteria ledger

The table records the reviewed proposals. `P` = present, `p` = partial,
`M` = missing, `N` = not applicable. `F1` and `F3` require the status changes
above; `F2` changes the note only. All other cells were accepted against the
captured scope.

| Criterion | Habitat | Community | Taxon | Pathway | CellStructure | Antibiotic |
| --- | --- | --- | --- | --- | --- | --- |
| search | p | p | P | P | P | p |
| facets | P | P | P | P | P | P |
| result_counts | P | P | P | P | P | P |
| sorting | P | P | P | P | P | P |
| shareable_state | P | P | p | P | P | P |
| full_catalogue | P | P | P | P | P | P |
| record_pages | P | P | P | P | P | P |
| term_links | p | P | P | p | P | p |
| evidence | p | P | P | P | P | P |
| review_status | P | M | P | M | P | P |
| curation_history | P | M | P | P | P | P |
| source_link | P | P | P | P | P | P |
| domain_view | P | P | P | P | P / F2 | P |
| cross_mech_links | p | p | p | M | P | p / F1 |
| corpus_stats | P | P | P | P | P | P |
| category_browse | P | p | P | p | P | P |
| suite_nav | P | P | P | P | P | P |
| downloads | p | p | p | P | P | p |
| schema_docs | p | P | p | p | p | p |
| license | p | p | P | p | P | P |
| build_provenance | p | M | p | p | P | p |
| theme_toggle | p | p | P | P / F3 | P | P |
| responsive | p | p | P | P | P | P |
| load_failure | p | N | P | N | P | p |

For each site, `/actions` was compared with the search/facet/count/sort/reload/
reset claims; leading rows or record links were compared across sort choices.
`/pages` supplied populated bodies, term/citation/source/history anchors,
category and suite navigation, footers, fresh/resized 390px widths and actual
theme colors. `/downloads` and `coverage.json` distinguished compact indexes
from record or graph exports. Pathway's linked KGX exports include the graph
nodes, mechanistic edges, evidence and reference metadata; its plain index
alone would not justify the download verdict. `/licenses` was compared with
page statements, and `/failures` distinguished intercepted data requests from
static pages. Saved desktop map screenshots were visually inspected for all
six sites; their rendered point sets corroborate the DOM/data counts without
asserting biological validity of the projections.

The review also checked `scripts/adhoc/revalidate_group_a_20261119.py`, including
fresh mobile browser contexts, actual reset activation, map-pointer limitations,
fault injection and recovery, and the publication/coverage helper outputs.
External citation status codes were not conflated with whether the page renders
a citation link. No new live browser batch or site mutation was performed.
