# Central-directory refresh review, 2026-10-30

Reviewed PR [527](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/527)
at `f1787aafb0e30d307dccd89d6cc7b9eb2ce21101`, then reconciled the concurrent
XREF correction `721f8f0423cd02716c84f1fa0852660ba8b01763` by fast-forward.
The shared working copy was left untouched.

## Snapshot and counts

The corpus snapshot remains bounded by `2026-10-30T04:50:55+00:00` and pins
CLAW to `18774380e032acb6da0d195214c59368cd47594f`. All fourteen source pins
remain aligned across the census, graph/cell assets, statistics and site audit.
The manifest matches the published CLAW snapshot.

The committed repository-record counts sum to **1,087,840**. The merged-PR
total advances from **7,619 to 7,638**, across fourteen Mechs, CLAW and this
website. These are distinct from the hand-curated published-site card totals.
The count derivation is retained in
`scripts/adhoc/repair_refresh_review_20261030.py`.

The existing 5.9 GB snapshot is preserved at
`/Users/marcin/.gemini/antigravity-cli/brain/a82df092-2184-496c-a3ad-fe1f9f5ee1ae/scratch/xmech-refresh-20261029`.
It is needed for reproduction until the PR is merged.

## Review findings and disposition

- [528](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/528):
  eleven XREF entries in two maintained sources retained five previous Mech
  pins. Seven distinct cited files, including textual path/commit citations,
  were verified byte-identical at old and new pins. The concurrent `721f8f0`
  commit supplies the same correction and regenerates the page.
- [529](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/529):
  feature-audit dates and served revisions were advanced without saved new
  feature-level browser evidence. Restored the supported October 26 baseline
  from published main, leaving feature verdicts intact. The corpus-audit scope
  now distinguishes that baseline from deployment freshness checks.
- [530](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/530):
  the PR description used incorrect per-repository PR counts and an incorrect
  record total. Corrected the description using committed baseline/new
  statistics. For example, CLAW advances from 227 to 228 merged PRs and
  AntibioticMech from 701 to 702.

All findings belong in this refresh. The separate broader website-feature
review in PR 503 remains independent; deployment and landing-page smoke checks
do not rejudge every feature in the catalogue.

## Verification

- Baseline and initial corrected trees: 244 unit tests passed in each run.
  The final tree adds two deployment-audit regression tests, for 246 passing
  tests. Their review findings and mutation checks are documented in the
  [fleet deployment report](fleet-pages-20261030.md).
- Generated `mechs.md` matches its maintained sources.
- Manifest check: fourteen members match CLAW at its pinned revision.
- `build_site_audit.py` regenerated provenance from the same snapshot at
  `2026-10-31T00:54:45Z`, recording live growth separately from snapshot cards.
- Live card check: ten exact matches and four within the documented 14-day,
  50-percent grace: CMMMech 663 to 668, CellStructureMech 1,001 to 1,008,
  PathwayMech 275 to 276, ProteinTraitsMech 429,394 to 429,406.
- `git diff --check` passed.
- A full local Jekyll render was not available: `bundle check` reports missing
  gems. No claim of a completed local Jekyll render is made.

No merge was performed. Publication of this central snapshot still requires
the maintainer's merge decision.
