---
name: review-open-issues
description: Sweep and prioritize this site's complete open GitHub issue queue against the deployed pages, the generated fleet page and its sources, the fleet pipeline, and each Mech's own published site. Use for full backlog triage or deciding what is genuinely urgent; do not use as permission to close issues, rerun the pipeline, or implement fixes.
category: workflow
requires_database: false
requires_internet: true
version: 1.0.0
---

# Review and prioritize open issues

Produce a complete, dependency-aware triage of this repository's open issues.

The issue queue, the working tree, and **the live site** are three different
surfaces, and on this repository the third is the one that matters: almost every
defect here is a wrong claim on a public research page. Sweep the queue, then
test every claim against the deployed HTML and the current sources.

This is a read-only review by default. It does not implement fixes, rerun the
fleet pipeline, close or edit issues, change labels, or push anything unless the
user separately authorizes that exact mutation.

**When to use**: the user asks to review, triage, or prioritize issues or the
backlog; asks what is genuinely urgent; or a review pass has just filed a batch
of issues that need sorting.

**When NOT to use**: picking the next unit of work during active development, or
acting on a single known issue. This skill produces a ranking, not a fix, and is
expensive enough that it should not run on every "what's next".

## What this repository actually is

A Jekyll site published by GitHub Pages from `main`. Two things make triage here
unlike ordinary web-site triage:

1. **`mechs.md` is generated.** Its sources are `_fleet/mechs_template.md` and
   `_fleet/fleet_fragment.html`, filled from `_fleet/data/*.json` by
   `scripts/fleet/assemble_page.py`. An issue describing a fault "in mechs.md"
   is nearly always a fault in a source or in the data; report it there.
2. **The page states numbers about ten other repositories.** Those numbers come
   from two different places with different refresh rules — see *The three
   numbers* below. Most of the hard bugs in this queue are a number taken from
   the wrong one.

## Sources of truth

Check these before trusting an issue title or an old note:

- `_fleet/README.md` — the pipeline: what each script does, what is hand-curated,
  and how to refresh. Read this first for any fleet-page issue;
- `scripts/fleet/roots.py` — where the Mech checkouts are (`MECHS_ROOT`), the
  record glob per Mech, directories excluded from a corpus, and `CITATION`;
- `scripts/fleet/assemble_page.py` — the assembler and, importantly, **its own
  validations**: fleet membership must match the manifest, every token must be
  used, no unresolved placeholder, no Liquid. Several invariants are enforced
  here rather than in tests;
- `_fleet/data/manifest.json` — fleet membership and capability declarations,
  pinned to a CLAW commit. `refresh_manifest.py --check` is the authority on
  whether it is stale, not the file's date;
- `tests/test_fleet_page.py` — what is actually guarded. Read it before claiming
  an invariant is or is not enforced;
- `.github/workflows/fleet-page.yml` — the only CI, and therefore the only thing
  that blocks a merge;
- **`../CLAUDE.md`** — the repository guidance, which sits *one directory above
  the git root and is untracked*. It never appears in a diff, a PR, or a fresh
  clone. Treat it as this machine's notes, not as a shared contract, and do not
  cite it as evidence that something is agreed;
- each Mech's **own published site and README** — the authority for anything the
  cards claim about that Mech.

Treat issue bodies and titles as claims. Read the comments: corrections and
narrowed scope are recorded there. A merged PR is evidence only after its code
and its acceptance criteria are both checked.

## The three numbers

Nearly every numeric issue in this queue is one of these confused for another.
Before quoting any figure, say which it is:

| | where it comes from | refreshed by |
|---|---|---|
| **published-site total** | the Mech's own live browser | hand, re-checked against the live site |
| **local-checkout count** | `record_paths()` over `MECHS_ROOT` | `prefix_census.py` / `mech_stats.py` |
| **census/heatmap count** | `_fleet/data/prefix_census.json` | the full pipeline |

