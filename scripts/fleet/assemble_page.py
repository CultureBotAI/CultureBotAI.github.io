"""Assemble mechs.md from the page sources and pinned fleet snapshot."""
import argparse
import datetime
from html import escape
import json
from pathlib import Path
import re

from card_markup import card_figures, card_names, markup_problems
from mech_stats import ADDITIONAL_REPOS, GH_REPO
from refresh_manifest import validate
from roots import ORDER

REPO = Path(__file__).resolve().parents[2]
FLEET = REPO / "_fleet"
# Words the capability keys abbreviate, spelled as the fleet writes them.
ACRONYMS = {"id": "ID", "kgx": "KGX", "sssom": "SSSOM", "metpo": "METPO"}


# Compound modifiers the page has always hyphenated (#318).
HYPHENATED = {"knowledge_gap_scan": "knowledge-gap scan", "causal_graph_coverage": "causal-graph coverage"}


def capability_label(key):
    """A capability key as a column heading: kgx_export -> KGX export."""
    words = [ACRONYMS.get(word, word) for word in HYPHENATED.get(key, key).replace(" ", "_").split("_")]
    return " ".join([words[0][:1].upper() + words[0][1:]] + words[1:])


def capability_columns(snapshot):
    """Every capability CLAW's catalogue declares, in its order. The table used
    to show a hand-picked eleven, so a capability CLAW added never appeared
    (#305); it now shows the whole catalogue (#310)."""
    return list(snapshot["capability_catalogue"])


def capability_head(snapshot):
    cells = ['<th scope="col">Mech</th>'] + [f'<th scope="col"><span>{escape(capability_label(key))}</span></th>'
                                             for key in capability_columns(snapshot)]
    return "<tr>" + "".join(cells) + "</tr>"


def capability_rows(snapshot, suite_order=None):
    rows = []
    for name in suite_order if suite_order is not None else snapshot["mechs"]:
        mech = snapshot["mechs"].get(name)
        cells = [f'<th scope="row">{escape(name)}</th>']  # #314
        for key in capability_columns(snapshot):
            if mech is None:
                # Suite coverage is independent of CLAW admission. An absent
                # declaration says neither disabled nor not applicable.
                css = "u"
                label = f"{capability_label(key)}: not declared in CLAW manifest"
            else:
                declaration = mech["capabilities"][key]
                status = declaration["status"]
                css = {"enabled": "e", "disabled": "d", "not_applicable": "n"}[status]
                label = f"{capability_label(key)}: {status.replace('_', ' ')}"  # #314
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


def fleet_records(template):
    """What the Mech cards add up to, one figure per card.

    The tile used to carry its own typed figure and drifted away from the
    cards it was meant to total: it read 448,724 while the ten cards summed to
    1,059,170, short by roughly the whole of TaxonMech, which was admitted
    after the tile was last edited (CultureBotAI.github.io#76). Summing the
    cards keeps the two true to each other by construction, and it is the
    right source because the cards cite each Mech's published browser (or, for
    CultureMech, its committed README), which
    the record-corpus census does not measure the same way.

    These are not counts of the same thing: the cards call theirs taxon
    records, published recipes, natural product structures and seed families.
    The tile names both records and seed families instead of claiming that all
    entries are curated mechanisms.

    Keyed by Mech and read card by card through card_markup, the parser
    check_cards.py also uses, so the total and the nightly check cannot read the
    markup differently (#114).
    """
    # Exactly one figure per card, and none outside the cards: a second stat
    # tile used to replace a card's headline in the total without failing (#218).
    problems = markup_problems(template)
    if problems:
        raise ValueError("Every counted Mech card must carry a record count, exactly once: "
                         + "; ".join(f"{mech}: {why}" for mech, why in problems))
    figures = card_figures(template)
    if not figures:
        raise ValueError("No Mech card record counts found")
    return figures


def pr_activity(stats):
    """Validate the distinct repositories behind the displayed activity total."""
    extra = stats.get("additional_repositories", [])
    if (len(extra) != len(ADDITIONAL_REPOS)
            or {row["repo"] for row in extra} != set(ADDITIONAL_REPOS)):
        raise ValueError("PR activity must include CLAW and the project website exactly once")
    rows = stats["mechs"] + extra
    if any(row["repo"] != GH_REPO.get(row["mech"], row["mech"]) for row in stats["mechs"]):
        raise ValueError("PR activity repository must match its Mech")
    repos = [row["repo"] for row in rows]
    expected = {GH_REPO.get(row["mech"], row["mech"]) for row in stats["mechs"]} | set(ADDITIONAL_REPOS)
    if len(set(repos)) != len(repos) or set(repos) != expected:
        raise ValueError("PR activity must count each repository exactly once")
    if any(type(row["merged_prs"]) is not int or row["merged_prs"] < 0 for row in rows):
        raise ValueError("PR activity counts must be nonnegative integers")
    total = sum(row["merged_prs"] for row in rows)
    if type(stats["merged_prs_total"]) is not int or stats["merged_prs_total"] != total:
        raise ValueError("PR activity total must equal the sum across all repositories")
    return total, len(repos)


