"""Assemble mechs.md from the page sources and pinned fleet snapshot."""
import argparse
from html import escape
import json
from pathlib import Path
import re

from refresh_manifest import validate

REPO = Path(__file__).resolve().parents[2]
FLEET = REPO / "_fleet"
COLUMNS = ("curation_history", "strict_validation", "vendored_sync", "deep_research",
           "knowledge_gap_scan", "environment_coverage", "sssom_export", "kgx_export",
           "source_queue", "source_catalogue", "site_contract")


def capability_rows(snapshot):
    rows = []
    for name, mech in snapshot["mechs"].items():
        cells = [f"<td>{escape(name)}</td>"]
        for key in COLUMNS:
            declaration = mech["capabilities"][key]
            status = declaration["status"]
            css = {"enabled": "e", "disabled": "d", "not_applicable": "n"}[status]
            label = f"{key}: {status.replace('_', ' ')}"
            if declaration.get("reason"):
                label += ". " + declaration["reason"].strip()
            label = escape(label, quote=True)
            cells.append(f'<td><i class="{css}" role="img" title="{label}" aria-label="{label}"></i></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(rows)


def script_json(value):
    # A reason containing markup must remain data inside the inline script.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def assemble(template, fragment, data, snapshot):
    validate(snapshot)
    names = set(snapshot["mechs"])
    badges = re.findall(r"<!--FLEET_BADGE:([^>]+)-->", template)
    if len(badges) != len(names) or set(badges) != names:
        raise ValueError("Mech cards must match canonical fleet membership exactly")
    cards = re.findall(r'<article\b[^>]*\bdata-mech="([^"]+)"', template)
    if len(cards) != len(names) or set(cards) != names:
        raise ValueError("Actual Mech cards must match canonical fleet membership exactly")
    metadata = fragment.split("var MECHS = {", 1)[1].split("\n  };", 1)[0]
    node_names = re.findall(r"^\s+([A-Za-z]+Mech):\s*\{", metadata, re.MULTILINE)
    if len(node_names) != len(names) or set(node_names) != names:
        raise ValueError("Graph metadata must match canonical fleet membership exactly")
    measured = set(data["order"])
    if not measured or len(data["order"]) != len(measured) or not measured <= names:
        raise ValueError("Census order must be a unique subset of fleet members")
    if set(data["heat"]) != measured or any(set(data["heat"][m]) != set(data["voc"]) for m in measured):
        raise ValueError("Census heat rows must cover the measured members and vocabularies")
    if any(edge["a"] not in measured or edge["b"] not in measured for edge in data["vocab_edges"]):
        raise ValueError("Census edges must connect measured members")
    replacements = {
        "/*FLEET_DATA*/{}/*END*/": script_json(data),
        "/*FLEET_MANIFEST*/{}/*END_MANIFEST*/": script_json(snapshot),
    }
    for token, value in replacements.items():
        if fragment.count(token) != 1:
            raise ValueError(f"Expected one {token}")
        fragment = fragment.replace(token, value)
    if template.count("<!--FLEET_FRAGMENT-->") != 1:
        raise ValueError("Expected one fleet fragment")
    page = template.replace("<!--FLEET_FRAGMENT-->", fragment)
    source = snapshot["source"]
    tokens = {
        "<!--FLEET_COUNT-->": str(len(names)),
        "<!--FLEET_ARTIFACT_COUNT-->": str(snapshot["artifact_count"]),
        "<!--FLEET_MANIFEST_SOURCE-->": f'<a href="{escape(source["url"], quote=True)}">CLAW fleet manifest at {escape(source["revision"][:7])}</a>',
        "<!--FLEET_CAPABILITIES-->": capability_rows(snapshot),
    }
    tokens.update({f"<!--FLEET_BADGE:{name}-->": '<span class="badge">in fleet manifest</span>' for name in names})
    for token, value in tokens.items():
        if token not in page:
            raise ValueError(f"Missing source token {token}")
        page = page.replace(token, value)
    if re.search(r"<!--FLEET_|/\*FLEET_", page):
        raise ValueError("Unresolved fleet placeholder")
    if "{{" in page or "{%" in page:
        raise ValueError("Liquid tags would be interpreted by Jekyll")
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    page = assemble((FLEET / "mechs_template.md").read_text(),
                    (FLEET / "fleet_fragment.html").read_text(),
                    json.loads((FLEET / "data/fleet_data.json").read_text()),
                    json.loads((FLEET / "data/manifest.json").read_text()))
    target = REPO / "mechs.md"
    if args.check:
        if target.read_text() != page:
            raise SystemExit("mechs.md is stale; run scripts/fleet/assemble_page.py")
        print("Generated mechs.md is current")
    else:
        target.write_text(page)
        print(f"Wrote mechs.md ({len(page.encode())} bytes)")


if __name__ == "__main__":
    main()
