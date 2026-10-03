# Sources for the X-Mech Suite page

`mechs.md` at the site root is **generated**. Edit the sources here and rebuild:

- `mechs_template.md` — the page prose, cards and cross-reference list. Membership
  badges and capability rows are generated from the manifest snapshot; the suite
  count includes separately listed additions.
- `fleet_fragment.html` — the self-contained graph component (CSS, markup, JS). The
  per-Mech facts (`MECHS`), cross-references (`XREFS`) and kg-microbe ties (`HUB`) are
  hand-curated at the top of the script.
- `data/manifest.json` — membership and all capability declarations from a pinned
  commit of CLAW's canonical manifest, plus the canonical artifact count.
- `audit_notes.json` — hand-checked explanations of each source and its counted
  entities. PathwayMech records and DUFMech seed families use the same pinned
  census, statistics and site-audit pipeline as the other ten Mechs.
- Other `data/` files — derived numbers: `prefix_census.json`, `subsets_summary.json`, `fleet_data.json`, `mech_stats.json`; `site_audit.json` is the provenance record, written by `scripts/fleet/build_site_audit.py` from the snapshot, the live sites and the audited notes in `_fleet/audit_notes.json`.

## Membership and capability updates

The site currently lists twelve Mechs. CLAW's manifest lists eleven, including
PathwayMech; DUFMech is listed separately without a manifest membership declaration. The
October 3 vocabulary census, shared-term assets and repository statistics cover
all twelve Mechs. DUFMech's contribution is a measured seed worklist, labeled
as families rather than curated mechanism records. Its capability row reports
undeclared values without inventing CLAW membership.

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
except CultureMech's, which comes from its committed README, and DUFMech's,
which counts families in its frozen JSON worklist. Nothing regenerates the
hand-curated card figures. `scripts/fleet/check_cards.py` compares each card
against the page it cites and is the one script here that needs the network:

```bash
python3 scripts/fleet/check_cards.py
```

`scripts/fleet/check_updates.py` goes further, read-only: it compares each
repository's main with its pin through the GitHub API and sorts the changed
files into census records, files the hand-curated layer cites, and the rest,
alongside the card check and a manifest check against CLAW's main. The
`check-xmech-updates` skill runs it and reads the flagged files.

