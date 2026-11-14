# Maintaining the knowledge-gap browser

The [implementation plan](IMPLEMENTATION.md) follows the reviewed research plan: shared CLAW export contract, TraitMech pilot, public-fleet acquisition and browser, then validation and publication. The current work is tracked in website #577 and CLAW #1212 / PR #1215.

The browser reads a retained native-data snapshot. It makes no visitor-time GitHub API calls and runs no literature scans. It does not change scientific records or infer gaps from absent fields. Default results are active knowledge gaps and human/model mismatches; all discussions and review-required candidates are separate views. Recorded does not mean scientifically validated.

## Inputs and provenance

- `sources.json` declares the sixteen public corpus repositories, immutable revisions, source roots, adapters, schema/license digests and publication holds. Support and permission are separate. Unsupported or held roots have unknown counts, never zero.
- `snapshot.json` retains normalized public items and measured coverage. Record identity includes its source path: distinct documents can share a semantic identifier. Discussion identity also includes the native discussion ID. Source renames need an explicit migration decision.
- `toolchain.json` pins the CLAW normalizer commit and module/schema bytes. CI checks out that commit, validates the snapshot and reproduces the public assets byte for byte.
- `../assets/gaps/manifest.json` points to hashed search and detail assets. Large Mechs are partitioned by stable item-ID order into numbered shards below 500 KiB compressed; index rows identify their detail shard. The search worker covers the complete index; details load on demand. JSON and CSV exports include every match, not just the current page.

Native `research_gaps` in CofactorMech and AssayMech map to `CURATION_TODO`, with unspecified lifecycle/review and no inherited record evidence. Their native target corpus/scope provides the discussion key. Scanner origin, current attribution, review state and native storage are separate contract fields. A scanner-like ID alone establishes none of them.

Dedicated evidence snippets and unconstrained notes are excluded; retained prompts and explanations can still contain attributed material and remain subject to source terms. Every item links its pinned source. Source licenses, contributor attribution and projection changes are recorded in `sources.json`.

## Refresh procedure

Use a new branch and PR. Review current public source roots, schemas and data licenses before updating pins. The dated helpers in `scripts/adhoc/` preserve how the initial configuration was researched. Keep clones and inspection data in repository `.temp/`, never commit raw corpora. Existing source working trees are read through pinned Git objects, so dirty and untracked files are excluded. Tracked ignored records remain included.

Install `scripts/fleet/requirements.txt` in a suitable Python environment. Obtain the exact CLAW revision printed by `python scripts/gaps/pin.py` in a checkout with the canonical origin. Set `CLAW_CHECKOUT` and `MECH_CHECKOUTS` to those local paths. The optional acquisition `--cache-root` can supply missing public repositories.

Run the read-only plan first, then exactly one complete TraitMech canary through the same code path as the fleet:

```sh
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --source TraitMech --output .temp/gaps-pilot.json --plan
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --source TraitMech --output .temp/gaps-pilot.json
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --snapshot .temp/gaps-pilot.json --output .temp/gaps-pilot-assets --summary .temp/gaps-pilot-summary.html --pilot
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --snapshot .temp/gaps-pilot.json --output .temp/gaps-pilot-assets --summary .temp/gaps-pilot-summary.html --pilot --check
```

Verify persisted counts, hashes and source links; inspect a corrected scanner-origin discussion and run the browser canary. If fixes change the acquisition/contract, repeat the canary before expanding. Only then acquire and build the full fleet:

```sh
python scripts/gaps/snapshot.py --claw-root "$CLAW_CHECKOUT" --repos-root "$MECH_CHECKOUTS" --output _gaps/snapshot.json
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT"
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --check
python -m unittest discover -s tests -v
node --test tests/gap-search.test.js
python scripts/fleet/assemble_page.py --check
bundle exec jekyll build --destination .temp/ci-site
```

Acquisition validates every supported, publishable record. A parse, schema, provenance or boundary failure prevents replacing the previous snapshot. Asset installation stages all outputs and rolls back on failure. Search and detail payload size budgets fail the build rather than publishing an oversized bundle. Inspect the specific failure; do not quietly drop a source or relax its count.

## Review and publication

Retain receipts under `reviews/`; browser screenshots and downloads stay under `.temp/`. The browser QA helper supports a one-case canary and then expanded desktop/mobile, URL/history, complete exports, literal markup, no-JavaScript, network failure/retry and timing checks. Its live-shell preview is supplemental. PR CI builds Jekyll in production mode and retains the `gap-browser-preview` artifact for three days. Download it beneath `.temp/` and pass its root through the helper's `--site` option, with `--assets` pointing to that build's `assets/gaps`, to test the actual layouts, includes and navigation.

Review each PR independently and read-only; file findings as issues, fix in scope, then re-review. Merge the shared contract first, then the website, only after explicit authorization for those PRs. Pinning the contract protects reproducibility before and after its merge. Verify the deployed Pages revision, manifest and populated browser before calling publication complete. Delete only the merged task branches and owned clean worktrees; preserve unrelated local work.

To roll back published data, revert the snapshot/config/toolchain/generated-assets commit together through a PR. Do not mix assets from different build IDs. Hashed assets and client verification turn a mixed or missing deployment into a visible retryable failure rather than misleading empty results.
