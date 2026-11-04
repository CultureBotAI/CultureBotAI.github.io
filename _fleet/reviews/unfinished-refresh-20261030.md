# Unfinished October 30 refresh inventory

Captured 2026-11-04T11:35:27.882582+00:00 from `/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io`.

Branch `update/xmech-refresh-20261030` at `56ec3db204095e425e2ed7481d4f97b997906815` has **112 modified tracked files and 2 untracked helpers (114 dirty paths total)**. No protected files were changed. Every dirty path's SHA-256, size, modification time, mode and Git status is retained in the companion JSON, together with branch, HEAD and logical index hash.

The tracked modifications comprise 6 derived summaries, 61 cell payloads and 45 graph-edge payloads.

Dirty-file modification times span `2026-10-31T04:30:30.475013+00:00` to `2026-11-02T00:30:59.722984+00:00`. Timestamps support ordering; they do not establish execution success by themselves.

## Pipeline evidence

| Stage | Modified paths | Earliest mtime (UTC) | Latest mtime (UTC) |
| --- | ---: | --- | --- |
| prefix_census.py | 1 | 2026-10-31T04:37:47.244241+00:00 | 2026-10-31T04:37:47.244241+00:00 |
| build_subsets.py | 46 | 2026-10-31T04:53:27.061848+00:00 | 2026-10-31T04:53:28.214796+00:00 |
| build_cells.py | 62 | 2026-10-31T05:00:41.158470+00:00 | 2026-10-31T05:00:41.264932+00:00 |
| recent_terms.py | 1 | 2026-10-31T05:01:23.787949+00:00 | 2026-10-31T05:01:23.787949+00:00 |
| build_data.py | 1 | 2026-10-31T05:01:23.896507+00:00 | 2026-10-31T05:01:23.896507+00:00 |
| mech_stats.py | 1 | 2026-10-31T05:05:18.358853+00:00 | 2026-10-31T05:05:18.358853+00:00 |

The five pin-bearing summaries agree across all 14 Mechs and match the saved snapshot. All 342 cell payloads were checked against their summary SHA-256 values; mismatches: 0.

## Exact source pins

The same working pin column applies to census, subsets, cells, statistics and recent terms. Their exact individual maps, including HEAD maps, are retained in JSON.

| Mech | HEAD pin | Unfinished working pin |
| --- | --- | --- |
| HabitatMech | `1a40d0958114e6e3facd148ccec6197fa4dd679c` | `73f5de1ffa3a7ab7e7bfb0e60149aef034c51aa0` |
| CommunityMech | `a0631777d79ffe10235c6022408c58084a9e3283` | `a0631777d79ffe10235c6022408c58084a9e3283` |
| TraitMech | `46f241a730ecd3c48997c8ddfd02e8ae313cde39` | `fa9f7b05b54ae0865f25a0c3b84f3967bf8eb21f` |
| PathwayMech | `a1e182c64645f53884173356b0505bc77b68d584` | `b93b5fc48a6bd1508f49923efe62103f1370f9ce` |
| CellStructureMech | `7ef24d1dc70b776adec2a86b127907a8d5f02d33` | `ecd788f5a2090d23dddea6a1c8757ed55f7ddf68` |
| ProteinTraitsMech | `7276814bdf3bed73569a202c5e2c4b404e43d8f1` | `64daeedca4e133f20ec6f2cc6fa9819b18f8daa3` |
| DUFMech | `1ad8fdccc772ffb9d68948351b7b2b0b8e43cd6b` | `aa7d08bcf3a9a03879d06cffd075bc083d29788f` |
| NaturalProductMech | `ce6a5498df5be51116bd5e0c119023ee62bb5464` | `9deaa5eb0b78cecd2d2511449fb0b9eccb716580` |
| AntibioticMech | `f3506448c0ca3af3c86631dd0329cb93f94b9e64` | `13bf5681ca4fac4a15c87b7c4c78391594e472d4` |
| CMMMech | `4f543693bee75b97389de4d4c915a1e451297f1f` | `e954c96898ce97da6781984c7da7ea5d4fda9bfa` |
| MediaIngredientMech | `9afaec7a8071bdcd528503d9ed50122e3791ac7b` | `0626be26e60e99006d3ca31319392ebe0dcd2aa2` |
| CultureMech | `a74dd489720c9df96cc073ffd11568d407d3c06c` | `a74dd489720c9df96cc073ffd11568d407d3c06c` |
| TaxonMech | `830eb576c1381e73aba1ed284c1ae005c7a5337e` | `830eb576c1381e73aba1ed284c1ae005c7a5337e` |
| AIMech | `97c308f4a2560523cbabe9834fc9db7430073727` | `97c308f4a2560523cbabe9834fc9db7430073727` |

