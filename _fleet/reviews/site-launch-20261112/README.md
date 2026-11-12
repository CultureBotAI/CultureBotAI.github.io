# Two-site directory review, 2026-11-12

This evidence set supports the focused CofactorMech and AssayMech directory
follow-up. Corpus census pins and unrelated website verdicts are preserved.

## Independent preflight review

A separate read-only reviewer verified commit
`960012db7d2b7f1dfda86e3dd39ba9308f1c20ee` against directory base
`dc9daa500c8ddeb38fc08ee6ddbe1fc54c91b595`:

- Both original pinned LICENSE files support the correction in
  [issue 565](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/565).
- Generated audit changes are confined to the two maintained-note prefixes.
  The builder-generated suffixes, corpus pins, dates, hashes, counts, manifest,
  census, statistics and assets remain unchanged.
- The correction helper replays the maintained text into the existing audit
  copy and asserts that all mechanical values remain equal. This corrects a
  description that was false at the original pins; it does not assert a new
  corpus observation or refresh the old audit's dates.

The same reviewer found three problems in the initial browser-audit helper,
before its first live run:

| Issue | Finding | Correction |
|---|---|---|
| [566](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/566) | Pages packaging omits internal dotfiles listed in the build manifest | Verify the workflow's exact uploader and its action blob; record only `.nojekyll` and `.site-generated` as unpublished packaging exclusions |
| [567](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/567) | An absolute manifest URL or redirect could leave the reviewed site | Require canonical relative paths and enforce the exact Mech root before requests and redirects |
| [568](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/568) | Repeated runs could overwrite earlier screenshots | Require a new screenshot directory before network activity |

The independent re-review found all three resolved, with no further actionable
findings, at audit-helper SHA-256
`20dbf2d6cd0a3a6673d8e3d9c03b95440ba26d9ca0046c615595d4d74d478a12`.
The reviewer did not modify files or write outputs. Three offline adversarial
guard tests passed in the implementation pass. The license correction passed
all 261 directory tests and the generated-page and whitespace checks.

## Live evidence

Live audit receipts will record the exact served revisions and observations.
An audit receipt's `complete` flag means evidence collection completed, not
that every catalogue feature is present. Each feature verdict still needs
review against the recorded browser observations and the directory's rubric.
No live success or feature verdict is asserted by this preflight record.
