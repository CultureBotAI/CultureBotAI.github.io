# Sources for the X-Mech Suite page

`mechs.md` at the site root is **generated**. Edit the sources here and rebuild:

- `mechs_template.md` — the page prose, cards and cross-reference list. Membership
  badges, counts and capability rows are generated from the manifest snapshot.
- `fleet_fragment.html` — the self-contained graph component (CSS, markup, JS). The
  per-Mech facts (`MECHS`), cross-references (`XREFS`) and kg-microbe ties (`HUB`) are
  hand-curated at the top of the script.
- `data/manifest.json` — membership and all capability declarations from a pinned
  commit of CLAW's canonical manifest, plus the canonical artifact count.
- Other `data/` files — derived numbers: `prefix_census.json`, `subsets_summary.json`, `fleet_data.json`.

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
graph and cards with its 100-taxon snapshot, but its vocabulary counts have not
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
python3 scripts/fleet/assemble_page.py    # mechs.md
```

The two scanning passes take about two minutes each, dominated by
ProteinTraitsMech's ~430k records.

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, ProteinTraitsMech
hash routes) and to the record's source file on GitHub for CultureMech,
MediaIngredientMech and NaturalProductMech in the existing census indexes.
NaturalProductMech and TaxonMech both publish browse sites linked from their
cards; these links are separate from the historical census's record-link routes.

MIBiG and NPAtlas are carried through the whole pipeline alongside the
ontologies, because they are how NaturalProductMech grounds its corpus.