They legitimately disagree. CultureMech publishes 6,288 merged canonical media
and serves 15,878 normalized records from the same site. CommunityMech's hero
counts `kb/communities` only while the fleet glob also takes `data/isolates`, so
the site is permanently four below the fleet number. A local checkout can be
twenty commits behind its remote.

Two traps specifically:

- **A landing page can contradict its own data.** ProteinTraitsMech ships
  `408,978 records` as static HTML and overwrites it at runtime from
  `data/facets.json`, which serves 429,293. A scraper and a visitor see different
  numbers. Read the number the page *renders*.
- **A published tile can match nothing at all.** CultureMech's `10,657` is a
  hand-typed figure from a March 2026 merge input; nothing regenerates it.

Fetch the `pages/` or `app/` URL directly. Several Mech repo roots are
client-side meta-refresh shells that return 200, so `curl -L` stops at the shell
and never reaches the real page.

## Workflow

### 1. Fetch the entire queue

```bash
gh repo view --json nameWithOwner,url,defaultBranchRef
gh issue list --state open --limit 5000 --json number | jq length
gh issue list --state open --limit 5000 \
  --json number,title,body,comments,labels,createdAt,updatedAt,author
gh label list --limit 200
```

Fetch the count first, then re-run with `--limit` comfortably above it. Omitting
`--limit` caps silently at 30, which looks like a complete sweep.

State the exact number reviewed and whether coverage was complete. Read every
body and its comments. Read the queue yourself rather than splitting it across
agents: ranking requires seeing all of it, and a split sweep is first-page
sampling arriving by another route.

### 2. Place each issue on the pipeline

```text
Mech checkouts (MECHS_ROOT)  +  CLAW fleet manifest
  -> prefix_census.py     prefix counts per Mech
  -> build_subsets.py     assets/fleet/{edges,cells}/*.json
  -> build_data.py        fleet_data.json — which vocabularies become columns
  -> mech_stats.py        reviewed records, merged PRs
  -> assemble_page.py     mechs.md
  -> GitHub Pages         the live page
```

Alongside it runs a **hand-curated layer**: the card headline numbers in
`_fleet/mechs_template.md` and the `MECHS` / `XREFS` / `HUB` blocks in
`_fleet/fleet_fragment.html`, each taken from a Mech's published site. The
records tile sums the cards by construction. A fault in the hand-curated layer
is invisible to the pipeline and vice versa; say which layer an issue is in.

An upstream fault invalidates everything below it. Recommend fixing the root
before regenerating.

Group issues sharing a root cause — most of this queue is filed in batches by
review passes, so duplicates cluster on a shared commit, a shared file, or the
same failure seen from a different angle. Report groups explicitly and keep every
issue number visible.

For each issue record, when applicable: layer; whether it is a *generated* file
or a source; which Mech and whether the claim is about that Mech's site or its
checkout; which gate would catch it and whether that gate exists; prerequisites,
duplicates, superseding issues; cheapest decisive evidence; and execution class —
read-only check, source edit plus reassemble, a full pipeline rerun (~15 min), or
a change to what the page measures.

### 3. Check current reality and staleness

```bash
git log --all --oneline --perl-regexp --grep '#<N>\b'
gh pr list --state merged --search '<N>' --limit 100
```

The word boundary matters: `#48` must not match `#480`. GitHub's search matches
the number anywhere in indexed text — open each candidate before citing it.

Then:

- **Check the deployed page, not the working tree.** This is the single most
  useful move in this repository. `curl -s https://culturebotai.github.io/<page>/`
  and read what is actually served; the site can be ahead of a stale checkout or
  behind an unmerged branch.
- Use `rg` to confirm named paths, functions and tokens still exist — but see
  *Measurement discipline* on proving absence.
- Compare acceptance criteria against the merged change. Partial fix keeps the
  issue open with a narrowed residual.
- Verify a count against its actual immediate source, and name which of *the
  three numbers* it is.

### 4. Stop-the-line checks

Treat as P0 when live and externally consequential:

