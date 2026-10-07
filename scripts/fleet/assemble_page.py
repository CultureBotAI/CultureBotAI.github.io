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


# Website features are judged on each Mech's live site, unlike the capabilities
# above, which CLAW declares. Each status has a marker class; the half marker
# shows partial support and the dash a feature that does not apply.
SITE_STATUSES = {"present": ("e", "present"), "partial": ("p", "partial"),
                 "missing": ("m", "missing"), "not_applicable": ("na", "not applicable"),
                 "unknown": ("u", "not verified")}
SITE_KEY = {"present": "present", "partial": "partial, as its note explains",
            "missing": "missing", "not_applicable": "does not apply to this site",
            "unknown": "not verified"}
# Classes for the table's structure. They must never equal a marker class: the
# missing marker once shared the Mech column's class and turned sticky (#365).
MECH_CELL = "mech"
GROUP_START = "grp"
NO_SITE = "none"
SHA = re.compile(r"[0-9a-f]{40}")


def _text(value):
    """A non-empty string, or None: str() would pass null as "None" (#377)."""
    return value.strip() if isinstance(value, str) and value.strip() else None


def _audit_date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label}: checked_on must be an ISO date")
    try:
        day = datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label}: checked_on must be an ISO date") from None
    if day.isoformat() != value:
        raise ValueError(f"{label}: checked_on must be YYYY-MM-DD")
    return day


def site_feature_columns(features):
    """(group title, feature key) pairs in display order. Every catalogue
    feature sits in exactly one group, so no column can go unshown."""
    columns = [(group["title"], key) for group in features["groups"] for key in group["features"]]
    keys = [key for _, key in columns]
    if len(keys) != len(set(keys)) or set(keys) != set(features["catalogue"]):
        raise ValueError("Site feature groups must list every catalogue feature exactly once")
    return columns


