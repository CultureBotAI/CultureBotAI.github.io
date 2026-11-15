# Mech terms in knowledge-gap discussions

Implementation started 2026-11-15. Extends the published knowledge-gap browser with entity-linked occurrence frequencies and within-discussion co-occurrence. Native scientific records and the acquired discussion snapshot remain authoritative and unchanged.

## Implementation plan

1. Acquire a reproducible vocabulary from the pinned, publication-allowed Mech record roots in `sources.json`: stable record identifiers, names and declared synonyms, with source provenance. Account for all sixteen Mechs, including roots that lack native discussions. Preserve publication holds. Run and inspect one TraitMech acquisition before the fleet run.
2. Recognize entities in the public discussion prose using deterministic dictionary matching. Do not manufacture mentions from the owning record's label, aliases or source metadata. Preserve matched fields and spans, reject ambiguous surface forms, and test token boundaries, case, repeated mentions and overlapping names. Describe this as dictionary-based recognition, with explicit limitations rather than claims of complete biological entity detection.
3. Generate a hash-verified term sidecar bound to the existing gap snapshot. Check exact reproduction and enforce a download budget. Keep recognition outside the visitor's browser; the search worker joins accepted mentions to discussion IDs.
4. Extend the existing browser with independent Source Mech and Term vocabulary selectors, a clickable occurrence cloud, exact term/pair filters, complete ranked term counts and co-occurrence among the top twenty terms. Reuse native controls, URL history, full filtered exports, the site theme and explicit loading/error/empty states.
5. Run focused Python and JavaScript tests, the repository checks, and actual Jekyll browser checks at desktop and mobile sizes. Independently review the PR, file findings, address them and re-review. Request merge approval after the result is reviewable; approval of the previous release does not authorize this PR's merge.

## Counting and interaction contract

- Cloud size is based on accepted mention occurrences. Also display the number of distinct discussions containing a term. A repeated occurrence in one field contributes another occurrence, but not another discussion. Separate prose fields are counted independently.
- A co-occurrence is one discussion containing both accepted entities. Count each unordered pair once per discussion, without self-pairs. This describes co-mention, not a biological relationship or evidence that a claim is true.
- The Source Mech selector filters the discussions being counted. The Term vocabulary selector separately restricts entity owners, so readers can explore TraitMech terms across every source's questions or within one source. Shared canonical entities can belong to more than one Mech vocabulary; each is still counted once. Choosing a vocabulary clears the current term/pair selection without changing ordinary discussion filters.
- Frequencies use the complete filtered discussion scope, not the current result page. All existing view, lifecycle, review, kind and text filters apply. The initial scope remains active recorded knowledge gaps. Candidate and other discussion views remain explicitly selectable.
- Compute the cloud and top-twenty pair universe before term/pair selection, so selecting a term does not collapse the chart. Term clicks filter exact recognized membership; pair clicks require both entities in the same discussion. Clear selection, back/forward, cold URLs and exports must retain that meaning.
- Unsupported or unavailable discussion sources retain their coverage explanation. A source with no recognized mentions is not evidence of an absence of scientific gaps. Ambiguous, unmapped and out-of-vocabulary language is not assigned invented identities.

## Ownership and review evidence

Vocabulary acquisition, recognition and frontend implementation are delegated separately. The integration owner maintains the builder, CI, generated assets and release notes. Tests, source counts, vocabulary/matching policy and browser evidence will be recorded here as implementation completes.
