---
name: update-xmech-page
description: Refresh the X-Mech Suite page (/mechs/) and every page that repeats its figures from each Mech's current GitHub main and live GitHub Pages site — full fleet pipeline at pinned revisions, a verified re-check of every hand-curated claim, propagation to the other pages, provenance, and a reviewed PR. Use when asked to update, refresh or re-sync the X-Mech page or its numbers. Not for changing what the page measures (new census vocabularies, adding a Mech to the census), and never a licence to merge.
category: workflow
requires_database: false
requires_internet: true
version: 1.0.0
---

# Update the X-Mech page

Refresh `/mechs/` so every claim on it is true of the Mechs **as they are now**:
each Mech's `main` on GitHub and its live GitHub Pages browser. A refresh keeps
the page's methodology fixed and changes only the facts.

The page has three sources, and a refresh must redo all three from one moment in time:

| source | what | refreshed by |
|---|---|---|
| **manifest** | membership badges, capability table, the stat strip's Mech count | `refresh_manifest.py` from CLAW at its pin (step 1) |
| **derived** | census heatmap, overlap chords, `assets/fleet/`, reviewed and merged-PR counts, the stat strip's vocabulary and merged-PR tiles | the pipeline in `scripts/fleet/`, run over pinned checkouts |
| **hand-curated** | card headline figures and their secondary figure, tag lines, vocab chips, graph panels (`MECHS`), cross-references (`XREFS` and the template list), kg-microbe ties (`HUB`), Explore links; the stat strip's records tile sums the card figures, so it moves only when they do (#225) | a person or agent, re-checked claim by claim against the live sites and the pinned repos |

Read `_fleet/README.md` first. It is the pipeline reference; this skill is the
procedure around it.

