# Independent review of TraitMech and AIMech

Reviewed on 2026-11-19 Pacific after the Group A auditor proposals were frozen.
This was a separate read-only pass over all 48 proposed judgments in
`../root/proposals.json`, the current `trait-auditor.json.gz` and
`aimech-auditor-v2.json.gz` receipts, their supplements, and retained screenshots.
The superseded AIMech v1 receipt was excluded. No files, receipts, or upstream
sites were modified during the review.

The successful deployment brackets remain at TraitMech
`1db07d7456e55572546e2215fed19b0b870f911b` and AIMech
`2d9910fad1acb4a193122b9418d910a8a72f7b8a`; served Last-Modified timestamps are
later than their deployment requests. The complete listing counts agree with
the untruncated pinned source inventories: 1,130 TraitMech records and 1,930
AIMech records. Record rendering remains sampled rather than exhaustive.

| Criterion | TraitMech review | AIMech review |
|---|---|---|
| Search | Accept present | Accept present |
| Filters | Accept present | Accept present |
| Result counts | Accept present | Accept present |
| Sorting | Accept present | Accept present |
| Linkable search | Accept present | Accept present |
| Complete catalogue | Accept present | Accept present |
| Record pages | Accept present | Accept present |
| Term links | Accept partial; correct evidence pointer | Accept present |
| Evidence links | Accept present | Accept present |
| Curation status | Accept present | Accept present |
| Curation history | Accept present | Accept partial |
| Source link | Accept present | Accept present |
| Domain visual | Accept present | Accept present |
| Cross-Mech links | Accept present; correct evidence pointer | Accept missing |
| Corpus statistics | Accept present | Accept present |
| Category browsing | Accept present | Accept present |
| Suite link | Accept present | Accept present |
| Downloads | Accept present | Accept partial |
| Schema docs | Accept partial | Accept partial |
| License | Change present to partial | Accept partial |
| Build or version | Accept present; correct evidence pointer | Accept present |
| Theme toggle | Accept present | Accept present |
| Narrow screens | Accept partial | Accept partial |
| Load errors | Accept present | Accept not applicable |

## Findings

1. **P2 — TraitMech's discussion page omits the project licenses.**
   [TraitMech issue 2098](https://github.com/CultureBotAI/TraitMech/issues/2098)
   records this finding. The reviewed `app/discussions/index.html` page has an
   empty footer and no data/code-license statement. Its complete retained body
   is 838,647 characters; the two occurrences of “license” refer to identifier
   reuse in scientific discussion, not the project terms. This requires
   `license: partial` under the same linked-page coverage rule used for Habitat.
   Evidence: `../root/trait-auditor.json.gz` at
   `/pages/https:~1~1culturebotai.github.io~1TraitMech~1app~1discussions~1index.html/desktop`.

2. **P3 — Several TraitMech feature pointers name the wrong supporting page.**
   [Hub issue 626](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/626)
   records this audit-ledger correction. `term_links` describes the unlabeled GO:0009060 cross-reference on
   `aerobic_respiration.html`, but its evidence names `animal_pathogen.html`.
   `cross_mech_links` needs the Wood–Ljungdahl source page as well as the target
   HTTP check. `build_provenance` needs the landing, Browse or map corpus footer,
   rather than the animal-pathogen record footer and source inventory. All
   supporting observations already exist in `trait-auditor.json.gz`; no new
   collection or feature-status change is necessary for these three entries.

No other actionable finding arose from this scoped pass. It checked positive
identifier and label queries, unmatched queries, facets and reset, sort rows,
URL restoration, complete listing/source counts, populated record evidence and
provenance, source/download links, map subset counts, current schema routes,
license text, theme continuity, fresh/resized 390px measurements, and retained
failure/recovery states. Screenshots corroborate TraitMech text-map overflow
and AIMech TrainingStrategy overflow. The actual live upstream implementations
were not changed or exhaustively audited.

## Targeted resolution check

After the review ended, the root editor regenerated its proposals. A separate
read-only recheck confirmed that TraitMech now has `license: partial` and a note
distinguishing its licensed templated pages from the discussion index. The
`term_links` pointer now names aerobic respiration, `cross_mech_links` names
Wood–Ljungdahl plus its target check, and `build_provenance` includes the landing
and complete captured page set. These changes address both review findings;
the upstream missing notices remain tracked by TraitMech issue 2098. Hub issue
626 records the corrected audit evidence mapping.
