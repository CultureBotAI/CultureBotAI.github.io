The November 4 refresh's pre-PR diff review found stale secondary claims in `resources.md` after the headline totals had been updated:

- AntibioticMech still said 309 records have molecular targets; the pin `47746980c7f56e7d9a37ebb7eb4d475d3a7ea6e5` contains 333.
- NaturalProductMech still said 3,077 producer-bearing records, universal biosynthetic gene-cluster coverage and no REVIEWED records. Its pin `b0fb4c22274771cd75308eaf5e209b584c12bcdf` instead reports 3,097 producer-bearing records, 3,123 gene-cluster-bearing records out of 3,136, and 20 REVIEWED records.

Evidence: the pinned NaturalProductMech README inventory, `secondary-fleet.json`, and the dedicated `secondary-NaturalProductMech.json` recount under `_fleet/reviews/refresh-20261104/`. The recount uses the existing record globs and truthy native fields; it does not change census methodology.

Correct these resource-page claims in the refresh PR and search maintained page sources, including ignored files, for surviving old statements.
