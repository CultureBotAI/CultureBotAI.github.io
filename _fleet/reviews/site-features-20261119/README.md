# Live browser-feature revalidation — November 19, 2026

This is a feature-only revalidation of the sixteen published corpus Mech sites.
The audit date uses America/Los_Angeles; raw observation timestamps use UTC.
It does not refresh the corpus census, card figures, corpus pins, or membership.
`scope.json` records the current canonical public fleet and verifies that its
public membership agrees with the retained manifest.

The existing 24 criteria were retained. A new deployment was a reason to inspect
the served site, not evidence that any rating changed. Each accepted capture
records a successful deployment before and after the browser pass and a served
Last-Modified date at least as recent as that deployment request. Browser checks
cover reader actions, populated details, themes, fresh and resized 390px layouts,
and failed-request recovery. Catalogue claims have separate complete-index,
manifest or deployed-source inventory evidence. Most individual record pages
were sampled; CofactorMech and AssayMech were checked exhaustively.

## Evidence and reproduction

- `root/proposals.json`: TraitMech, AIMech, CofactorMech and AssayMech auditor judgments.
- `group-a/proposals.json`: HabitatMech, CommunityMech, TaxonMech, PathwayMech,
  CellStructureMech and AntibioticMech auditor judgments.
- `group-b/proposals.json` and `group-b/evidence.json`: CultureMech,
  MediaIngredientMech, ProteinTraitsMech, DUFMech, NaturalProductMech and CMMMech.
- `changes.json`: previous and final feature values, with rating changes distinguished
  from changes to notes and counts.
- `review-complete.json`: independent reviewer assignments and completion record.

Large captures are committed as deterministic `.json.gz` files. Decompress a
file before following its JSON pointer or documented locator. Publication indexes
record the uncompressed and archive SHA-256 values. The uncompressed originals and
screenshots remain local and ignored; archives preserve the complete captured
observations. Group B's evidence index maps logical `.json` names to these archives.
Incomplete/superseded attempts are excluded: Habitat audit-1/audit-2, Pathway
audit-1, CellStructure audit-1 and root AIMech auditor v1.

The `scripts/adhoc/revalidate_*20261119*.py` helpers retain the observation,
coverage, packaging and integration procedures. Browser helpers require Python
with Playwright and an installed Chromium/Chrome executable, plus authenticated
read access through `gh`. They write new receipt paths and do not edit source
corpora. Rerunning a live observation later may observe a different deployment;
it is not a deterministic reproduction of a historical website.

The integration helper reads the immutable website baseline and the reviewed
proposals, then updates only `_fleet/data/site_features.json` and the change
ledger. `scripts/fleet/assemble_page.py` regenerates `mechs.md` from those sources.

## Scope of the EdgeMech work

[EdgeMech PR #225](https://github.com/CultureBotAI/EdgeMech/pull/225) implements a
separate sample-occurrence browser. It is not counted as a published browser in
this audit. It exposes the public 10,000-occurrence sample, not the full native
graph; its 100 historical canary reviews retain distinct source-fidelity and
scientific-support assessments. Deployment and a later live-site audit must
precede adding it to this published-site matrix.

## Findings tracked separately

- [MediaIngredientMech #1548](https://github.com/CultureBotAI/MediaIngredientMech/issues/1548):
  inconsistent data/code licence notices across browser, maps and schema routes.
- [MediaIngredientMech #888](https://github.com/CultureBotAI/MediaIngredientMech/issues/888):
  existing issue reproduced for a plain-text DOI in GYPS component evidence.
- [CommunityMech #2716](https://github.com/CultureBotAI/CommunityMech/issues/2716):
  existing issue reproduced for broken TaxonMech record handoffs.
- [CommunityMech #2959](https://github.com/CultureBotAI/CommunityMech/issues/2959):
  text and sequence maps ignore the saved dark preference.
- [TraitMech #2098](https://github.com/CultureBotAI/TraitMech/issues/2098):
  discussion index omits the project data and code licence notices.
- [PathwayMech #809](https://github.com/CultureBotAI/PathwayMech/issues/809):
  manual theme variables do not control the main page background and text.
- [AntibioticMech #1374](https://github.com/CultureBotAI/AntibioticMech/issues/1374):
  generic MediaIngredientMech exploration links use a missing route. The working
  specific-record relationship keeps that separate criterion present.
- [Hub #626](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/626):
  corrected TraitMech evidence pointers and an unproven CellStructureMech
  point-activation claim before publication.

These upstream site defects are reflected in the ratings. This revalidation does
not silently fix or close them. The new EdgeMech implementation has its own
independent review and issue record in its PR.
