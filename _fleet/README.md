# Sources for the X-Mech Suite page

`mechs.md` at the site root is **generated**. Edit the sources here and rebuild:

- `mechs_template.md` — the page prose, cards and cross-reference list. Membership
  badges, counts and capability rows are generated from the manifest snapshot.
- `fleet_fragment.html` — the self-contained graph component (CSS, markup, JS). The
  per-Mech facts (`MECHS`), cross-references (`XREFS`) and kg-microbe ties (`HUB`) are
  hand-curated at the top of the script.
- `data/manifest.json` — membership and all capability declarations from a pinned
  commit of CLAW's canonical manifest, plus the canonical artifact count.
- Other `data/` files — derived numbers: `prefix_census.json`, `subsets_summary.json`, `fleet_data.json`, `mech_stats.json`; `site_audit.json` is the hand-written provenance record.

## Membership and capability updates

Use a CLAW checkout at the desired published `main` revision. The refresh reads
committed Git blobs at that checkout's HEAD; uncommitted changes are excluded.

```bash
python3 -m pip install -r scripts/fleet/requirements.txt
python3 scripts/fleet/refresh_manifest.py --claw-root /path/to/culturebotai-claw
python3 scripts/fleet/assemble_page.py
python3 -m unittest discover -s tests -v
```

When a Mech joins, add its curated card, graph facts and scale label to the
template/fragment and update the home-page links. The assembler refuses to omit
a manifest member from the cards or graph. Its capability table and badges must
never be maintained by hand. The rendered page links to the source revision.

The card headline figures are hand-curated from each Mech's published browser,
except CultureMech's, which comes from its committed README (see below), so
nothing regenerates them. `scripts/fleet/check_cards.py` compares each card
against the page it cites and is the one script here that needs the network:

```bash
python3 scripts/fleet/check_cards.py
```

