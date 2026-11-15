# Knowledge-gap browser implementation

Started 2026-11-14. Implements the [reviewed research plan](../_fleet/reviews/gap-browser-20261113/README.md), including review issues #574–576. Native discussions are the MVP; new literature scanning and domain-schema changes are later work.

## Work packages and ownership

| Order | Owner | Repository / paths | Deliverable and gate |
|---|---|---|---|
| 1 | Export-contract agent | CLAW `kg_microbe_discussions/public_export.py`, schema, tests and guide | Strict versioned public item model, deterministic identity, evidence/experiment preservation, native candidate classification. Existing exporter remains compatible. |
| 1 | Source-adapter agent | Website `_gaps/sources.json`, source-inspection helper | Current immutable public source pins, exact roots and exclusions, root-level schema support, licenses and coverage decisions for all sixteen corpus Mechs. |
| 2 | Integration owner | Website `scripts/gaps/`, `_gaps/` | Read pinned Git objects, normalize through the shared exporter and persist one complete TraitMech pilot. Verify counts, correction/candidate cases, hashes and source links before fleet extraction. |
| 3 | Browser agent | `knowledge-gaps.md`, `assets/gaps/` JS/CSS and search tests | Search worker, URL state, facets, paging, lazy detail, complete filtered export and explicit failure/empty states. May develop against the fixed contract while the pilot runs. |
| 4 | Integration owner | Generated public bundle, coverage summary, navigation and CI | Expand after successful canary, account for every public corpus root, reproducible assets, complete search and safe publication boundary. |
| 5 | Independent reviewer | Read-only PR diffs and running preview | Adversarial review, issues for every finding, fixes and re-review. Browser checks at desktop/mobile, keyboard, failure, literal markup and no-JS states. |
| 6 | Maintainer / integration owner | CLAW PR then website PR | Merge decisions are separate from implementation. Verify exact deployed revision and live populated page after authorization; delete only merged task branches/worktrees. |

## Scope and dependency decisions

- Two implementation PRs: shared export contract in CLAW, then this site's consumer/browser. The site pins the exact exported contract commit; source snapshots never depend on moving branches.
- Scientific YAML, existing Mech schemas, scanner schedules and paid providers are unchanged. Unsupported native roots remain visibly unsupported, never “zero gaps.”
- The public source list is the existing sixteen-corpus allowlist reconciled with the pinned canonical fleet manifest. Infrastructure is not a corpus. Withheld identities must not enter generated metadata, indexes or downloads.
- Origin, review state and storage are independent. Explicit review-required native scanner proposals use the candidate view; a scanner ID alone never determines a current assessment.
- Evidence reference/support/explanation and proposed experiment fields are exported. Third-party quote snippets and unconstrained curator notes are omitted from the public projection; pinned source links preserve access to context.
- Each agent owns separate paths. The integration owner alone writes aggregate generated bundles, navigation, workflow changes and commits. Helper scripts stay in their owning repository.

## Acceptance checklist

- [x] Current source and exporter pins recorded; public boundary validated.
- [x] Shared schema/normalizer and meaningful negative tests pass.
- [x] TraitMech pilot completes through the same extractor and builder used for the fleet; artifacts read back and reconciled.
- [x] Every public Mech/root has an explicit coverage state; partial/errors cannot become empty success.
- [x] Search covers the full indexed corpus, including unloaded detail shards; filters/sort/page restore from URLs.
- [x] Native candidates and corrected native discussions remain distinct; no automatic scientific validation claims.
- [x] Complete filtered JSON/CSV export, source attribution, static coverage fallback and failure recovery work.
- [x] Deterministic bundle rebuild, hash/ID/count validation, current repository checks and browser QA pass.
- [x] Independent adversarial PR review performed; findings filed and triaged.
- [x] PRs published with passing checks and exact dependency order.
- [x] After merge authorization: deployment verified and task cleanup completed.

## Validation records

