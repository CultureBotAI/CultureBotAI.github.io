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
import subprocess
import unicodedata

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


def _git(root: str, *args: str) -> str:
    # --no-optional-locks: plain `git status` takes index.lock and may rewrite
    # the index, and the default checkouts are shared with other work (#123).
    return subprocess.run(["git", "--no-optional-locks", "-C", root, *args],
                          capture_output=True, text=True, check=True).stdout


def _record_dirs(name: str) -> list[str]:
    """The fixed directory prefix of each record glob, e.g. data/traits."""
    dirs = []
    for pattern in RECORD_GLOBS[name]:
        parts = []
        for part in pattern.split("/"):
            if any(ch in part for ch in "*?["):
                break
            parts.append(part)
        dirs.append("/".join(parts))
    return dirs


def head(name: str) -> str | None:
    """The checkout's HEAD commit, or None if the directory is not a repository.

    A directory that is not itself a repository's top level returns None rather
    than the HEAD of whatever repository encloses it (#124).
    """
    root = mech_root(name)
    try:
        top = _git(root, "rev-parse", "--show-toplevel").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if os.path.realpath(top) != os.path.realpath(root):
        return None
    return _git(root, "rev-parse", "HEAD").strip()


def revision(name: str, paths: list[str] | None = None) -> str | None:
    """The commit a checkout's records are, or None outside git.

    Recorded by prefix_census.py, build_subsets.py and mech_stats.py so the
    committed outputs say which revision each number came from, and a test can
    check they were taken from the same one. The census and the stats had
    drifted to different checkouts before anything recorded that: 364
    CommunityMech records in one and 396 in the other (#85).

    "+dirty" is appended unless the records counted are exactly that commit's.
    `git status` alone cannot say so: it never lists ignored files, hides
    untracked ones under status.showUntrackedFiles=no, and says nothing about
    paths a sparse checkout leaves out, while record_paths() globs the disk. So
    the counted paths are compared with the files git tracks under the same
    globs, and status is consulted only for modified tracked files, scoped to
    the record directories and src/ (the schemas mech_stats.py reads), so an
    unrelated scratch file does not mark a checkout dirty (#121).

    Pass `paths` when record_paths(name) is already in hand.
    """
    sha = head(name)
    if sha is None:
        return None
    root = mech_root(name)
    if paths is None:
        paths = record_paths(name)
    counted = {unicodedata.normalize("NFC", os.path.relpath(p, root)) for p in paths}
    specs = [f":(glob){pattern}" for pattern in RECORD_GLOBS[name]]
    tracked = {unicodedata.normalize("NFC", p)
               for p in _git(root, "ls-files", "-z", "--", *specs).split("\0") if p}
    # Match glob.glob's semantics, which skip hidden files and directories.
    tracked = {p for p in tracked if not any(part.startswith(".") for part in p.split("/"))}
    for prefix in EXCLUDE_DIRS.get(name, []):
        tracked = {p for p in tracked if not p.startswith(prefix)}
    scope = [d for d in _record_dirs(name) + ["src"] if os.path.exists(os.path.join(root, d))]
    modified = _git(root, "status", "--porcelain", "--untracked-files=all", "--", *scope).strip()
    return sha + ("+dirty" if counted != tracked or modified else "")


def read_record(path: str, errors: str = "ignore") -> str:
    """One record's text. An unreadable record stops the run.

    The scans used to skip a file they could not open and still report the full
    glob count, so a partial read looked like a complete one (#127). The handle
    is closed, too: a bare open().read() per record left ~450,000 handles to the
    garbage collector, and each one warns under -W error::ResourceWarning (#135).
    """
    try:
        with open(path, encoding="utf-8", errors=errors) as handle:
            return handle.read()
    except OSError as error:
        raise SystemExit(f"could not read record {path}: {error}")


def unchanged(name: str, before: str | None) -> None:
    """Stop if a checkout's HEAD moved while its records were being read (#122)."""
    if before is None:
        return
    now = head(name)
    if now != before.split("+", 1)[0]:
        raise SystemExit(f"{name}: HEAD moved from {before[:12]} to {str(now)[:12]} during the scan; "
                         "rerun against a checkout nothing is updating, such as a pinned snapshot.")


def summary() -> str:
    return "\n".join(f"{name:22s} {len(record_paths(name)):>7,} records" for name in ORDER)


if __name__ == "__main__":
    print(f"MECHS_ROOT={MECHS_ROOT}")
    print(summary())