`SOURCES` at its top pins where each Mech publishes its count, and `REGIONS`
restricts a source to the part that states it where the same words appear
elsewhere (CultureMech's generated README block). The page is a snapshot at a
refresh's pins, so a site up to 10% ahead of its card (`GROWTH_TOLERANCE`) only
warns. It fails when a site is further ahead than that or behind its card, when
a source answers 4xx or no longer states a figure the parser can read, when a
card and a `SOURCES` entry do not pair up, and when more than half the sources
could not be fetched at all. One site's outage only warns (#148, #115, #176).
It runs on the workflow's nightly schedule, not on pull requests, so a Mech
shipping records overnight does not block an unrelated change; a nightly red
means either the card figures in `mechs_template.md` and the `MECHS` block in
`fleet_fragment.html` need refreshing together, or a `SOURCES` entry needs
repointing. A new card needs a `SOURCES` entry; a test enforces that. The cards
are read by `scripts/fleet/card_markup.py`, the one parser the assembler, this
check and the tests share (#114).

The `Fleet page` workflow checks pull requests, pushes and the live CLAW manifest
daily. It detects changes to membership, capability declarations (including
reasons/settings), and artifact count; unrelated CLAW commits do not make the
snapshot stale. To run the read-only checks locally:

```bash
python3 scripts/fleet/refresh_manifest.py --claw-root /path/to/culturebotai-claw --check
python3 scripts/fleet/assemble_page.py --check
```

## Cross-reference arrows

`XREFS` in `fleet_fragment.html` and the "How the Mechs reference each other" list
in `mechs_template.md` hold the same entries, one per ordered pair, and the graph
draws each as an arrow pointing at the Mech that consumes, or at the one a scope
decision defers to. An arrow needs an implemented, committed reference: a record
field or id in the other Mech's namespace, a schema slot, enum or prefix naming it,
a vendored snapshot of its data or vocabulary, code that reads its repository,
data or site, a scope rule in its docs handing a concept over, or a practice
credited to it in the file that implements it. Rules that have come up:

- Shared ontology identifiers are the vocabulary layer, not arrows; that is how
  taxa tie TaxonMech to the fleet.
- Family navigation, sibling lists, and files vendored from culturebotai-claw into
  every Mech do not count. Neither does a fleet contract rolled out from claw,
  even where a Mech's copy names the others as prior art (#157).
- A credit that exists only in a changelog, a commit message or a plan does not
  count (#161).
- Code ported along a chain gets an arrow from the immediate source, judged by
  the code rather than an inherited docstring: AntibioticMech's helpers say
  "Ported from TraitMech's" but match HabitatMech's copies, so the credit sits on
  HabitatMech to AntibioticMech (#159).

The last full sweep, over records, schemas, scripts, config, vendored data,
curation decisions, docs and site generators in all ten repositories at the
pins, found 30 arrows.

## Vocabulary census updates

Membership updates do not require rescanning the record corpora. The September
2026 vocabulary census covers all ten Mechs. TaxonMech joined it in #87: its
625,960 records are species-level and infraspecific taxa keyed by NCBI Taxonomy
id, each carrying its lineage, so a higher taxon is counted once per record
under it and TaxonMech's NCBITaxon cell dwarfs everyone else's. Its overlaps are
what tie taxa to the rest of the fleet: most taxa that ProteinTraitsMech,
HabitatMech, NaturalProductMech, CommunityMech, TraitMech, AntibioticMech,
CellStructureMech and CultureMech cite are TaxonMech records. A new member
needs a record glob in `roots.py` and a link route in `build_subsets.py` before
its vocabulary can be measured.

`build_subsets.py` scans ProteinTraitsMech and TaxonMech last and keeps only
terms another Mech also cites, which is all an overlap needs. The proteins also
keep every taxon they cite, so their overlap with TaxonMech is exact. TaxonMech
record links use `pages/taxon.html?id=<identifier>`, which renders every taxon;
the files under `pages/taxa/` are redirects kept for old URLs.

Pipeline (from the site root, with the Mech checkouts available locally):

`scripts/fleet/roots.py` is where the checkouts are found. It expects one
directory holding every Mech as a direct child; set `MECHS_ROOT` to relocate
them. A missing checkout or a record glob that matches nothing stops the run,
because the numbers here become claims on the page and an empty corpus is
indistinguishable from a shrunken one otherwise. Run it on its own to see what
it resolves:

```bash
python3 scripts/fleet/roots.py
```


```bash
python3 scripts/fleet/prefix_census.py    # heatmap counts
python3 scripts/fleet/build_subsets.py    # assets/fleet/{edges,cells}/*.json + subsets_summary.json
python3 scripts/fleet/build_data.py       # _fleet/data/fleet_data.json
python3 scripts/fleet/mech_stats.py       # _fleet/data/mech_stats.json (needs gh)
python3 scripts/fleet/assemble_page.py    # mechs.md
```

The census takes about eight minutes and `build_subsets.py` about six over the
ten-Mech snapshot, both dominated by TaxonMech's ~626k and ProteinTraitsMech's
~430k records (#230).

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, NaturalProductMech,
TaxonMech's taxon.html route, ProteinTraitsMech hash routes) and to the record's
source file on GitHub for CultureMech and MediaIngredientMech.
NaturalProductMech's pages are committed under `pages/<class>/<slug>.html`, one per
record, and served by its branch build (#149). CultureMech's `pages/media/` pages
come and go with its Actions deployment (#175), so its links stay on GitHub until
that deployment is stable (#223).
CommunityMech's four `data/isolates` records have no published page, so they get
no record link and are left out of the record lists and overlaps; the census
still counts them. TaxonMech's record links open its taxon pages.

MIBiG and NPAtlas are carried through the whole pipeline alongside the
ontologies, because they are how NaturalProductMech cites its corpus. MIBiG is a
seeded grounding source; NPAtlas is a cross-reference target only, since its
licence bars ingestion into a CC BY 4.0 corpus.

`prefix_census.py`'s prefix alternation is a hand-maintained list and is known to
be incomplete: TOGO, UTEX and CCAP are absent although comparable registries
(MediaDive, DSMZ, ATCC, GOLD) are present. TOGO is CultureMech's second-largest
structured namespace at 2,833 occurrences, so the heatmap currently understates
it. Adding a prefix changes the heatmap's columns, so it needs a full rescan.

## Published-site refresh (September 24, 2026)

Every number on the page was re-derived from one set of pinned revisions: each
Mech's GitHub `main` and CLAW's, fetched once at the start of the run. The
census, the card stats and `data/site_audit.json` each record the revision they
read, and `RefreshProvenanceTests` fails if they disagree. The corpora were read
from sparse clones of the shared checkouts at those commits, never from the
checkouts' working trees, several of which lagged their remotes by dozens of
commits or carried uncommitted files. `.claude/skills/update-xmech-page/` is the
procedure.

`data/site_audit.json` records, per repository, the pinned revision, the URL each
card figure is read from (a Pages URL, except CultureMech's committed README on
`main`), the figure, response hashes and merged
pull-request totals. The three dedicated pages link their descriptions and
commands to those same revisions.

Follow client-side meta refreshes from site roots to `pages/` or `app/`. Read
JavaScript-backed headline counts from the data files they load: MIM uses
`data/ingredients.json` (2,953 ingredients; 2,611 MAPPED), and ProteinTraitsMech
uses `data/facets.json` (429,293 records; 34 source labels). The latter's static
HTML still has a legacy fallback count.

Card figures follow the published sites, CultureMech's its committed README
instead, and the census follows the pinned repositories. At this refresh they agree for every Mech except CommunityMech:
its site lists 422 communities, while its record glob also takes four isolate
records, so the census and `mech_stats.json` count 426. CellStructureMech and
TraitMech published new records after the pins were taken; their cards keep the
pinned figures, and `site_audit.json` records what the two sites showed when it
was written. `check_cards.py` reports both as grown, a warning, until the next refresh.
NaturalProductMech's landing page and MediaIngredientMech's data file also
changed after the pins without changing their figures; the audit records each
live hash beside the hash of the committed copy at the pin.

CultureMech's README inventory at the pinned revision reports 15,878 normalized
records and 6,288 merged records, and the card cites it: no page CultureMech
reliably serves states the canonical count. The `app/` landing tile, which the
site root redirects to, still reads 10,657. The `app/` browser's data
(`app/data.js`), the `/pages/` media index and the dashboard are all built and
deployed by CultureMech's generate-pages workflow through GitHub Actions, while
the site's Pages source is set to branch builds; a push to `main` outside the
workflow's paths triggers a branch build that replaces the deployment. So all
three appear and disappear: live on September 24, gone on September 25, when the
browser never finished loading (#175, #182, #204). The fix is upstream, setting the
Pages source to GitHub Actions (#172). `check_cards.py` therefore reads the
committed README on `main`.

Reviewed-record counts come from `mech_stats.py`, which counts a record as
reviewed only where the Mech's schema has a status that can say REVIEWED; the
card secondary figures were checked against each live site. Merged pull-request
totals come from GitHub search at run time and were cross-checked against the
GraphQL `pullRequests(states: MERGED)` count for every repository.

The CLAW manifest's projected membership and capabilities are unchanged; the
snapshot now points to the pinned main revision. Its README distinguishes
supported discovery, validation and dry-run tools from unimplemented CLI agent
execution and disabled cross-repository apply modes. Capability adoption must
not be described as proof that those workflows execute unattended.

The vocabulary census and overlap assets were rescanned at the same pinned
revisions, and TaxonMech was added to it (#87).
The previous census's ProteinTraitsMech counts had been read from a checkout
with uncommitted files: it reported 770,276 UniProt references where the
revision the September 20 audit pinned (`700b6f7`) holds 657,598. The rescan's
lower figures are a correction, not a loss of data.
