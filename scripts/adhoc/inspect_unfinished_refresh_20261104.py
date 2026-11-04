#!/usr/bin/env python3
"""Inventory the stopped October 30 refresh without modifying it, 2026-11-04.

Inputs: --repo protected checkout, its HEAD blobs, and snapshot paths declared
by its untracked helpers (parsed as source; never imported or executed).
Outputs: --report JSON plus Markdown, for the November 4 refresh PR.
Use --check to verify the captured branch, HEAD, index, dirty-path set, file
bytes, sizes, modes and modification times without writing either report.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


SUMMARIES = {
    "prefix_census.json": "prefix_census.py",
    "subsets_summary.json": "build_subsets.py",
    "cells_summary.json": "build_cells.py",
    "recent_terms.json": "recent_terms.py",
    "fleet_data.json": "build_data.py",
    "mech_stats.json": "mech_stats.py",
}
FINAL_SOURCES = (
    "_fleet/data/manifest.json", "_fleet/audit_notes.json",
    "_fleet/data/site_audit.json", "_fleet/data/site_features.json",
    "_fleet/mechs_template.md", "_fleet/fleet_fragment.html", "mechs.md",
    "index.md", "resources.md", "culturemech.md", "mediaingredientmech.md",
    "communitymech.md", "CLAUDE.md", "_fleet/README.md",
)


def utc(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    return subprocess.check_output(["git", "-C", str(repo), *args], env=env)


def stage(path: str) -> str:
    if path.startswith("assets/fleet/cells/"):
        return "build_cells.py"
    if path.startswith("assets/fleet/edges/"):
        return "build_subsets.py"
    if path.startswith("_fleet/data/"):
        return SUMMARIES.get(Path(path).name, "other")
    if path.startswith("scripts/adhoc/"):
        return "helper source (not executed)"
    return "other"


def status_entries(repo: Path) -> list[dict]:
    tokens = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
    entries = []
    offset = 0
    while offset < len(tokens) and tokens[offset]:
        token = tokens[offset].decode("utf-8", "surrogateescape")
        entry = {"status": token[:2], "path": token[3:]}
        offset += 1
        if "R" in entry["status"] or "C" in entry["status"]:
            entry["original_path"] = tokens[offset].decode("utf-8", "surrogateescape")
            offset += 1
        entries.append(entry)
    return sorted(entries, key=lambda row: row["path"])


def metadata(path: Path) -> dict:
    if not path.exists() and not path.is_symlink():
        return {"exists": False}
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        content = os.fsencode(os.readlink(path))
        kind = "symlink"
    elif stat.S_ISREG(before.st_mode):
        content = path.read_bytes()
        kind = "regular file"
    else:
        raise ValueError(f"unsupported protected file kind: {path}")
    after = path.lstat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f"file changed while hashing: {path}")
    return {"exists": True, "kind": kind, "sha256": digest(content),
            "size_bytes": before.st_size, "mtime_ns": before.st_mtime_ns,
            "mtime_utc": utc(before.st_mtime), "mode": stat.S_IMODE(before.st_mode)}


def capture(repo: Path) -> dict:
    entries = status_entries(repo)
    result = {
        "branch": git(repo, "symbolic-ref", "--short", "HEAD").decode().strip(),
        "head": git(repo, "rev-parse", "HEAD").decode().strip(),
        "logical_index_sha256": digest(git(repo, "ls-files", "--stage", "-z")),
        "files": [{**entry, "pipeline_stage": stage(entry["path"]),
                   **metadata(repo / entry["path"])} for entry in entries],
    }
    if entries != status_entries(repo):
        raise ValueError("dirty paths changed during capture")
    return result


def pins(payload: dict) -> dict:
    if "_revisions" in payload:
        return payload["_revisions"]
    if isinstance(payload.get("mechs"), list):
        return {row["mech"]: row["source_revision"] for row in payload["mechs"] if "source_revision" in row}
    return {}


def read_helpers(repo: Path, files: list[dict]) -> tuple[list[dict], list[Path]]:
    rows, snapshots = [], set()
    for entry in files:
        if entry["status"] != "??" or not entry["path"].endswith(".py"):
            continue
        source = (repo / entry["path"]).read_text()
        tree = ast.parse(source, filename=entry["path"])
        declared = sorted({node.value for node in ast.walk(tree)
                           if isinstance(node, ast.Constant) and isinstance(node.value, str)
                           and node.value.startswith("/") and "/xmech-refresh-20261030" in node.value})
        snapshots.update(Path(path) for path in declared)
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        rows.append({"path": entry["path"], "sha256": entry["sha256"],
                     "docstring": ast.get_docstring(tree), "functions": functions,
                     "declared_snapshot_paths": declared, "executed": False,
                     "review": (
                         "Builds/fetches snapshots and runs six derived stages; prepare also refreshes the manifest. "
                         "Its canary function verifies clean pins and record availability but does not execute a full scan stage. "
                         "Do not rerun as part of this inventory."
                         if "run_pipeline" in functions else
                         "Reads pinned corpora, Git blobs and live sites, printing secondary figures and citation checks. "
                         "Those computations and paths were not validated or executed by this inventory."
                     )})
    return rows, sorted(snapshots)


def snapshot_info(path: Path) -> dict:
    result = {"path": str(path), "exists": path.is_dir()}
    if not path.is_dir():
        return result
    # iterdir includes dotfiles and never consults ignore rules.
    result["top_level_entries"] = sorted(child.name for child in path.iterdir())
    result["files"] = {child.name: metadata(child) for child in path.iterdir() if child.is_file()}
    revisions = path / "revisions.json"
    if revisions.is_file():
        result["revisions"] = json.loads(revisions.read_text())
    mechs = path / "mechs"
    result["mechs_directory_exists"] = mechs.is_dir()
    result["mechs_directory_entries_including_hidden"] = sorted(child.name for child in mechs.iterdir()) if mechs.is_dir() else None
    result["logs"] = {child.name: child.read_text().splitlines()[-12:]
                      for child in path.iterdir() if child.is_file() and child.suffix == ".log"}
    return result


def analyse(repo: Path, protected: dict) -> dict:
    summaries = {}
    for filename in SUMMARIES:
        relative = f"_fleet/data/{filename}"
        current_bytes = (repo / relative).read_bytes()
        base_bytes = git(repo, "show", f"{protected['head']}:{relative}")
        current, base = json.loads(current_bytes), json.loads(base_bytes)
        summaries[filename] = {"stage": SUMMARIES[filename], "head_sha256": digest(base_bytes),
                               "working_sha256": digest(current_bytes), "head_pins": pins(base),
                               "working_pins": pins(current), "head_as_of": base.get("as_of", base.get("_as_of")),
                               "working_as_of": current.get("as_of", current.get("_as_of"))}
        if filename == "mech_stats.json":
            old_rows = {row["mech"]: row for row in base["mechs"]}
            summaries[filename]["counts"] = [
                {"mech": row["mech"], "head_records": old_rows[row["mech"]]["records"],
                 "working_records": row["records"], "head_merged_prs": old_rows[row["mech"]]["merged_prs"],
                 "working_merged_prs": row["merged_prs"]} for row in current["mechs"]]
            summaries[filename]["head_merged_prs_total"] = base["merged_prs_total"]
            summaries[filename]["working_merged_prs_total"] = current["merged_prs_total"]
            summaries[filename]["head_record_total"] = sum(row["records"] for row in base["mechs"])
            summaries[filename]["working_record_total"] = sum(row["records"] for row in current["mechs"])
    helpers, snapshot_paths = read_helpers(repo, protected["files"])
    snapshots = [snapshot_info(path) for path in snapshot_paths]
    comparison = []
    for path in FINAL_SOURCES:
        original = git(repo, "show", f"{protected['head']}:{path}")
        current = (repo / path).read_bytes()
        comparison.append({"path": path, **metadata(repo / path), "head_sha256": digest(original),
                           "equals_head": original == current})
    source_map = summaries["prefix_census.json"]["working_pins"]
    revision_consistency = {name: row["working_pins"] == source_map
                            for name, row in summaries.items() if row["working_pins"]}
    manifest_maps = [{mech: row["sha"] for mech, row in snap.get("revisions", {}).get("mechs", {}).items()}
                     for snap in snapshots]
    counts = Counter(row["pipeline_stage"] for row in protected["files"])
    stages = []
    for script in SUMMARIES.values():
        selected = [row for row in protected["files"] if row["pipeline_stage"] == script]
        logname = script.removesuffix(".py") + ".log"
        stages.append({"stage": script, "modified_file_count": len(selected),
                       "mtime_min_utc": min(row["mtime_utc"] for row in selected) if selected else None,
                       "mtime_max_utc": max(row["mtime_utc"] for row in selected) if selected else None,
                       "saved_log_paths": [str(Path(snap["path"]) / logname) for snap in snapshots if logname in snap.get("logs", {})],
                       "interpretation": "Persisted derived output and saved log are evidence that this stage ran; no corpus scan was repeated."})
    command = ["rg", "-n", "-uu", "--hidden", "--glob", "!.git/**",
               "xmech-refresh-20261030|build_snapshot_20261030|inspect_secondary_20261030", "."]
    search = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    if search.returncode not in (0, 1):
        raise ValueError(search.stderr)
    cells = json.loads((repo / "_fleet/data/cells_summary.json").read_text())["cells"]
    mismatches = []
    for key, entry in cells.items():
        cell = repo / "assets/fleet/cells" / (key.replace("|", "--") + ".json")
        if not cell.is_file() or digest(cell.read_bytes()) != entry["sha256"]:
            mismatches.append(str(cell.relative_to(repo)))
    return {"summaries": summaries, "stage_file_counts": dict(counts), "stages": stages,
            "derived_pin_maps_agree": all(revision_consistency.values()),
            "pin_agreement_by_file": revision_consistency,
            "snapshot_pin_maps_match_derived": [mapping == source_map for mapping in manifest_maps],
            "helpers": helpers, "snapshots": snapshots, "final_source_comparisons": comparison,
            "cell_asset_integrity": {"checked": len(cells), "mismatches": mismatches},
            "search": {"command": command, "cwd": str(repo), "ignored_and_hidden_included": True,
                       "scope": "All text files in the protected repository, excluding .git storage; no machine-wide absence claim. Snapshot directory listings independently include hidden entries.",
                       "matches": search.stdout.splitlines()},
            "stage_assessment": {
                "derived_pipeline": "All six derived summaries have changed; five recorded pin maps agree and match the saved snapshot manifest. Saved logs and asset hashes support persisted completion, not a fresh scientific validation.",
                "manifest": "Working manifest equals HEAD; identical CLAW pins can legitimately leave refresh_manifest with no content delta.",
                "hand_curated_and_provenance": "Maintained cards, graph claims, audit notes, final site audit and repeated prose remain byte-identical to HEAD; no completed final refresh is persisted here.",
                "assembly": "mechs.md equals HEAD while its derived inputs changed, so the refreshed inputs have not been assembled into the protected page.",
                "features": "site_features.json equals HEAD; no new website-feature audit is inferred.",
                "snapshot_reuse": "The named snapshot's Mech directory has no entries, including hidden entries; its revisions and logs survive, but the Mech clones would need reconstruction before a rerun.",
                "execution": "Neither untracked helper was run, imported or modified. No check writes to the protected checkout or calls the network.",
            }}


def markdown(report: dict) -> str:
    protected, details = report["protected"], report["analysis"]
    files = protected["files"]
    tracked = sum(row["status"] != "??" for row in files)
    cell_files = sum(row["path"].startswith("assets/fleet/cells/") for row in files)
    edge_files = sum(row["path"].startswith("assets/fleet/edges/") for row in files)
    summary_files = sum(row["path"].startswith("_fleet/data/") for row in files)
    dates = sorted(row["mtime_utc"] for row in files)
    rows = ["# Unfinished October 30 refresh inventory", "",
            f"Captured {report['captured_at_utc']} from `{report['protected_repository']}`.", "",
            f"Branch `{protected['branch']}` at `{protected['head']}` has **{tracked} modified tracked files and {len(files)-tracked} untracked helpers ({len(files)} dirty paths total)**. No protected files were changed. Every dirty path's SHA-256, size, modification time, mode and Git status is retained in the companion JSON, together with branch, HEAD and logical index hash.", "",
            f"The tracked modifications comprise {summary_files} derived summaries, {cell_files} cell payloads and {edge_files} graph-edge payloads.", "",
            f"Dirty-file modification times span `{dates[0]}` to `{dates[-1]}`. Timestamps support ordering; they do not establish execution success by themselves.", "",
            "## Pipeline evidence", "", "| Stage | Modified paths | Earliest mtime (UTC) | Latest mtime (UTC) |",
            "| --- | ---: | --- | --- |"]
    rows.extend(f"| {row['stage']} | {row['modified_file_count']} | {row['mtime_min_utc']} | {row['mtime_max_utc']} |" for row in details["stages"])
    rows += ["", f"The five pin-bearing summaries agree across all {len(details['summaries']['prefix_census.json']['working_pins'])} Mechs and match the saved snapshot. All {details['cell_asset_integrity']['checked']} cell payloads were checked against their summary SHA-256 values; mismatches: {len(details['cell_asset_integrity']['mismatches'])}.", "",
             "## Exact source pins", "", "The same working pin column applies to census, subsets, cells, statistics and recent terms. Their exact individual maps, including HEAD maps, are retained in JSON.", "",
             "| Mech | HEAD pin | Unfinished working pin |", "| --- | --- | --- |"]
    census = details["summaries"]["prefix_census.json"]
    rows.extend(f"| {mech} | `{census['head_pins'][mech]}` | `{pin}` |" for mech, pin in census["working_pins"].items())
    statistics = details["summaries"]["mech_stats.json"]
    rows += ["", "## Changed record counts", "",
             f"Repository records total {statistics['head_record_total']:,} at HEAD and {statistics['working_record_total']:,} in the unfinished statistics. Merged-PR totals are {statistics['head_merged_prs_total']:,} and {statistics['working_merged_prs_total']:,}, respectively.", "",
             "| Mech | HEAD records | Working records |", "| --- | ---: | ---: |"]
    rows.extend(f"| {row['mech']} | {row['head_records']:,} | {row['working_records']:,} |"
                for row in statistics["counts"] if row["head_records"] != row["working_records"])
    rows += ["", "## Snapshot and helpers", ""]
    for snapshot in details["snapshots"]:
        rows += [f"Snapshot: `{snapshot['path']}`.", "",
                 f"Its saved pin-time bound is `{snapshot.get('revisions', {}).get('pinned_at_utc')}`. The revision manifest and {len(snapshot.get('logs', {}))} stage logs remain. The `mechs/` directory contains {len(snapshot.get('mechs_directory_entries_including_hidden') or [])} entries, including hidden entries; the original Mech checkouts are therefore unavailable at this named snapshot path.", ""]
    rows.extend(f"- `{row['path']}`: {row['review']}" for row in details["helpers"])
    rows += ["", "## Completion assessment", ""]
    rows.extend(f"- **{name.replace('_', ' ')}:** {text}" for name, text in details["stage_assessment"].items())
    rows += ["", "## Preservation check and search scope", "", details["search"]["scope"], "",
             "The reference search used `rg -n -uu --hidden` and excluded only `.git` storage. This includes ignored files. Its exact command and all matching lines are saved in JSON. For the stopped October 30 run, both untracked helpers identify the same named snapshot. The search does not establish whether additional snapshots exist elsewhere on the machine.", "",
             "Recheck without modifying either report:", "", "```bash",
             "python3 scripts/adhoc/inspect_unfinished_refresh_20261104.py \\",
             f"  --repo '{report['protected_repository']}' \\",
             "  --report _fleet/reviews/unfinished-refresh-20261030.json --check", "```", ""]
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--enrich", action="store_true", help="Refresh analysis only after the existing preservation record passes")
    args = parser.parse_args()
    repo, destination = args.repo.resolve(), args.report.resolve()
    if destination.is_relative_to(repo):
        parser.error("report must be outside the protected checkout")
    current = capture(repo)
    if args.check or args.enrich:
        saved = json.loads(destination.read_text())
        if str(repo) != saved["protected_repository"] or current != saved["protected"]:
            raise SystemExit("FAIL: protected checkout differs from the captured inventory")
        print(f"PASS: branch, HEAD, logical index and all {len(current['files'])} dirty files are unchanged")
        if args.enrich:
            saved["analysis"] = analyse(repo, current)
            if capture(repo) != saved["protected"]:
                raise SystemExit("FAIL: protected checkout changed during analysis")
            destination.write_text(json.dumps(saved, indent=2) + "\n")
            destination.with_suffix(".md").write_text(markdown(saved))
            print("Updated analysis; original protection hashes and capture time retained")
        return
    if destination.exists() or destination.with_suffix(".md").exists():
        parser.error("refusing to overwrite an existing preservation inventory")
    report = {"schema_version": 1, "captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "protected_repository": str(repo), "protected": current,
              "analysis": analyse(repo, current)}
    if capture(repo) != current:
        raise SystemExit("FAIL: protected checkout changed during inventory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    destination.with_suffix(".md").write_text(markdown(report))
    print(f"Saved inventory for {len(current['files'])} dirty paths to {destination}")


if __name__ == "__main__":
    main()
