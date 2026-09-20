"""Where the Mech checkouts are, and which files in each one are its records.

One directory holds every Mech as a direct child, so a single `MECHS_ROOT`
locates all of them:

    MECHS_ROOT=/path/to/Mechs python3 scripts/fleet/prefix_census.py

The scripts used to carry two roots and a per-Mech path each, which encoded the
layout the checkouts happened to have; when they moved, every script needed
editing (CultureBotAI.github.io#40). A missing root or a glob that matches
nothing raises here rather than producing an empty census, because both scripts
write numbers the page then states as fact, and zero records is indistinguishable
from a corpus that shrank unless somebody is told.
"""

from __future__ import annotations

import glob
import os

MECHS_ROOT = os.environ.get(
    "MECHS_ROOT", "/Users/marcin/Documents/VIMSS/ontology/Mechs"
)

# Record globs are relative to each Mech's checkout: the canonical corpus the
# page counts, not everything the repository stores.
RECORD_GLOBS: dict[str, list[str]] = {
    "HabitatMech": ["data/habitats/**/*.yaml"],
    "CommunityMech": ["kb/communities/*.yaml", "data/isolates/*.yaml"],
    "TraitMech": ["data/traits/**/*.yaml"],
    "CellStructureMech": ["data/structures/**/*.yaml"],
    "ProteinTraitsMech": ["data/traits/**/*.yaml"],
    "NaturalProductMech": ["data/natural_products/**/*.yaml"],
    "AntibioticMech": ["data/antibiotics/**/*.yaml"],
    "MediaIngredientMech": ["data/ingredients/**/*.yaml"],
    "CultureMech": ["data/merge_yaml/merged/*.yaml"],
}

# Paths a record glob sweeps up that are not records. A `**` glob cannot say
# "but not this subtree", and MediaIngredientMech keeps timestamped copies of
# edited records under data/ingredients/mapped/backups/. Counting those six made
# the census report 2,957 ingredient records where the Mech's own site, its
# published data/ingredients.json and its tracked tree all say 2,951
# (CultureBotAI.github.io#88). Matched against the path relative to the checkout.
EXCLUDE_DIRS: dict[str, list[str]] = {
    "MediaIngredientMech": ["data/ingredients/mapped/backups/"],
}

ORDER = list(RECORD_GLOBS)

# Prefixes that identify a piece of literature rather than a concept. Every
# Mech cites papers, so counting them alongside the ontologies would say only
# that, which is why build_subsets.py writes no record lists for them and
# build_data.py keeps them out of the heatmap's ordering. Declared once here
# because those two decisions have to agree (CultureBotAI.github.io#61).
CITATION = ["PMID", "DOI"]


def mech_root(name: str) -> str:
    """The checkout for one Mech, verified to exist."""
    root = os.path.join(MECHS_ROOT, name)
    if not os.path.isdir(root):
        raise SystemExit(
            f"{name}: no checkout at {root}. Set MECHS_ROOT to the directory "
            f"holding the Mech checkouts (currently {MECHS_ROOT})."
        )
    return root


def record_paths(name: str) -> list[str]:
    """Every record file for one Mech. Empty is an error, not a result."""
    root = mech_root(name)
    paths: list[str] = []
    for pattern in RECORD_GLOBS[name]:
        paths.extend(glob.glob(os.path.join(root, pattern), recursive=True))
    for prefix in EXCLUDE_DIRS.get(name, []):
        excluded = os.path.join(root, prefix)
        paths = [p for p in paths if not p.startswith(excluded)]
    if not paths:
        raise SystemExit(
            f"{name}: {', '.join(RECORD_GLOBS[name])} matched no files under {root}. "
            "Either the checkout is empty or the corpus moved; both need a look "
            "before the page states a number derived from it."
        )
    return sorted(paths)


def summary() -> str:
    return "\n".join(f"{name:22s} {len(record_paths(name)):>7,} records" for name in ORDER)


if __name__ == "__main__":
    print(f"MECHS_ROOT={MECHS_ROOT}")
    print(summary())
