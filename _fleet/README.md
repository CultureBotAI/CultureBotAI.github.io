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
so nothing regenerates them. `scripts/fleet/check_cards.py` compares each card
against the page it cites and is the one script here that needs the network:

```bash
python3 scripts/fleet/check_cards.py
```

It exits 1 on a figure that differs from the site and only warns on a page it
could not read, and `SOURCES` at its top pins where each Mech publishes its
count. It runs on the workflow's nightly schedule, not on pull requests, so a
Mech shipping records overnight does not block an unrelated change; a nightly
red means the card figures in `mechs_template.md` and the `MECHS` block in
`fleet_fragment.html` need refreshing together. A new card needs a `SOURCES`
entry; a test enforces that.

The `Fleet page` workflow checks pull requests, pushes and the live CLAW manifest
daily. It detects changes to membership, capability declarations (including
reasons/settings), and artifact count; unrelated CLAW commits do not make the
snapshot stale. To run the read-only checks locally:

```bash
python3 scripts/fleet/refresh_manifest.py --claw-root /path/to/culturebotai-claw --check
python3 scripts/fleet/assemble_page.py --check
```

## Vocabulary census updates

Membership updates do not require rescanning the record corpora. The current
September 2026 vocabulary census covers nine Mechs; TaxonMech is shown in the
graph and cards with its published 625,960-taxon total (checked September 24, 2026), but its vocabulary counts have not
been measured by this pipeline. The heatmap uses the measured `fleet_data.json`
order, and the page states this limitation. Add TaxonMech to the census roots
and scanners before publishing measured vocabulary cells or overlap counts for it.

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

The two scanning passes take about two minutes each, dominated by
ProteinTraitsMech's ~430k records.

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, ProteinTraitsMech
hash routes) and to the record's source file on GitHub for CultureMech,
MediaIngredientMech and NaturalProductMech in the existing census indexes,
although CultureMech (`pages/media/`) and NaturalProductMech (`pages/<class>/`)
now publish per-record pages.
NaturalProductMech and TaxonMech both publish browse sites linked from their
cards; these links are separate from the historical census's record-link routes.

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

`data/site_audit.json` records, per repository, the pinned revision, the Pages
URL each card figure is read from, the figure, response hashes and merged
pull-request totals. The three dedicated pages link their descriptions and
commands to those same revisions.

Follow client-side meta refreshes from site roots to `pages/` or `app/`. Read
JavaScript-backed headline counts from the data files they load: MIM uses
`data/ingredients.json` (2,953 ingredients; 2,611 MAPPED), and ProteinTraitsMech
uses `data/facets.json` (429,293 records; 34 source labels). The latter's static
HTML still has a legacy fallback count.

Card figures follow the published sites, and the census follows the pinned
repositories. At this refresh they agree for every Mech except CommunityMech:
its site lists 422 communities, while its record glob also takes four isolate
records, so the census and `mech_stats.json` count 426. CellStructureMech and
TraitMech published new records after the pins were taken; their cards keep the
pinned figures, and `site_audit.json` records what the two sites showed when it
was written. `check_cards.py` will report both as drifted until the next refresh.

CultureMech's README inventory at the pinned revision reports 15,878 normalized
records and 6,288 merged records. `/pages/` is live again and lists the same
6,288 merged media records, so the card links there and `check_cards.py` reads
it. The `app/` landing tile, which the site root redirects to, still reads
10,657; the `app/` browser itself serves the 15,878 normalized records.

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
revisions for the nine measured Mechs; TaxonMech remains outside the census.
The previous census's ProteinTraitsMech counts had been read from a checkout
with uncommitted files: it reported 770,276 UniProt references where the
revision the September 20 audit pinned (`700b6f7`) holds 657,598. The rescan's
lower figures are a correction, not a loss of data.