`SOURCES` at its top pins where each Mech publishes its count, and `REGIONS`
restricts a source to the part that states it where the same words appear
elsewhere (CultureMech's generated README block). The page is a snapshot at a
refresh's pins, so a site ahead of its card only warns ("grew") for
`GRACE_DAYS` (14) after the pins in `site_audit.json`, and only while the site is
at most `MAX_LEAD` (50%) ahead. Past either limit it fails as STALE. It also
fails when a card differs from `figure_at_pin`, the figure `site_audit.json`
records its source stating at the pin (the card was never right), when a site is
behind its card, when a source answers a 4xx other than a throttle or no longer
states a figure the parser can read, when a counted card lacks exactly one headline
figure or has no checked source, when the audit is missing or malformed, its
pin time is missing, unreadable or in the future, or a source lacks a
whole-number `figure_at_pin` (all but ProteinTraitsMech, whose file is built in
CI), and
when more than half the sources could not be fetched. One site's outage or
throttle only warns (#148, #115, #176, #217-#220, #231, #232). It runs on the
workflow's nightly schedule, not on pull requests, so a Mech shipping records
overnight does not block an unrelated change. The run's closing line names the
remedy for each failing verdict (#235):

- STALE or SHRANK: the card figures in `mechs_template.md` and the `MECHS` block
  in `fleet_fragment.html` need a full refresh, since the page is a snapshot.
- WRONG: a card differs from the figure its source stated at the pin. Correct the card
  and every other occurrence of its figure, found by grepping the tree for it as
  step 6 of the update skill does: the MECHS `records:` and `extra:` text in
  `fleet_fragment.html`, cross-references and the pages that repeat it, and
  `card_records` in `site_audit.json`, the one audit field a WRONG fix edits, to
  match the corrected card (a test requires the two to agree; #277). Then rerun `assemble_page.py`; no re-pin (#248,
  #258). If `figure_at_pin` itself is wrong, re-derive it with
  `build_site_audit.py` against a snapshot at the audit's pins (update skill
  step 11); it is derived, never typed (#268). The unit tests catch this on the
  PR and in the nightly, which still runs the card check after a failed test
  step so its report prints (#239, #240).
- GONE or CHANGED: a `SOURCES` entry needs repointing.
- MARKUP or UNCARDED: fix the card markup or `SOURCES`.
- AUDIT: never edit `site_audit.json` by hand, apart from `card_records` under
  WRONG (#273, #276, #277). A missing or
  non-integer `figure_at_pin`: regenerate it with `build_site_audit.py` against a
  snapshot at its pins (update skill steps 7 and 11). A bad pin time, or a missing
  or malformed audit: the builder copies the pin time from `revisions.json`, so
  take the pins and pin time from the last audit the builder wrote (`git log -p --
  _fleet/data/site_audit.json`), then regenerate. A Mech
  with no source entry needs a checked source and a full refresh at matching
  pins before its figures can join the common census.
- UNCHECKED: most sites could not be reached; rerun before changing anything.

Each numeric card needs a checked source in `SOURCES`; tests enforce that.
PathwayMech counts record links in its published browser. DUFMech counts the
6,532 family rows in its frozen seed worklist, preserving the distinction
between a candidate family and a curated mechanism record. Its card, statistics,
heatmap cells and shared-term links all use that same source snapshot. The cards
are read by `scripts/fleet/card_markup.py`, the parser shared by the assembler,
card check and tests; every card requires exactly one numeric headline.

The `Fleet page` workflow runs the tests and `assemble_page.py --check` on every
pull request and push, and checks the committed manifest against CLAW's live
`main` nightly and on manual dispatch, not on pull requests, for the same reason
as the card check: CLAW changes its manifest on its own schedule, and a check
that read it on every PR failed them all until a refresh landed (#303, #319).
The check detects changes to membership, capability declarations (including
reasons/settings), and artifact count; unrelated CLAW commits do not make the
snapshot stale. A PR that refreshes the manifest can run it on its own branch
with `gh workflow run fleet-page.yml --ref <branch>`. To run the read-only
checks locally:

```bash
python3 scripts/fleet/refresh_manifest.py --claw-root /path/to/culturebotai-claw --check
python3 scripts/fleet/assemble_page.py --check
```

## Cross-reference arrows

`XREFS` in `fleet_fragment.html` and the "How the Mechs reference each other" list
in `mechs_template.md` hold the same entries, one per ordered pair. The biological
graph shows the entries classified as data links or complementary biological
scope. Its arrows point at the Mech that consumes the data, or at the one a scope
decision defers to. Software reuse and unpopulated schema links remain in the
detailed list. Hover summaries describe the biological subject and data use;
the original implementation evidence stays in `what`, `ev` and the source links.
Hub spokes likewise require a data relationship; a shared namespace alone is
kept out of the graph. A documented reference needs an implemented, committed
source: a record
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

The September 28 sweep over records, schemas, scripts, config, vendored data,
curation decisions, docs and site generators found 30 arrows among the original
ten Mechs. PathwayMech adds an evidenced schema reference from TaxonMech; the
October 3 refresh checks that reference at the common refresh pin. DUFMech's
shared family identifiers produce vocabulary chords, not an invented direct
reference or kg-microbe ingestion claim.

## Vocabulary census updates

The October 3, 2026 census measures all twelve Mechs. PathwayMech contributes
152 pathway records. DUFMech contributes 6,532 seed-family rows from its frozen
JSON worklist, with Pfam and InterPro identifiers read from their typed fields.
A worklist row is one measured family; the JSON container and its redundant TSV
copy are not additional records. TaxonMech joined the census in #87; its 625,960 records are species-level and infraspecific taxa keyed by NCBI Taxonomy
id, each carrying its lineage, so a higher taxon is counted once per record
under it and TaxonMech's NCBITaxon cell dwarfs everyone else's. Its overlaps are
what tie taxa to the rest of the fleet: most taxa that ProteinTraitsMech,
HabitatMech, NaturalProductMech, CommunityMech, TraitMech, AntibioticMech,
CellStructureMech and CultureMech cite are TaxonMech records. A new member
needs a record source in `roots.py` and a link route in `build_subsets.py` before
its vocabulary can be measured. `duf_records.py` validates the selected dated
worklist and its manifest before projecting individual family documents.
`record_paths` tracks physical provenance; `record_documents` and the census's
record counts represent logical records, including those worklist rows.

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

The original ten-Mech benchmark took about eight minutes for the census and
fourteen for `build_subsets.py`, both dominated by TaxonMech's ~626k and ProteinTraitsMech's
~430k records (#230); `build_subsets.py` scans each record's text twice since it
separates prose fields from cited ones (#254).

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, NaturalProductMech,
TaxonMech's taxon.html route, ProteinTraitsMech hash routes, PathwayMech record
pages) and to the record's source file on GitHub for CultureMech and
MediaIngredientMech. DUFMech family links open the corresponding Pfam entry in
InterPro, using the family's stable accession.
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

`prefix_census.py`'s prefix alternation is a hand-maintained list. Its `norm`
table folds every namespace named for or qualified by a counted registry into
that registry: case and alternate names (`gold:` and `GOLD:`, `SwissProt:` and
`UniProt:`, `TAXON:` and `NCBITaxon:`, `CAS-RN:` and `CAS:`, `TC:` and `TCDB:`), and entity-qualified
namespaces (`kegg.compound:`, `mediadive.medium:`, `gtdb.genome:`,
`uniprot.location:`, `RHEA-COMP:`), as `gold.ecosystem` and `pubchem.compound`
always did (#271). Reference and curator collections named for a registry are
not its terms and do not fold into it: `GO_REF:` and `PO_REF:` are literature,
counted on their own and listed in `roots.CITATION`, and `GOC:` is curator
attribution, which the #84 rule never counts (#282). Mechs mix lowercase bioregistry spellings with upper-case ones,
TaxonMech most heavily (#279). The list was measured by scanning every record at the
#120 pins with a pattern allowing dots, underscores and hyphens; a spelling a
Mech adopts later is missed until someone scans again. Until #84's fold (#244,
#255, #270) those spellings went uncounted, 1.49 million GOLD and 556,160 BacDive
identifiers in TaxonMech among them. `build_subsets.py` folds the same spellings
for heatmap columns. Rhea compounds, whose ids share values with Rhea reactions,
and PDB ligand codes, a different kind of identifier from entries, keep their own
term keys, so an overlap never pairs a compound with a reaction or shows a
ligand as an entry. Overlap terms come only from what a record cites outside
prose fields (`build_subsets.PROSE`: notes and any `*_note(s)` key, change logs
and curation history, descriptions, definitions, rationales, discussion prompts,
quoted source snippets, `data_source`), because a note that rejects a term names it without
citing it: MediaIngredientMech's cobalamin record once made cob(I)alamin,
CHEBI:15982, a term it shared with CommunityMech (#254). An `evidence` list holds
structured references, so it still counts, apart from the notes and snippets in
it. The field list comes from an inventory of the keys holding identifiers at the
2026-09-28 pins, with `prompt` added after review (#327). MediaIngredientMech's
bare `cas_rn: 64-19-7` field is read as CAS:64-19-7, so its CAS identities stay
shared although their only prefixed copy is in the curation history (#328). The
heatmap and its cell lists still count every mention, as the census does.

Which namespaces to count is the inclusion rule in `roots.py` (#84): every
external identifier namespace a record cites, whether ontology, database or
registry, folded to one name per registry. Every culture collection counts as a
single entry, `CultureCollection`, whether an id names a strain or a medium in
the collection's catalogue: ATCC and DSMZ, counted separately before, the
forty-odd collections TaxonMech cites in `source_strain_identifiers`, and the
collection media CultureMech cites (CCAP, UTEX, JCM's medium list).
Literature and other citable works (ISBN, GO_REF, patents, Wikipedia, Zenodo
and the rest) are counted and listed in `roots.CITATION` beside PMID and DOI. A
Mech's own ids, other Mechs' ids, kg-microbe's ids, metamodel prefixes (skos,
biolink, rdf), curator attribution (GOC) and provenance are never counted.
`prefix_census.ADDED` lists what the rule brought in. At the 2026-09-28 pins,
every prefix with 20 or more occurrences, and every prefix at any count that
appears in a structured position (a list item or a whole field value), was
classified with sample ids read for each (#333). What the rule leaves out is
own, cross-Mech and kg-microbe ids, metamodel, attribution and provenance
prefixes, dictionaries cited without ids, and tokens that only look like
prefixes: chemical names, serotypes, strain designations, mass-shift notation.
Prefixes seen only in running text fewer than 20 times were not each checked. The largest additions are
ProteinTraitsMech's domain and structure resources (CATH, CDD, PROSITE, ECOD) and
TaxonMech's strain and genome registries (StrainInfo, NCBI Assembly, PATRIC,
BioSample). Every namespace present in the dated census appears in the heatmap
and its vocabulary total. `build_data.vocabularies()` derives the columns from
that snapshot; the table scrolls horizontally with sticky Mech names. DOI and
PMID lead; all remaining columns sort by Mech coverage, then occurrence total
and vocabulary name.
The table includes measured numeric rows for every suite member, including
PathwayMech and DUFMech.
`build_subsets.PREF` remains the smaller set with record lists and shared-term
edges. Other columns show plain counts and do not offer graph filters, because
this snapshot has not indexed their overlaps. Adding a namespace to the census
requires a full rescan; displaying the saved census does not.

The October 1 namespace audit adds SGD, WikiPathways, Rfam and GO-CAM's
`gomodel`, and folds uppercase HMDB and the additional case spellings found in
DUF family descriptions. `gomodel` identifiers are imported Gene Ontology
model and activity identifiers, not PathwayMech-local ids: Gene Ontology's
[upstream sulfate-activation model](https://github.com/geneontology/noctua-models/blob/master/models/YeastPathways_PWY-5340.ttl)
defines the namespace and the same model/reaction identifiers carried by
PathwayMech. The identifier namespace is counted separately from ontology
terms in GO. Metamodel prefixes such as skos and semapv remain excluded.

## Published-site refresh (October 3, 2026)

All twelve Mechs were pinned at their published `main` revisions at
2026-10-03 06:03 UTC. The census, shared-term subsets, repository statistics and
`data/site_audit.json` record the same revisions; provenance checks reject a
mixture of snapshots. The corpora are read from isolated snapshots of committed
Git blobs, never from shared checkouts' uncommitted files.
Record statistics use those pinned commits. Merged-PR totals are all-time GitHub
counts queried during the refresh, rather than counts cut off at the pin time.
The headline PR total includes all twelve Mechs, `culturebotai-claw` and
`CultureBotAI.github.io`. The two supporting repositories are stored in
`mech_stats.json` under `additional_repositories`; each Mech card retains its
own PR count. The stat strip lists one orchestrator and one project website
alongside the twelve knowledge factories.
`.claude/skills/update-xmech-page/` documents the refresh procedure.

`data/site_audit.json` records each pinned revision, card source URL, count at the
pin, response hashes and merged pull-request total. `build_site_audit.py` derives
those fields; `_fleet/audit_notes.json` supplies the checked explanatory notes.
The dedicated Mech pages link to the same pinned repository revisions.

Card figures follow the published browsers, except CultureMech's generated
README inventory and DUFMech's frozen JSON worklist. CommunityMech's browser
lists 456 communities; its repository additionally includes four isolates, so
the census and statistics count 460. DUFMech's 6,532 rows describe 4,533 unknown
candidates and 1,999 historical DUFs. The aggregate is labeled records and seed
families to preserve that distinction. PathwayMech contributes 152 records,
4,690 mechanistic edges and 15 taxa. Its KGX and SSSOM products are available in
the repository; their existence does not establish ingestion into kg-microbe.

CellStructureMech's pin contains 826 records, 742 GO-grounded, and TraitMech's
contains 959 records with 49.7% embedding coverage and 715 causal graphs.
NaturalProductMech records 809 evidence-supported producer claims; 155 records
describe biosynthetic pathways and 205 contain causal graphs (289 individual
graphs). Its 3,115-record total is unchanged.
Live sites may advance after the pins;
`check_cards.py` applies its documented grace window before declaring them stale.

CultureMech's generated README and landing page now both distinguish 15,910
normalized records from 6,320 merged records. Its documentation requires GitHub
Actions publishing to carry the generated browser data and indexes. The card
checker retains the committed README as its stable count source.

Follow client-side meta refreshes from site roots to `pages/` or `app/`. Read
JavaScript-backed figures from their data files: MediaIngredientMech uses
`data/ingredients.json` (2,953 ingredients; 2,611 MAPPED), and ProteinTraitsMech
uses `data/facets.json` (429,293 records; 34 source labels). ProteinTraitsMech's
static HTML still carries a legacy fallback count.

Reviewed-record counts are reported only where a schema defines a review
status. A Mech without that field still receives its merged-PR count and pinned
provenance, rather than an invented zero reviewed count. All twelve repositories
participate in statistics collection.

CLAW's b196e67 snapshot declares eleven members and enables PathwayMech's KGX and
SSSOM exporters. DUFMech remains outside that upstream manifest; its capability
row is explicitly undeclared. The capability table preserves CLAW's full
catalogue and recorded reasons. Capability adoption does not establish that all
CLAW workflows execute unattended.

All twelve pinned repositories license project-authored data under CC BY 4.0
and code under BSD-3-Clause. Redistributed source material retains its applicable terms.

The kg-microbe integration was checked at `1408e7099d039026d7611c240938d8e177753406`.
Its reviewed ingredient mappings and optional ingredient-context graph are
candidate inputs; production promotion and a graph release remain separate
review and validation steps. The graph and related pages preserve that
distinction.

The DUF nightly card check resolves the latest dated worklist on `main` through
GitHub directory metadata. Its pinned audit still records the frozen source
used for this page, so a new worklist cannot leave the live freshness check
reading the old snapshot indefinitely.