## Changed record counts

Repository records total 1,087,840 at HEAD and 1,087,866 in the unfinished statistics. Merged-PR totals are 7,638 and 7,717, respectively.

| Mech | HEAD records | Working records |
| --- | ---: | ---: |
| PathwayMech | 275 | 277 |
| CellStructureMech | 1,001 | 1,008 |
| ProteinTraitsMech | 429,394 | 429,406 |
| CMMMech | 663 | 668 |

## Snapshot and helpers

Snapshot: `/Users/marcin/.gemini/antigravity-cli/brain/fce06610-c3eb-40c8-ab6b-48056807ad41/scratch/xmech-refresh-20261030`.

Its saved pin-time bound is `2026-10-31T03:11:08+00:00`. The revision manifest and 6 stage logs remain. The `mechs/` directory contains 0 entries, including hidden entries; the original Mech checkouts are therefore unavailable at this named snapshot path.

- `scripts/adhoc/build_snapshot_20261030.py`: Builds/fetches snapshots and runs six derived stages; prepare also refreshes the manifest. Its canary function verifies clean pins and record availability but does not execute a full scan stage. Do not rerun as part of this inventory.
- `scripts/adhoc/inspect_secondary_20261030.py`: Reads pinned corpora, Git blobs and live sites, printing secondary figures and citation checks. Those computations and paths were not validated or executed by this inventory.

## Completion assessment

- **derived pipeline:** All six derived summaries have changed; five recorded pin maps agree and match the saved snapshot manifest. Saved logs and asset hashes support persisted completion, not a fresh scientific validation.
- **manifest:** Working manifest equals HEAD; identical CLAW pins can legitimately leave refresh_manifest with no content delta.
- **hand curated and provenance:** Maintained cards, graph claims, audit notes, final site audit and repeated prose remain byte-identical to HEAD; no completed final refresh is persisted here.
- **assembly:** mechs.md equals HEAD while its derived inputs changed, so the refreshed inputs have not been assembled into the protected page.
- **features:** site_features.json equals HEAD; no new website-feature audit is inferred.
- **snapshot reuse:** The named snapshot's Mech directory has no entries, including hidden entries; its revisions and logs survive, but the Mech clones would need reconstruction before a rerun.
- **execution:** Neither untracked helper was run, imported or modified. No check writes to the protected checkout or calls the network.

## Preservation check and search scope

All text files in the protected repository, excluding .git storage; no machine-wide absence claim. Snapshot directory listings independently include hidden entries.

The reference search used `rg -n -uu --hidden` and excluded only `.git` storage. This includes ignored files. Its exact command and all matching lines are saved in JSON. For the stopped October 30 run, both untracked helpers identify the same named snapshot. The search does not establish whether additional snapshots exist elsewhere on the machine.

Recheck without modifying either report:

```bash
python3 scripts/adhoc/inspect_unfinished_refresh_20261104.py \
  --repo '/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io' \
  --report _fleet/reviews/unfinished-refresh-20261030.json --check
```