Retain machine-readable acquisition/pilot/browser results under `_gaps/reviews/` and temporary clones or preview assets under `.temp/knowledge-gaps-20261114/`. Generated public files go under `assets/gaps/`; acquisition caches and raw corpus contents do not ship. Record measured results here as implementation completes; unchecked items are not claims of completion.

## Implementation decisions from current source inspection

- Tracking: [website #577](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/577), [CLAW #1212](https://github.com/CultureBotAI/culturebotai-claw/issues/1212), [exporter PR #1215](https://github.com/CultureBotAI/culturebotai-claw/pull/1215) and [website PR #582](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/582).
- CofactorMech and AssayMech have added native `research_gaps` since the research baseline. Their target `corpus`/`scope` plus source document is a stable key for the projection; duplicate keys fail. They describe curation/protocol coverage, so the adapter uses `CURATION_TODO`, unspecified lifecycle/review, and no inherited record evidence. No scientific record is changed.
- MIM semantic identifiers can repeat across distinct documents. Public identity therefore includes the repository, source path, native record ID and native discussion ID. Renames require an explicit identity migration in a later refresh; no row index or mutable prose is used.
- The renewed TraitMech canary at CLAW `014bbb6324d4c017b2868a4f88bf6acaa00e68d6` read 1,130 records and produced 925 discussions in 640 source documents. Written assets passed exact reproduction checks; `reviews/canary.json` retains the measured receipt. Origin-lineage finding [CLAW #1216](https://github.com/CultureBotAI/culturebotai-claw/issues/1216) is fixed and independently re-reviewed. All eight exporter PR checks pass.
- Website tests now include real committed-Git fixtures and deterministic bundle checks, including missing/excluded roots, false complete coverage, source/config/hash mismatches, failed acquisition retaining the previous snapshot and JSON-in-YAML native gap records.
- Review fixes [#578](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/578), [#579](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/579) and [#580](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/580) enforce root publication holds, document hash/denominator consistency and one history transition per Enter search. The browser helper retains the failing history baseline and passing regression.
- CellStructureMech integration exposed the detail size limit ([#581](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/581)). Deterministic partitioning preserves all 1,543 items in two hashed shards below the 500 KiB compressed limit. Fresh Trait and Cell builder checks pass; the acquisition path is unchanged.
- Full acquisition parsed 1,085,682 supported, publishable native records. The retained snapshot contains 3,830 discussions in 2,550 source documents, including eight current scanner candidates and ten corrected discussions with documented scanner origin. All sixteen Mechs and eighteen roots are accounted for: fifteen roots complete, PathwayMech and CMMMech unsupported, and AIMech's maintained-concept root unavailable under its publication hold.
- Full build `33c56cd4ba45f871e80cf3c4e12b19f9ab1cd662cc1d648185e80f2d0a75a864` passes strict validation and byte-for-byte reproduction. The search index is 1,167,795 compressed bytes; all eleven detail shards meet the 500 KiB compressed budget. `reviews/full-snapshot.json` retains source/root counts, classification cohorts and asset verification.
- Production Jekyll preview [CI run 43645133078](https://github.com/CultureBotAI/CultureBotAI.github.io/actions/runs/43645133078) passes 293 Python tests, twelve JavaScript tests, exact reproduction and the real site build. `reviews/browser-jekyll.json` verifies 1280/390 px layouts, eight candidate results, numbered-shard loading, all 3,830 exported rows, query/history restoration, injected load failures/retry and no-JavaScript coverage. Thirty warm worker queries measured p95 6.7 ms on the recorded macOS/Chrome reference platform; this is not a network-load measurement. Page/UI/CSS hashes preserve the tested rendering provenance.
- Published after explicit authorization: CLAW #1215 merged as `23899092a4a2aedf53ff4435c0bdc03ebd79e6be`, then website #582 as `e6ce1d445b63ffec2a0f36e322e41916fb841bf0`. Exact live Pages assets, desktop/mobile behavior and exports passed; task branches and the owned checkout were removed. The [release record](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/582#issuecomment-6888461694) links the published surface and records retained evidence. The subsequent term explorer is a separate change described in `TERM_EXPLORER.md`.
