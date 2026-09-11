# Sources for the X-Mech Suite page

`mechs.md` at the site root is **generated**. Edit the sources here and rebuild:

- `mechs_template.md` — the page prose, cards, cross-reference list, capability matrix.
- `fleet_fragment.html` — the self-contained graph component (CSS, markup, JS). The
  per-Mech facts (`MECHS`), cross-references (`XREFS`) and kg-microbe ties (`HUB`) are
  hand-curated at the top of the script.
- `data/` — derived numbers: `prefix_census.json`, `subsets_summary.json`, `fleet_data.json`,
  `mech_stats.json`.

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
python3 scripts/fleet/mech_stats.py       # _fleet/data/mech_stats.json
python3 scripts/fleet/assemble_page.py    # mechs.md
```

The two scanning passes take about two minutes each, dominated by
ProteinTraitsMech's ~430k records.

`mech_stats.py` counts reviewed records and asks GitHub for merged pull-request
totals, which `assemble_page.py` then substitutes into the stat strip and the
Mech cards; the build fails rather than shipping an unfilled placeholder. It
needs `gh` authenticated against the CultureBotAI repositories and PyYAML, which
it uses to find each Mech's review slot in that Mech's LinkML schema. Pass
`--no-prs` to recount records while keeping the pull-request numbers on file.

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, ProteinTraitsMech
hash routes) and to the record's source file on GitHub for CultureMech,
MediaIngredientMech and NaturalProductMech, whose per-record pages are not
deployed. NaturalProductMech does now publish a site; its repository root
redirects to `pages/index.html`.

MIBiG and NPAtlas are carried through the whole pipeline alongside the
ontologies, because they are how NaturalProductMech grounds its corpus.
