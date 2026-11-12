#!/usr/bin/env python3
"""Promote one independently reviewed new-site row and links, 2026-11-12.

Inputs: retained live audit and reviewed verdicts, current directory sources.
Outputs: maintained links/features plus a bounded audit-note prefix replay.
No census pins, measured fields, historical audit times or record links change.
Run the directory assembler afterward; merging requires separate approval.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "_fleet/reviews/site-launch-20261112"
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import validate_site_features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", required=True, choices=["CofactorMech", "AssayMech"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    name = args.mech
    slug = "cofactor" if name == "CofactorMech" else "assay"
    receipt = json.loads((REVIEW / f"{slug}-audit.json").read_text())
    verdicts = json.loads((REVIEW / f"{slug}-verdicts.json").read_text())
    assert receipt["complete"] and receipt["mech"] == name
    for phase in ("deployment_before", "deployment_after"):
        assert receipt[phase]["state"] == "success"
        assert receipt[phase]["sha"] == verdicts["deployed_revision"]
        assert receipt[phase]["site"] == verdicts["site"]
    assert receipt["manifest"]["data"]["revision"] == verdicts["deployed_revision"]
    site, github = verdicts["site"], verdicts["repository"]
    assert site == f"https://culturebotai.github.io/{name}/"
    assert github == f"https://github.com/CultureBotAI/{name}"
    updates = {}

    def edit(relative, function):
        path = ROOT / relative
        before = updates.get(path, path.read_text())
        after = function(before)
        assert before != after, f"No expected edit in {relative}"
        updates[path] = after

    def replace_once(text, before, after):
        assert text.count(before) == 1, (before, text.count(before))
        return text.replace(before, after)

    features_path = ROOT / "_fleet/data/site_features.json"
    features = json.loads(features_path.read_text())
    assert features["mechs"][name]["site"] is None, "Already published; inspect instead of replacing a later audit"
    features["mechs"][name] = verdicts
    validate_site_features(features, set(features["mechs"]))
    updates[features_path] = json.dumps(features, indent=2, ensure_ascii=False) + "\n"

    def card(text):
        pattern = rf'(<article class="mech-card" data-mech="{name}".*?</article>)'
        matches = list(re.finditer(pattern, text, re.S))
        assert len(matches) == 1
        block = matches[0].group(1)
        primary = re.search(r'<a class="primary" href="([^"]+)">Records at pin</a>', block)
        assert primary and primary.group(1).startswith(github + "/tree/")
        replacement = f'<a class="primary" href="{site}">Browse</a><a href="{primary.group(1)}">Records at pin</a>'
        return text[:matches[0].start()] + block.replace(primary.group(0), replacement) + text[matches[0].end():]

    edit("_fleet/mechs_template.md", card)

    def graph(text):
        text = replace_once(text, f'href="{github}"', f'href="{site}"')
        text = replace_once(text, f'title="Open {name} on GitHub"', f'title="Open {name}"')
        pattern = r'^    ' + re.escape(name) + r': \{ .*?$'
        lines = re.findall(pattern, text, re.M)
        assert len(lines) == 1 and lines[0].count('site: ""') == 1
        return text.replace(lines[0], lines[0].replace('site: ""', f'site: "{site}"'))

    edit("_fleet/fleet_fragment.html", graph)
    edit("_includes/footer.html", lambda text: replace_once(text, f'href="{github}">{name}</a>', f'href="{site}">{name}</a>'))
    for relative in ("index.md", "communitymech.md", "culturemech.md", "mediaingredientmech.md", "microgrowagents.md"):
        edit(relative, lambda text: replace_once(text, f'[{name}]({github})', f'[{name}]({site})'))

    def resources(text):
        text = replace_once(text, f'**[GitHub Repository]({github})** |', f'**[Browse]({site})** | **[GitHub Repository]({github})** |')
        pattern = rf'^### {name}[^\n]*\n.*?(?=^### |\Z)'
        matches = list(re.finditer(pattern, text, re.M | re.S))
        assert len(matches) == 1
        block = matches[0].group(0)
        changed = replace_once(block, "No public GitHub Pages browser is deployed yet.", "Its public browser presents these records with source provenance and scoped relationships; the suite's website feature audit records the deployed revision separately from these corpus pins.")
        return text[:matches[0].start()] + changed + text[matches[0].end():]

    edit("resources.md", resources)

    def guidance(text):
        text = replace_once(text, f'**{name}** ({github})', f'**{name}** ({site})')
        published = sum(features["mechs"][mech]["site"] is not None for mech in ("CofactorMech", "AssayMech"))
        count = {1: "twelve", 2: "thirteen"}[published]
        replacement = f"Three corpus\nMechs have pages here; {count} link to their own GitHub Pages sites."
        pending = [mech for mech in ("CofactorMech", "AssayMech") if features["mechs"][mech]["site"] is None]
        if pending:
            replacement += f"\n{pending[0]} links to its pinned repository until its browser is deployed."
        else:
            replacement += "\nCofactorMech and AssayMech's website verdicts have their own November 12, 2026 review; their corpus pins and record links remain unchanged."
        pattern = r"Three corpus\nMechs have pages here;.*?(?= CMMMech and AIMech began publishing theirs)"
        assert len(re.findall(pattern, text, re.S)) == 1
        return re.sub(pattern, replacement, text, flags=re.S)

    edit("CLAUDE.md", guidance)
    notes_path, audit_path = ROOT / "_fleet/audit_notes.json", ROOT / "_fleet/data/site_audit.json"
    notes, audit = json.loads(notes_path.read_text()), json.loads(audit_path.read_text())
    original = copy.deepcopy(audit)
    old = notes["notes"][name]
    new = replace_once(old, "no public GitHub Pages browser is deployed yet", "website publication is recorded separately in the dated site-feature audit")
    notes["notes"][name] = new
    row = next(row for row in audit["repositories"] if row["repo"] == name)
    assert row["notes"].startswith(old)
    row["notes"] = new + row["notes"][len(old):]
    restored = copy.deepcopy(audit)
    for current, previous in zip(restored["repositories"], original["repositories"], strict=True):
        current["notes"] = previous["notes"]
    assert restored == original, "Mechanical corpus audit values must not move"
    updates[notes_path] = json.dumps(notes, indent=2) + "\n"
    updates[audit_path] = json.dumps(audit, indent=1, ensure_ascii=False) + "\n"
    for path, content in updates.items():
        print(path.relative_to(ROOT))
        if args.apply:
            path.write_text(content)
            assert path.read_text() == content


if __name__ == "__main__":
    main()
