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

- [ ] Current source and exporter pins recorded; public boundary validated.
- [ ] Shared schema/normalizer and meaningful negative tests pass.
- [ ] TraitMech pilot completes through the same extractor and builder used for the fleet; artifacts read back and reconciled.
- [ ] Every public Mech/root has an explicit coverage state; partial/errors cannot become empty success.
- [ ] Search covers the full indexed corpus, including unloaded detail shards; filters/sort/page restore from URLs.
- [ ] Native candidates and corrected native discussions remain distinct; no automatic scientific validation claims.
- [ ] Complete filtered JSON/CSV export, source attribution, static coverage fallback and failure recovery work.
- [ ] Deterministic bundle rebuild, hash/ID/count validation, current repository checks and browser QA pass.
- [ ] Independent adversarial PR review performed; findings filed and triaged.
- [ ] PRs published with passing checks and exact dependency order.
- [ ] After merge authorization: deployment verified and task cleanup completed.

## Validation records

Retain machine-readable acquisition/pilot/browser results under `_gaps/reviews/` and temporary clones or preview assets under `.temp/knowledge-gaps-20261114/`. Generated public files go under `assets/gaps/`; acquisition caches and raw corpus contents do not ship. Record measured results here as implementation completes; unchecked items are not claims of completion.

## Implementation decisions from current source inspection

- Tracking: [website #577](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/577), [CLAW #1212](https://github.com/CultureBotAI/culturebotai-claw/issues/1212) and [exporter PR #1215](https://github.com/CultureBotAI/culturebotai-claw/pull/1215).
- CofactorMech and AssayMech have added native `research_gaps` since the research baseline. Their target `corpus`/`scope` plus source document is a stable key for the projection; duplicate keys fail. They describe curation/protocol coverage, so the adapter uses `CURATION_TODO`, unspecified lifecycle/review, and no inherited record evidence. No scientific record is changed.
- MIM semantic identifiers can repeat across distinct documents. Public identity therefore includes the repository, source path, native record ID and native discussion ID. Renames require an explicit identity migration in a later refresh; no row index or mutable prose is used.
- The initial full TraitMech extraction read 1,130 records and produced 925 discussions in 640 source documents. The same builder wrote hashed search/detail assets and passed its read-only reproduction check. A subsequent origin-lineage review finding is tracked as [CLAW #1216](https://github.com/CultureBotAI/culturebotai-claw/issues/1216); the final contract must pass this pilot again before fleet extraction.
- Website tests now include real committed-Git fixtures and deterministic bundle checks, including missing/excluded roots, false complete coverage, source/config/hash mismatches, failed acquisition retaining the previous snapshot and JSON-in-YAML native gap records.
