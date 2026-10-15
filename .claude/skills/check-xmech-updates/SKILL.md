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
python3.12 scripts/fleet/check_updates.py      # about a minute; needs gh (repo scope) and network
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
- per Mech site, whether GitHub Pages has deployed it again since the
  `deployed_revision` the website feature table (`_fleet/data/site_features.json`)
  records. The table is judged on live sites, not pins, so a redeployment is its
  staleness signal; its evidence URLs are not part of `claims`. A site counts as
  served only while its repository has GitHub Pages enabled, its latest
  deployment has succeeded, and a HEAD request to it succeeds (no HTTP error
  status after redirects) with an answer from GitHub Pages: one that carries
  its `X-GitHub-Request-Id` header and does not come from one of GitHub's own
  hosts, such as the repository's page, which carry the header too. The
  answer's `Last-Modified` date must also be no earlier than the deployment's
  creation, since a run that skips publishing still ends in success while Pages
  serves what an earlier deployment published. A recorded site that is served
  is `same` or `redeployed`; one whose repository no longer has Pages enabled is
  `gone`; one whose recorded page GitHub Pages answers with 404 is `not found`,
  which a removed or moved page and an unpublished or transferred site all
  give, at the recorded revision or a newer one. A newer successful deployment
  also reads `redeployed` when the HEAD request fails, the site returns another
  error status, another host or a GitHub host answers, or the answer has no
  valid `Last-Modified`, with the failure in its detail; but a page last
  published before that deployment was created is NOT CHECKED at any revision,
  naming the recorded revision, since a run that skipped publishing may have
  left the recorded one served. A Mech the table records without a site is
  `new site` once its site is served, and `no site` while Pages is not enabled
  or while its latest successful deployment is still the `deployed_revision`
  an audit judged not to be a website. That judgement holds until a
  github-pages deployment of another commit, which most of these repositories
  make on every push to main and some only when site files change or on a
  schedule (a scheduled run deploys main's head, a new commit once main has
  moved); that deployment reads `new site` again, naming the judged revision. A
  redeployment of the same commit, such as a re-run or a scheduled run while
  main has not moved, is not reported, for a judged revision or a recorded one
  (#487). Any other state
  is NOT CHECKED: that includes Pages enabled with no deployment record, since a
  deploy job that names no environment records none; at the recorded revision,
  a successful deployment whose site returns an error status, does not answer,
  is served by another host at a custom domain or by a GitHub host, or has no
  valid `Last-Modified`; and a 404 for a new site, whose root can be missing
  while its pages exist. A detail names where a redirect ended. For a `same` or
  `redeployed` row with no failure whose redirect ends at an https URL, the
  recorded `site` should move there, and the closing line lists it as a site
  whose URL now redirects. The table accepts only https URLs, so a redirect to
  http leaves the recorded URL as it is, and a row whose failure came through a
  redirect needs a browser check instead. A new site's URL comes from
  `repos/<repo>/pages`, which needs gh's `repo` scope (Pages read for a
  fine-grained token), even for a public repository; without it these Mechs
  read NOT CHECKED, naming that request;
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
  pages, `CLAUDE.md`);
- its row of the website feature table: for a site the mechanical pass reports
  as redeployed, re-test the verdicts the changed pages could move, against the
  criteria in the file's `catalogue`. A redeployed row that names a failed
  request also means the recorded `site` URL needs checking in a browser.

For a Mech the mechanical pass reports as a new site, whether or not its
repository has `claims` changes, every statement that it has no website stops
holding once the new site is judged a website, as `update-xmech-page` does;
report each one. When the row ends "the table judged `<sha>` not to be a
website", an audit found an earlier deployment to be a placeholder or similar:
report the statements as candidates that are stale only if the new deployment
is a website, and say that it still needs that judgement.

