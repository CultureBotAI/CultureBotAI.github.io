# Knowledge-gap embedding map

Implementation for website issue [#609](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/609). The map extends the existing browser; one point represents one indexed discussion and uses the same search, source, lifecycle and entity filters. A vocabulary selection alone retains its current meaning and does not filter discussions.

## Input and artifact contracts

`embedding-inputs.json` retains the exact text supplied to the encoder and its scientific provenance:

- `schema_version: 1`, `build_id` (discussion snapshot digest), `terms_sha256`, `term_build_id`, `vocabulary_sha256`, `source_config_sha256`, `policy`, `coverage`.
- `records`: sorted native owner records, each with `id` (existing vocabulary entity ID), `mech`, `record_id`, `canonical_id`, `label`, `description`, `description_field`, `description_status` (`present`, `missing_native_field`, or `unsupported_field`), `definition_sources`, and the existing pinned `source` descriptor.
- `items`: sorted by `discussion_id`, each with `gap_fields` (`field`, `text`), `matched_terms` (`term_id`, `record_ids`, `occurrence_count`), `record_ids`, `input_text`, and `input_sha256` (SHA-256 of UTF-8 text).

Gap prose comes from `terms.iter_item_texts`: prompt, rationale, evidence explanations, proposed experiment prose and resolution text. Each nonempty field retains its original text. The input then appends each matched native record once, not once per occurrence. Identical canonical ID/name/description blocks are deduplicated in input text while every owner remains in metadata. Canonical identity, native label and description determine block ordering. Names alone never merge scientific identities. Missing definitions retain the native label and identifier without embedding a synthetic definition or curation-note fallback. The appended descriptions do not trigger another entity-recognition pass.

`scripts/gaps/embedding_inputs.py` resolves only the owners already identified by accepted term postings, rather than reacquiring every Mech record. It reads exact pinned Git blobs from existing working-tree or bare checkouts, verifies repository identity, root permission, schema/license bytes, native record identity and raw SHA-256, and persists the permitted projection. Dirty and untracked working-tree files do not enter the result. The committed `_fleet/data/manifest.json` projection of CLAW's `FleetManifest.public()` API is the public source allowlist. Both acquisition and offline publication validation enforce it, along with the AIMech maintained-concept hold. A root without native gap support can still contribute permitted vocabulary descriptions.

`embedding-layout.json` retains inference and projection results:

- `schema_version: 1`, `build_id`, `terms_sha256`, `inputs_sha256` (canonical JSON digest of the complete input artifact), `input_policy`, `model`, `projection`, `diagnostics`, `coverage`, and `vectors` (file name, SHA-256, dtype and shape).
- `points`: sorted by discussion ID, each with `id`, finite `x` and `y`, `input_sha256`, `token_count`, `chunk_count`, `chunk_token_counts`, and `neighbors` (up to 15 objects containing `id` and `cosine_similarity`, derived from original normalized vectors).
- Full vectors are retained in `embedding-vectors.npy` in the same sorted order. They are not downloaded by visitors.

The normal asset builder validates these retained artifacts, then includes one hashed `embedding` asset in its existing atomic publication transaction. This public asset contains the layout metadata/points plus the retained `records` and compact per-discussion context references. It binds the discussion snapshot and exact term asset separately: a recognition correction can change term postings without changing the discussion build ID.

The map has a separate **5 MiB gzip budget** and loads only on request or navigation to its section. The complete asset measures 13,902,258 raw bytes and 4,344,892 gzip bytes (4.14 MiB). Original-vector neighbor identities account for most of the transfer. The larger lazy-download budget preserves all 15 neighbors, native definitions and source provenance; the existing 2 MiB initial-search budget is unchanged. The button reports the estimated compressed size. Reproduce the measurement with `scripts/adhoc/measure_gap_embedding_assets_20261115.py`; gzip estimates are not measured negotiated HTTP transfer sizes.

## Native description fields and input coverage

Only the following top-level native fields supply description text. Native `definition_source` and `definition_sources` values are retained separately for attribution; other record notes do not enter the embedding.

| Native field | Mechs |
| --- | --- |
| `definition` | HabitatMech, TraitMech, CellStructureMech, ProteinTraitsMech, NaturalProductMech, AntibioticMech, TaxonMech, AIMech imported AIO records |
| `description` | CommunityMech, PathwayMech, DUFMech, CMMMech, CultureMech, CofactorMech, AssayMech |
| No supported field at the pinned schema | MediaIngredientMech |

`description_status` is `present` for nonempty native text, `missing_native_field` for an absent or empty supported field, and `unsupported_field` when the pinned record model has no permitted description field. The last two retain `description: ""`; they do not assert that a concept lacks a scientific definition elsewhere.

The November 15 input artifact retains all **3,830 discussions** and **3,380 native owner records** for **2,624 accepted entities**. Of the discussions, 2,976 have at least one native description, 240 have matched names/identifiers only, and 614 have no accepted match and use gap text alone. Of the owner records, 2,971 have descriptions and 409 do not:

| Source with missing descriptions | Matched owners | Missing | Reason |
| --- | ---: | ---: | --- |
| CultureMech | 9 | 6 | Supported field absent/empty |
| HabitatMech | 127 | 27 | Supported field absent/empty |
| MediaIngredientMech | 217 | 217 | No supported field |
| NaturalProductMech | 103 | 26 | Supported field absent/empty |
| TaxonMech | 133 | 133 | Supported optional field absent/empty |

All other currently matched owners have descriptions. DUFMech and AssayMech have no accepted owners in this term artifact; that is a measured matching result, not missing source support or an inferred absence of knowledge gaps. These are input-acquisition counts. Inference completion, token totals and projection diagnostics must be checked against the retained layout and run receipt separately.

## Encoding and projection

`scripts/gaps/embedding_compute.py` uses the cached [BGE-large-en-v1.5](https://huggingface.co/BAAI/bge-large-en-v1.5) revision `d4aa6901d3a41ba39fb536a557fa166f842b0e09`, with 1,024-dimensional vectors. It loads locally, offline, with remote code disabled and verifies the pinned weights SHA-256 `45e1954914e29bd74080e6c1510165274ff5279421c89f76c418878732f64ae7`. The descriptor retains hashes for the tokenizer, configuration and pooling files as well as runtime/dependency versions, device and batch size. No query instruction is added. Gap prose and matched-record context form one combined text input, not separately concatenated vectors.

The tokenizer reads the complete input without truncation. Non-overlapping chunks contain at most 480 content tokens, with BERT CLS/SEP tokens added within the model's 512-token limit. Each chunk uses the normalized final-layer CLS vector. Content-token counts weight the mean of those vectors; the result is normalized again and retained as float32. Accumulation uses float64. The per-input cache binds the exact text hash, model descriptor, runtime and chunk policy. Changing device, batch size, dependency versions or input text requires a matching canary and cache identity.

The fixed [PaCMAP](https://github.com/YingfanWang/PaCMAP) configuration uses version 0.9.1, sorted IDs, seed 42, 15 neighbors, Euclidean distances between normalized vectors, FAISS neighbors, one projection thread, no PCA preprocessing, and PCA initialization. The remaining parameters are `MN_ratio=0.5`, `FP_ratio=2.0`, `num_iters=[100,100,250]`, `lr=1.0`, and two output dimensions. The full layout requires at least 32 discussions; the one-document canary verifies encoding and persistence without projecting a misleading one-point map.

Original-vector cosine neighbors have stable discussion-ID tie breaking. Diagnostics retain cosine trustworthiness at 15 neighbors, overlap between original and projected neighbors, duplicate-vector counts, and a PCA baseline's explained variance and trustworthiness. The retained vectors and coordinates are authoritative; identical floating-point results across hardware or dependency versions are not promised. A fixed seed and diagnostics do not establish parameter robustness or biological validity. Two-dimensional distances lose information, and shared wording or shared record descriptions can dominate similarity. Filters only change visible points, never coordinates.

The retained run covers 1,102,273 content tokens in 4,430 discussion chunks, with zero truncated tokens, missing discussions or zero vectors. There are 3,731 distinct input texts and 99 duplicate vector rows. PaCMAP cosine trustworthiness at 15 neighbors is 0.9186, compared with 0.7502 for the two-component PCA baseline. Mean original-neighbor overlap is 31.7% (median 26.7%): many true vector neighbors are displaced in two dimensions. Use the displayed original-vector neighbor list when assessing textual similarity.

Projection neighbors explicitly exclude each query by row identity, retaining distinct discussions with identical vectors. This repairs PaCMAP 0.9.1's positional self-removal behavior for duplicate vectors ([#615](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/615)). Candidate lookup and local-distance scaling use the pinned dependency's preprocessing and FAISS configuration. All 57,450 nearest, 30,640 mid-near and 114,900 far pairs are validated before fitting, and their hashes must remain unchanged afterward. The graph policy, pair counts and hashes are retained in projection metadata.

## Refresh commands

Run from the repository root on a feature branch. The ordinary pipeline uses `scripts/fleet/requirements.txt`. Explicit inference needs a separate environment with `scripts/gaps/requirements-embeddings.txt`; ordinary CI does not install that optional toolchain. One example environment setup is:

```sh
python3 -m venv .temp/gap-embedding-env
.temp/gap-embedding-env/bin/python -m pip install -r scripts/gaps/requirements-embeddings.txt
GAP_EMBED_PY=.temp/gap-embedding-env/bin/python
GAP_MODEL_PATH="$HOME/.cache/huggingface/hub/models--BAAI--bge-large-en-v1.5/snapshots/d4aa6901d3a41ba39fb536a557fa166f842b0e09"
GAP_EMBED_DEVICE=cpu
```

The model snapshot must already be present at `GAP_MODEL_PATH`; these commands do not download it. An existing environment with the pinned packages can be used instead. On a compatible Apple runtime, select `GAP_EMBED_DEVICE=mps` before the probe and keep that choice through the full run. Do not silently fall back to another backend after the canary.

Set `CLAW_CHECKOUT` to the pinned normalizer checkout and `MECH_CHECKOUTS` to the directory of existing native Mech repositories, as in [the main refresh procedure](README.md#refresh-procedure). The optional `--cache-root` supplies retained bare repositories for sources absent from that directory. If snapshot, vocabulary or recognition changed, first generate an intermediate term bundle; the normal build otherwise requires the complete retained map:

```sh
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --without-embeddings --output .temp/gaps-embedding-refresh-assets --summary .temp/gaps-embedding-refresh-summary.html
GAP_TERM_ASSETS=.temp/gaps-embedding-refresh-assets
```

If using the unchanged current public term bundle instead, set `GAP_TERM_ASSETS=assets/gaps`. Run the acquisition plan and exactly one native-record canary through the same launcher and cache/output paths as the full acquisition:

```sh
python scripts/gaps/embedding_inputs.py --repos-root "$MECH_CHECKOUTS" --cache-root .temp/knowledge-gaps-20261114/repos --assets "$GAP_TERM_ASSETS" --record-cache .temp/gap-embedding-20261115/records --output _gaps/embedding-inputs.json --plan
python scripts/gaps/embedding_inputs.py --repos-root "$MECH_CHECKOUTS" --cache-root .temp/knowledge-gaps-20261114/repos --assets "$GAP_TERM_ASSETS" --record-cache .temp/gap-embedding-20261115/records --output _gaps/embedding-inputs.json --canary
```

Inspect the nonempty cache JSON at the printed `cache_paths` entry: its native label/description, pinned source, raw hash and policy binding must match. This canary proves one record was acquired and persisted; it does not exercise every schema or publication root. Only then run the full acquisition and validate the retained result:

```sh
python scripts/gaps/embedding_inputs.py --repos-root "$MECH_CHECKOUTS" --cache-root .temp/knowledge-gaps-20261114/repos --assets "$GAP_TERM_ASSETS" --record-cache .temp/gap-embedding-20261115/records --output _gaps/embedding-inputs.json
python scripts/gaps/embedding_inputs.py --assets "$GAP_TERM_ASSETS" --check
```

Next probe the optional environment, inspect the tokenization plan, and encode exactly one real multichunk discussion. Keep the interpreter, model, device, batch size, cache, output paths and any launcher/environment wrapper identical for the canary and full run:

```sh
"$GAP_EMBED_PY" scripts/gaps/embedding_compute.py --model-path "$GAP_MODEL_PATH" --device "$GAP_EMBED_DEVICE" --batch-size 8 --inputs _gaps/embedding-inputs.json --cache .temp/gap-embedding-20261115/vectors --output _gaps/embedding-layout.json --vectors _gaps/embedding-vectors.npy --probe
"$GAP_EMBED_PY" scripts/gaps/embedding_compute.py --model-path "$GAP_MODEL_PATH" --device "$GAP_EMBED_DEVICE" --batch-size 8 --inputs _gaps/embedding-inputs.json --cache .temp/gap-embedding-20261115/vectors --output _gaps/embedding-layout.json --vectors _gaps/embedding-vectors.npy --plan
"$GAP_EMBED_PY" scripts/gaps/embedding_compute.py --model-path "$GAP_MODEL_PATH" --device "$GAP_EMBED_DEVICE" --batch-size 8 --inputs _gaps/embedding-inputs.json --cache .temp/gap-embedding-20261115/vectors --output _gaps/embedding-layout.json --vectors _gaps/embedding-vectors.npy --canary
```

Inspect `.temp/gap-embedding-20261115/canary.json` and the nonempty cached `.npy`/JSON pair. The receipt must record `complete`, `reloaded_vector_valid`, and `complete_token_coverage` as true. Token counts must sum across all chunks. The canary does not establish full-corpus throughput or projection quality. After inspection, run the same command without a mode flag:

```sh
"$GAP_EMBED_PY" scripts/gaps/embedding_compute.py --model-path "$GAP_MODEL_PATH" --device "$GAP_EMBED_DEVICE" --batch-size 8 --inputs _gaps/embedding-inputs.json --cache .temp/gap-embedding-20261115/vectors --output _gaps/embedding-layout.json --vectors _gaps/embedding-vectors.npy
```

The complete run writes and reloads the matrix, writes the layout and retains `.temp/gap-embedding-20261115/run.json`. Inspect that receipt and the actual artifacts, including point coverage, zero truncated tokens, chunk totals and projection diagnostics. Interrupted encoding can reuse verified cache entries with the same identity. A completed encoding can also reuse its cache when rerunning projection, but retain the successful canary receipt. Caches and receipts remain in `.temp/`; commit the input JSON, layout JSON, vector matrix, source code and regenerated public assets together.

For a projection-only correction, add `--projection-only` to that same full command. This mode requires every cached vector to be valid and exactly equal to the retained matrix, checks the previous layout's input/model bindings, and never invokes encoding. It preserves the matrix file and original-vector neighbor lists. Inspect the receipt for zero encoded inputs/chunks and the unchanged vector SHA before rebuilding the public asset. It is not a substitute for acquiring or encoding changed inputs.

Finish publication preparation using the ordinary environment:

```sh
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT"
python scripts/gaps/build.py --claw-root "$CLAW_CHECKOUT" --check
python scripts/gaps/embedding_inputs.py --check
python -m unittest discover -s tests -v
node --test tests/gap-search.test.js tests/gap-embedding.test.js
python scripts/fleet/assemble_page.py --check
bundle exec jekyll build --destination .temp/ci-site
```

The normal non-pilot build uses `_gaps/embedding-inputs.json`, `_gaps/embedding-layout.json` and `_gaps/embedding-vectors.npy` by default. Alternate retained paths can be passed through `--embedding-inputs`, `--embedding-layout`, and `--embedding-vectors`. `--without-embeddings` is for an intermediate refresh bundle, not a completed public release. CI validates the retained records, input hashes, layout, vector bytes, point IDs and neighbor scores and reproduces the hashed browser asset; it does not load/download a model, run inference, or rerun PaCMAP.

## Browser and validation

Add a seventh magenta section link and a native SVG map between the entity explorer and discussion results. Reuse verified asset loading, existing discussion selection/history and populated detail rendering. Provide source/kind/lifecycle coloring, a labelled legend, zoom/pan/reset, point inspection with matched names/definitions and source links, a complete keyboard-accessible result-list route, and JSON/CSV exports for every filtered point. Map failures must remain separate from search failures, with explicit retry and coverage states.

Validate the complete matching-ID set rather than the current result page. Reject stale term/input bindings, duplicate/unknown point IDs, nonfinite coordinates and incomplete token coverage. Exercise ordinary and entity/pair filters, stable coordinates, detail/history navigation, exports, failed loads, keyboard use and narrow screens. CI reproduces public assets from retained inputs/layout/vectors; it does not download a model or rerun inference. Review the PR independently, file and address findings, and obtain approval for that PR before merging and publishing.
