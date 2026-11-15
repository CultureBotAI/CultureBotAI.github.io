# Maintaining the knowledge-gap browser

The [original implementation plan](IMPLEMENTATION.md) covers the published native-discussion browser and shared export contract (website #582 and CLAW #1215). The [term explorer plan](TERM_EXPLORER.md) extends it with entity frequencies and co-occurrence, tracked in website #583.

The browser reads a retained native-data snapshot. It makes no visitor-time GitHub API calls and runs no literature scans. It does not change scientific records or infer gaps from absent fields. Default results are active knowledge gaps and human/model mismatches; all discussions and review-required candidates are separate views. Recorded does not mean scientifically validated.

The magenta section links below the title preserve search filters and support direct fragment URLs. The summary tiles count indexed `KNOWLEDGE_GAP` and `HUMAN_MODEL_MISMATCH` entries across all lifecycle states, excluding candidate entries. These snapshot-wide counts do not change with search filters. Selecting a count clears other filters and opens the corresponding gaps; unsupported or partially covered sources retain an explicit coverage label rather than claiming a measured zero.

## Inputs and provenance

- `sources.json` declares the sixteen public corpus repositories, immutable revisions, source roots, adapters, schema/license digests and publication holds. Support and permission are separate. Unsupported or held roots have unknown counts, never zero.
- `snapshot.json` retains normalized public items and measured coverage. Record identity includes its source path: distinct documents can share a semantic identifier. Discussion identity also includes the native discussion ID. Source renames need an explicit migration decision.
- `toolchain.json` pins the CLAW normalizer commit and module/schema bytes. CI checks out that commit, validates the snapshot and reproduces the public assets byte for byte.
- `term-vocabulary.json` retains candidate names, identifiers, unqualified native aliases and exact typed synonyms from every publishable pinned record root, with complete acquisition counts and source provenance. Lexical candidates include colliding identities; shared canonical entities also retain their other native owners even when an owner's local name is absent from the discussion prose. Source roots without native gap fields can still supply vocabulary. The AIMech maintained-concept publication hold also applies here.
- `../assets/gaps/manifest.json` points to hashed search, term and detail assets. Large Mechs are partitioned by stable item-ID order into numbered shards below 500 KiB compressed; index rows identify their detail shard. The search worker covers the complete index; details load on demand. JSON and CSV exports include every match, not just the current page, including exact term/pair filters.

`scripts/gaps/terms.py` performs dictionary-based entity recognition over prompt, rationale, evidence explanations, proposed experiment prose and resolution text. It excludes the owning record's metadata, handles Unicode with original-text spans, keeps canonical identifiers separate from document addresses, and leaves ambiguous names unlinked. The generated term sidecar records the policy, vocabulary digest, source coverage and every accepted occurrence. This is conservative lexical recognition, not contextual semantic disambiguation or an assertion of biological relationships. Cloud size uses raw occurrences; the adjacent counts distinguish discussions, and co-occurrence counts a pair once per discussion. Chart counts follow all ordinary search filters before applying the selected entity or pair. Source Mech restricts the questions; Term vocabulary independently restricts entity ownership. Shared entities can belong to multiple vocabularies without double-counting within a view.

Recognition policy version 2 rejects unqualified numeric forms, requires native case for compact gene-like symbols, and records source-scoped restrictions for demonstrated misleading aliases and underspecified labels. See the [precision review](reviews/terms-precision-20261115.md) for source definitions, baseline evidence and known recall limits. Scientific identities are never merged from a shared label alone.

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
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT"
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --check
python -m unittest discover -s tests -v
node --test tests/gap-search.test.js
python scripts/fleet/assemble_page.py --check
bundle exec jekyll build --destination .temp/ci-site
```

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

Review each PR independently and read-only; file findings as issues, fix in scope, then re-review. Merge the shared contract first, then the website, only after explicit authorization for those PRs. Pinning the contract protects reproducibility before and after its merge. Verify the deployed Pages revision, manifest and populated browser before calling publication complete. Delete only the merged task branches and owned clean worktrees; preserve unrelated local work.

For this rollout, `scripts/adhoc/verify_live_gap_browser_20261114.py` accepts `--expected-website-sha` and a `--report` path inside `.temp/`. It requires Playwright and an installed browser; `--browser-executable` can select one. Run `--canary` first, verify its saved receipt, then repeat without that flag. The verifier checks the successful Pages build before and after, compares live manifest/data/UI bytes with the exact website commit, follows the hub link and exercises search, full exports, detail shards and mobile navigation. It retains response headers, downloaded bodies, screenshots and measured results without changing the published site.

To roll back published data, revert the snapshot/config/toolchain/generated-assets commit together through a PR. Do not mix assets from different build IDs. Hashed assets and client verification turn a mixed or missing deployment into a visible retryable failure rather than misleading empty results.