def assemble(template, fragment, data, snapshot, stats, census):
    validate(snapshot)
    members = set(snapshot["mechs"])
    # The site measures the suite; CLAW declares its governed members. A new
    # canonical admission still requires a corresponding card and graph node.
    names = set(ORDER) | members
    badges = re.findall(r"<!--FLEET_BADGE:([^>]+)-->", template)
    if len(badges) != len(names) or set(badges) != names:
        raise ValueError("Mech cards must match declared suite membership exactly")
    cards = card_names(template)
    if len(cards) != len(names) or set(cards) != names:
        raise ValueError("Actual Mech cards must match declared suite membership exactly")
    metadata = fragment.split("var MECHS = {", 1)[1].split("\n  };", 1)[0]
    node_names = re.findall(r"^\s+([A-Za-z]+Mech):\s*\{", metadata, re.MULTILINE)
    if len(node_names) != len(names) or set(node_names) != names:
        raise ValueError("Graph metadata must match declared suite membership exactly")
    measured = set(data["order"])
    if not measured or len(data["order"]) != len(measured) or not measured <= names:
        raise ValueError("Census order must be a unique subset of fleet members")
    if set(data["heat"]) != measured or any(set(data["heat"][m]) != set(data["voc"]) for m in measured):
        raise ValueError("Census heat rows must cover the measured members and vocabularies")
    measured_mechs = {name: mech for name, mech in census.items() if not name.startswith("_")}
    if set(measured_mechs) != measured:
        raise ValueError("Census members must match the measured graph and heat rows")
    positive_cells = {m + "--" + v for m in measured for v, n in data["heat"][m].items() if n}
    if set(data["cells"]) != positive_cells:
        raise ValueError("Every populated heatmap cell must have a matching-record count")
    if any(type(n) is not int or n < 1 for n in data["cells"].values()):
        raise ValueError("Heatmap matching-record counts must be positive integers")
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
    counted = {m["mech"] for m in stats["mechs"]}
    if counted != names or len(stats["mechs"]) != len(names):
        raise ValueError("Mech stats must cover every suite member exactly once")
    prs_total, pr_repo_count = pr_activity(stats)
    counts = fleet_records(template)
    if set(counts) != names:
        raise ValueError("Every counted Mech card must carry a record count")
    # The census is a dated scan, so its vocabulary tally is labelled with its own
    # run date rather than as current, and its coverage is stated below.
    # Keys beginning with an underscore are the scan's own metadata, not Mechs.
    # Read rather than pop: assemble() is handed a parsed document and must not
    # consume it, or a second call with the same object fails (#81).
    as_of = census["_as_of"]
    vocabularies = {prefix for mech in measured_mechs.values() for prefix in mech["prefixes"]}
    tokens = {
        "<!--FLEET_COUNT-->": str(len(names)),
        "<!--FLEET_COUNT_WORD-->": number_word(len(names)),
        "<!--FLEET_RECORDS_TOTAL-->": f"{sum(counts.values()):,}",
        "<!--FLEET_VOCAB_COUNT-->": f"{len(vocabularies):,}",
        # State coverage from the measured corpus and suite membership.
        "<!--FLEET_CENSUS_COVERAGE-->": (f"all {number_word(len(names))} Mechs" if len(measured_mechs) == len(names)
                                         else f"{number_word(len(measured_mechs))} of the {number_word(len(names))} Mechs"),
        # The scan's own run date, carried in the file it writes. Not the file's
        # mtime: git neither records nor restores those, so a fresh clone would
        # date the census to the day somebody cloned it.
        "<!--FLEET_CENSUS_DATE-->": datetime.date.fromisoformat(as_of).strftime("%-d %B %Y"),
        "<!--FLEET_PRS_TOTAL-->": f"{prs_total:,}",
        "<!--FLEET_PR_REPO_COUNT-->": str(pr_repo_count),
        "<!--FLEET_ARTIFACT_COUNT-->": str(snapshot["artifact_count"]),
        "<!--FLEET_MANIFEST_COUNT_WORD-->": number_word(len(members)),
        "<!--FLEET_MANIFEST_SOURCE-->": f'<a href="{escape(source["url"], quote=True)}">CLAW fleet manifest at {escape(source["revision"][:7])}</a>',
        "<!--FLEET_CAPABILITIES-->": capability_rows(snapshot, cards),
        "<!--FLEET_CAPABILITY_HEAD-->": capability_head(snapshot),
    }
    tokens.update({f"<!--FLEET_BADGE:{name}-->": '<span class="badge">' +
                   ('in fleet manifest' if name in members else 'not yet in fleet manifest') + '</span>'
                   for name in names})
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
