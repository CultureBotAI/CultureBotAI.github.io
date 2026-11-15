# Term explorer review and verification

Work tracked in [#583](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/583). Vocabulary acquisition, matching and frontend implementation have separate owners. Review passes are read-only and cross those ownership boundaries; findings are filed before fixes. Final PR and full-vocabulary checks are recorded below when complete.

| Finding | Evidence and correction |
|---|---|
| [#584](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/584): ordinary “reduces” assigned chemical-reduction meaning | Retained pilot baseline has eight occurrences, seven in ordinary decrease contexts. The bare form is now excluded; explicit `METPO:2000017` remains recognizable. Regression preserves this precision/recall choice. |
| [#585](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/585): surviving combining marks disagree with lexical boundaries | The source-derived `iron` plus U+0338 case could emit a span whose normalized text differs from the matched form. Combining marks now block partial words, and exact span normalization is checked. Tests include complete marked labels, composed/decomposed text, ligatures, Hangul and emoji. |
| [#586](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/586): generic predicate verbs assigned narrower relation meanings | Bare `imports`, `produces` and `accumulates` are conservatively excluded after auditing nonchemical and nonintracellular contexts. Explicit identifiers remain available. Negative/contextual mentions of otherwise unambiguous entities still count. |
| [#587](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/587): placeholder labels and irrelevant regex alternatives | A recognized explicit identifier uses that identity for display when its source labels are only placeholders. Original labels and source references remain intact. Regex construction omits absent surfaces after retaining all concept collisions; an equivalence regression checks unchanged matching results. |
| [#588](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/588): exported filters lack recognition provenance | JSON exports capture the term asset descriptor, recognition/vocabulary hashes, policy and selected entity identities/source references. Exports abort if recognition state changes during preparation. CSV remains discussion rows only, explicitly documented in the method disclosure. |

The `terms-pilot-baseline.json` report retains the pre-fix precision evidence. `terms-pilot.json` validates every accepted occurrence's original-text span and the corrected counts. Browser receipts distinguish the supplemental local shell from actual Jekyll output; screenshots and downloaded files stay in `.temp/gap-terms-20261115/`.

The interface reuses the existing browser's worker, URL state, complete filtered exports, native buttons, site theme and source provenance. Source Mech scopes questions; Term vocabulary independently scopes entity ownership. Shared canonical identities are counted once within a view. The cloud uses raw occurrences, and co-occurrence counts a pair once per discussion among the twenty most frequent terms in that scope.

These checks do not claim contextual semantic disambiguation, complete recall, a biological interaction, or a priority score. Ambiguous aliases and selected common strings remain unlinked, and term counts include negated or contextual discussion of an entity. Public vocabulary coverage and native gap coverage remain separate; publication holds remain binding.

## Final gates

- Full vocabulary acquisition, immutable provenance and all-root coverage: pending.
- Generated sidecar reproduction, budget and precision audit: pending.
- Actual Jekyll desktop/mobile behavior, exports and load failures: pending.
- Independent review of the final PR diff and generated assets: pending.
- Publication: requires approval for the new PR; the previous release's approval does not apply.
