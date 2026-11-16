# Next tasks

Last reconciled: **2026-11-15 (America/Los_Angeles)** against `main` at
`09a2fee12c21119040693fb0c2c5d4eb17666e8d`, GitHub issue/PR state, current source,
and retained browser evidence.

This is a prioritized working backlog, not a complete audit of the
[open issue queue](https://github.com/CultureBotAI/CultureBotAI.github.io/issues).
Reconcile each item against current source and merged PRs before starting it.
Update its status and this date when work starts or finishes; record completion
with the merge date and PR link. An open issue can describe work already shipped.
Follow the branch, PR, independent review, issue tracking, and explicit merge
approval workflow in [CLAUDE.md](CLAUDE.md).

## Recommended next: mobile Mech hub

**Pending — actionable:** [#533](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/533).
The retained preview reports a 506px document width at a 390px viewport and
identifies overflowing `.fleet-recent-card` content. The relevant CSS remains
unchanged at the reconciliation revision.

- Start with the recent-additions grid/card containment in
  [_fleet/fleet_fragment.html](_fleet/fleet_fragment.html); regenerate `mechs.md`
  through `scripts/fleet/assemble_page.py`, never by editing the generated page.
- Reproduce on a real Jekyll build, then verify at 390px and desktop widths.
  Retain browser evidence and confirm the deployed result after an approved merge.
- Investigate [#572](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/572)
  in the same pass. Preview evidence shows pointer interception by sticky
  headings/header, while keyboard activation works. A deployed pointer failure
  is **not yet established**; reproduce it before choosing a fix.
- Starting evidence: [overflow receipt](_fleet/reviews/refresh-20261112/hub-preview-layout-1/browser.json),
  [pointer receipt](_fleet/reviews/refresh-20261112/hub-preview-remaining-1/browser.json),
  and [keyboard receipt](_fleet/reviews/refresh-20261112/hub-preview-keyboard-1/browser.json).

## Other actionable work, in priority order

1. **Pending — public-page claim corrections:**
   [#151](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/151),
   [#153](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/153), and
   [#339](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/339).
   In [communitymech.md](communitymech.md), replace publication-topic placeholders
   with verified citations or accurately label them, and source or remove the
   unsupported species count. In [resources.md](resources.md) and
   [mediaingredientmech.md](mediaingredientmech.md), verify and correct
   CultureMech/MicroMediaParam roles and dependency direction. Ground claimed
   MicroGrowAgents/Mech integrations and diagram arrows in authoritative evidence.
   Check every acceptance point in the linked issues before closing them; these
   notes summarize the next work, not the full issue scope.
2. **Pending — atomic generated-data writes:**
   [#118](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/118).
   [build_subsets.py](scripts/fleet/build_subsets.py) and
   [build_data.py](scripts/fleet/build_data.py) still write directly to final
   output paths. Some handle-management fixes have shipped, so scope the remaining
   work to interrupted-write safety and inspect the other writers named by the
   issue. Use validated temporary outputs and replacement, with failure-injection
   checks showing that an interrupted write preserves the prior usable artifact.
3. **In progress — guidance link:**
   [PR #513](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/513).
   The XMechBay fleet control-contract link remains absent from agent guidance,
   and the target document exists. Review the existing PR against current main
   and rerun applicable checks; its 2026-10-26 check is not current validation.
   Do not open a duplicate implementation PR.

## Completed implementation; bookkeeping remains

- **Done — 2026-11-15, [PR #603](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/603):**
  independent membership observation dates and filtering of retained audit rows
  and notes shipped with tests in `scripts/fleet/membership_audit.py` and
  `tests/test_membership_audit.py`. Issues
  [#552](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/552) and
  [#553](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/553) remain
  open and need closure with the implementation evidence.
- **Superseded — [PR #551](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/551):**
  retire the conflicting draft in favor of #603; do not revive its older snapshot.
- **Pending — reconcile older draft [PR #503](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/503):**
  compare its remaining changes with later website-feature refreshes before
  deciding whether to continue or close it. Its implementation scope was not
  audited in this focused triage.

## Recently completed

- **Done — 2026-11-15, [PR #613](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/613):**
  the [knowledge-gap embedding browser](https://culturebotai.github.io/knowledge-gaps/#gap-map-title)
  is merged and deployed. Each point embeds combined gap text and matched Mech
  entries, including available native definitions. Feature issue #609 and review
  issues #610, #611, #612, #614, #615, and #616 are closed. Desktop/mobile checks
  and post-merge CI passed; the implementation branch was deleted.

## Validation and maintenance

For implementation changes, use the relevant tests and browser checks described
by the issue and repository guidance. The current CI definition is
[.github/workflows/fleet-page.yml](.github/workflows/fleet-page.yml); it includes
Python and JavaScript tests, generated-page and pinned-contract checks, and a
production Jekyll build. A backlog-only edit needs a source/status reconciliation,
link/path review, and the normal PR checks, not a new fleet refresh.

This file is excluded from the published Jekyll site in `_config.yml`.
