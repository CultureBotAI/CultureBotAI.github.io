The refresh audit found two XREF descriptions that infer universal writer
coverage from the existence and use of shared helper functions:

- CultureMech → TraitMech says “nearly every TraitMech write script goes
  through them,” without defining or checking the denominator of write scripts.
- CellStructureMech → TaxonMech says “Every TaxonMech record is written through
  them,” while the cited source establishes helper reuse rather than every
  possible write path.

Both claims occur in `_fleet/fleet_fragment.html` and its mirrored list in
`_fleet/mechs_template.md`.

Verified evidence at the November 4 pins:

- TraitMech's `scripts/add_abia_system_trait.py` and
  `scripts/enrich_oxidase_test_trait.py` use both curation-history and validated
  writer helpers at `c7627fdb55a2b3352a4a12b2da8dbc98a4d1c8c6`.
- [TaxonMech's seeder](https://github.com/CultureBotAI/TaxonMech/blob/e0cc7c86ac2107242ab499db610737f5fcad1c9b/src/taxonmech/seed.py#L1372)
  calls `write_validated_taxon(doc, path)`.
- TaxonMech's helper docstrings retain the HabitatMech/CellStructureMech
  adaptation credit.

Use these bounded implementation claims in both descriptions. The arrows,
directions and software-reuse classification stay unchanged. Acceptance is
matching prose in the template and graph, with no unmeasured universal claim.

The independent hand-claim audit and the root editor verified these paths
separately. Existing issues were searched for writer and coverage findings;
the related coverage issues concern different measurements.
