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

ORDER = list(RECORD_GLOBS)


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
