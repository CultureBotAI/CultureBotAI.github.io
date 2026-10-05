"""The website feature table: one row per suite Mech, one verdict per feature."""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import (assemble, site_feature_columns, site_feature_key, site_feature_rows,
                           site_feature_totals, validate_site_features)
from card_markup import card_names
import roots


class SiteFeatureTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json")]
        self.features = json.loads((ROOT / "_fleet/data/site_features.json").read_text())
        self.order = card_names(self.template)

    def render(self):
        return assemble(self.template, self.fragment, *self.inputs, self.features)

    def table(self):
        page = self.render()
        start = page.index('<table class="fleet-site">')
        return page[start:page.index("</table>", start)]

    def test_every_suite_mech_has_a_row_in_card_order(self):
        body = self.table().split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        rows = re.findall(r"<tr>(.*?)</tr>", body, re.S)
        names = [re.sub(r"<[^>]+>", "", re.search(r'<th scope="row" class="m">(.*?)</th>', row).group(1))
                 for row in rows]
        self.assertEqual(names, self.order)
        self.assertEqual(set(names), set(roots.ORDER))

    def test_every_row_judges_every_feature_or_explains_why_not(self):
        columns = site_feature_columns(self.features)
        body = self.table().split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        for row in re.findall(r"<tr>(.*?)</tr>", body, re.S):
            if 'class="none g"' in row:
                self.assertIn(f'colspan="{len(columns)}"', row)
            else:
                self.assertEqual(len(re.findall(r"<td[ >]", row)), len(columns))
                self.assertEqual(len(re.findall(r'role="img"', row)), len(columns))

    def test_headers_cover_every_feature_once_under_its_group(self):
        head = self.table().split("<thead>", 1)[1].split("</thead>", 1)[0]
        groups = re.findall(r'<th scope="colgroup" colspan="(\d+)"', head)
        self.assertEqual(sum(map(int, groups)), len(self.features["catalogue"]))
        self.assertEqual(len(groups), len(self.features["groups"]))
        self.assertEqual(len(re.findall(r'<th scope="col"[ >]', head)), len(self.features["catalogue"]) + 1)

    def test_a_mech_without_a_site_gets_one_explanatory_cell(self):
        # Every Mech has a site today; DUFMech had none until October 5, 2026.
        changed = deepcopy(self.features)
        changed["mechs"]["DUFMech"] = {"site": None, "note": "No published website."}
        validate_site_features(changed, set(roots.ORDER))
        row = site_feature_rows(changed, ["DUFMech"])
        self.assertEqual(row.count("<td"), 1)
        self.assertIn(f'colspan="{len(site_feature_columns(changed))}"', row)
        self.assertNotIn('role="img"', row)
        changed["mechs"]["DUFMech"]["features"] = {}
        changed["mechs"]["DUFMech"]["note"] = ""
        with self.assertRaisesRegex(ValueError, "without a site needs a note"):
            validate_site_features(changed, set(roots.ORDER))

    def test_missing_or_invented_verdicts_fail_closed(self):
        names = set(roots.ORDER)
        name = next(n for n, m in self.features["mechs"].items() if m.get("site"))
        key = next(iter(self.features["catalogue"]))
        for change, message in [
            (lambda f: f["mechs"][name]["features"].pop(key), "every site feature"),
            (lambda f: f["mechs"][name]["features"][key].update(status="maybe"), "unknown status"),
            (lambda f: f["mechs"][name]["features"][key].update(note=" "), "needs a note"),
            (lambda f: f["mechs"][name]["features"][key].update(url="http://example.org"), "https evidence"),
            (lambda f: f["mechs"].pop(name), "every suite Mech"),
            (lambda f: f["groups"][0]["features"].pop(), "exactly once"),
        ]:
            changed = deepcopy(self.features)
            change(changed)
            with self.assertRaisesRegex(ValueError, message):
                validate_site_features(changed, names)

    def test_notes_are_escaped_into_the_tooltip(self):
        changed = deepcopy(self.features)
        name = next(n for n, m in changed["mechs"].items() if m.get("site"))
        key = next(iter(changed["catalogue"]))
        changed["mechs"][name]["features"][key]["note"] = 'A "quoted" <b>note</b>'
        row = site_feature_rows(changed, [name])
        self.assertIn("&quot;quoted&quot; &lt;b&gt;note&lt;/b&gt;", row)
        self.assertNotIn("<b>note</b>", row)

    def test_totals_count_present_verdicts_on_published_sites(self):
        totals = site_feature_totals(self.features)
        sites = [m for m in self.features["mechs"].values() if m.get("site")]
        for _, key in site_feature_columns(self.features):
            present = sum(m["features"][key]["status"] == "present" for m in sites)
            label = self.features["catalogue"][key]["label"]
            self.assertIn(f"{label}: present on {present} of {len(sites)} sites", totals)

    def test_the_key_lists_only_statuses_the_table_uses(self):
        used = {v["status"] for m in self.features["mechs"].values() for v in m.get("features", {}).values()}
        key = site_feature_key(self.features)
        self.assertEqual(key.count("<span>"), len(used))
        self.assertIn("present", key)

    def test_every_verdict_is_readable_without_hovering(self):
        # Tooltips never show on touch screens, so the notes are also listed.
        page = self.render()
        notes = page[page.index('<details class="fleet-site-notes">'):]
        notes = notes[:notes.index("</details>")]
        columns = site_feature_columns(self.features)
        sites = [m for m in self.features["mechs"].values() if m.get("site")]
        self.assertEqual(notes.count("<li>"), len(columns) * len(sites))
        for mech in sites:
            for _, key in columns:
                self.assertIn(f'<a href="{escape(mech["features"][key]["url"], quote=True)}">Evidence</a>', notes)

    def test_the_check_date_is_shown(self):
        page = self.render()
        self.assertIn("checked on October 5, 2026", page)


if __name__ == "__main__":
    unittest.main()
