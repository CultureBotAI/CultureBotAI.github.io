Refresh the stale October 30 X-Mech directory and its repeated figures from one new acquisition of all fourteen Mech heads and CLAW main, bounded by **2026-11-04T11:34:25.626729+00:00**. All corpus products use those immutable pins. Shared Mech working copies and the stopped October 30 website checkout were left untouched.

| Measure | Before | After | Change |
| --- | ---: | ---: | ---: |
| Merged PRs: fourteen Mechs, CLAW and website | 7,638 | **7,908** | +270 |
| Merged PRs: fourteen Mechs only | 7,341 | 7,602 | +261 |
| Repository records | 1,087,840 | **1,087,988** | +148 |
| Published card total | 1,087,831 | **1,087,979** | +148 |
| Tracked vocabularies | 163 | 163 | 0 |

CLAW contributes eight additional merged PRs and the website one. PR counts are the pipeline's all-time GitHub totals queried during the refresh, not counts cut off at the corpus pin time. CommunityMech's nine isolates explain the difference between repository and card totals.

The largest record increases are AntibioticMech +52, ProteinTraitsMech +27, CellStructureMech +21, NaturalProductMech +20 and CMMMech +15. All 342 heatmap cells and 69 overlap-edge assets were rebuilt; 103 cell and 49 edge metadata entries changed, with no cells or edges added or removed. Census code, record globs, prefix recognition/normalization, shared-term extraction, the feature catalogue and the kg-microbe core release comparison are unchanged.

CLAW now declares 28 capabilities, adding evidence-reference validation (enabled for MediaIngredientMech, explicitly disabled with reasons in the other thirteen members). Membership remains fourteen and the governed artifact count increases from 24 to 26.

All 336 website-feature verdicts (14 sites × 24 existing criteria) received browser checks, independent skepticism and a final comparison by feature. The new November 4 baseline changes 36 statuses. Evidence distinguishes capped search, navigation indexes from scientific downloads, inaccessible schema documentation and failed-request behavior. Representative record rendering was sampled; corpus-wide claims additionally used complete indexes or source inventories. The scope and successful served revisions are recorded separately from corpus pins in `site_features.json`.

CultureMech advanced to `09f908802989670d2cc799f75f67cf56f7834178` during the run. A follow-up browser pass retained all 24 ratings and updated the schema-guide note to 51 classes and 34 enumerations. Its recipe count remains 6,325, and its corpus pin remains the common acquisition's `a74dd489720c9df96cc073ffd11568d407d3c06c`; the update checker correctly reports the later schema commit rather than silently repinning one Mech.

CellStructureMech later deployed `d4d24c6c38d06ef27a6bac2c25ed381d50e96431`, whose only additions are 22 structured-review files. Its corpus pin remains `6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc`. The deployment follow-up verifies unchanged public inputs and browser behavior separately from the pinned record counts.

CMMMech also advanced to `ff4a9841deb7e4f6e9fff025eccd2ffa07b5493c`: ten records changed, with corresponding history, reviews and regenerated pages; renderer, schema, configuration and workflow inputs did not change. The served total remains 678. Its corpus pin stays at `8bf82c8dfa25a35f12b60617b86751bc3ce7df71`; the feature-audit follow-up separately checks the newer served pages.

TaxonMech's later deployment caught up to the common corpus pin `e0cc7c86ac2107242ab499db610737f5fcad1c9b`. The nine changed files are documentation, reviews and a test; data and browser inputs are unchanged. Its focused auditor/skeptic follow-up retains all 24 ratings, including the existing URL-filter restoration limitation.

Hand-curated evidence is retained under `_fleet/reviews/refresh-20261104/`:

