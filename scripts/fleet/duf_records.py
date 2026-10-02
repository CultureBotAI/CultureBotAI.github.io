"""Read DUFMech's frozen family worklist as one logical record per Pfam family.

The worklist is a JSON array, unlike the fleet's one-YAML-file-per-record
corpora. Its manifest authenticates the payload and identifies the newest
snapshot. Older snapshots remain provenance, not additional families. These
records are seed families; their unknown_status does not record review.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
from pathlib import Path
import re

MANIFEST = re.compile(r"interpro-pfam-duf-(\d{4}-\d{2}-\d{2})\.manifest\.json$")
PFAM = re.compile(r"PF[0-9]{5}$")
INTERPRO = re.compile(r"IPR[0-9]{6}$")
STATUSES = {"UNKNOWN_CANDIDATE", "KNOWN_HISTORICAL_DUF"}


def _fail(message):
    raise SystemExit(f"DUFMech: {message}")


def _json(path):
    try:
        content = path.read_bytes()
        return content, json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"could not read {path}: {error}")


def snapshot(paths):
    """Return (payload path, family rows) from the newest verified manifest.

    An invalid newest snapshot stops the scan instead of silently substituting
    an older one. Both files must belong to the caller's physical record paths,
    so roots.revision() accounts for everything that is read.
    """
    physical = {Path(path).resolve() for path in paths}
    manifests = []
    for path in physical:
        match = MANIFEST.fullmatch(path.name)
        if match:
            try:
                date = datetime.date.fromisoformat(match.group(1))
            except ValueError:
                _fail(f"invalid snapshot date in {path.name}")
            manifests.append((date, path))
    if not manifests:
        _fail("no dated worklist manifest found")
    _, manifest_path = max(manifests)
    _, manifest = _json(manifest_path)
    if not isinstance(manifest, dict):
        _fail(f"{manifest_path.name}: manifest must be an object")
    date = MANIFEST.fullmatch(manifest_path.name).group(1)
    expected_id = "interpro-pfam-duf-" + date
    metadata = manifest.get("snapshot", {})
    if not isinstance(metadata, dict) or metadata.get("date") != date or metadata.get("id") != expected_id:
        _fail(f"{manifest_path.name}: snapshot identity disagrees with its filename")
    files = manifest.get("files", {})
    payload_info = files.get("json", {}) if isinstance(files, dict) else {}
    if not isinstance(payload_info, dict) or payload_info.get("path") != expected_id + ".json":
        _fail(f"{manifest_path.name}: JSON payload must be the matching snapshot filename")
    payload_path = (manifest_path.parent / payload_info["path"]).resolve()
    if payload_path not in physical:
        _fail(f"{manifest_path.name}: JSON payload is missing from the record paths")
    content, rows = _json(payload_path)
    if type(payload_info.get("bytes")) is not int or payload_info["bytes"] != len(content):
        _fail(f"{payload_path.name}: byte count differs from its manifest")
    if payload_info.get("sha256") != hashlib.sha256(content).hexdigest():
        _fail(f"{payload_path.name}: SHA-256 differs from its manifest")
    if not isinstance(rows, list):
        _fail(f"{payload_path.name}: family records must be an array")
    row_info = manifest.get("rows", {})
    if (not isinstance(row_info, dict) or type(row_info.get("total")) is not int
            or row_info["total"] != len(rows)):
        _fail(f"{payload_path.name}: family count differs from its manifest")
    seen = set()
    statuses = collections.Counter()
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            _fail(f"{payload_path.name}: family {number} must be an object")
        pfam = row.get("pfam_id")
        if not isinstance(pfam, str) or not PFAM.fullmatch(pfam):
            _fail(f"{payload_path.name}: family {number} has no valid Pfam identifier")
        if pfam in seen:
            _fail(f"{payload_path.name}: duplicate Pfam identifier {pfam}")
        seen.add(pfam)
        interpro = row.get("interpro_id")
        if interpro not in (None, "") and (not isinstance(interpro, str) or not INTERPRO.fullmatch(interpro)):
            _fail(f"{payload_path.name}: {pfam} has an invalid InterPro identifier")
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            _fail(f"{payload_path.name}: {pfam} has no family name")
        if not isinstance(row.get("description"), str):
            _fail(f"{payload_path.name}: {pfam} description must be text")
        if row.get("unknown_status") not in STATUSES:
            _fail(f"{payload_path.name}: {pfam} has an unsupported unknown status")
        statuses[row["unknown_status"]] += 1
    if row_info.get("by_unknown_status") != dict(statuses):
        _fail(f"{payload_path.name}: unknown-status counts differ from its manifest")
    return str(payload_path), rows


def documents(paths):
    """Yield (physical JSON path, YAML-shaped text) for each seed family.

    Only the explicit Pfam/InterPro identifier fields become structured CURIEs.
    Description text stays prose, preserving mention counts without treating
    its references as overlap evidence. InterPro's cite:PUB identifiers are
    left unchanged; they are not PubMed identifiers.
    """
    path, rows = snapshot(paths)
    for row in rows:
        lines = ["identifier: Pfam:" + row["pfam_id"],
                 "label: " + json.dumps(row["name"], ensure_ascii=False)]
        if row.get("interpro_id"):
            lines.append("interpro_id: InterPro:" + row["interpro_id"])
        lines.extend(["unknown_status: " + row["unknown_status"], "description: |"])
        lines.extend("  " + line for line in row["description"].splitlines())
        yield path, "\n".join(lines) + "\n"
