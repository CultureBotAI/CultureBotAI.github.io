# Use the existing schema-documentation rubric for the new sites

The proposed CofactorMech feature row marks schema documentation as missing
because it links raw LinkML YAML instead of a rendered class/slot browser.
That conflicts with the existing column: annotated raw YAML links receive
partial coverage for AntibioticMech, CellStructureMech, HabitatMech and other
sites in the [current feature audit](https://github.com/CultureBotAI/CultureBotAI.github.io/blob/dc9daa500c8ddeb38fc08ee6ddbe1fc54c91b595/_fleet/data/site_features.json).

The live [CofactorMech schema](https://culturebotai.github.io/CofactorMech/schema/cofactormech.yaml)
has class and attribute descriptions. Rate it partial while keeping the note
that rendered schema navigation is absent. Apply the same criterion when
reviewing AssayMech; do not change the rubric only for the new sites.

Found by the independent reviewer during the Cofactor canary verdict review.
This is a directory-rating consistency finding, not a site implementation bug.
