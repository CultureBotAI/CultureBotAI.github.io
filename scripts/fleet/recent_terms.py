"""Build _fleet/data/recent_terms.json with the 5 most recently added records per Mech.

Run from the site root: `python3 scripts/fleet/recent_terms.py`. Reads the Mech
checkouts through scripts/fleet/roots.py (set MECHS_ROOT to relocate them) at
their clean HEAD revisions and writes _fleet/data/recent_terms.json.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse

import build_subsets
import duf_records
from roots import ORDER, mech_root, record_paths, revision, unchanged

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "_fleet/data/recent_terms.json"
COUNT = 5
GH_REPO = {"ProteinTraitsMech": "proteintraitsmech"}
BLOB_MECHS = {"MediaIngredientMech", "CultureMech", "CMMMech", "AIMech"}
ORIGINAL_NAME = re.compile(r"^original_name\s*:\s*(.+)$", re.M)


def _git_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("GIT_CONFIG_GLOBAL", "/dev/null")
    env.setdefault("GIT_CONFIG_NOSYSTEM", "1")
    return env


def _git(root: str, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", root, *args],
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} in {root} failed: {done.stderr.strip()}")
    return done.stdout


def _clean_revision(mech: str, paths: list[str] | None = None) -> str:
    rev = revision(mech, paths=paths)
    if not rev or not re.fullmatch(r"[0-9a-f]{40}", rev):
        raise SystemExit(
            f"{mech}: refusing to record recent terms from {rev or 'an unversioned directory'} "
            "(commit, stash or clean changes under its record globs first)"
        )
    return rev


def _record_url(mech: str, rev: str, rel_path: str, full_path: str, doc_id: str, label: str) -> str:
    gh_repo = GH_REPO.get(mech, mech)
    if mech not in BLOB_MECHS:
        slug = build_subsets.slug_for(mech, full_path, doc_id, label)
        if slug is not None:
            return build_subsets.SITE_BASE[mech] + slug
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in rel_path.split("/"))
    return f"{build_subsets.GH}{gh_repo}/blob/{rev}/{quoted}"


def _display_identity(mech: str, full_path: str, text: str) -> tuple[str, str]:
    doc_id, label, _ = build_subsets.record_identity(full_path, text, mech)
    if mech == "AIMech" and doc_id and label.endswith(" · " + doc_id):
        label = label[: -len(" · " + doc_id)]
    if mech == "CultureMech":
        match = ORIGINAL_NAME.search(text[:2000])
        if match:
            orig = build_subsets.unq(match.group(1))
            if orig:
                label = orig
    return doc_id, label


def _duf_recent(root: str, rev: str, paths: list[str], count: int = COUNT) -> list[dict]:
    _, current_rows = duf_records.snapshot(paths)
    by_id = {row["pfam_id"]: row for row in current_rows}
    worklists_dir = Path(root) / "data/worklists"
    snapshots = sorted(
        p for p in worklists_dir.glob("interpro-pfam-duf-*.json")
        if not p.name.endswith(".manifest.json")
    )
    items: list[dict] = []
    seen: set[str] = set()
    for idx in range(len(snapshots) - 1, -1, -1):
        snap = snapshots[idx]
        rel = snap.relative_to(root).as_posix()
        log_line = _git(root, "log", "-n", "1", "--format=%H %aI", rev, "--", rel).strip()
        if log_line:
            commit_sha, commit_iso = log_line.split(" ", 1)
        else:
            commit_sha, commit_iso = rev, ""
        snap_date = snap.stem.removeprefix("interpro-pfam-duf-")
        rows = json.loads(snap.read_text(encoding="utf-8"))
        prev_ids = (
            {r["pfam_id"] for r in json.loads(snapshots[idx - 1].read_text(encoding="utf-8"))}
            if idx > 0
            else set()
        )
        added = [r for r in rows if r["pfam_id"] not in prev_ids and r["pfam_id"] in by_id]
        for row in reversed(added):
            pfam_id = row["pfam_id"]
            if pfam_id in seen:
                continue
            seen.add(pfam_id)
            cur = by_id[pfam_id]
            doc_id = f"Pfam:{pfam_id}"
            items.append({
                "id": doc_id,
                "label": cur["name"],
                "url": build_subsets.SITE_BASE["DUFMech"] + pfam_id + ".html",
                "path": rel,
                "commit": commit_sha[:7],
                "added_at": commit_iso or (snap_date + "T00:00:00Z"),
                "added_date": snap_date,
            })
            if len(items) >= count:
                return items
    return items


def recent_for_mech(mech: str, count: int = COUNT) -> dict:
    root = mech_root(mech)
    paths = record_paths(mech)
    rev = _clean_revision(mech, paths=paths)
    if mech == "DUFMech":
        records = _duf_recent(os.path.realpath(root), rev, paths, count=count)
        unchanged(mech, rev)
        return {
            "mech": mech,
            "repo": GH_REPO.get(mech, mech),
            "source_revision": rev,
            "records": records,
        }

    active_rel = {
        os.path.relpath(p, root).replace(os.sep, "/"): p
        for p in paths
    }
    chosen: list[tuple[str, str, str]] = []
    seen_rel: set[str] = set()
    for limit in (["-n", "50"], []):
        log_out = _git(
            root,
            "log",
            *limit,
            rev,
            "--diff-filter=A",
            "--format=COMMIT %H %aI",
            "--name-only",
        )
        cur_sha = ""
        cur_iso = ""
        for raw_line in log_out.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("COMMIT "):
                _, cur_sha, cur_iso = line.split(" ", 2)
                continue
            if line in active_rel and line not in seen_rel:
                seen_rel.add(line)
                chosen.append((line, cur_sha, cur_iso))
                if len(chosen) >= count:
                    break
        if len(chosen) >= count:
            break

    records = []
    for rel, commit_sha, commit_iso in chosen:
        full_path = active_rel[rel]
        text = Path(full_path).read_text(encoding="utf-8", errors="replace")
        doc_id, label = _display_identity(mech, full_path, text)
        url = _record_url(mech, rev, rel, full_path, doc_id, label)
        added_date = datetime.datetime.fromisoformat(commit_iso).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d")
        records.append({
            "id": doc_id or Path(rel).stem,
            "label": label,
            "url": url,
            "path": rel,
            "commit": commit_sha[:7],
            "added_at": commit_iso,
            "added_date": added_date,
        })
    unchanged(mech, rev)
    return {
        "mech": mech,
        "repo": GH_REPO.get(mech, mech),
        "source_revision": rev,
        "records": records,
    }


def build_all(count: int = COUNT) -> dict:
    build_subsets.prepare()
    mechs = [recent_for_mech(mech, count=count) for mech in ORDER]
    # Pick the 5 most recently added records across the suite (at most 1 per Mech
    # so the suite-wide highlight spans multiple repositories).
    newest_per_mech = []
    for entry in mechs:
        if entry["records"]:
            first = dict(entry["records"][0], mech=entry["mech"])
            newest_per_mech.append(first)
    newest_per_mech.sort(
        key=lambda r: (
            datetime.datetime.fromisoformat(r["added_at"].replace("Z", "+00:00")),
            r["mech"],
            r["id"],
        ),
        reverse=True,
    )
    return {
        "count_per_mech": count,
        "latest_across_suite": newest_per_mech[:count],
        "mechs": mechs,
    }


def main() -> int:
    data = build_all()
    out_path = Path(os.environ.get("RECENT_TERMS_OUT") or OUT)
    out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(data['mechs'])} Mechs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
