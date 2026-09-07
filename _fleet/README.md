# Sources for the X-Mech Suite page

`mechs.md` at the site root is **generated**. Edit the sources here and rebuild:

- `mechs_template.md` — the page prose, cards, cross-reference list, capability matrix.
- `fleet_fragment.html` — the self-contained graph component (CSS, markup, JS). The
  per-Mech facts (`MECHS`), cross-references (`XREFS`) and kg-microbe ties (`HUB`) are
  hand-curated at the top of the script.
- `data/` — derived numbers: `prefix_census.json`, `subsets_summary.json`, `fleet_data.json`.

Pipeline (from the site root, with the Mech checkouts available locally; the
ProteinTraitsMech pass over ~430k records takes several minutes):

```bash
python3 scripts/fleet/prefix_census.py    # heatmap counts
python3 scripts/fleet/build_subsets.py    # assets/fleet/{edges,cells}/*.json + subsets_summary.json
python3 scripts/fleet/build_data.py       # _fleet/data/fleet_data.json
python3 scripts/fleet/assemble_page.py    # mechs.md
```

Jekyll ignores `_fleet/` (leading underscore) and `scripts/` is excluded in `_config.yml`.
Record links resolve to each Mech's published page where one exists (TraitMech,
CellStructureMech, AntibioticMech, HabitatMech, CommunityMech, ProteinTraitsMech
hash routes) and to the record's source file on GitHub for CultureMech and
MediaIngredientMech, whose per-record pages are not deployed.
