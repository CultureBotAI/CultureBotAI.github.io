"""Introductions must not pretend to be measured corpora or CLAW admissions."""
from copy import deepcopy
import datetime
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import additions
from assemble_page import assemble
from card_markup import card_figures
import check_cards


class IntroductionTests(unittest.TestCase):
    def setUp(self):
        self.entries = additions.load()
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json")]

    def render(self):
        return assemble(self.template, self.fragment, *self.inputs, self.entries)

    def test_seed_worklist_is_present_but_neither_counted_nor_admitted(self):
        page = self.render()
        figures = card_figures(self.template)
        self.assertNotIn("DUFMech", figures)
        self.assertEqual(figures["PathwayMech"], 152)
        self.assertIn(f"<b>{sum(figures.values()):,}</b>", page)
        self.assertIn("ten of the twelve Mechs", page)
        self.assertIn("<b>Seed worklist</b>", page)
        self.assertIn('<span class="badge">not yet in fleet manifest</span>', page)
        self.assertNotIn('<tr><th scope="row">DUFMech</th>', page)

    def test_a_worklist_cannot_be_silently_added_to_curated_entry_totals(self):
        self.template = self.template.replace('<div class="status"><b>Seed worklist</b>',
                                               '<div class="num"><b>6,532</b>')
        with self.assertRaisesRegex(ValueError, "uncounted card"):
            self.render()

    def test_numeric_addition_must_match_its_independent_pin(self):
        self.entries["PathwayMech"]["figure_at_pin"] = 153
        with self.assertRaisesRegex(ValueError, "separately pinned source"):
            self.render()

    def test_a_missing_introduction_cannot_bypass_membership_validation(self):
        del self.entries["DUFMech"]
        with self.assertRaisesRegex(ValueError, "membership"):
            self.render()

    def test_record_list_counts_only_unique_complete_record_links(self):
        item = '<li><a href="records/a.html">A</a></li>'
        outside = '<li><a href="records/outside.html">Outside</a></li>'
        self.assertEqual(check_cards.published("record-list", outside + '<ul class="record-list">' + item + '</ul>', "record-list"), 1)
        for body in (item + item, '<li>No link</li>', '<li><a href="other.html">Other</a></li>'):
            self.assertIsNone(check_cards.published("record-list", '<ul class="record-list">' + body + '</ul>', "record-list"))
        self.assertIsNone(check_cards.published("record-list", '<ul class="changed"></ul>', "record-list"))

    def test_growth_uses_the_introductions_pin_not_the_older_census_date(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = deepcopy(self.entries["PathwayMech"])
        entry.update(repo="NewMech", figure_at_pin=100,
                     commit_date=(now - datetime.timedelta(days=3)).isoformat(),
                     pinned_at_utc=(now - datetime.timedelta(days=2)).isoformat(),
                     source=["json", "NewMech/data.json", "total"])
        audit = {"pinned_at_utc": (now - datetime.timedelta(days=19)).isoformat(), "repositories": []}
        template = '<article data-mech="NewMech"><div class="num"><b>100</b></div></article>'
        with mock.patch.dict(check_cards.SOURCES, {}, clear=True):
            rows = check_cards.check(template, lambda url: '{"total":125}', audit, now,
                                     additions={"NewMech": entry})
        self.assertEqual([(status, mech) for status, mech, _ in rows], [("grew", "NewMech")])

    def test_stats_do_not_partially_recount_unmeasured_introductions(self):
        import mech_stats
        self.assertEqual(set(mech_stats.MEMBERS), {entry['mech'] for entry in self.inputs[2]['mechs']})
        self.assertFalse(set(mech_stats.MEMBERS) & set(self.entries))


if __name__ == "__main__":
    unittest.main()
