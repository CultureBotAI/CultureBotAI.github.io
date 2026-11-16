# Maintaining the knowledge-gap browser

The [original implementation plan](IMPLEMENTATION.md) covers the published native-discussion browser and shared export contract (website #582 and CLAW #1215). The [term explorer plan](TERM_EXPLORER.md) extends it with entity frequencies and co-occurrence, tracked in website #583. The [embedding-map contract and refresh commands](EMBEDDING_MAP.md) cover the text-and-record map in website #609.

The browser reads a retained native-data snapshot. It makes no visitor-time GitHub API calls and runs no literature scans. It does not change scientific records or infer gaps from absent fields. Default results are active knowledge gaps and human/model mismatches; all discussions and review-required candidates are separate views. Recorded does not mean scientifically validated.

The magenta section links below the title preserve search filters and support direct fragment URLs. The summary tiles count indexed `KNOWLEDGE_GAP` and `HUMAN_MODEL_MISMATCH` entries across all lifecycle states, excluding candidate entries, across all sixteen public corpus Mechs plus any public non-corpus fleet infrastructure (`EdgeMech`, declared in `_fleet/infrastructure.json`). These snapshot-wide counts do not change with search filters. Selecting a corpus count clears other filters and opens the corresponding gaps; unsupported, partially covered, or non-corpus infrastructure members link to explicit scope details rather than claiming a measured zero.

## Inputs and provenance

- `sources.json` declares the sixteen public corpus repositories, immutable revisions, source roots, adapters, schema/license digests and publication holds. `_fleet/infrastructure.json` declares non-corpus public fleet infrastructure (`EdgeMech`) and is validated against `_fleet/data/manifest.json` so all seventeen public fleet members are accounted for without inventing corpus counts or website URLs. Support and permission are separate. Unsupported or held roots have unknown counts, never zero.
- Public source names and repositories must belong to the committed `_fleet/data/manifest.json` allowlist projected by CLAW's `FleetManifest.public()` API. Membership validation applies before acquisition and again when retained artifacts are published; no private-name denylist is maintained.
- `snapshot.json` retains normalized public items and measured coverage. Record identity includes its source path: distinct documents can share a semantic identifier. Discussion identity also includes the native discussion ID. Source renames need an explicit migration decision.
- `toolchain.json` pins the CLAW normalizer commit and module/schema bytes. CI checks out that commit, validates the snapshot and reproduces the public assets byte for byte.
- `term-vocabulary.json` retains candidate names, identifiers, unqualified native aliases and exact typed synonyms from every publishable pinned record root, with complete acquisition counts and source provenance. Lexical candidates include colliding identities; shared canonical entities also retain their other native owners even when an owner's local name is absent from the discussion prose. Source roots without native gap fields can still supply vocabulary. The AIMech maintained-concept publication hold also applies here.
- `embedding-inputs.json` retains each discussion's complete permitted prose followed by its accepted matched records' identifiers, names and native definitions/descriptions. Every native owner keeps its source attribution even when identical text blocks are deduplicated. `embedding-layout.json` retains model/runtime, chunk coverage, fixed coordinates, original-vector cosine neighbors and projection diagnostics. `embedding-vectors.npy` retains the normalized float32 vectors in discussion-ID order; browsers do not download it.
- `../assets/gaps/manifest.json` points to hashed search, term, embedding, synthesis-analytics and detail assets. Large Mechs are partitioned by stable item-ID order into numbered shards below 500 KiB compressed; index rows identify their detail shard and carry compact facet projections (`posed_date`, `resolved_date`, `has_experiments`, `evidence_stances`, and normalized `attach_layers`). The search worker covers the complete index; details load on demand. JSON and CSV exports include every match, not just the current page, including exact term/pair, schema-layer, stance, reference, experiment and month filters.

## Cross-Mech analyses and synthesis sidecar

`assets/gaps/search-core.js` computes live filter-responsive summaries across the matching discussion scope (before entity-chip narrowing for entity charts):
- **Fleet-wide discussion breakdown:** Lists all sixteen corpus Mechs and `EdgeMech` infrastructure, stacking matching discussions by `kind`, `status`, `evidence_stance`, or normalized `attach_layer` (`attaches_to` path prefix before `#`, `.`, `[`, or `/`, with CURIEs grouped under `entity_curie` and external HTTP(S) URIs under `external_uri`). Zero-count corpus rows distinguish complete zero extractions (`CultureMech`, `HabitatMech`, `TaxonMech`) from unsupported schemas (`CMMMech`, `PathwayMech`), held roots (`AIMech`), and non-corpus infrastructure (`EdgeMech`).
- **16 × 16 Source Mech × Term vocabulary cross-pollination matrix:** Rows are discussion source Mechs and columns are Mech entity vocabularies matched in prose, separating within-Mech diagonal mentions from off-diagonal cross-Mech reuse.
- **Posed vs. resolved timeline and reference silos:** Aggregates monthly ISO `posed_date` and `resolved_date` counts alongside canonicalized `DOI:` and `PMID:` citations (folding both CURIE prefixes and `doi.org` / `pubmed.ncbi.nlm.nih.gov` URLs) and cross-Mech citation overlap.
- **Co-occurrence network and specificity metrics:** Top-20 entity pairs report shared discussions, Jaccard overlap $|A \cap B| / |A \cup B|$, and normalized pointwise mutual information $\text{NPMI}(A,B) = \ln(P(A,B)/(P(A)P(B))) / (-\ln P(A,B))$ over the active discussion scope $N$ (with $\text{NPMI}=0$ when $|A \cap B| = N$).

`scripts/gaps/analytics.py` builds the hashed `analytics.<sha16>.json` sidecar (512 KiB compressed budget, bound by SHA-256 to `snapshot.json`, `terms.*.json`, and `embedding-inputs.json`), precomputing corpus-wide synthesis views without browser-side vector math:
- **Cross-Mech semantic bridges:** Unordered original-vector cosine nearest-neighbor pairs crossing Mech boundaries (diversified to at most two featured bridges per discussion ID), Mech-to-Mech neighbor edge summaries, duplicate-input hash clusters, and per-entity neighborhood cohesion (share of top-15 neighbors sharing the entity).
- **Proposed-experiments backlog and unmatched blind-spots:** Structured `proposed_experiments` across Mechs, plus frequent bigrams and unigrams in discussions (and recorded knowledge gaps) with zero accepted dictionary entity matches. All phrases and neighbor scores are exploratory aids, not biological assertions.

`scripts/gaps/terms.py` performs dictionary-based entity recognition over prompt, rationale, evidence explanations, proposed experiment prose and resolution text. It excludes the owning record's metadata, handles Unicode with original-text spans, keeps canonical identifiers separate from document addresses, and leaves ambiguous names unlinked. The generated term sidecar records the policy, vocabulary digest, source coverage and every accepted occurrence. This is conservative lexical recognition, not contextual semantic disambiguation or an assertion of biological relationships. Cloud size uses raw occurrences; the adjacent counts distinguish discussions, and co-occurrence counts a pair once per discussion. Chart counts follow all ordinary search filters before applying the selected entity or pair. Source Mech restricts the questions; Term vocabulary independently restricts entity ownership. Shared entities can belong to multiple vocabularies without double-counting within a view.

Recognition policy version 3 retains the version-2 numeric, compact-symbol and source-scoped precision protections, and adds a canonical case rule for `PFAM:PF02597`: `ThiS family` must preserve the symbol's native case, while `family` remains case-insensitive. Ordinary `this family` prose is excluded across both vocabulary owners; explicit Pfam identifiers remain available. Bare `ThiS` remains excluded by the existing `this` stop-form rule. See the [precision review](reviews/terms-precision-20261115.md) for source definitions, baseline evidence and known recall limits. Scientific identities are never merged from a shared label alone.

The retained embedding inputs cover all 3,830 indexed discussions: 2,976 include at least one native description, 240 have matched record identifiers/names without a native description, and 614 contain gap text alone. The 2,624 accepted entities resolve to 3,380 native owners; 2,971 owners supply descriptions and 409 do not. MediaIngredientMech has no native definition/description field at its pin, so its 217 matched owners are explicitly `unsupported_field`. Optional fields absent from other records are `missing_native_field`. Neither status is filled from curation notes or generated definitions. These counts describe input coverage, not inference or biological validation; the [field mapping](EMBEDDING_MAP.md#native-description-fields-and-input-coverage) records the source distinctions.

The map uses one combined text embedding per discussion, with long inputs chunked in full. Search and entity filters select existing points without recomputing coordinates. Its two-dimensional distances are an exploratory approximation; the inspectable neighbor scores use the original normalized vectors. Labels, source coverage and repeated wording can influence either representation.

Native `research_gaps` in CofactorMech and AssayMech map to `CURATION_TODO`, with unspecified lifecycle/review and no inherited record evidence. Their native target corpus/scope provides the discussion key. Scanner origin, current attribution, review state and native storage are separate contract fields. A scanner-like ID alone establishes none of them.

Dedicated evidence snippets and unconstrained notes are excluded; retained prompts and explanations can still contain attributed material and remain subject to source terms. Every item links its pinned source. Source licenses, contributor attribution and projection changes are recorded in `sources.json`.

## Refresh procedure

Use a new branch and PR. Review current public source roots, schemas and data licenses before updating pins. The dated helpers in `scripts/adhoc/` preserve how the initial configuration was researched. Keep clones and inspection data in repository `.temp/`, never commit raw corpora. Existing source working trees are read through pinned Git objects, so dirty and untracked files are excluded. Tracked ignored records remain included.

Install `scripts/fleet/requirements.txt` in a suitable Python environment. Obtain the exact CLAW revision printed by `python scripts/gaps/pin.py` in a checkout with the canonical origin. Set `CLAW_CHECKOUT` and `MECH_CHECKOUTS` to those local paths. The optional acquisition `--cache-root` can supply missing public repositories.

Run the read-only plan first, then exactly one complete TraitMech canary through the same code path as the fleet:

```sh
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --source TraitMech --output .temp/gaps-pilot.json --plan
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --source TraitMech --output .temp/gaps-pilot.json
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --snapshot .temp/gaps-pilot.json --source TraitMech --output .temp/gaps-pilot-vocabulary.json --plan
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --snapshot .temp/gaps-pilot.json --source TraitMech --output .temp/gaps-pilot-vocabulary.json
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --snapshot .temp/gaps-pilot.json --vocabulary .temp/gaps-pilot-vocabulary.json --output .temp/gaps-pilot-assets --summary .temp/gaps-pilot-summary.html --pilot
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --snapshot .temp/gaps-pilot.json --vocabulary .temp/gaps-pilot-vocabulary.json --output .temp/gaps-pilot-assets --summary .temp/gaps-pilot-summary.html --pilot --check
```

Verify persisted counts, hashes and source links; inspect a corrected scanner-origin discussion and run the browser canary. If fixes change the acquisition/contract, repeat the canary before expanding. Only then acquire and build the full fleet:

```sh
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --output _gaps/snapshot.json
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --output _gaps/term-vocabulary.json
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --without-embeddings --output .temp/gaps-embedding-refresh-assets --summary .temp/gaps-embedding-refresh-summary.html
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --without-embeddings --output .temp/gaps-embedding-refresh-assets --summary .temp/gaps-embedding-refresh-summary.html --check
```

The normal non-pilot build now requires matching retained embedding inputs, layout and vectors by default. `--without-embeddings` produces the intermediate term bundle needed when snapshot, vocabulary or recognition changes make the previous embeddings stale. Keep that bundle under `.temp/`; it is not a publication substitute. Set `GAP_TERM_ASSETS=.temp/gaps-embedding-refresh-assets` and complete the [native-record acquisition and encoder canaries](EMBEDDING_MAP.md#refresh-commands), then their full runs. If the snapshot and term asset have not changed, reuse the existing retained embeddings and skip inference. Finish with the normal publication checks:

```sh
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT"
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --check
python scripts/gaps/embedding_inputs.py --check
python -m unittest discover -s tests -v
node --test tests/gap-search.test.js tests/gap-embedding.test.js
python scripts/fleet/assemble_page.py --check
bundle exec jekyll build --destination .temp/ci-site
```

To check inputs before the normal build installs refreshed public assets, pass `--assets "$GAP_TERM_ASSETS"`. Normal CI needs only the ordinary fleet dependencies: it validates the retained input/layout/vector bindings and reproduces the public map asset byte for byte, without downloading a model, running inference or rerunning PaCMAP. Only an explicit embedding refresh needs the separate environment in `scripts/gaps/requirements-embeddings.txt` and the pinned model already cached locally.

Acquisition validates every supported, publishable record. A parse, schema, provenance or boundary failure prevents replacing the previous snapshot. Vocabulary acquisition separately scans all publishable roots and preserves explicit coverage. Vocabulary and discussion snapshot hashes must agree. Asset installation stages all outputs and rolls back on failure. Search and term payloads each have a 2 MiB compressed budget; detail shards have a 500 KiB budget. Inspect a failure rather than quietly dropping a source or relaxing its count.

Normal vocabulary acquisition closes shared canonical ownership after lexical selection. To repair a retained version-1 vocabulary without repeating its full YAML extraction, use the pinned identity-field closure path. Run the CofactorMech canary first, inspect its saved ownership/provenance, then run the full repair:

```sh
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --close-owners _gaps/term-vocabulary.json --source CofactorMech --output .temp/cofactor-owner-canary.json --plan
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --close-owners _gaps/term-vocabulary.json --source CofactorMech --output .temp/cofactor-owner-canary.json --receipt .temp/cofactor-owner-canary-receipt.json
python scripts/gaps/vocabulary.py --repos-root "$MECH_CHECKOUTS" --close-owners _gaps/term-vocabulary.json --output _gaps/term-vocabulary.json --receipt _gaps/reviews/vocabulary-owner-closure.json
```

The repair checks original pins and native record totals, parses candidate owners or uncertain identity serializations, and records owner coverage separately. A canary with pending roots cannot pass the public build gate. Rebuild and verify all generated assets after a completed repair.

## Review and publication

Retain receipts under `reviews/`; browser screenshots and downloads stay under `.temp/`. The browser QA helper supports a one-case canary and then expanded desktop/mobile, URL/history, complete exports, literal markup, no-JavaScript, network failure/retry and timing checks. Its live-shell preview is supplemental. PR CI builds Jekyll in production mode and retains the `gap-browser-preview` artifact for three days. Download it beneath `.temp/` and pass its root through the helper's `--site` option, with `--assets` pointing to that build's `assets/gaps`, to test the actual layouts, includes and navigation.

`scripts/adhoc/check_gap_overview_20261115.py` checks the section links and statistics against independently counted index rows. Run its `--canary` and inspect the saved receipt before the full pass. Supply `--site`, `--assets`, `--summary`, `--report` and optionally `--browser-executable` as with the browser helper. The full pass exercises every Mech tile, fragment/query history, discussion permalinks, light/dark contrast, loading/error headings and no-JavaScript anchors on both sides of the mobile-header breakpoint. `--static-only` isolates the native anchor checks. Screenshots and failure diagnostics remain under `.temp/gap-overview-20261115`.

The term-specific helper, `scripts/adhoc/check_gap_terms_20261115.py`, independently counts the published postings and verifies the cloud, top-twenty pairs, source/view filters, exact term/pair downloads, keyboard/history/cold URLs and missing-index retry. Run `--canary` and inspect its receipt before the full desktop/mobile pass. Supply `--site` for actual Jekyll output. Its screenshots and downloads stay under `.temp/gap-terms-20261115/`. The live release verifier also exercises the term view when the deployed manifest declares it.

`scripts/adhoc/check_gap_embedding_20261115.py` checks the map against the complete filtered ID set, including results beyond the current page. It verifies fixed coordinates and colors, matched descriptions, discussion history, keyboard selection, pan/zoom, term/pair filters, complete JSON/CSV exports, empty states and isolated download failure/retry. Use the same `--site`, `--assets`, `--summary`, `--report` and optional `--browser-executable` arguments. Run `--canary`, inspect the saved receipt, then repeat without it for desktop/mobile and localhost failure injection. Artifacts remain under `.temp/gap-embedding-20261115/`. The live verifier compares the declared map bytes with the release commit and exercises map interactions without injecting failures on production.

Review each PR independently and read-only; file findings as issues, fix in scope, then re-review. Merge the shared contract first, then the website, only after explicit authorization for those PRs. Pinning the contract protects reproducibility before and after its merge. Verify the deployed Pages revision, manifest and populated browser before calling publication complete. Delete only the merged task branches and owned clean worktrees; preserve unrelated local work.

For this rollout, `scripts/adhoc/verify_live_gap_browser_20261114.py` accepts `--expected-website-sha` and a `--report` path inside `.temp/`. It requires Playwright and an installed browser; `--browser-executable` can select one. Run `--canary` first, verify its saved receipt, then repeat without that flag. The verifier checks the successful Pages build before and after, compares live manifest/data/UI bytes with the exact website commit, follows the hub link and exercises search, full exports, detail shards and mobile navigation. It retains response headers, downloaded bodies, screenshots and measured results without changing the published site.

To roll back published data, revert the snapshot/config/toolchain/vocabulary/embedding/generated-assets changes together through a PR. Do not mix assets from different build IDs or term/input hashes. Hashed assets and client verification turn a mixed or missing deployment into a visible retryable failure rather than misleading empty results.
