#!/usr/bin/env python3
"""Correct two source-backed license claims for website issue #565, 2026-11-12.

Inputs: maintained graph/resources/notes and their existing generated audit copy.
Outputs: CC0 code/schema descriptions; no pins, measurements or audit dates move.
The generated audit receives only the corrected maintained-note prefix, retaining
its builder-derived suffix and every mechanical field byte-for-byte in value.
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MECHS = ("CofactorMech", "AssayMech")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    updates = {}
    for relative in ("_fleet/fleet_fragment.html", "resources.md"):
        path = ROOT / relative
        text = path.read_text()
        lines = text.splitlines(keepends=True)
        for mech in MECHS:
            matches = [i for i, line in enumerate(lines) if mech in line and "BSD-3-Clause code" in line]
            assert len(matches) == 1, (relative, mech, matches)
            index = matches[0]
            lines[index] = lines[index].replace("BSD-3-Clause code", "CC0 1.0 code and schemas")
        updates[path] = "".join(lines)
    notes_path = ROOT / "_fleet/audit_notes.json"
    audit_path = ROOT / "_fleet/data/site_audit.json"
    notes = json.loads(notes_path.read_text())
    audit = json.loads(audit_path.read_text())
    original_audit = copy.deepcopy(audit)
    for mech in MECHS:
        old = notes["notes"][mech]
        phrase = "Project code is BSD-3-Clause and data is CC BY 4.0"
        assert old.count(phrase) == 1
        corrected = old.replace(phrase, "Original project code and schemas are CC0 1.0 and curated data is CC BY 4.0")
        rows = [row for row in audit["repositories"] if row["repo"] == mech]
        assert len(rows) == 1 and rows[0]["notes"].startswith(old)
        rows[0]["notes"] = corrected + rows[0]["notes"][len(old):]
        notes["notes"][mech] = corrected
    only_notes_restored = copy.deepcopy(audit)
    for row, original in zip(only_notes_restored["repositories"], original_audit["repositories"], strict=True):
        row["notes"] = original["notes"]
    assert only_notes_restored == original_audit, "Mechanical audit fields must remain unchanged"
    updates[notes_path] = json.dumps(notes, indent=2) + "\n"
    updates[audit_path] = json.dumps(audit, indent=1, ensure_ascii=False) + "\n"
    for relative in ("CLAUDE.md", "_fleet/mechs_template.md"):
        path = ROOT / relative
        text = path.read_text()
        phrase = "The suite licensing policy is CC BY 4.0 for data and BSD-3-Clause for code."
        assert text.count(phrase) == 1
        text = text.replace(phrase, phrase + " CofactorMech and AssayMech dedicate their original code and schemas under CC0 1.0; their curated data is CC BY 4.0.")
        updates[path] = text
    for path, content in updates.items():
        print(path.relative_to(ROOT))
        if args.apply:
            path.write_text(content)
            assert path.read_text() == content


if __name__ == "__main__":
    main()