| Updated claims | Evidence |
| --- | --- |
| Headline and secondary counts, statuses and graph coverage | `source-excerpts-fleet.json`, `secondary-fleet.json`, dedicated NaturalProductMech recount, `comparison.json` |
| All 59 XREFs, their direction and cited paths; 13 HUB relationships | `hand-claims-review.md`, source and auxiliary receipts; pinned source links in the page |
| Writer-coverage claims narrowed to implemented paths | #534 and the hand-claims review |
| Resource-page secondary figures and reviewed status | #535 and the pinned recount |
| CLAW artifact narrative aligned with the refreshed manifest | #536 and the pinned manifest check |
| Dedicated-page recent additions and displayed pins | #537, rebuilt `recent_terms.json`, and propagation helper |
| Explicit reuse of the saved kg-microbe comparison | #539, independent adversarial review and unchanged comparison hashes |
| License caveats propagated for CMMMech and AIMech | #523 and checked license files |
| 336 feature judgments and rubric arbitration | Auditor/skeptic ledgers, `arbitration.md`, `feature-column-review.json` |

The separate kg-microbe integration check at `ba19536867b1d1e93fe14745dac6b232bffcd4d3` still describes candidate inputs, not production promotion. The scientific release comparison was not repinned. Broader feature-catalogue work in #503 and the central directory's existing 390-pixel overflow (#533) remain separate.

Pins acquired together:

| Repository | Revision |
| --- | --- |
| CultureMech | `a74dd489720c9df96cc073ffd11568d407d3c06c` |
| MediaIngredientMech | `0874614ea8a2a939c82707d19056b2208606c1b7` |
| CommunityMech | `a4e963e5bebc49fa7a9908ac441d003e3ad4a817` |
| TraitMech | `c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6` |
| proteintraitsmech | `fa794e90b67bdafe7972f48c1288e0c939c53eea` |
| AntibioticMech | `47746980c7f56e7d9a37ebb7eb4d475d3a7ea6e5` |
| CellStructureMech | `6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc` |
| HabitatMech | `13ae9f8a89e7b002257470e911453a6c7d38c0f5` |
| NaturalProductMech | `b0fb4c22274771cd75308eaf5e209b584c12bcdf` |
| TaxonMech | `e0cc7c86ac2107242ab499db610737f5fcad1c9b` |
| PathwayMech | `bc9795173651f6b032afcdd7270228392dd5ff99` |
| DUFMech | `aa7d08bcf3a9a03879d06cffd075bc083d29788f` |
| CMMMech | `8bf82c8dfa25a35f12b60617b86751bc3ce7df71` |
| AIMech | `7ad7d92709e8816ab33bc8979d7187dec109a1ab` |
| culturebotai-claw | `09b39ca8d0d1b7395249a1b3ae527ce36f7d8d7e` |

Validation:

- 246 unit tests pass; assembled-page check, pinned-CLAW manifest check, live cards, update checker and `git diff --check` pass. Compact command receipts are in `validation.json`.
- All 342 cell hashes match their summary; all pin-bearing products match the common snapshot. No shared checkout was pulled or reset.
- TraitMech was the real persisted-output canary before scans, secondary counts and browser checks expanded to the fleet. The browser canary included an independent skeptic for all 24 criteria. These verify the exercised paths, not all possible live records or failures.
- All 53 card/Explore links resolved. Every XREF and HUB relationship was rechecked against pinned implementation evidence.
- Full local Jekyll rendering is unavailable because required gems are missing. The existing central-page overflow is tracked as #533.

Snapshot: `/private/tmp/xmech-refresh-20261104-snapshot`, approximately **5.9 GB**, retained until merge. Worktree: `/private/tmp/xmech-refresh-20261104-worktree`, branch `update/xmech-refresh-20261104`, based on origin/main `56ec3db204095e425e2ed7481d4f97b997906815`.

The protected checkout's 114 dirty paths are **112 modified tracked products plus two untracked helpers**: six summaries, 61 cell assets and 45 edge assets. They belong to the unfinished snapshot bounded by `2026-10-31T03:11:08+00:00`, with 7,717 merged PRs and 1,087,866 repository records. The six derived stages persisted, but cards, audit provenance, feature judgments and assembled page remained at HEAD. Their exact pins, hashes, timestamps and completion evidence are in `_fleet/reviews/unfinished-refresh-20261030.md` and `.json`; the original snapshot's `mechs/` directory is empty. No decision about discarding or resuming that work is made here.

Closes #523.
Closes #534.
Closes #535.
Closes #536.
Closes #537.
Closes #539.