- a **wrong number, licence, or grounding claim on a published page** — this is a
  research group's public site and the Mech pages are cited;
- an enumeration of the suite that is short of the current membership, or a page
  that contradicts another page on the same fact;
- a **dead link** on a published page, or a card linking to a browser that does
  not exist;
- `mechs.md` edited by hand, so the next `assemble_page.py` silently reverts it —
  or committed out of sync with its sources (`--check` catches this; cite it);
- a **partial pipeline run**: refreshing the census without rerunning the rest
  leaves the page dating itself to one run over data from another;
- a pipeline script that does work at import, so reading a constant costs a
  multi-minute scan and overwrites committed data;
- a claim on the page contradicted by that Mech's own README or licence file —
  particularly a licence, since several Mechs are dual-licensed and the corpus
  half is not the repo half.

### 5. What actually gates a merge

Only `.github/workflows/fleet-page.yml` runs. Three steps block a merge:

```bash
python -m unittest discover -s tests -v
python scripts/fleet/refresh_manifest.py --claw-root .claw --check
python scripts/fleet/assemble_page.py --check
```

A fourth runs only on the nightly schedule and on manual dispatch, never on a
pull request, so it can be red without blocking anything:

```bash
python scripts/fleet/check_cards.py   # card headline figures vs each Mech's site
```

A drifted card therefore shows up as a failed scheduled run, not a failed PR
check. Look at the latest scheduled run before crediting the cards as current.

An issue asserting a defect that one of these already blocks is P2 unless it
shows the gate is porous — and they have been porous: a test can pass because
its assertion compares a corrupted file against itself, or because it was
exercised only against a slow corpus. **Mutation-test before crediting a gate.**
Break the invariant in a scratch copy and confirm the test fails.

Everything else — running the pipeline, checking links, comparing a card against
its Mech's site — happens only when a person types it. An invariant guarded only
by an unrun command is unguarded, and a missing gate over a consequential claim
is itself worth an issue.

Re-derive this from the workflow file rather than trusting this list.

### 6. Assign priority and execution order

- **P0 — stop the line.** A wrong public claim, a dead published link, corpus or
  committed-data corruption, or a blocker in front of an already-planned
  expensive run.
- **P1 — important and schedulable.** Correctness, provenance and gate-coverage
  gaps; a defect that would waste a full pipeline run; a missing guard over a
  claim the page makes.
- **P2 — low-risk or historical.** Styling and accessibility polish, refactors,
  theoretical edge cases, work confined to paths with no live spillover.
- **CLOSE/UPDATE.** Fixed, superseded, duplicate, or title materially broader
  than the residual. Cite the exact commit, PR, code, or deployed HTML.

Calibrate P0 sparingly. Order within and across tiers by:

1. upstream unblockers before downstream consumers;
2. a correct number before a prettier presentation of it;
3. add the missing gate before clearing the backlog it would protect;
4. read-only checks before anything that reruns the pipeline;
5. batch anything needing a full pipeline run, since it costs ~15 minutes and
   touches ~40 committed files.

Do not prioritize by age or by a `P0` string in a stale title.

### 7. Report

1. coverage: repository, timestamp, number reviewed, completeness;
2. top 2–3 next actions and why they unblock later work;
3. a dependency-ordered P0/P1/P2 table: number, status, evidence, blockers,
   execution class, next acceptance test;
4. CLOSE/UPDATE candidates with specific evidence;
5. unresolved evidence gaps and cross-repository ownership;
6. a short sequence showing which costly work must wait.

Call out old issues explicitly rather than silently dropping them. Separate
measured findings, code inspection, inference, and proposed work.

## Measurement discipline

The recurring failure here is mismeasuring evidence, not misreading it. Each of
these has produced a wrong conclusion in this repository:

- **`rg` does not prove absence.** It skips gitignored files. Any claim of the
  form "nothing references X" needs `grep -r` or `rg -uu`. Say which you ran.
- **`grep --no-ignore` is not a `grep` flag.** It is an `rg` flag; BSD `grep`
  fails and the surrounding `&&` chain silently skips the work, which reads as
  "no matches found".
