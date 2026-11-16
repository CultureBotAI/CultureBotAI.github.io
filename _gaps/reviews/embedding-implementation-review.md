# Embedding browser implementation and review

PR [#613](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/613), feature [#609](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/609), November 15, 2026.

The browser embeds complete discussion text followed by the identifiers, names and permitted native descriptions of accepted matched Mech entries. All 3,830 discussions and 3,380 native owners are retained. Of the discussions, 2,976 contain native descriptions, 240 contain matched labels without descriptions, and 614 use discussion text alone. No additional entity recognition runs on the added descriptions.

## Recorded findings

| Issue | Finding | Resolution |
| --- | --- | --- |
| [#610](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/610) | A repeated encoder canary could succeed entirely from cache. | Canary mode always performs one fresh complete inference and verifies persistence. A populated-cache recanary encoded three chunks and reproduced the original vector checksum. |
| [#611](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/611) | The declared model revision enforced weights but only recorded auxiliary file hashes. | All seven required model/tokenizer/configuration files have fixed SHA-256 checks before inference. |
| [#612](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/612) | CSV formula shielding changed negative numeric map coordinates into text. | Finite typed numbers retain numeric CSV representation; untrusted text still uses the existing formula protection. The regression failed before the fix and passed afterward. |
| [#614](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/614) | Missing, invalid or nonfinite projection diagnostics could pass publication and produce browser-invalid JSON. | Required diagnostic fields and ranges are validated; strict serialization rejects nonfinite values anywhere in the map. Independently re-reviewed without further findings. |
| [#615](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/615) | PaCMAP's positional self removal was unsafe for the 99 duplicate vector rows. | Explicit identity filtering removes self at any rank and preserves zero-distance peers. All three pair families are checked before fitting and hash-checked afterward. Projection-only regeneration preserved the vector matrix and original-space neighbors; independently re-reviewed without further findings. |
| [#616](https://github.com/CultureBotAI/CultureBotAI.github.io/issues/616) | Mobile markers shrank to roughly 1.4 CSS pixels in radius and were difficult to see or select. | Markers retain 4 CSS-pixel radii (7 when selected) through zoom/resize, with visible boundaries in both themes. Rendered-size and real-pointer checks are included in browser QA. |

The acquisition/publication review and compute review were separate, read-only passes over code the respective reviewer had not authored. An independent UI pass at `dd8566f` found no additional defects in filtering, pagination, async/history handling, keyboard controls, exports, injection protection or isolated map failures.

## Evidence and limits

The first model canary and full local encoding receipts are retained as `embedding-model-canary.json` and `embedding-model-run.json`. The latter records 309.85 seconds for the previously uncached inputs; including the canary, 3,731 distinct input texts cover all 3,830 discussions. The matrix accounts for 1,102,273 content tokens in 4,430 discussion chunks, with zero truncation or missing vectors. `embedding-model-recanary.json` proves fresh inference after the cache was populated. The first encoding receipt predates the separately reviewed projection graph repair; it remains evidence for the unchanged vector matrix.

`embedding-projection-run.json` records the corrected projection: 3,830 verified cache rows, zero inference, and unchanged vector SHA `d80aff4cb9b470bf9de79b265425cb2a3965fed97afc6a1929feb7d06362f3a9`. The explicit graph contains 57,450 nearest, 30,640 mid-near and 114,900 far pairs, with no self or duplicate pairs. The fitted graph hashes and original-vector neighbors remain unchanged. Independent re-review found no remaining issues in #614, #615 or #616.

The browser preview canary passed at 1280px after #612. Its expanded pass covered 1280px and 390px, all 3,830 exported points, exact term/pair subsets, fixed coordinates/colors under filtering, off-page discussion details and definitions, history/cold links, keyboard selection, pan/zoom, empty states, dark mode, and map-download failure/retry without breaking search. A fresh canary after #615 and #616 also confirms an 8 CSS-pixel marker diameter through zoom/resize and actual pointer selection. Production Jekyll CI at `dd8566f` passed; full section-navigation/statistics checks passed at 1280px, 620px and 390px, including no-JavaScript and failure/loading states. Final artifact verification follows these fixes.

The map is a separate, explicitly loaded asset with a 5 MiB gzip limit; it does not enlarge the initial search index download. `embedding-asset-measurements.json` records the final validated payload and field-cost measurements. Definitions and provenance remain present. The browser reports an approximate compressed size rather than claiming a measured HTTP transfer size.

The model represents text similarity. Shared prose and shared matched descriptions can dominate the result. The map retains every discussion, including duplicate representations; colors and point density do not establish scientific importance. Source support and recognition coverage remain those of the retained native snapshot. The two-dimensional projection is lossy, so the interface also exposes original-vector cosine neighbors and measured projection diagnostics.
