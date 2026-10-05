"""The website feature table: one row per suite Mech, one verdict per feature."""
from copy import deepcopy
import datetime
from html import escape
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import (GROUP_START, MECH_CELL, NO_SITE, SITE_KEY, SITE_STATUSES, assemble,
                           site_feature_columns, site_feature_key, site_feature_rows,
                           site_feature_totals, validate_site_features)
from card_markup import card_names
import roots


def section(page, start, end):
    begin = page.index(start)
    return page[begin:page.index(end, begin)]


class SiteFeatureTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json")]
        self.features = json.loads((ROOT / "_fleet/data/site_features.json").read_text())
        self.order = card_names(self.template)
        self.names = set(roots.ORDER)

    def render(self, features=None):
        return assemble(self.template, self.fragment, *self.inputs, features or self.features)

    def table(self, features=None):
        return section(self.render(features), '<table class="fleet-site">', "</table>")

    def body_rows(self, table):
        body = table.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        return re.findall(r"<tr>(.*?)</tr>", body, re.S)

    def published(self, features=None):
        return [m for m in (features or self.features)["mechs"].values() if m.get("site") is not None]

    def without_site(self, name="DUFMech"):
        changed = deepcopy(self.features)
        changed["mechs"][name] = {"site": None, "note": "No published website yet."}
        return changed

    def test_every_suite_mech_has_a_row_in_card_order(self):
        names = [re.sub(r"<[^>]+>", "", re.search(r'<th scope="row" class="mech">(.*?)</th>', row).group(1))
                 for row in self.body_rows(self.table())]
        self.assertEqual(names, self.order)
        self.assertEqual(set(names), self.names)

    def test_each_marker_sits_under_its_own_heading_and_group(self):
        # #385: count checks alone let a misaligned table through.
        table = self.table()
        columns = site_feature_columns(self.features)
        head = table.split("<thead>", 1)[1].split("</thead>", 1)[0]
        top, labels = re.findall(r"<tr>(.*?)</tr>", head, re.S)
        self.assertEqual([int(n) for n in re.findall(r'scope="colgroup" colspan="(\d+)"', top)],
                         [len(group["features"]) for group in self.features["groups"]])
        self.assertEqual(re.findall(r"<span>(.*?)</span>", labels),
                         [escape(self.features["catalogue"][key]["label"]) for _, key in columns])
        starts = [i for i, (title, _) in enumerate(columns) if i == 0 or columns[i - 1][0] != title]
        heads = re.findall(r"<th ([^>]*)>", labels)
        self.assertEqual([i for i, attrs in enumerate(heads) if f'class="{GROUP_START}"' in attrs], starts)
        for row in self.body_rows(table) + re.findall(r"<tr>(.*?)</tr>", table.split("<tfoot>")[1], re.S):
            cells = re.findall(r"<td([^>]*)>(.*?)</td>", row, re.S)
            self.assertEqual(len(cells), len(columns))
            self.assertEqual([i for i, (attrs, _) in enumerate(cells) if f'class="{GROUP_START}"' in attrs], starts)
            for (attrs, inner), (_, key) in zip(cells, columns):
                label = escape(self.features["catalogue"][key]["label"], quote=True)
                self.assertRegex(attrs + inner, rf'aria-label="{re.escape(label)}: ')

    def test_column_groups_anchor_the_group_headings(self):
        # #382: scope="colgroup" needs a column group to be anchored in.
        table = self.table()
        spans = re.findall(r'<colgroup(?: span="(\d+)")?></colgroup>', table.split("<thead>")[0])
        self.assertEqual(spans, [""] + [str(len(group["features"])) for group in self.features["groups"]])

    def test_verdict_order_in_the_data_does_not_move_markers(self):
        shuffled = deepcopy(self.features)
        for mech in self.published(shuffled):
            mech["features"] = dict(reversed(list(mech["features"].items())))
        self.assertEqual(self.table(shuffled), self.table())

    def test_marker_classes_never_reuse_structural_classes(self):
        # #365: the missing marker shared the Mech column's sticky class.
        markers = {css for css, _ in SITE_STATUSES.values()}
        self.assertEqual(len(markers), len(SITE_STATUSES))
        self.assertFalse(markers & {MECH_CELL, GROUP_START, NO_SITE})
        css = self.fragment[self.fragment.index("---- Website features"):self.fragment.index(".fleet-site-notes {")]
        sticky = re.findall(r"([^{}\n]+)\{[^}]*position: sticky", css)
        self.assertEqual([s.strip() for s in sticky], [f"table.fleet-site .{MECH_CELL}"])

    def test_a_mech_without_a_site_renders_end_to_end(self):
        # #383: DUFMech had no website until October 5, 2026.
        changed = self.without_site()
        validate_site_features(changed, self.names)
        page = self.render(changed)
        table = section(page, '<table class="fleet-site">', "</table>")
        columns = site_feature_columns(changed)
        row = next(r for r in self.body_rows(table) if ">DUFMech</th>" in r)
        self.assertEqual(row.count("<td"), 1)
        self.assertIn(f'colspan="{len(columns)}" class="{NO_SITE} {GROUP_START}"', row)
        self.assertNotIn('role="img"', row)
        self.assertIn("across the eleven published sites", page)
        self.assertIn("of 11 sites", table.split("<tfoot>")[1])
        notes = section(page, '<details class="fleet-site-notes">', "</details>")
        self.assertIn("<h4>DUFMech</h4><p>No published website yet.</p>", notes)

    def test_missing_or_invented_entries_fail_closed(self):
        name = next(n for n, m in self.features["mechs"].items() if m.get("site"))
        other = next(n for n, m in self.features["mechs"].items() if m.get("site") and n != name)
        key = next(iter(self.features["catalogue"]))
        extra_mech = lambda f: f["mechs"].__setitem__("PhantomMech", deepcopy(f["mechs"][name]))
        for change, message in [
            (lambda f: f["mechs"][name]["features"].pop(key), "every site feature"),
            (lambda f: f["mechs"][name]["features"].__setitem__("invented", {"status": "present", "note": "x", "url": "https://x"}), "every site feature"),
            (lambda f: f["mechs"][name]["features"][key].update(status="maybe"), "unknown status"),
            (lambda f: f["mechs"][name]["features"][key].update(note=" "), "needs a note"),
            (lambda f: f["mechs"][name]["features"][key].update(note=None), "needs a note"),
            (lambda f: f["mechs"][name]["features"][key].update(note=0), "needs a note"),
            (lambda f: f["mechs"][name]["features"][key].update(url="http://example.org"), "https evidence"),
            (lambda f: f["mechs"][name].update(site="http://example.org/"), "https URL"),
            (lambda f: f["mechs"][name].update(site=["https://example.org/"]), "https URL"),
            (lambda f: f["mechs"][name].pop("repository"), "repository"),
            (lambda f: f["mechs"][name].update(repository=None), "repository"),
            (lambda f: f["mechs"][name].update(repository=["https://github.com/CultureBotAI/AMech"]), "repository"),
            (lambda f: f["mechs"][name].update(repository="https://github.com/CultureBotAI"), "repository"),
            (lambda f: f["mechs"][name].update(repository="https://example.org/CultureBotAI/AMech"), "repository"),
            (lambda f: f["mechs"][name].update(deployed_revision="f23f307"), "deployed_revision"),
            (lambda f: f["mechs"][name].pop("deployed_revision"), "deployed_revision"),
            (lambda f: f["mechs"][name].update(features=None), "every site feature"),
            (lambda f: f["mechs"].pop(name), "every suite Mech"),
            (extra_mech, "every suite Mech"),
            (lambda f: f["groups"][0]["features"].pop(), "exactly once"),
            (lambda f: f["groups"][1]["features"].append(f["groups"][0]["features"][0]), "exactly once"),
            (lambda f: f["catalogue"][key].update(definition=""), "label and a definition"),
            (lambda f: f["catalogue"][key].update(criteria=" "), "empty criteria"),
            (lambda f: f.update(scope=""), "scope"),
            (lambda f: f["mechs"].__setitem__(other, {"site": None, "note": "x", "features": deepcopy(f["mechs"][name]["features"])}), "no feature verdicts"),
            (lambda f: f["mechs"].__setitem__(other, {"site": None, "note": None}), "needs a note"),
        ]:
            changed = deepcopy(self.features)
            change(changed)
            with self.assertRaisesRegex(ValueError, message):
                validate_site_features(changed, self.names)

    def test_notes_are_escaped_into_the_tooltip_and_the_list(self):
        changed = deepcopy(self.features)
        name = next(n for n, m in changed["mechs"].items() if m.get("site"))
        key = next(iter(changed["catalogue"]))
        changed["mechs"][name]["features"][key]["note"] = 'A "quoted" <b>note</b>'
        row = site_feature_rows(changed, [name])
        self.assertIn("&quot;quoted&quot; &lt;b&gt;note&lt;/b&gt;", row)
        notes = section(self.render(changed), '<details class="fleet-site-notes">', "</details>")
        self.assertIn("&quot;quoted&quot; &lt;b&gt;note&lt;/b&gt;", notes)
        self.assertNotIn("<b>note</b>", row + notes)

    def test_totals_show_present_counts_and_account_for_every_site(self):
        # #387, #374: the visible number, and a tooltip naming every status.
        foot = self.table().split("<tfoot>", 1)[1]
        cells = re.findall(r'<td[^>]* title="([^"]*)" aria-label="[^"]*">(\d+)</td>', foot)
        sites = self.published()
        columns = site_feature_columns(self.features)
        self.assertEqual(len(cells), len(columns))
        for (title, shown), (_, key) in zip(cells, columns):
            count = {s: sum(m["features"][key]["status"] == s for m in sites) for s in SITE_STATUSES}
            self.assertEqual(int(shown), count["present"])
            expected = f'{self.features["catalogue"][key]["label"]}: present on {count["present"]} of {len(sites)} sites'
            expected += "".join(f", {SITE_STATUSES[s][1]} on {count[s]}"
                                for s in ("partial", "missing", "not_applicable", "unknown") if count[s])
            self.assertEqual(title, escape(expected, quote=True))
            self.assertEqual(sum(count.values()), len(sites))

    def test_the_key_lists_exactly_the_statuses_in_use(self):
        # #388: which statuses, in order, each with its own marker.
        def expected(features):
            used = {v["status"] for m in self.published(features) for v in m["features"].values()}
            return "".join(f'<span><i class="{SITE_STATUSES[s][0]}"></i>{escape(SITE_KEY[s])}</span>'
                           for s in SITE_STATUSES if s in used)
        self.assertEqual(site_feature_key(self.features), expected(self.features))
        changed = deepcopy(self.features)
        for mech in self.published(changed):
            for verdict in mech["features"].values():
                if verdict["status"] == "not_applicable":
                    verdict["status"] = "missing"
        first = self.published(changed)[0]
        next(iter(first["features"].values()))["status"] = "unknown"
        key = site_feature_key(changed)
        self.assertEqual(key, expected(changed))
        self.assertIn('<i class="u"></i>not verified', key)
        self.assertNotIn('class="na"', key)

    def test_every_verdict_is_readable_without_hovering(self):
        # #384: each list item is that verdict's own label, status, note and link.
        page = self.render()
        notes = section(page, '<details class="fleet-site-notes">', "</details>")
        columns = site_feature_columns(self.features)
        blocks = re.findall(r'<h4><a href="([^"]*)">([^<]*)</a></h4><ul>(.*?)</ul>', notes, re.S)
        self.assertEqual([name for _, name, _ in blocks], self.order)
        for site, name, items in blocks:
            mech = self.features["mechs"][name]
            self.assertEqual(site, escape(mech["site"], quote=True))
            expected = [f'<b>{escape(self.features["catalogue"][key]["label"])}</b> '
                        f'<span>{escape(SITE_STATUSES[mech["features"][key]["status"]][1])}</span>: '
                        f'{escape(mech["features"][key]["note"].strip())} '
                        f'<a href="{escape(mech["features"][key]["url"], quote=True)}">Evidence</a>'
                        for _, key in columns]
            self.assertEqual(re.findall(r"<li>(.*?)</li>", items, re.S), expected)

    def test_feature_definitions_and_criteria_are_visible(self):
        # #376, #368: definitions and criteria are text, not only tooltips.
        notes = section(self.render(), '<details class="fleet-site-notes">', "</details>")
        for _, key in site_feature_columns(self.features):
            entry = self.features["catalogue"][key]
            dd = escape(entry["definition"]) + (f' {escape(entry["criteria"])}' if entry.get("criteria") else "")
            self.assertIn(f'<dt>{escape(entry["label"])}</dt><dd>{dd}</dd>', notes)

    def test_the_table_states_its_own_check_date(self):
        # #366: the table's sentence, not the card paragraph's "checked on".
        def sentence(day):
            return f"tested on the live sites on {day:%B} {day.day}, {day.year} in a headless browser"
        day = datetime.date.fromisoformat(self.features["checked_on"])
        self.assertIn(sentence(day), self.render())
        moved = deepcopy(self.features)
        moved["checked_on"] = "2026-11-02"
        page = self.render(moved)
        self.assertIn(sentence(datetime.date(2026, 11, 2)), page)
        self.assertNotIn(sentence(day), page)


if __name__ == "__main__":
    unittest.main()