Some statements say so in words: its entry in
`site_features.json` and the feature table's notes, its card, its `MECHS` entry
(an empty `site` sends the graph's node and panel links to GitHub, and `extra`
can say that no website is deployed), its note in `_fleet/audit_notes.json`
(copied into `_fleet/data/site_audit.json`), `resources.md`, `CLAUDE.md`,
`_fleet/README.md`, and the comments in `scripts/fleet/build_subsets.py` and
`scripts/fleet/check_cards.py` that give it as a reason. Others say so only by
linking its repository where every Mech with a site links the site: the footer
(`_includes/footer.html`), the ladder at the top of `_fleet/fleet_fragment.html`,
the suite sentence in `index.md`, every page's Related Tools list and the tool
lists in `research.md`. CLAW's capability reasons in `_fleet/data/manifest.json`,
shown as tooltips in the capability table, can deny a site too ("No pages/ tree
exists"). They quote CLAW verbatim, so report them for CLAW to correct and never
edit the snapshot.

Read the named files whole, since their prose wraps across lines. The list is
not exhaustive, so then search the whole tree, ignored files included except
Jekyll's build copy in `_site`, for other wordings and for links to the
repository, with `<repo>` the repository name from the entry's `repository`
field. `command grep` runs the system grep: in Claude Code's shell a plain
`grep` runs a ugrep wrapper that skips ignored files.

```bash
command grep -rniE --exclude-dir=.git --exclude-dir=_site 'no (published |public )?(website|browser)' .
command grep -rniE --exclude-dir=.git --exclude-dir=_site 'github\.com/CultureBotAI/<repo>[)"]' .
```

Leave judging the new site's features to `update-xmech-page`.

For a Mech reported as `gone`, the reverse holds: its feature row and every
statement or link that presents its site describe a site that is no longer
published. Report them. A recorded site is often a deep page (many end in
`pages/index.html`) while links point at its root and other pages, so search
for the site's URL prefix, case-insensitive and with no terminator; this also
finds the generated record lists under `assets/fleet`:

```bash
command grep -rniE --exclude-dir=.git --exclude-dir=_site 'culturebotai\.github\.io/<repo>/' .
```

Two places join a base URL and a path, so no URL search finds them: the card
source in `SOURCES` in `scripts/fleet/check_cards.py` and the record-link base in
`SITE_BASE` in `scripts/fleet/build_subsets.py`, which `build_cells.py` reuses.
Report both, with the record lists generated from them. Statements that present
the site in words carry no URL: read whole every hand-written file the URL
search returns (not the generated record lists under `assets/fleet` or
`mechs.md`, whose sources are listed here),
the Mech's dedicated page if it has one (`culturemech.md`, `communitymech.md`,
`mediaingredientmech.md`, front matter included), and the places listed above
for a new site, now for what says the site is served, among them the Mech's note in
`_fleet/audit_notes.json` and CLAW's capability reasons in
`_fleet/data/manifest.json` (report those for CLAW to correct; never edit the
snapshot). Then search the Mech's name with the words that describe a site:

```bash
command grep -rniE --exclude-dir=.git --exclude-dir=_site '<repo>.{0,80}(website|site|browser|pages)' .
```

For a Mech reported as `not found`, GitHub Pages itself has nothing at the
recorded page. Open the site's root and its Pages URL in a browser and report
whether the page moved (the feature row's `site` and the links above need the
new URL, and its verdicts a re-check) or the whole site is no longer served
(as for `gone`). In that last case Pages stays enabled with a successful
deployment, so a plain site-less entry would read NOT CHECKED on every run:
`update-xmech-page` records that deployment as a judged `deployed_revision`.

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
   membership and capabilities; website feature verdicts that a redeployment
   moved, new sites the table records as absent, recorded sites that are `gone`
   or `not found`, and recorded URLs that now redirect; dead links.
4. **What was not checked**, such as files past the API's 300-file cap that were
   not paged through.

Do not refresh, and do not offer to refresh as if it were part of this skill; if
the user wants the page updated, that is `update-xmech-page`.

## Related

- `update-xmech-page` — the refresh this check reports on.
- `scripts/fleet/check_cards.py` — the card-only check the nightly runs.
- `_fleet/README.md` — what each part of the page is derived from.
