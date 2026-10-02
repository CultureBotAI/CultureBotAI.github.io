"""All suite projects are measured without inventing governance declarations."""
import datetime
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import assemble, capability_rows
from card_markup import card_figures
import check_cards
import roots


class SuiteIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json")]

    def render(self):
        return assemble(self.template, self.fragment, *self.inputs)

    def test_seed_families_are_measured_without_inventing_claw_admission(self):
        page = self.render()
        figures = card_figures(self.template)
        self.assertEqual(set(figures), set(roots.ORDER))
        self.assertGreater(figures["DUFMech"], 0)
        self.assertIn(f"<b>{sum(figures.values()):,}</b>", page)
        self.assertIn("records and seed families", page)
        self.assertIn("all twelve Mechs", page)
        self.assertIn('<span class="badge">not yet in fleet manifest</span>', page)
        self.assertNotIn("DUFMech", self.inputs[1]["mechs"])
        rows = capability_rows(self.inputs[1], ["DUFMech"])
        self.assertEqual(rows.count('class="u"'), len(self.inputs[1]["capability_catalogue"]))
        self.assertIn("not declared in CLAW manifest", rows)
        self.assertNotIn('class="d"', rows)
        self.assertNotIn('class="n"', rows)

    def test_a_missing_new_mech_stat_cannot_be_silently_omitted(self):
        for name in ("PathwayMech", "DUFMech"):
            original = self.inputs[2]["mechs"]
            self.inputs[2]["mechs"] = [row for row in original if row["mech"] != name]
            with self.assertRaisesRegex(ValueError, "Mech stats"):
                self.render()
            self.inputs[2]["mechs"] = original

    def test_the_census_and_heatmap_must_cover_the_same_members(self):
        self.inputs[3].pop("DUFMech")
        with self.assertRaisesRegex(ValueError, "Census members"):
            self.render()

    def test_record_list_counts_only_unique_complete_record_links(self):
        item = '<li><a href="records/a.html">A</a></li>'
        outside = '<li><a href="records/outside.html">Outside</a></li>'
        self.assertEqual(check_cards.published("record-list", outside + '<ul class="record-list">' + item + '</ul>', "record-list"), 1)
        for body in (item + item, '<li>No link</li>', '<li><a href="other.html">Other</a></li>'):
            self.assertIsNone(check_cards.published("record-list", '<ul class="record-list">' + body + '</ul>', "record-list"))
        self.assertIsNone(check_cards.published("record-list", '<ul class="changed"></ul>', "record-list"))

    def test_duf_worklist_card_uses_the_same_pin_validation_as_other_cards(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        audit = {"pinned_at_utc": (now - datetime.timedelta(days=2)).isoformat(),
                 "repositories": [{"repo": "DUFMech", "figure_at_pin": 3}]}
        template = '<article data-mech="DUFMech"><div class="num"><b>3</b></div></article>'
        source = check_cards.SOURCES["DUFMech"]
        def fetch(url):
            if url == check_cards.DUF_WORKLISTS:
                return json.dumps([{"name": "interpro-pfam-duf-2026-10-01" + suffix, "type": "file"}
                                   for suffix in (".json", ".manifest.json")])
            return '[{}, {}, {}]'
        with mock.patch.dict(check_cards.SOURCES, {"DUFMech": source}, clear=True):
            rows = check_cards.check(template, fetch, audit, now)
            self.assertEqual([(status, name) for status, name, _ in rows], [("ok", "DUFMech")])
            audit["repositories"][0]["figure_at_pin"] = 2
            rows = check_cards.check(template, fetch, audit, now)
            self.assertEqual([(status, name) for status, name, _ in rows], [("WRONG", "DUFMech")])

    def test_duf_nightly_counts_the_newest_dated_worklist_instead_of_its_pin(self):
        source = check_cards.SOURCES["DUFMech"]
        audit = {"pinned_at_utc": "2026-10-01T22:44:02Z",
                 "repositories": [{"repo": "DUFMech", "figure_at_pin": 2}]}
        now = datetime.datetime(2026, 11, 1, tzinfo=datetime.timezone.utc)
        template = '<article data-mech="DUFMech"><div class="num"><b>2</b></div></article>'
        latest = check_cards.DUF_RAW + "interpro-pfam-duf-2026-10-02.json"
        payloads = {source[1]: '[{}, {}]', latest: '[{}, {}, {}]'}
        listing = [{"name": f"interpro-pfam-duf-{date}{suffix}", "type": "file"}
                   for date in ("2026-10-02", "2026-10-01") for suffix in (".manifest.json", ".json")]
        fetched = []
        def fetch(url):
            fetched.append(url)
            return json.dumps(listing) if url == check_cards.DUF_WORKLISTS else payloads[url]
        with mock.patch.dict(check_cards.SOURCES, {"DUFMech": source}, clear=True):
            rows = check_cards.check(template, fetch, audit, now)
        self.assertEqual([(status, name) for status, name, _ in rows], [("STALE", "DUFMech")])
        self.assertEqual(fetched, [check_cards.DUF_WORKLISTS, latest])
        self.assertEqual(check_cards.SOURCES["DUFMech"], source)

    def test_duf_nightly_does_not_fall_back_from_an_incomplete_newest_snapshot(self):
        source = check_cards.SOURCES["DUFMech"]
        listing = [{"name": "interpro-pfam-duf-2026-10-01" + suffix, "type": "file"}
                   for suffix in (".manifest.json", ".json")]
        listing.append({"name": "interpro-pfam-duf-2026-10-02.manifest.json", "type": "file"})
        status, reason = check_cards.read_source("DUFMech", *source, fetcher=lambda _: json.dumps(listing))
        self.assertEqual(status, "CHANGED")
        self.assertIn("newest DUF manifest has no matching payload", reason)

    def test_stats_count_logical_families_not_worklist_files(self):
        import mech_stats
        self.assertEqual(set(mech_stats.MEMBERS), set(roots.ORDER))
        docs = [("worklist.json", "id: Pfam:PF00001"), ("worklist.json", "id: Pfam:PF00002"),
                ("worklist.json", "id: Pfam:PF00003")]
        with (mock.patch.object(mech_stats, "record_paths", return_value=["manifest.json", "worklist.json"]),
              mock.patch.object(mech_stats, "record_documents", return_value=iter(docs)),
              mock.patch.object(mech_stats, "revision", return_value="a" * 40),
              mock.patch.object(mech_stats, "unchanged"),
              mock.patch.object(mech_stats, "review_slot", return_value=None)):
            self.assertEqual(mech_stats.review_census("DUFMech"), (3, None, None, "a" * 40))


if __name__ == "__main__":
    unittest.main()
