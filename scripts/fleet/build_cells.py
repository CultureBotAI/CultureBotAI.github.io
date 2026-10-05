"""Build record lists for every populated vocabulary-census cell.

Uses the census matcher, including prose and citations, without changing the
structured-term rules used for graph overlaps. Run after prefix_census.py and
before build_data.py, against the same pinned source checkouts.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote

from build_subsets import MECHS, prepare, record_identity, slug_for
from prefix_census import norm, rx
from roots import ORDER, record_documents, record_paths, revision, unchanged

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "_fleet/data"
OUT = REPO / "assets/fleet"


def encoded(document):
    return json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _scan(mech, cap_cell=300, *, source_revision=None, paths=None):
    if type(cap_cell) is not int or cap_cell < 1:
        raise ValueError("Record-list cap must be a positive integer")
    cfg = MECHS[mech]
    cells, files = {}, 0
    for path, text in record_documents(mech, paths):
        files += 1
        occurrences = Counter(norm.get(p, p) for p in rx.findall(text))
        ref = None
        for prefix, count in occurrences.items():
            cell = cells.setdefault(prefix, {"mech": mech, "prefix": prefix,
                "base": cfg["base"], "total": 0, "occurrences": 0, "records": []})
            cell["total"] += 1
            cell["occurrences"] += count
            if len(cell["records"]) < cap_cell:
                if ref is None:
                    doc_id, label, _ = record_identity(path, text)
                    slug = slug_for(mech, path, doc_id, label)
                    if slug:
                        if not re.fullmatch(r"[A-Za-z0-9_.~%\-/]+", slug):
                            raise ValueError(f"{mech}: unsafe record link {slug!r}")
                        ref = [slug, label]
                    else:
                        # Isolates and other records without a published page
                        # still contribute to the census. Link their exact source.
                        if not source_revision:
                            source_revision = revision(mech, paths)
                        if not re.fullmatch(r"[0-9a-f]{40}", source_revision or ""):
                            raise ValueError(f"{mech}: a clean source pin is required for fallback links")
                        relative = Path(path).relative_to(cfg["root"]).as_posix()
                        repo = "proteintraitsmech" if mech == "ProteinTraitsMech" else mech
                        url = f"https://github.com/CultureBotAI/{repo}/blob/{source_revision}/{quote(relative, safe='/')}"
                        ref = ["", label, url]
                cell["records"].append(ref)
    return files, cells


def scan(mech, cap_cell=300, *, source_revision=None, paths=None):
    """Return one cell document per vocabulary; counts include every logical record."""
    return _scan(mech, cap_cell, source_revision=source_revision, paths=paths)[1]


def build(census, cap_cell=300):
    """Read and verify all inputs before allowing any output to be replaced."""
    pins = census.get("_revisions", {})
    if set(pins) != set(ORDER) or any(not re.fullmatch(r"[0-9a-f]{40}", p or "") for p in pins.values()):
        raise ValueError("Census must identify a clean source revision for every Mech")
    if {m for m in census if not m.startswith("_")} != set(ORDER):
        raise ValueError("Census members must match the measured suite")
    prepare()
    paths = {m: record_paths(m) for m in ORDER}
    for mech in ORDER:
        if revision(mech, paths[mech]) != pins[mech]:
            raise ValueError(f"{mech}: source revision differs from the census or is dirty")
    documents, summary = {}, {"_revisions": dict(pins), "cells": {}}
    for mech in ORDER:
        files, cells = _scan(mech, cap_cell, source_revision=pins[mech], paths=paths[mech])
        if files != census[mech]["files"]:
            raise ValueError(f"{mech}: logical record count differs from the census ({files})")
        counts = {prefix: doc["occurrences"] for prefix, doc in cells.items()}
        if counts != census[mech]["prefixes"]:
            raise ValueError(f"{mech}: vocabulary occurrence counts differ from the census")
        for prefix, doc in sorted(cells.items()):
            key = mech + "|" + prefix
            documents[key] = doc
            summary["cells"][key] = {"records": doc["total"], "occurrences": doc["occurrences"],
                "sha256": hashlib.sha256(encoded(doc)).hexdigest()}
        unchanged(mech, pins[mech])
        print(mech, files, "records;", len(cells), "vocabulary lists", flush=True)
    for mech in ORDER:
        if revision(mech, paths[mech]) != pins[mech]:
            raise ValueError(f"{mech}: source revision changed or became dirty during the scan")
    return summary, documents


def write_outputs(summary, documents):
    """Stage complete validated output, replace assets, then publish the summary."""
    out, data = Path(OUT), Path(DATA)
    out.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    cells = out / "cells"
    expected = {key.replace("|", "--") + ".json" for key in documents}
    if set(summary["cells"]) != set(documents):
        raise ValueError("Cell documents and summary differ")
    with tempfile.TemporaryDirectory(prefix=".cells-", dir=out) as staging:
        staging = Path(staging)
        for key, doc in documents.items():
            filename = key.replace("|", "--") + ".json"
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.json", filename):
                raise ValueError(f"Unsafe cell filename: {filename}")
            payload = encoded(doc)
            if hashlib.sha256(payload).hexdigest() != summary["cells"][key]["sha256"]:
                raise ValueError(f"Cell hash differs from summary: {key}")
            (staging / filename).write_bytes(payload)
        staged_summary = staging / "cells_summary.json"
        staged_summary.write_text(json.dumps(summary, indent=1) + "\n")
        # Path.iterdir includes ignored/hidden entries. Refuse to remove anything
        # other than previously generated top-level JSON cell files.
        stale = []
        if cells.exists():
            for path in cells.iterdir():
                if path.is_symlink() or not path.is_file() or not re.fullmatch(r"[A-Za-z]+Mech--[A-Za-z0-9_.-]+\.json", path.name):
                    raise ValueError(f"Unexpected file in generated cell directory: {path}")
                if path.name not in expected:
                    stale.append(path)
        cells.mkdir(exist_ok=True)
        for filename in sorted(expected):
            os.replace(staging / filename, cells / filename)
        for path in stale:
            path.unlink()
        # Hashes in the last-written summary expose an interrupted mixed write.
        os.replace(staged_summary, data / "cells_summary.json")


def main():
    with (Path(DATA) / "prefix_census.json").open() as handle:
        census = json.load(handle)
    summary, documents = build(census)
    write_outputs(summary, documents)
    print("Wrote", len(documents), "complete census cell lists", flush=True)


if __name__ == "__main__":
    main()