**When NOT to use:** adding prefixes to the census or columns to the heatmap
(#84), adding a Mech to the census (#87), or redesigning the page. Those change
what the page measures, need their own decision, and belong in their own PR.
A refresh that also changes methodology cannot be reviewed, because every number
moves for two reasons at once.

## Ground rules

- **One set of revisions for everything.** Pin every Mech and CLAW once, at the
  start, and derive every number from those commits. The census, the stats and
  the site audit each record the revision they read, and
  `RefreshProvenanceTests` fails if they disagree. A partial rerun is the failure
  this exists to catch: a census from one checkout and stats from another put 364
  and 396 CommunityMech records on the same page.
- **Never pull or reset the shared checkouts** under `MECHS_ROOT`. Other sessions
  work in them; ProteinTraitsMech has carried tens of thousands of uncommitted
  files. Build a snapshot from their object stores instead (step 2), which reads
  them and writes nothing into them.
- **`mechs.md` is generated.** Edit `_fleet/`, never `mechs.md`.
- **The three numbers** differ legitimately; know which one a figure is before
  changing it. Card figures are *published-site totals*. The census and stats are
  *pinned-checkout counts*. They disagree whenever a Mech's site lags its repo,
  and the page says so rather than forcing them equal.
- **Evidence for every changed figure.** A URL or `path@sha` and a verbatim
  excerpt. "Looks right" is not a source.
- **Branch, PR, adversarial review, issues from the review, triage** — per the
  global git workflow. **Merging is the user's call**, every time.

## Procedure

Work from the site root. The snapshot and logs go in a directory of their own
inside the session scratchpad, never the scratchpad itself, which also holds
other work (worktrees of open PRs, among other things). Create it fresh:

```bash
SNAP=<session scratchpad>/xmech-refresh-$(date +%Y%m%d)
mkdir "$SNAP" || exit 1       # refuse to reuse a directory that already exists
```

Shell variables do not survive between tool calls, so write the absolute path
down: it goes in the PR body and the report (step 10), and step 11 needs it
after the merge, which may come in another session (#227, #228). Keep only the
snapshot and its logs, each named `<stage>.log`, in `$SNAP`; working files, including before/after copies
of the derived data for step 9, drafts, review records and helper scripts, go
elsewhere in the scratchpad, because step 11 removes the directory whole and
stops if it finds anything else there (#237, #245).

### 1. Branch, locate the checkouts, pin CLAW and refresh the manifest

```bash
git switch -c update/xmech-refresh-$(date +%Y%m%d) main
SRC=$(python3 -c 'import sys; sys.path.insert(0, "scripts/fleet"); import roots; print(roots.MECHS_ROOT)')
```

`SRC` is where the shared Mech checkouts live; `roots.py` holds the default and
`MECHS_ROOT` overrides it. Keep the two names apart: from step 3 on,
`MECHS_ROOT=$SNAP/mechs` is set per command so the scripts read the snapshot,
and it must never leak into the commands that read `SRC` (#133).

CLAW comes first, because its manifest decides which Mechs to pin and
`mech_stats.py` reads that list on import (#138). CLAW is not under `SRC` and any
local copy may be shallow, so clone it from GitHub at its pin (#130):

```bash
claw=$(gh api repos/CultureBotAI/culturebotai-claw/commits/main --jq .sha)
git init -q "$SNAP/claw"
git -C "$SNAP/claw" fetch -q --depth 1 https://github.com/CultureBotAI/culturebotai-claw.git "$claw"
git -C "$SNAP/claw" -c advice.detachedHead=false checkout -q FETCH_HEAD
python3 scripts/fleet/refresh_manifest.py --claw-root "$SNAP/claw" --check   # say what changed
python3 scripts/fleet/refresh_manifest.py --claw-root "$SNAP/claw"
```

Then, for each Mech in the refreshed `_fleet/data/manifest.json`:
`git -C "$SRC/<Mech>" fetch -q origin`, take `origin/main`, and cross-check it
against `gh api repos/CultureBotAI/<repo>/commits/main --jq .sha`. The
repository name is not always the Mech name (`proteintraitsmech`). Write the
pins and CLAW's to `$SNAP/revisions.json` with the pin time. Corpora move within
minutes, so pin once and do not re-pin mid-run.

### 2. Snapshot at the pins

A sparse, shared clone per Mech, checked out detached at its pin:

```bash
git clone -q --shared --no-checkout "$SRC/$m" "$SNAP/mechs/$m"
git -C "$SNAP/mechs/$m" sparse-checkout set --cone <record dirs> src
git -C "$SNAP/mechs/$m" checkout -q --detach "$sha"
```

The directories each Mech needs are its `roots.RECORD_GLOBS` directories (plus
`mech_stats.EXTRA_GLOBS` for Mechs outside the census), `src` for the schema that
`mech_stats.py` reads, and HabitatMech's `pages/habitats`, which
`build_subsets.py` matches record links against. About 6 GB and a million
files (5.7 GB at the 2026-09-24 refresh); TaxonMech (3.2 GB) and
ProteinTraitsMech (2.3 GB) are most of it. Keep it until the PR merges, because
reruns after review fixes go against the same pins; step 11 removes it. The detached checkout
works although the pin exists only in the source's remote-tracking refs,
because a shared clone borrows the source's whole object store.

macOS ships bash 3.2: no associative arrays, so write the per-Mech directory map
as a `case`, not `declare -A`.

### 3. Free checks before any scan

With `MECHS_ROOT=$SNAP/mechs`, `roots.revision(m)` must equal the pin with no
`+dirty`, for every Mech. It compares the records the globs find with the files
git tracks at HEAD under the same globs, so it fails on a wrong pin, on a sparse
set that left out a record directory, and on untracked or ignored files the
globs would count (#121). If you compare paths by hand, use
`git ls-tree -r -z --name-only <sha>` and NFC-normalize both sides: **without
`-z`, git quotes non-ASCII paths** and every `α` or `ß` in a filename reads as a
mismatch.

### 4. Pipeline, canary first

Run each stage the same way, in the same environment and from the same launcher,
and verify its output before starting the next. The first stage is the canary:

```bash
MECHS_ROOT=$SNAP/mechs python3 scripts/fleet/prefix_census.py   # ~8 min
MECHS_ROOT=$SNAP/mechs python3 scripts/fleet/build_subsets.py   # ~6 min
python3 scripts/fleet/build_data.py
MECHS_ROOT=$SNAP/mechs python3 scripts/fleet/mech_stats.py      # needs gh
```

After each, check the side effects, not the exit code: the file changed, it
parses, every census Mech has a row, `_revisions` equals the pins in both the
census and `subsets_summary.json`, `files` per Mech equals the record count at
the pin, and `mech_stats.json` names the same revisions and counts. Each scan
records its revision before reading and stops if HEAD moves during the read
(#122), and stops on an unreadable record rather than skipping it (#127).
Since #107, two `build_subsets.py` runs over the same snapshot must be
byte-identical; `SubsetDeterminismTests` checks that on a fixture.

Long scripts piped to `tail` print nothing until they exit. Check the process,
not the empty log. Exit codes through pipes are the last command's, so use
`${PIPESTATUS[0]}` or write to a log file: `$SNAP/<stage>.log`, since step 11
removes only logs with that suffix (#251).

### 5. Re-check the hand-curated layer

Every hand-curated claim, for every Mech, against its live site and its repo at
the pin. That means the card, the `MECHS` entry, the Explore bullets, `HUB`, both
cross-reference lists, the licence bullet, the Orchestration section, and each
page listed in step 6. For a large fleet this fans out well: one read-only
auditor per Mech, one for fleet-wide claims, one for cross-references, and an
independent skeptic per auditor who re-derives each proposed change and tries to
refute it. Apply only changes that survive, with one editor making all the edits
so shared files do not conflict.

Canary this fan-out too (#136). Run one auditor and its skeptic on one small
Mech first, and check that the claims come back with verbatim, unique locators,
evidence as a URL or `path@sha` plus an excerpt, and replacements that read
correctly in place. Then fan out. Findings the skeptics raise that the auditors
missed have been verified by nobody; give them their own verification round
before editing anything on their strength.

Traps that have produced wrong figures here:

- **Meta-refresh roots.** Several `https://culturebotai.github.io/<Mech>/` roots
  are client-side redirects that return 200; `curl -L` stops at the shell. Read
  the `pages/` or `app/` URL.
- **Runtime counts.** MediaIngredientMech's headline comes from
  `data/ingredients.json` and ProteinTraitsMech's from `data/facets.json`. The
  static HTML carries a placeholder or a stale fallback.
- **A tile can match nothing.** CultureMech's `app/` landing tile is a legacy
  hand-typed figure; `scripts/fleet/check_cards.py` `SOURCES` records where each
  card's figure really comes from. Keep `SOURCES` in step with the cards.
- **Site vs repo.** CommunityMech's site counts `kb/communities` while the fleet
  glob also takes `data/isolates`, so the two never match. A Mech's site can lag
  its repo by a deploy; the card follows the site and the census follows the repo.
- **Schema, not records, says what a record is.** Check a `MECHS` entry's `root`
  against the schema's `tree_root`, and its licence against the LICENSE files.
- The two cross-reference lists, `XREFS` in the fragment and the template's list,
  must describe the same references, and each arrow points at the Mech that
  consumes. Check direction as well as existence: three entries once pointed
  the wrong way.
- `HUB` entries render after a prefix ("Exports ", "Receives ", "Namespace: "),
  so write each `what` to read correctly after it. A Mech with an exporter but no
  published release is a namespace tie, not an export.
- `git grep -E` has no `\b`; a pattern using it matches nothing and reads as a
  zero count.

### 6. Propagate

The card figures are repeated across the site. Update every occurrence, and every
"checked on" date and pinned README permalink next to them:

- `index.md` (X-Mech sentence), `resources.md` (each Mech's section),
  `research.md`, `microgrowagents.md`;
- the dedicated pages `culturemech.md`, `mediaingredientmech.md`,
  `communitymech.md`;
- `_fleet/README.md` "Published-site refresh" section, retitled to the run date;
- the card-section intro in `_fleet/mechs_template.md`, which states the date the
  cards were checked.

Find stragglers by searching the *old* figures across the whole tree, gitignored
files included (`grep -rn`, not `rg`), excluding `_site/` and generated files.
A page that still states an old figure contradicts `/mechs/`, which is worse than
either being stale alone.

### 7. Provenance

Rewrite `_fleet/data/site_audit.json` for the run: per repository the pinned
`sha` from `$SNAP/revisions.json` (not from `mech_stats.json`, or the audit-pin
test compares a value with itself, #125) and its commit date, the URL each card figure is read from, the figure, the
sha256 of the fetched HTML and of any data file, merged PRs, and short notes on
how the site figure relates to the repo count. Set `checked_at_utc`,
`local_date`, `pinned_at_utc` and `scope`. Derive the mechanical fields rather
than typing them: the figure through `check_cards.read_source()`, which applies `REGIONS`, merged PRs from
`mech_stats.json`, SHAs and commit dates from the pins, and assert that the
pins equal the stats' `source_revision` before writing. Hash the served page as
committed at the pin too (`git show <sha>:pages/index.html`, or `docs/`), record
it beside the live hash, and let the builder say whether the two match. Never
type "byte-identical" into a note: sites publish during the run, and a
hand-written claim of identity went stale for four Mechs in the first run (#155). The provenance tests require its SHAs to equal the
stats' `source_revision`.

`CLAUDE.md` at the repository root records when the page was last refreshed.
Update its "Last refreshed" sentence in the same PR, so the guidance and the
page never disagree (#173, #196).

### 8. Assemble and gate

```bash
python3 scripts/fleet/assemble_page.py
python3 -m unittest discover -s tests -v
python3 scripts/fleet/assemble_page.py --check
python3 scripts/fleet/refresh_manifest.py --claw-root "$SNAP/claw" --check
python3 scripts/fleet/check_cards.py        # exit 0; "grew" lines are sites that moved past their pin (below)
```

Rerun `check_cards.py` immediately before opening the PR and again before any
merge. A Mech can publish between the audit and the merge; the check reads the
live site, so it is the only gate that sees that.

When a site has moved past its pin, do not re-pin that one Mech: the census and
overlaps are computed across Mechs, so a single re-pin is a partial rerun, and a
fast Mech moves again before the rerun finishes. Keep the page a consistent
snapshot at the pins, record the live figure as `site_figure_at_check` in that
Mech's `site_audit.json` entry, and say in the PR which cards the check reports
as grown. That stays a warning for `GRACE_DAYS` (14) after `pinned_at_utc` while
the site is at most half as large again as the card; past either limit the
check reports STALE and fails, and the page is due a full refresh. The check
also reads each `*_sha256_at_pin` in the audit, so record them for every source
the check reads: a card that differs from a source still byte-identical to its
pin fails as WRONG.

Emoji headings render with a leading hyphen in their id on GitHub Pages. Verify
anchors against the deployed HTML, not a local kramdown.

### 9. Read the diff before the PR

A refresh touches about forty data files. Before opening the PR, account for
every class of change: records per Mech against the pins, edges gained or lost,
the vocabulary tile, per-Mech reviewed and PR deltas, each hand-curated edit
against its evidence. An unexplained change is a finding, not noise.

### 10. PR, review, issues

Open the PR with the pins, what changed and why, the canary result, what was
left out and why (methodology issues stay open), the evidence table for
hand-curated edits, and the snapshot's absolute path and size ("Snapshot:
`<path>`, 5.7 GB, remove after merge"). Then review it adversarially as a separate read-only pass,
file every finding as an issue, fix the ones that belong in this PR, and leave
the rest filed with a reason. Report and stop: **do not merge without the user's
explicit go-ahead in the current conversation.** After a merge, delete the branch
locally and remotely, and close issues the PR resolved that GitHub did not
auto-close. GitHub honours only the first number after a closing keyword.

### 11. Remove the snapshot

After the merge and the branch deletion, and not before: until then a review fix
means a rerun at the same pins, which needs the snapshot. Take the path from the
PR body, not from a shell variable, and remove that directory whole: the Mech
clones, the CLAW clone, `revisions.json` and the scan logs. Remove it only if
it is recognizably a snapshot and holds nothing else:

```bash
SNAP=<path from the PR body>
test -f "${SNAP:?}/revisions.json" && test -d "$SNAP/mechs" && test -d "$SNAP/claw" \
  || { echo "not a refresh snapshot: $SNAP"; exit 1; }
extra=$(ls -A "$SNAP" | while IFS= read -r name; do
  case "$name" in
    (revisions.json|mechs|claw) ;;
    (*.log) [ -f "$SNAP/$name" ] || printf '%s\n' "$name" ;;
    (*) printf '%s\n' "$name" ;;
  esac
done)
[ -z "$extra" ] || { printf 'not snapshot data; move it out or decide first:\n%s\n' "$extra"; exit 1; }
du -sh "$SNAP"                # about 6 GB; say it in the report
rm -rf "$SNAP"
```

`${SNAP:?}` stops the command if `SNAP` is unset, and the three tests stop it if
the path is the scratchpad or anything else that is not a snapshot. The listing
stops it if the directory holds anything but the clones, `revisions.json` and
logs: a script or record left there cannot be rebuilt from the pins (#237). It
compares names literally and accepts a `*.log` only if it is a regular file, and
finding nothing extra exits 0, so the snippet also runs under `set -e`; the
`(pattern)` form keeps macOS's bash 3.2 from misreading a `case` inside `$( )`
(#252, #253). If
the directory is already gone, say so rather than searching for another. Only
`$SNAP` goes. Never `$SRC`: those are the shared checkouts other
sessions use. Removing the shared clones is safe for `$SRC`, because a
`--shared` clone borrows the source's object store and the source knows nothing
about it; the reverse, pruning or deleting `$SRC` while a clone exists, is what
would break a clone. A second refresh builds a fresh snapshot at its own pins
(#174). A later PR that must rerun at these same pins builds one too, from the
pins committed in `_fleet/data/site_audit.json`: create `$SNAP` as above, clone
CLAW with step 1's three `git` commands but at the audit's `culturebotai-claw`
sha rather than `main`, and run `refresh_manifest.py` only with `--check`, so the
committed manifest stays at its pin. Write `$SNAP/revisions.json` from the
audit, in the shape step 1 writes and step 7 reads:

```json
{"pinned_at_utc": "<the audit's pinned_at_utc>",
 "mechs": {"<Mech name>": {"repo": "<repository>", "sha": "<sha>", "commit_date": "<commit_date>"}},
 "claw": "<the audit's culturebotai-claw sha>"}
```

keyed by Mech name, not repository name (ProteinTraitsMech's repository is
`proteintraitsmech`). Then set `SRC` as in step 1 and run step 2 for each Mech
(#236, #246).

## Related

- `_fleet/README.md` — the pipeline and what each script reads and writes.
- `review-open-issues` — read-only triage of the backlog; its "three numbers" and
  measurement-discipline sections apply here too.
- `scripts/fleet/check_cards.py` — card-vs-site drift check, nightly in CI.