- **The deployed id is the only authority on an anchor.** An emoji heading
  renders with a leading hyphen (`## 🔬 Advanced` → `#-advanced`), and an emoji
  carrying a variation selector keeps that codepoint *in the id*. A locally
  installed kramdown reports something different. Verify with
  `curl -s <page> | grep -oE '<h2[^>]*id="[^"]*"'`.
- **A generated file is not a source.** Report faults in `mechs.md` against
  `_fleet/`; a fix committed to `mechs.md` alone fails `--check` and is reverted
  by the next assembly.
- **A passing test may not be able to fail.** Before crediting a guard, break the
  invariant in a scratch copy and watch the test go red. Two guards in this
  repository passed against the very regression they named.
- **Mutation-test with a *fast* fixture.** A guard whose only real teeth are a
  timeout looks sound against the real corpus and is useless against a small one.
- **Argument evaluation order can be load-bearing.** `json.dump(f(), open(p,"w"))`
  leaves `p` intact when `f()` raises; the idiomatic `with open(p,"w")` does not.
  Do not treat such safety as designed unless it is written down.
- **A local checkout is not the repository.** Verify with `gh api` or a fresh
  fetch. Several Mech checkouts here lag their remotes by tens of commits.
- **Exit codes through pipes.** `cmd | tail -3; echo $?` reports `tail`'s status.
  Use `cmd >/tmp/o 2>/tmp/e; echo $?` or `${PIPESTATUS[0]}`.
- **Buffered output looks like a hang.** A long script piped to `tail` prints
  nothing until it exits; check the process, not the empty file.
- **Backticks in a double-quoted `-m`.** `git commit -m "...\`cmd\`..."` executes
  the backticked text. Write bodies containing shell examples via `-F` or a
  quoted heredoc, and read the result back before pushing.

## Conventions this skill enforces

- **Full-queue coverage, not first-page sampling.** State how many issues were
  reviewed and whether coverage was complete.
- **Evidence over vibes.** Every CLOSE/UPDATE/duplicate cites a specific commit,
  PR, code location, or deployed page — never "this looks done".
- **P0 is rare.** If more than ~10% of the queue lands P0, recalibrate.
- **Titles drift.** Re-read them at report time, not as fetched at the start.
- **The queue moves during the sweep.** Re-check the open set immediately before
  reporting and say so if it changed.
- **Read-only by default.** Ranking happens automatically; closing an issue or
  touching a tracker requires explicit confirmation.

## Notes and limitations

- `gh issue list --json` omits `comments` unless asked for. Corrections and
  narrowed scope live there, so a body-only fetch overstates what is open.
- An issue may be addressed in code while its acceptance criteria are not. Say
  which part is done.
- Many issues here are properly owned by a Mech repository, not this one — a
  wrong figure on a Mech's own site is theirs to fix, and this site can only work
  around it. Note the ownership; do not open issues in sibling repositories
  without being asked.
- Jekyll is not installed in this checkout, so rendering cannot be verified
  locally. The deployed page is the only rendering evidence.
- No @-mentions in issue comments or reports without explicit per-mention
  authorization (standing rule).

## Mutation boundary

Do not close, comment on, relabel, retitle, or create issues during the review.
If the user later asks to act, present the exact numbers and proposed mutation
first, then apply one at a time, carrying the evidence into the comment:

```bash
gh issue close <N> --comment "<commit/PR/code/deployed HTML that resolves this>"
```

Confirm each number before its own close. A general "yes, go ahead" is not
authorization for an unattended loop.

Do not rerun the fleet pipeline, regenerate `mechs.md`, or push as part of
triage. A recommended command is a proposal, not permission to run it. Note that
a census rerun mutates ~40 committed files and must be a *full* pipeline run —
a partial one leaves the page internally inconsistent.

## Related

- `_fleet/README.md` — the pipeline reference this skill defers to for how a
  refresh is actually performed.
