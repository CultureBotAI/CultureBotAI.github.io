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

An audit receipt's `complete` flag means evidence collection completed, not
that every catalogue feature is present. Each feature verdict needs review
against the recorded browser observations and the directory's rubric.

### CofactorMech canary

`cofactor-audit.json` records deployment `7729964604` at
`89a8ca3b37b4cd3607fdbb0b74b7b73c5c539fee`, observed from 06:19:53 to 06:20:17 UTC.
Its SHA-256 is
`835771147d1cd9c03b7ae65319d06dd66c39bb2d5074aec41f096b5cf0886234`.
The deployment stayed successful and the served revision stayed fixed. All 36
publicly packaged manifest assets matched their expected hashes; the manifest
itself has a separately recorded hash. The two internal build markers are
explicitly excluded, not claimed as publicly served.

The browser pass covered the catalogue and all 14 record pages at 1280 and 390
pixels. No document overflow, page errors or fetch/XHR data requests were
observed. Identifier/name searches, category filtering and keyboard reset
returned the expected records and counts; all 14 records remained accessible
without JavaScript. The persisted receipt and screenshots were read back.
This canary exercised the same helper, environment, output layout and network
path planned for AssayMech; it does not establish AssayMech's behavior.

A separate read-only skeptic checked every proposed feature verdict against the
receipts, current rubric and live sources. The reviewer independently confirmed
that all three pinned Biotin sibling-record URLs return HTTP 200 and that the
deployment remained successful. One finding,
[569](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/569), corrected
the schema-documentation rating from missing to partial, matching the existing
column's treatment of linked annotated LinkML YAML. The reviewer read back that
bounded correction and cleared the canary audit. The other 23 verdicts stood.

The resulting row records 14 present features, five partial, four missing and
one not applicable. These are website capabilities, not scientific-quality
ratings. AssayMech's audit remains dependent on its own successful publication.
