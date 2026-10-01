---
name: check-xmech-updates
description: Read-only deep check of whether the site's GitHub Pages deployment serves the current main and whether the X-Mech Suite page (/mechs/) is out of date. Compares each Mech's repository and live site with the pins in _fleet/data/site_audit.json, sorts what changed into what it would move on the page (census and overlaps, card figures, hand-curated claims, fleet membership), reads the changed files behind every flagged claim, and reports what a refresh would change and whether one is due. Use when asked whether GitHub Pages or the X-Mech page is current, what has changed since the last refresh, or whether a refresh is needed. Never edits, pins, commits or refreshes; update-xmech-page does that.
---

# Check the X-Mech page for updates

Answers "is `/mechs/` current, and what would a refresh change?" without doing
the refresh. The page is a snapshot at the pins in `_fleet/data/site_audit.json`,
so "out of date" always means "the Mechs have moved since those pins"; the
question is whether the moves touch anything the page states.

`update-xmech-page` is what acts on the answer. This skill only reports.

## Ground rules

- **Read-only.** No branch, no commit, no file written in this repository, no
  pipeline stage run (every stage writes `_fleet/data/` or `assets/fleet/`), no
  issue or comment unless the user asks for one.
- **Never touch the shared Mech checkouts** under `roots.MECHS_ROOT`, not even a
  fetch: other sessions use them. Everything here comes from the GitHub API, the
  live sites and a temporary shallow clone of CLAW.
- **Quote evidence.** Every claim in the report names the file, commit or URL it
  came from; "probably changed" is not a finding.

## Procedure

### 1. The mechanical pass

```bash
python3.12 scripts/fleet/check_updates.py      # about a minute; needs gh and network
```

Use a Python with `scripts/fleet/requirements.txt` installed (3.12 is what CI
uses); without PyYAML the membership line says NOT CHECKED. The script prints:

- whether GitHub Pages serves this repository's `main`: the commit of the latest
  Pages build against `main`'s head, as current, building, behind (the live site
  lags `main`), errored (with GitHub's message) or NOT CHECKED. A deploy that is
  behind or errored means the live pages are not what the repository says, so
  read it before anything else;
- per repository, commits since its pin and what the changed files touch:
  `records` (census record globs, read as `glob.glob` and the census read them),
  `claims` (README, schema, licence and citation files, landing page, every file
  the fleet page or a content page links on GitHub or through a Pages URL, each
  audited data file, and CLAW's `fleet.yaml`,
  `vendored_artifacts.json` and Mech standard), or nothing the page uses; a
  repository the API could not answer for is UNCHECKED;
- the card check (`check_cards.check`), with the grace and lead limits applied;
- `refresh_manifest --check` against CLAW's current main;
- dead XREFS evidence links, and links that could not be checked;
- a closing line naming everything a refresh would change, and what was not checked.

The compare API lists at most 300 files per repository. Where the report says the
list is capped, its record counts are floors: take the live totals from the card
lines, and look at the rest of the changes in step 2 before calling a Mech
unaffected.

### 2. Read what the flagged claims rest on

For each repository with `claims` changes, read the diff of each flagged file
since the pin (`gh api repos/CultureBotAI/<repo>/compare/<pin>...main` and the
file's `patch`, or `gh api repos/CultureBotAI/<repo>/contents/<path>?ref=main`
for the whole file) and compare it with every place the page states something
about that Mech:

- its card in `_fleet/mechs_template.md`: headline figure and label, secondary
  figure, tag line, vocabulary chips, Explore links;
- its `MECHS` entry in `_fleet/fleet_fragment.html`: `records`, `unit`, `root`,
  `vocab`, `sources`, `license`, `extra`;
- every `XREFS` arrow from or to it, and its `HUB` tie to kg-microbe;
- the pages that repeat its figures (`index.md`, `resources.md`, the dedicated
  pages, `CLAUDE.md`).

Report each claim that no longer holds, with the old statement, the new fact and
its source. A changed file that leaves every claim true is a no-change finding;
say so.

For a capped file list, compare each claim file's contents at the pin and at
main directly; a commit query filtered by date would miss branch commits
authored before the pin and merged after it (#302):

```bash
gh api "repos/CultureBotAI/<repo>/contents/<path>?ref=<pin sha>" --jq .sha
gh api "repos/CultureBotAI/<repo>/contents/<path>?ref=main" --jq .sha
```

Different blob shas mean the file changed; read both versions.

### 3. Membership and capabilities

When the manifest line says the snapshot is stale, say what changed: clone CLAW
shallowly into the scratchpad and compare
`src/kg_microbe_fleet/fleet.yaml` with `_fleet/data/manifest.json` (members
added or removed, capability states and their reasons). A change here moves the
badges, the capability table and the Mech count, and a new member needs a card,
a graph node and a census glob before a refresh can include it.

### 4. Report

One short report, in this order:

1. **Verdict:** whether GitHub Pages serves `main`, then whether the page is
   current or which layers are out of date. Say whether a refresh
   is due, and why.
2. **Deadlines:** the date the card check's grace period ends (`pinned_at_utc` +
   `GRACE_DAYS`) and any card within reach of the lead limit (`MAX_LEAD`), since
   those turn the nightly red.
3. **Per layer:** card figures; census and overlaps (records added, removed,
   edited per Mech); hand-curated claims that no longer hold, each with evidence;
   membership and capabilities; dead links.
4. **What was not checked**, such as files past the API's 300-file cap that were
   not paged through.

Do not refresh, and do not offer to refresh as if it were part of this skill; if
the user wants the page updated, that is `update-xmech-page`.

## Related

- `update-xmech-page` — the refresh this check reports on.
- `scripts/fleet/check_cards.py` — the card-only check the nightly runs.
- `_fleet/README.md` — what each part of the page is derived from.
