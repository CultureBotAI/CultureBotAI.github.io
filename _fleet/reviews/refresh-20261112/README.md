# X-Mech directory integration, November 12, 2026

This update combines the corpus refresh from PR 564 with the separately audited
CofactorMech and AssayMech browser launches from PR 570. It retains both commit
histories. The integration keeps the newer corpus values when resolving shared
source edits and regenerates `mechs.md` from its maintained sources.

## Source checks

`freshness-check.txt` records `scripts/fleet/check_updates.py` against the
combined sources. All sixteen card headlines match their current sources, all
54 cross-reference evidence links resolve, and the public membership/capability
snapshot matches current CLAW. No measured corpus changed after the November 11
pins. The two changed README claims concern the new browsers already covered by
the separately retained `../site-launch-20261112/` evidence.

The census, overlap assets, recent-record lists, reviewed-record statistics and
historical PR counts therefore retain their November 11 acquisition provenance.
The live source check is dated November 12; it does not claim a new corpus scan
or a new historical PR tally.

The five landing-page browser spot-checks cover the changed counts and newly
published browsers. They are content checks, not complete feature audits.
The `*-final-landing.json` receipts use headers from the final rendered URL,
following client-side redirects; earlier receipts are retained as preliminary
observations. The CofactorMech canary exercised the same browser helper and
evidence path before the remaining four sites.

## Review finding and correction

[Issue 571](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/571)
records that the November 11 refresh advanced the website-feature audit date
and deployment revisions without retained evidence of the asserted complete
browser recheck. `restore_feature_provenance_20261112.py` restores the documented
November 9 baseline and preserves PR 570's separately verified November 12 rows.
Feature notes describe those dated observations, even where a current count has
since changed. Deployment drift reported by the checker remains visible rather
than being treated as a fresh review.

## Validation

- All 261 repository tests passed; the complete output is in `tests.txt`.
- Generated-page consistency and whitespace checks passed.
- Current source and landing-page checks are retained alongside this report.
- Full local Jekyll validation is unavailable because the Gemfile dependencies
  are not installed. Any local Kramdown browser preview is a component/rendering
  check, not a complete GitHub Pages build.
- The desktop preview exercises all sixteen graph nodes, both new browser links,
  the 14-record CofactorMech/ChEBI heatmap list and persisted theme choice without
  JavaScript or HTTP errors. At 390 pixels, the page has 506 pixels of horizontal
  extent (the recent-record lists overflow, within the scope of existing issue
  533). A sticky header also intercepted the attempted heatmap pointer click
  ([issue 572](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/572));
  keyboard focus and Enter successfully loaded the same 14-record list. This is
  a partial-render observation, not a confirmed regression against a full build.
  The retained preview receipts distinguish completed checks from failed ones;
  this content update does not claim to repair those layout behaviors.

The update remains on a review branch. Publishing requires the maintainer's
explicit merge decision.