def validate_site_features(features, names):
    """Fail closed: every suite Mech has a row, every row judges every feature."""
    baseline = _audit_date(features.get("checked_on"), "Site features")
    if not _text(features.get("scope")):
        raise ValueError("Site features need a scope saying what was checked and how")
    columns = site_feature_columns(features)
    for key, entry in features["catalogue"].items():
        if not (_text(entry.get("label")) and _text(entry.get("definition"))):
            raise ValueError(f"Catalogue feature {key} needs a label and a definition")
        if "criteria" in entry and not _text(entry["criteria"]):
            raise ValueError(f"Catalogue feature {key} has empty criteria")
    if set(features["mechs"]) != set(names):
        raise ValueError("Site features must cover every suite Mech exactly once")
    for name, mech in features["mechs"].items():
        if "checked_on" in mech or "scope" in mech:
            checked = _audit_date(mech.get("checked_on"), name)
            if checked < baseline:
                raise ValueError(f"{name}: site-specific check cannot predate the baseline audit")
            if not _text(mech.get("scope")):
                raise ValueError(f"{name}: site-specific check needs its own scope")
            if mech.get("site") is None:
                raise ValueError(f"{name}: site-specific check needs a published site")
        if mech.get("site") is None:
            # A Mech without a website gets one explanatory cell, not a row of
            # markers that would read as twenty-four separate judgements.
            if "features" in mech or not _text(mech.get("note")):
                raise ValueError(f"{name}: a Mech without a site needs a note and no feature verdicts")
            continue
        if not (isinstance(mech["site"], str) and mech["site"].startswith("https://")):
            raise ValueError(f"{name}: site must be an https URL")
        if not (isinstance(mech.get("repository"), str) and
                re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", mech["repository"])):
            raise ValueError(f"{name}: repository must be a GitHub repository URL")
        if not (isinstance(mech.get("deployed_revision"), str) and SHA.fullmatch(mech["deployed_revision"])):
            raise ValueError(f"{name}: deployed_revision must be the full SHA of the deployment checked")
        verdicts = mech.get("features")
        if not isinstance(verdicts, dict) or set(verdicts) != {key for _, key in columns}:
            raise ValueError(f"{name}: every site feature needs a verdict")
        for key, verdict in verdicts.items():
            if verdict.get("status") not in SITE_STATUSES:
                raise ValueError(f"{name}: unknown status for {key}")
            if not _text(verdict.get("note")):
                raise ValueError(f"{name}: {key} needs a note giving the evidence")
            if not (isinstance(verdict.get("url"), str) and verdict["url"].startswith("https://")):
                raise ValueError(f"{name}: {key} needs an https evidence URL")
    return columns


def _groups(columns):
    """[title, span] runs of consecutive columns."""
    groups = []
    for title, _ in columns:
        if not groups or groups[-1][0] != title:
            groups.append([title, 0])
        groups[-1][1] += 1
    return groups


def _starts_group(columns, i):
    return i == 0 or columns[i - 1][0] != columns[i][0]


def _cls(*names):
    names = [name for name in names if name]
    return f' class="{" ".join(names)}"' if names else ""


def site_feature_colgroups(features):
    """One column group per feature group, which scope="colgroup" headings need
    to be anchored in (#382); the first group holds the Mech column."""
    return "<colgroup></colgroup>" + "".join(
        f'<colgroup span="{span}"></colgroup>' for _, span in _groups(site_feature_columns(features)))


def site_feature_head(features):
    columns = site_feature_columns(features)
    top = [f'<th scope="col" rowspan="2"{_cls(MECH_CELL)}>Mech</th>'] + [
        f'<th scope="colgroup" colspan="{span}"{_cls(GROUP_START)}>{escape(title)}</th>'
        for title, span in _groups(columns)]
    labels = []
    for i, (_, key) in enumerate(columns):
        entry = features["catalogue"][key]
        labels.append(f'<th scope="col"{_cls(GROUP_START if _starts_group(columns, i) else "")} '
                      f'title="{escape(entry["definition"], quote=True)}"><span>{escape(entry["label"])}</span></th>')
    return "<tr>" + "".join(top) + "</tr>\n<tr>" + "".join(labels) + "</tr>"


def site_feature_rows(features, suite_order):
    columns = site_feature_columns(features)
    rows = []
    for name in suite_order:
        mech = features["mechs"][name]
        if mech.get("site") is None:
            rows.append(f'<tr><th scope="row"{_cls(MECH_CELL)}>{escape(name)}</th>'
                        f'<td colspan="{len(columns)}"{_cls(NO_SITE, GROUP_START)}>{escape(mech["note"])}</td></tr>')
            continue
        cells = [f'<th scope="row"{_cls(MECH_CELL)}><a href="{escape(mech["site"], quote=True)}">{escape(name)}</a></th>']
        for i, (_, key) in enumerate(columns):
            verdict = mech["features"][key]
            css, word = SITE_STATUSES[verdict["status"]]
            label = escape(f'{features["catalogue"][key]["label"]}: {word}. {verdict["note"].strip()}', quote=True)
            cells.append(f'<td{_cls(GROUP_START if _starts_group(columns, i) else "")}>'
                         f'<i class="{css}" role="img" title="{label}" aria-label="{label}"></i></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(rows)


def site_feature_totals(features):
    """How many published sites offer each feature, as the table's last row.
    The tooltip accounts for every site, so no verdict goes unmentioned (#374)."""
    columns = site_feature_columns(features)
    sites = [mech for mech in features["mechs"].values() if mech.get("site") is not None]
    cells = [f'<th scope="row"{_cls(MECH_CELL)}>Sites with it</th>']
    for i, (_, key) in enumerate(columns):
        count = {status: sum(mech["features"][key]["status"] == status for mech in sites) for status in SITE_STATUSES}
        label = f'{features["catalogue"][key]["label"]}: present on {count["present"]} of {len(sites)} sites'
        label += "".join(f", {SITE_STATUSES[status][1]} on {count[status]}"
                         for status in ("partial", "missing", "not_applicable", "unknown") if count[status])
        label = escape(label, quote=True)
        cells.append(f'<td{_cls(GROUP_START if _starts_group(columns, i) else "")} title="{label}" '
                     f'aria-label="{label}">{count["present"]}</td>')
    return "<tr>" + "".join(cells) + "</tr>"


def site_feature_evidence(features, suite_order):
    """The feature definitions and every verdict's note and evidence link, for
    readers who cannot hover: tooltips never appear on touch screens (#376)."""
    columns = site_feature_columns(features)
    terms = []
    for _, key in columns:
        entry = features["catalogue"][key]
        terms.append(f'<dt>{escape(entry["label"])}</dt><dd>{escape(entry["definition"])}'
                     + (f' {escape(entry["criteria"])}' if entry.get("criteria") else "") + "</dd>")
    parts = [f'<h4>Baseline audit</h4><p>{escape(features["scope"].strip())}</p>',
             "<h4>Features</h4><dl>" + "".join(terms) + "</dl>"]
    for name in suite_order:
        mech = features["mechs"][name]
        if mech.get("site") is None:
            parts.append(f"<h4>{escape(name)}</h4><p>{escape(mech['note'])}</p>")
            continue
        items = []
        for _, key in columns:
            verdict = mech["features"][key]
            items.append(f'<li><b>{escape(features["catalogue"][key]["label"])}</b> '
                         f'<span>{escape(SITE_STATUSES[verdict["status"]][1])}</span>: '
                         f'{escape(verdict["note"].strip())} <a href="{escape(verdict["url"], quote=True)}">Evidence</a></li>')
        recheck = ""
        if "checked_on" in mech:
            day = _audit_date(mech["checked_on"], name).strftime("%B %-d, %Y")
            revision = mech["deployed_revision"]
            source = f'{mech["repository"].rstrip("/")}/tree/{revision}'
            recheck = (f'<p>Site-specific check on {day}, '
                       f'<a href="{escape(source, quote=True)}">deployed revision {revision[:7]}</a>. '
                       f'{escape(mech["scope"].strip())}</p>')
        parts.append(f'<h4><a href="{escape(mech["site"], quote=True)}">{escape(name)}</a></h4>'
                     f'{recheck}<ul>{"".join(items)}</ul>')
    return "\n".join(parts)


def site_feature_rechecks(features, suite_order):
    checks = [f'{escape(name)} ({_audit_date(features["mechs"][name]["checked_on"], name):%B %-d, %Y})'
              for name in suite_order if "checked_on" in features["mechs"][name]]
    if not checks:
        return ""
    note = "Site-specific rechecks: " + "; ".join(checks) + ". Their methods and deployed revisions are recorded below."
    if len(checks) < sum(m.get("site") is not None for m in features["mechs"].values()):
        note += " Other sites retain the baseline audit date and method."
    return note


def site_schema_note(features, name):
    verdict = features["mechs"][name].get("features", {}).get("schema_docs")
    if verdict is None:
        return f"There is no website feature verdict for {escape(name)}'s schema documentation."
    status = SITE_STATUSES[verdict["status"]][1]
    return (f"The website audit records {escape(name)}'s schema documentation as "
            f'<a href="{escape(verdict["url"], quote=True)}">{escape(status)}</a>.')


def site_feature_key(features):
    """A legend for the statuses the table actually uses."""
    used = {verdict["status"] for mech in features["mechs"].values()
            for verdict in (mech.get("features") or {}).values()}
    return "".join(f'<span><i class="{SITE_STATUSES[status][0]}"></i>{escape(SITE_KEY[status])}</span>'
                   for status in SITE_STATUSES if status in used)


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


def assemble(template, fragment, data, snapshot, stats, census, features):
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
    validate_site_features(features, names)
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
        "<!--FLEET_UNDECLARED_NOTE-->": (
            "Separately listed projects without a declaration: "
            + ", ".join(escape(name) for name in cards if name not in members) + "."
            if names - members else "All projects shown here have a manifest declaration."),
        "<!--FLEET_MANIFEST_SOURCE-->": f'<a href="{escape(source["url"], quote=True)}">CLAW fleet manifest at {escape(source["revision"][:7])}</a>',
        "<!--FLEET_CAPABILITIES-->": capability_rows(snapshot, cards),
        "<!--FLEET_CAPABILITY_HEAD-->": capability_head(snapshot),
        "<!--FLEET_SITE_COLGROUPS-->": site_feature_colgroups(features),
        "<!--FLEET_SITE_HEAD-->": site_feature_head(features),
        "<!--FLEET_SITE_ROWS-->": site_feature_rows(features, cards),
        "<!--FLEET_SITE_TOTALS-->": site_feature_totals(features),
        "<!--FLEET_SITE_KEY-->": site_feature_key(features),
        "<!--FLEET_SITE_EVIDENCE-->": site_feature_evidence(features, cards),
        "<!--FLEET_SITE_DATE-->": datetime.date.fromisoformat(features["checked_on"]).strftime("%B %-d, %Y"),
        "<!--FLEET_SITE_RECHECKS-->": site_feature_rechecks(features, cards),
        "<!--FLEET_DUF_SCHEMA_NOTE-->": site_schema_note(features, "DUFMech"),
        "<!--FLEET_SITE_COUNT_WORD-->": number_word(sum(m.get("site") is not None for m in features["mechs"].values())),
        "<!--FLEET_SITE_FEATURE_COUNT_WORD-->": number_word(len(features["catalogue"])),
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
                    json.loads((FLEET / "data/prefix_census.json").read_text()),
                    json.loads((FLEET / "data/site_features.json").read_text()))
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
