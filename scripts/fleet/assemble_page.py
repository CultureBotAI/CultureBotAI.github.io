"""Assemble mechs.md from the page sources and pinned fleet snapshot."""
import argparse
import datetime
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


# The fleet size reads as prose almost everywhere it appears — a heading, an
# intro sentence, an SVG title — where the site's other pages write "ten". Only
# the stat tile wants a numeral, so the count is offered in both forms rather
# than spelled out at every call site (CultureBotAI.github.io#93).
WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve")


def number_word(value: int) -> str:
    """The count as prose. Past the short words a numeral reads better anyway."""
    return WORDS[value] if 0 <= value < len(WORDS) else f"{value:,}"


CARD_RECORDS = re.compile(r'<div class="num"><b>([\d,]+)</b>')


def fleet_records(template):
    """What the Mech cards add up to.

    The tile used to carry its own typed figure and drifted away from the
    cards it was meant to total: it read 448,724 while the ten cards summed to
    1,059,170, short by roughly the whole of TaxonMech, which was admitted
    after the tile was last edited (CultureBotAI.github.io#76). Summing the
    cards keeps the two true to each other by construction, and it is the
    right source because the cards cite each Mech's published browser, which
    the record-corpus census does not measure the same way.

    The ten are not ten counts of the same thing: the cards call theirs taxon
    records, published recipes, natural product structures and so on. The tile
    says "curated entries" rather than "records" for that reason (#82).
    """
    counts = [int(n.replace(",", "")) for n in CARD_RECORDS.findall(template)]
    if not counts:
        raise ValueError("No Mech card record counts found")
    return counts


def assemble(template, fragment, data, snapshot, stats, census):
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
    # mech_stats.py follows the same manifest, so every card is covered; an
    # admission that reached the manifest but not a recount would otherwise
    # leave a stat line unfilled, which the placeholder sweep below catches.
    counted = {m["mech"] for m in stats["mechs"]}
    if counted != names:
        raise ValueError("Mech stats must cover canonical fleet membership exactly")
    counts = fleet_records(template)
    if len(counts) != len(names):
        raise ValueError("Every Mech card must carry a record count")
    # The census is a dated scan, so its vocabulary tally is labelled with its own
    # run date rather than as current, and its coverage is stated below.
    # Keys beginning with an underscore are the scan's own metadata, not Mechs.
    # Read rather than pop: assemble() is handed a parsed document and must not
    # consume it, or a second call with the same object fails (#81).
    as_of = census["_as_of"]
    measured_mechs = {name: mech for name, mech in census.items() if not name.startswith("_")}
    vocabularies = {prefix for mech in measured_mechs.values() for prefix in mech["prefixes"]}
    tokens = {
        "<!--FLEET_COUNT-->": str(len(names)),
        "<!--FLEET_COUNT_WORD-->": number_word(len(names)),
        "<!--FLEET_RECORDS_TOTAL-->": f"{sum(counts):,}",
        "<!--FLEET_VOCAB_COUNT-->": f"{len(vocabularies):,}",
        # "all ten Mechs" once the census reaches every member, which it has
        # since TaxonMech was added (#87); "nine of the ten Mechs" otherwise.
        "<!--FLEET_CENSUS_COVERAGE-->": (f"all {number_word(len(names))} Mechs" if len(measured_mechs) == len(names)
                                         else f"{number_word(len(measured_mechs))} of the {number_word(len(names))} Mechs"),
        # The scan's own run date, carried in the file it writes. Not the file's
        # mtime: git neither records nor restores those, so a fresh clone would
        # date the census to the day somebody cloned it.
        "<!--FLEET_CENSUS_DATE-->": datetime.date.fromisoformat(as_of).strftime("%-d %B %Y"),
        "<!--FLEET_PRS_TOTAL-->": f"{stats['merged_prs_total']:,}",
        "<!--FLEET_ARTIFACT_COUNT-->": str(snapshot["artifact_count"]),
        "<!--FLEET_MANIFEST_SOURCE-->": f'<a href="{escape(source["url"], quote=True)}">CLAW fleet manifest at {escape(source["revision"][:7])}</a>',
        "<!--FLEET_CAPABILITIES-->": capability_rows(snapshot),
    }
    tokens.update({f"<!--FLEET_BADGE:{name}-->": '<span class="badge">in fleet manifest</span>' for name in names})
    for mech in stats["mechs"]:
        prs = f"{mech['merged_prs']:,} merged PRs"
        # A null reviewed count means the Mech's schema has no status that can
        # say REVIEWED, which is not the same as nothing having been reviewed,
        # so the card says nothing rather than zero. See mech_stats.py.
        line = prs if mech["reviewed"] is None else f"{mech['reviewed']:,} reviewed \u00b7 {prs}"
        tokens[f"<!--FLEET_STATS:{mech['mech']}-->"] = line
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
                    json.loads((FLEET / "data/manifest.json").read_text()),
                    json.loads((FLEET / "data/mech_stats.json").read_text()),
                    json.loads((FLEET / "data/prefix_census.json").read_text()))
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
