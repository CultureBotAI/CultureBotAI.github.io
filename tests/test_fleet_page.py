"""Regression coverage for fleet admission, capability drift and generated output."""
from copy import deepcopy
import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import assemble, capability_rows, number_word, script_json
from card_markup import card_figures, card_names
from refresh_manifest import ARTIFACT_PATH, MANIFEST_PATH, read_canonical, semantic, validate
import roots


class FleetPageTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.data = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())
        self.stats = json.loads((ROOT / "_fleet/data/mech_stats.json").read_text())
        self.census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())

    def render(self):
        return assemble(self.template, self.fragment, self.data, self.snapshot, self.stats, self.census)

    def test_rendering_twice_does_not_consume_the_census(self):
        self.assertEqual(self.render(), self.render())

    def test_records_tile_equals_the_sum_of_the_cards(self):
        page = self.render()
        total = sum(card_figures(self.template).values())
        self.assertIn(f"<div><b>{total:,}</b><span>curated entries across the fleet</span></div>", page)

    def test_a_card_without_a_record_count_cannot_be_left_out_of_the_total(self):
        self.template = self.template.replace('<div class="num"><b>625,960</b>', '<div class="num"><b>', 1)
        with self.assertRaisesRegex(ValueError, "record count"):
            self.render()

    def test_a_figure_outside_every_card_cannot_join_the_total(self):
        # #218, #234: a stray figure used to be ignored, and a second one in a
        # card used to replace its headline in the total.
        stray = self.template.replace("<!--FLEET_FRAGMENT-->", '<div class="num"><b>7</b></div><!--FLEET_FRAGMENT-->', 1)
        self.template = stray
        with self.assertRaisesRegex(ValueError, "outside any card"):
            self.render()

    def test_card_stats_must_cover_every_fleet_member(self):
        self.stats["mechs"] = [m for m in self.stats["mechs"] if m["mech"] != "TaxonMech"]
        with self.assertRaisesRegex(ValueError, "Mech stats"):
            self.render()

    def test_a_mech_that_cannot_record_review_shows_only_its_pull_requests(self):
        page = self.render()
        by_name = {m["mech"]: m for m in self.stats["mechs"]}
        untracked = next(m for m in by_name.values() if m["reviewed"] is None)
        tracked = next(m for m in by_name.values() if m["reviewed"] is not None)
        self.assertIn(f'<p class="prov">{untracked["merged_prs"]:,} merged PRs</p>', page)
        self.assertIn(f'{tracked["reviewed"]:,} reviewed \u00b7 {tracked["merged_prs"]:,} merged PRs', page)
        self.assertNotIn("0 reviewed \u00b7 " + f'{untracked["merged_prs"]:,}', page)

    def test_published_page_contains_both_new_members_with_distinct_capabilities(self):
        page = self.render()
        self.assertEqual(page, (ROOT / "mechs.md").read_text())
        self.assertEqual(page.count('<span class="badge">in fleet manifest</span>'), 10)
        self.assertIn('Relationship graph of the ten autonomous knowledge factories', page)
        self.assertNotIn('not yet in fleet manifest', page)
        self.assertNotIn('one revision behind', page)
        caps = self.snapshot['mechs']
        self.assertEqual(caps['NaturalProductMech']['capabilities']['source_queue']['status'], 'enabled')
        self.assertEqual(caps['NaturalProductMech']['capabilities']['curation_history']['status'], 'disabled')
        self.assertEqual(caps['TaxonMech']['capabilities']['source_queue']['status'], 'disabled')
        self.assertEqual(caps['TaxonMech']['capabilities']['curation_history']['status'], 'enabled')
        self.assertIn('<tr><td>NaturalProductMech</td>', capability_rows(self.snapshot))
        self.assertIn('<tr><td>TaxonMech</td>', capability_rows(self.snapshot))

    def test_fleet_size_reads_as_prose_but_the_tile_stays_a_numeral(self):
        # The heading, intro and SVG title are sentences, and the rest of the
        # site writes "ten" in prose; only the stat tile wants a figure (#93).
        page = self.render()
        self.assertIn('# X-Mech Suite: ten autonomous knowledge factories', page)
        self.assertIn('## The ten Mechs', page)
        self.assertIn('census covers all ten Mechs', page)
        self.assertIn('<b>10</b><span>autonomous knowledge factories</span>', page)
        self.assertNotIn('The 10 Mechs', page)

    def test_the_meta_description_opens_like_a_sentence(self):
        # It is the snippet search engines show, and every other page's
        # description starts with a capital. Substituting a spelled-out count
        # at the front of it would open the snippet in lower case (#93).
        page = self.render()
        description = re.search(r'^description: "(.)', page, re.M)
        self.assertIsNotNone(description, "front matter carries no description")
        self.assertTrue(description.group(1).isupper(),
                        f"description opens with {description.group(1)!r}, not a capital")

    def test_census_coverage_reads_as_a_fraction_while_a_member_is_unmeasured(self):
        # The page said "nine of the ten Mechs" until TaxonMech was measured (#87);
        # the same wording has to come back if a member ever drops out (#171).
        self.census.pop("TaxonMech")
        self.data["order"].remove("TaxonMech")
        self.data["heat"].pop("TaxonMech")
        self.data["vocab_edges"] = [e for e in self.data["vocab_edges"] if "TaxonMech" not in (e["a"], e["b"])]
        self.data["cells"] = {k: v for k, v in self.data["cells"].items() if not k.startswith("TaxonMech--")}
        page = self.render()
        self.assertIn("census covers nine of the ten Mechs", page)
        self.assertNotIn("all ten Mechs", page)

    def test_number_word_falls_back_to_a_numeral_past_the_short_words(self):
        self.assertEqual(number_word(9), 'nine')
        self.assertEqual(number_word(10), 'ten')
        self.assertEqual(number_word(12), 'twelve')
        # A fleet that outgrows the table should read as digits, not break.
        self.assertEqual(number_word(13), '13')
        self.assertEqual(number_word(1000), '1,000')

    def test_new_admission_cannot_silently_omit_card_or_graph_node(self):
        self.snapshot['mechs']['NewMech'] = deepcopy(self.snapshot['mechs']['TaxonMech'])
        self.snapshot['mechs']['NewMech'].update(key='newmech', github='CultureBotAI/NewMech')
        with self.assertRaisesRegex(ValueError, 'cards'):
            self.render()
        self.template += '\n<!--FLEET_BADGE:NewMech-->'
        self.template += '\n<article class="mech-card" data-mech="NewMech"></article>'
        with self.assertRaisesRegex(ValueError, 'Graph metadata'):
            self.render()

    def test_duplicate_actual_card_cannot_hide_behind_valid_badges(self):
        self.template = self.template.replace('data-mech="TaxonMech"', 'data-mech="TraitMech"')
        with self.assertRaisesRegex(ValueError, 'Actual Mech cards'):
            self.render()

    def test_census_cannot_reference_unknown_or_unmeasured_members(self):
        self.data['order'].append('GhostMech')
        with self.assertRaisesRegex(ValueError, 'Census order'):
            self.render()
        self.data['order'].pop()
        self.data['vocab_edges'][0]['a'] = 'GhostMech'
        with self.assertRaisesRegex(ValueError, 'Census edges'):
            self.render()

    def test_missing_heat_row_cannot_publish_as_zero(self):
        self.data['heat'].pop('NaturalProductMech')
        with self.assertRaisesRegex(ValueError, 'Census heat rows'):
            self.render()

    def test_invalid_provenance_is_rejected(self):
        self.snapshot['source']['url'] = 'https://example.org/wrong'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.render()

    def test_incomplete_or_unknown_capability_fails_closed(self):
        caps = self.snapshot['mechs']['NaturalProductMech']['capabilities']
        original = caps.pop('curation_history')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.snapshot)
        caps['curation_history'] = {'status': 'unknown'}
        with self.assertRaisesRegex(ValueError, 'unknown status'):
            validate(self.snapshot)
        caps['curation_history'] = {'status': 'disabled'}
        with self.assertRaisesRegex(ValueError, 'missing reason'):
            validate(self.snapshot)
        caps['curation_history'] = original
        validate(self.snapshot)

    def test_semantic_drift_includes_capability_reason_and_membership(self):
        original = semantic(self.snapshot)
        self.snapshot['source']['revision'] = 'unrelated-commit'
        self.assertEqual(original, semantic(self.snapshot))
        changed = deepcopy(self.snapshot)
        changed['mechs']['NaturalProductMech']['capabilities']['source_queue']['status'] = 'disabled'
        self.assertNotEqual(original, semantic(changed))
        changed = deepcopy(self.snapshot)
        changed['mechs'].pop('NaturalProductMech')
        self.assertNotEqual(original, semantic(changed))
        changed = deepcopy(self.snapshot)
        changed['mechs']['NaturalProductMech']['capabilities']['curation_history']['reason'] = 'Changed evidence'
        self.assertNotEqual(original, semantic(changed))

    def test_script_data_and_tooltips_escape_markup(self):
        reason = '</script><script>alert("x")</script> & evidence'
        self.snapshot['mechs']['NaturalProductMech']['capabilities']['curation_history']['reason'] = reason
        self.assertNotIn('</script>', script_json(self.snapshot))
        self.assertIn('&lt;/script&gt;', capability_rows(self.snapshot))
        self.assertEqual(json.loads(script_json(self.snapshot)), self.snapshot)

    def test_unresolved_template_token_fails(self):
        self.template += '\n<!--FLEET_UNKNOWN-->'
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            self.render()

    def test_snapshot_reads_committed_sources_despite_dirty_checkout(self):
        # Model a CLAW checkout with a valid committed fleet and a dirty removal.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL)
            git('init', '-q')
            manifest = {'capability_catalogue': self.snapshot['capability_catalogue'], 'mechs': {}}
            for name, entry in self.snapshot['mechs'].items():
                manifest['mechs'][entry['key']] = dict(entry, display_name=name)
            registry = {'canonical_repository': 'CultureBotAI/culturebotai-claw',
                        'artifacts': [{}] * self.snapshot['artifact_count']}
            for path, data in [(MANIFEST_PATH, manifest), (ARTIFACT_PATH, registry)]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data))
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.org',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
            (root / MANIFEST_PATH).write_text('mechs: {}')
            result = read_canonical(root)
            self.assertEqual(semantic(result), semantic(self.snapshot))
            self.assertEqual(result['source']['revision'], git('rev-parse', 'HEAD').strip())


class RecordPathTests(unittest.TestCase):
    """record_paths() decides what counts as a record, so the page's numbers start here."""

    def resolve(self, name, layout, excluded=None):
        """Run record_paths() against a throwaway checkout with the given files."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in layout:
                target = root / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('id: x\n')
            patched = {
                'MECHS_ROOT': str(root),
                'EXCLUDE_DIRS': dict(roots.EXCLUDE_DIRS if excluded is None else excluded),
            }
            original = {key: getattr(roots, key) for key in patched}
            for key, value in patched.items():
                setattr(roots, key, value)
            try:
                return [str(Path(p).relative_to(root / name)) for p in roots.record_paths(name)]
            finally:
                for key, value in original.items():
                    setattr(roots, key, value)

    def test_backups_are_not_ingredient_records(self):
        # Six timestamped copies under mapped/backups/ were being counted as
        # records, and their prefixes double-counted in the heatmap (#88).
        found = self.resolve('MediaIngredientMech', [
            'data/ingredients/mapped/glucose.yaml',
            'data/ingredients/unmapped/peptone.yaml',
            'data/ingredients/mapped/backups/glucose_20260807_213601.yaml',
        ])
        self.assertEqual(found, ['data/ingredients/mapped/glucose.yaml',
                                 'data/ingredients/unmapped/peptone.yaml'])

    def test_exclusion_matches_a_directory_not_a_name_prefix(self):
        # "backups/" must not also swallow a sibling called "backups_archive".
        found = self.resolve('MediaIngredientMech', [
            'data/ingredients/mapped/glucose.yaml',
            'data/ingredients/mapped/backups_archive/kept.yaml',
        ])
        self.assertIn('data/ingredients/mapped/backups_archive/kept.yaml', found)

    def test_a_corpus_emptied_by_exclusion_is_an_error_not_a_zero(self):
        # An empty result is indistinguishable from a corpus that vanished, so
        # record_paths() refuses to return one however it was emptied.
        with self.assertRaises(SystemExit):
            self.resolve('MediaIngredientMech',
                         ['data/ingredients/mapped/backups/only_a_backup.yaml'])

    def test_every_excluded_mech_is_one_the_census_actually_reads(self):
        # A renamed Mech would leave a dead entry here that silently does nothing.
        self.assertLessEqual(set(roots.EXCLUDE_DIRS), set(roots.RECORD_GLOBS))



@contextlib.contextmanager
def census_sandbox():
    """A throwaway repo root for importing prefix_census in a child.

    The child derives its own REPO from `__file__`, so pointing it at the real
    scripts/ would make its DATA the tracked _fleet/data. Nothing is written
    there today only because `json.dump(census(), open(PATH, "w"))` evaluates
    census() — which exits — before open() truncates. Rewrite that as the
    idiomatic `with open(PATH, "w") as fh:` and the order reverses, leaving the
    tracked census at zero bytes every time the suite runs. Copying the scripts
    into a temp tree means the guard cannot depend on that accident (#102).
    """
    with tempfile.TemporaryDirectory() as box:
        root = Path(box)
        shutil.copytree(ROOT / "scripts/fleet", root / "scripts/fleet")
        data = root / "_fleet/data"
        data.mkdir(parents=True)
        (root / "empty").mkdir()
        yield root, data, dict(os.environ,
                               PYTHONPATH=str(root / "scripts/fleet"),
                               MECHS_ROOT=str(root / "empty"))

class PrefixListTests(unittest.TestCase):
    """The pipeline carries three hand-maintained prefix lists that must agree.

    `P` in prefix_census.py decides what is counted at all; `VOC` in
    build_data.py decides which vocabularies become heatmap columns; `PREF` in
    build_subsets.py decides which cells and edges get clickable record lists.
    Nothing enforced their relationship, and a mismatch is silent in both
    directions — a column with no cells renders dead, and a prefix counted but
    absent from VOC never reaches the page at all (#84, #95).
    """

    def setUp(self):
        # Read P and norm out of a SEPARATE interpreter, never this one. An
        # in-process import here is what made the old guard test toothless, and
        # splitting that test out fixed its detection without closing this hole:
        # against a regressed module, setUp itself still ran the scan and
        # overwrote the tracked census every time the suite ran (#98). The empty
        # MECHS_ROOT means a regressed module dies here in milliseconds instead.
        constants = self.module_constants()
        # What the census can actually EMIT: every alternative in P after norm
        # is applied. Taking P plus norm's values instead would also accept the
        # 15 raw spellings norm exists to fold away — UniProtKB, IPR, mesh,
        # pubchem.compound and the rest — none of which ever appear as a key,
        # so a column named one of them would pass while rendering as zeros.
        def literal_prefix(p):
            return p.replace("\\.", ".")  # the regex escapes dots
        norm = constants["norm"]
        self.census = {norm.get(literal_prefix(p), literal_prefix(p))
                       for p in constants["P"].split("|")}
        # Imported, not parsed out of the source. Until #97 both modules did
        # their work at import — build_subsets resolved every checkout and
        # build_data read and rewrote fleet_data.json — so the lists had to be
        # recovered from the source text with ast. That could not see a list
        # rebuilt after its literal, which is what #99 and #101 were about.
        # Reading the objects the pipeline actually uses retires the whole class.
        import build_data, build_subsets
        self.voc = build_data.VOC
        self.pref = build_subsets.PREF

    @staticmethod
    def module_constants():
        """prefix_census's P and norm, fetched without importing it here."""
        with census_sandbox() as (root, data, environment):
            done = subprocess.run(
                [sys.executable, "-c",
                 "import json, prefix_census as p; print(json.dumps({'P': p.P, 'norm': p.norm}))"],
                env=environment, timeout=60, capture_output=True, text=True)
        if done.returncode != 0:
            raise AssertionError(
                "could not read prefix_census's constants; it does work at import "
                f"(#95):\n{done.stderr}")
        return json.loads(done.stdout)

    def test_every_heatmap_column_is_a_vocabulary_the_census_counts(self):
        # A column the census never counts renders as a stripe of zeros.
        self.assertEqual([v for v in self.voc if v not in self.census], [])

    def test_every_clickable_cell_prefix_is_a_vocabulary_the_census_counts(self):
        self.assertEqual([p for p in self.pref if p not in self.census], [])

    def test_columns_and_clickable_cells_describe_the_same_vocabularies(self):
        # Citation prefixes are deliberately asymmetric: they get a column but
        # no record lists, which is what roots.CITATION exists to say.
        import roots
        columns = {v for v in self.voc if v not in roots.CITATION}
        cells = {p for p in self.pref if p not in roots.CITATION}
        self.assertEqual(sorted(columns - cells), [], "heatmap column with no cells behind it")
        self.assertEqual(sorted(cells - columns), [], "record lists built for a vocabulary no column shows")




class CensusImportGuardTests(unittest.TestCase):
    """That importing prefix_census does no work (#95).

    Deliberately its own class with no setUp: PrefixListTests imports the
    module in setUp, and that import is the thing under test here. Sharing it
    meant the scan ran before the snapshot was taken, so the assertion compared
    a clobbered file against itself and passed (#98).
    """

    def test_importing_the_census_module_does_not_scan_or_write(self):
        tracked = ROOT / "_fleet/data/prefix_census.json"
        before = tracked.read_bytes()
        # The empty MECHS_ROOT gives this teeth: an unguarded import reaches
        # roots.mech_root, which exits rather than counting an empty corpus, so
        # the child dies in milliseconds and the returncode assertion reports
        # its stderr. No dependence on the real corpus being slow enough to trip
        # a timeout. The sandbox means the child cannot touch the real tree
        # whatever it does.
        with census_sandbox() as (root, data, environment):
            done = subprocess.run([sys.executable, "-c", "import prefix_census"],
                                  env=environment, timeout=60,
                                  capture_output=True, text=True)
            # Positive evidence, and independent of the exit code: a scan that
            # ran would have left its census here.
            written = sorted(path.name for path in data.iterdir())
        self.assertEqual(done.returncode, 0,
                         f"importing prefix_census did work:\n{done.stderr}")
        self.assertEqual(written, [], f"importing prefix_census wrote {written}")
        self.assertEqual(tracked.read_bytes(), before)


class CardSourceTests(unittest.TestCase):
    """Every card must have somewhere to be checked against (#104)."""

    def test_every_card_has_a_published_source(self):
        # The drift check is only as complete as this table. An eleventh Mech
        # would otherwise get a card and be silently exempt from checking,
        # which is the failure this whole issue is about.
        import check_cards
        stated = card_figures((ROOT / "_fleet/mechs_template.md").read_text())
        self.assertEqual(sorted(set(stated) - set(check_cards.SOURCES)), [],
                         "card with no entry in check_cards.SOURCES")
        self.assertEqual(sorted(set(check_cards.SOURCES) - set(stated)), [],
                         "SOURCES entry with no card")

    def test_culturemech_is_read_from_its_committed_readme(self):
        # CultureMech's figure comes from its README, not a Pages URL (#175). The
        # test reads the SOURCES entry itself, so a mistyped URL or selector fails
        # here rather than turning into a silent "unread" at night (#177, #183).
        import check_cards
        kind, path, selector = check_cards.SOURCES["CultureMech"]
        # The whole URL, not a prefix: a typo in the branch or file name also 404s (#189).
        self.assertEqual(path, "https://raw.githubusercontent.com/CultureBotAI/CultureMech/main/README.md")
        self.assertEqual(check_cards.source_url(path), path)
        line = "The tracked corpus currently contains **15,878 normalized records** and **6,288 merged records**."
        self.assertEqual(check_cards.published(kind, line, selector), 6288)
        # The number alone in bold, or the line wrapped, must still read.
        self.assertEqual(check_cards.published(kind, "and **6,288** merged records.", selector), 6288)
        self.assertEqual(check_cards.published(kind, "and 6,288\nmerged records.", selector), 6288)
        # A wrap inside the label too (#207).
        self.assertEqual(check_cards.published(kind, "and 6,288 merged\n  records.", selector), 6288)

    def test_a_relative_source_is_read_from_the_pages_host(self):
        import check_cards
        self.assertEqual(check_cards.source_url("TraitMech/pages/index.html"),
                         "https://culturebotai.github.io/TraitMech/pages/index.html")

    def test_the_card_parser_reads_every_member(self):
        snapshot = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
        template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.assertEqual(sorted(card_figures(template)), sorted(snapshot["mechs"]))
        self.assertEqual(sorted(card_names(template)), sorted(snapshot["mechs"]))

    def test_a_card_without_a_figure_does_not_borrow_its_neighbours(self):
        # The old check_cards regex paired a name with the next figure in the
        # file, so the first card here would have been read as 20 (#114).
        template = ('<article class="card" data-mech="AMech"><h3>A</h3></article>\n'
                    '<article class="card" data-mech="BMech"><div class="num"><b>20</b></div></article>')
        self.assertEqual(card_figures(template), {"BMech": 20})
        self.assertEqual(card_names(template), ["AMech", "BMech"])


class CardCheckTests(unittest.TestCase):
    """What the nightly card check fails on and what it only warns about."""

    NAMES = ("AMech", "BMech", "CMech")

    def setUp(self):
        import check_cards
        from unittest import mock
        self.check_cards = check_cards
        self.real_sources = dict(check_cards.SOURCES)
        self.sources = mock.patch.dict(check_cards.SOURCES, {
            m: ("html", f"{m}/pages/index.html", f"{m[0].lower()} records") for m in self.NAMES
        }, clear=True)
        self.sources.start()
        self.addCleanup(self.sources.stop)
        self.cards = {m: 1000 for m in self.NAMES}
        self.site = {m: 1000 for m in self.NAMES}
        self.pinned_at = datetime.datetime(2026, 9, 25, 2, 0, tzinfo=datetime.timezone.utc)
        self.now = self.pinned_at + datetime.timedelta(hours=18)
        # The figure each source stated at the pin, as the audit records it.
        self.at_pin = {m: 1000 for m in self.NAMES}

    def body(self, mech, value):
        return f"<div><b>{value:,}</b><span>{mech[0].lower()} records</span></div>"

    def fetch(self, url):
        mech = url.split("/")[3]
        value = self.site[mech]
        if isinstance(value, Exception):
            raise value
        return self.body(mech, value) if isinstance(value, int) else value

    def template(self):
        return "".join(f'<article data-mech="{m}"><div class="num"><b>{n:,}</b></div></article>'
                       for m, n in self.cards.items())

    def audit(self):
        entries = []
        for m in self.check_cards.SOURCES:
            if m in self.at_pin:
                entry = {"repo": m}
                if self.at_pin[m] is not None:
                    entry["figure_at_pin"] = self.at_pin[m]
                entries.append(entry)
        return {"pinned_at_utc": self.pinned_at.isoformat(), "repositories": entries}

    def rows(self, template=None):
        return self.check_cards.check(template or self.template(), self.fetch, self.audit(), self.now)

    def statuses(self):
        return {mech: status for status, mech, _ in self.rows()}

    def failed(self, template=None):
        return sorted(status for status, _, _ in self.rows(template) if status in self.check_cards.FAILURES)

    def test_matching_figures_pass(self):
        self.assertEqual(set(self.statuses().values()), {"ok"})
        self.assertEqual(self.failed(), [])

    def test_a_site_ahead_of_a_recent_pin_only_warns(self):
        # #148, #217: CellStructureMech adds about 9% a day; within the grace
        # period that is growth, not a wrong card.
        self.site["AMech"] = 1400
        self.assertEqual(self.statuses()["AMech"], "grew")
        self.assertEqual(self.failed(), [])

    def test_growth_past_the_grace_period_fails(self):
        self.assertEqual(self.check_cards.GRACE_DAYS, 14)  # #243: the documented figure
        self.site["AMech"] = 1001
        self.now = self.pinned_at + datetime.timedelta(days=self.check_cards.GRACE_DAYS, hours=1)
        self.assertEqual(self.failed(), ["STALE"])
        self.now = self.pinned_at + datetime.timedelta(days=self.check_cards.GRACE_DAYS)
        self.assertEqual(self.failed(), [])

    def test_a_card_that_understates_its_site_by_more_than_the_lead_fails_early(self):
        self.site["AMech"] = 1500
        self.assertEqual(self.failed(), [])
        self.site["AMech"] = 1501
        self.assertEqual(self.failed(), ["STALE"])

    def test_growth_without_an_audit_fails(self):
        self.site["AMech"] = 1001
        rows = self.check_cards.check(self.template(), self.fetch, None, self.now)
        self.assertIn(("STALE", "AMech"), [(s, m) for s, m, _ in rows])

    def test_a_mistyped_card_fails_however_the_site_has_moved(self):
        # #217, #231: 3,026 typed for 3,206 used to pass as "grew", and a hash
        # comparison caught it only while the source was unchanged since the pin.
        self.cards["AMech"] = 3026
        self.at_pin["AMech"] = 3206
        for live in (3206, 3300):
            self.site["AMech"] = live
            self.assertEqual(self.statuses()["AMech"], "WRONG", live)
            self.assertEqual(self.failed(), ["WRONG"])
        # #249: overstated too, with the site ahead of both.
        self.cards["AMech"] = 3260
        self.site["AMech"] = 3300
        self.assertEqual(self.statuses()["AMech"], "WRONG")

    def test_a_source_with_no_figure_at_the_pin_is_checked_against_the_site_only(self):
        # ProteinTraitsMech's data file is built in CI, so the audit has no copy.
        from unittest import mock
        self.at_pin["AMech"] = None
        self.site["AMech"] = 1100
        with mock.patch.object(self.check_cards, "NO_PIN_COPY", ("AMech",)):
            self.assertEqual(self.statuses()["AMech"], "grew")
            self.assertEqual(self.failed(), [])

    def test_a_missing_or_mistyped_figure_at_the_pin_is_an_audit_failure(self):
        # #260: each of these used to switch WRONG off without a word, so a
        # mistyped card passed as "grew".
        self.cards["AMech"] = 3026
        self.site["AMech"] = 3206
        for at_pin in ("3206", 3206.0, True, None):
            self.at_pin["AMech"] = at_pin
            rows = self.rows()
            self.assertIn(("AUDIT", "AMech"), [(s, m) for s, m, _ in rows], at_pin)
            self.assertIn("AUDIT", self.failed(), at_pin)

    def test_a_pin_time_without_an_offset_is_utc_and_an_unreadable_one_fails(self):
        # #232: both used to end the run with a traceback before any row printed.
        audit = self.audit()
        audit["pinned_at_utc"] = self.pinned_at.replace(tzinfo=None).isoformat()
        self.site["AMech"] = 1100
        rows = self.check_cards.check(self.template(), self.fetch, audit, self.now)
        self.assertIn(("grew", "AMech"), [(s, m) for s, m, _ in rows])
        audit["pinned_at_utc"] = "25 September 2026"
        rows = self.check_cards.check(self.template(), self.fetch, audit, self.now)
        statuses = [s for s, _, _ in rows]
        self.assertIn("AUDIT", statuses)
        self.assertIn(("STALE", "AMech"), [(s, m) for s, m, _ in rows])

    def audit_failures(self, audit):
        return sorted(s for s, _, _ in self.check_cards.check(self.template(), self.fetch, audit, self.now)
                      if s in self.check_cards.FAILURES)

    def test_a_missing_future_or_unreadable_pin_time_fails_on_its_own(self):
        # #242, #243: with every card equal to its site, the audit alone fails.
        audit = self.audit()
        del audit["pinned_at_utc"]
        self.assertEqual(self.audit_failures(audit), ["AUDIT"])
        audit["pinned_at_utc"] = "not a time"
        self.assertEqual(self.audit_failures(audit), ["AUDIT"])
        for ahead in (datetime.timedelta(minutes=1), datetime.timedelta(days=365)):  # #249
            audit["pinned_at_utc"] = (self.now + ahead).isoformat()
            self.assertEqual(self.audit_failures(audit), ["AUDIT"], ahead)
        # And a future pin must not hold off the grace limit for a grown card.
        self.site["AMech"] = 1001
        self.assertIn("STALE", self.audit_failures(audit))

    def test_a_malformed_audit_is_an_audit_row_not_a_traceback(self):
        # #250: the other rows must still print.
        pinned = self.pinned_at.isoformat()
        for audit in ([], [1], {}, {"pinned_at_utc": pinned},  # #257, #259
                      {"pinned_at_utc": pinned, "repositories": [{"figure_at_pin": 1}]},
                      {"pinned_at_utc": pinned, "repositories": "x"},
                      {"pinned_at_utc": pinned, "repositories": 5}):
            rows = self.check_cards.check(self.template(), self.fetch, audit, self.now)
            self.assertIn("AUDIT", [s for s, _, _ in rows], audit)
            self.assertEqual(sorted(m for s, m, _ in rows if s == "ok"), list(self.NAMES), audit)
        rows = self.check_cards.check(self.template(), self.fetch, None, self.now,
                                      audit_error="site_audit.json is missing")
        self.assertEqual(sorted(s for s, _, _ in rows if s in self.check_cards.FAILURES), ["AUDIT"])

    def test_a_pin_time_without_an_offset_is_read_as_utc_not_local_time(self):
        # #243: in a UTC runner, local time and UTC agree, so pin a zone that differs.
        import time
        saved = os.environ.get("TZ")
        os.environ["TZ"] = "America/Los_Angeles"
        time.tzset()
        try:
            moment = self.check_cards.pin_time({"pinned_at_utc": "2026-09-25T02:06:03"})
        finally:
            if saved is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = saved
            time.tzset()
        self.assertEqual(moment, datetime.datetime(2026, 9, 25, 2, 6, 3, tzinfo=datetime.timezone.utc))
        self.assertEqual(moment.utcoffset(), datetime.timedelta(0))

    def test_a_site_behind_its_card_fails(self):
        self.site["AMech"] = 999
        self.assertEqual(self.failed(), ["SHRANK"])

    def test_a_missing_page_fails_but_an_outage_or_throttle_only_warns(self):
        # #176: a 404 is the cited page gone, which is how #175 began. #219: a
        # 429 is the host asking us to come back later.
        import urllib.error
        self.site["AMech"] = urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        self.site["BMech"] = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
        statuses = self.statuses()
        self.assertEqual((statuses["AMech"], statuses["BMech"]), ("GONE", "unread"))
        self.assertEqual(self.failed(), ["GONE"])
        for code in (408, 425, 500, 503):
            self.site["BMech"] = urllib.error.HTTPError("u", code, "x", {}, None)
            self.assertEqual(self.statuses()["BMech"], "unread", code)
        for code in (400, 403, 410, 499):  # #234, #243: any other 4xx
            self.site["AMech"] = urllib.error.HTTPError("u", code, "x", {}, None)
            self.assertEqual(self.statuses()["AMech"], "GONE", code)

    def test_a_body_cut_short_is_unread_not_a_traceback(self):
        # #220
        import http.client
        self.site["AMech"] = http.client.IncompleteRead(b"<div>", 500)
        self.assertEqual(self.statuses()["AMech"], "unread")
        self.assertEqual(self.failed(), [])

    def test_a_page_with_no_figure_fails(self):
        self.site["AMech"] = "<div><b>1,000</b><span>entries</span></div>"
        self.assertEqual(self.failed(), ["CHANGED"])

    def test_a_json_source_that_is_not_json_fails(self):
        # #222: an HTML shell served with 200 where the data file used to be.
        self.check_cards.SOURCES["AMech"] = ("json", "AMech/data/ingredients.json", "ingredients")
        self.site["AMech"] = "<html><meta http-equiv='refresh' content='0; url=app/'></html>"
        self.assertEqual(self.statuses()["AMech"], "CHANGED")

    def test_more_than_half_unread_fails_and_half_does_not(self):
        # #115: a run that read nothing used to exit 0. #222: ten sources, so
        # "more than half" can be told from "at least half".
        import urllib.error
        names = [f"M{i}Mech" for i in range(10)]
        self.check_cards.SOURCES.clear()
        self.check_cards.SOURCES.update({m: ("html", f"{m}/pages/index.html", "m records") for m in names})
        self.cards = {m: 1000 for m in names}
        self.site = {m: 1000 for m in names}
        self.at_pin = {m: 1000 for m in names}
        for m in names[:5]:
            self.site[m] = urllib.error.URLError("no route")
        self.assertEqual(self.failed(), [])
        self.site[names[5]] = TimeoutError("timed out")
        self.assertEqual(self.failed(), ["UNCHECKED"])

    def test_a_card_and_its_source_must_both_exist(self):
        del self.cards["CMech"]
        self.cards["DMech"] = 5
        self.assertEqual(self.failed(), ["UNCARDED", "UNCARDED"])

    def test_a_card_without_exactly_one_figure_is_reported_as_markup(self):
        # #218: not as a missing card, and a second figure is not silently dropped.
        template = self.template()
        unreadable = template.replace('<div class="num"><b>1,000</b></div></article><article data-mech="BMech">',
                                      '<div class="num"><b>1,000 </b></div></article><article data-mech="BMech">', 1)
        rows = self.rows(unreadable)
        self.assertIn(("MARKUP", "AMech"), [(s, m) for s, m, _ in rows])
        self.assertNotIn("UNCARDED", [s for s, _, _ in rows])
        doubled = template.replace('<article data-mech="BMech">',
                                   '<article data-mech="BMech"><div class="num"><b>7</b></div>', 1)
        self.assertEqual(self.failed(doubled), ["MARKUP"])
        stray = template + '<div class="num"><b>7</b></div>'
        self.assertEqual(self.failed(stray), ["MARKUP"])
        # #261: an unreadable figure is MARKUP, not int("") ending the run, and
        # a malformed second tile, in a card or outside one, still counts.
        comma = template.replace("<b>1,000</b>", "<b>,</b>", 1)
        self.assertEqual(self.failed(comma), ["MARKUP"])
        spaced = template.replace('<article data-mech="BMech">',
                                  '<article data-mech="BMech"><div class="num"><b>7 </b></div>', 1)
        self.assertEqual(self.failed(spaced), ["MARKUP"])
        self.assertEqual(self.failed(template + '<div class="num"><b>7 </b></div>'), ["MARKUP"])
        # #262: a second card for one Mech would have been checked instead of the first.
        twice = '<article data-mech="AMech"><div class="num"><b>3,026</b></div></article>' + template
        self.assertEqual(self.failed(twice), ["MARKUP"])

    def test_the_culturemech_figure_is_read_only_from_its_generated_block(self):
        # #176: the regex takes the first match, and the README's prose could
        # state an older "N merged records" above the generated block.
        kind, path, selector = self.real_sources["CultureMech"]
        begin, end = self.check_cards.REGIONS["CultureMech"]
        line = ("The tracked corpus currently contains **15,878 normalized records** and "
                "**6,288 merged records**.")
        readme = "Release 2 added 1,024 merged records.\n" + begin + "\n" + line + "\n" + end + "\n"
        read = self.check_cards.read_source
        self.assertEqual(read("CultureMech", kind, path, selector, lambda url: readme)[:2], ("value", 6288))
        for broken in ("The corpus has 6,288 merged records.", begin + "\n" + line + "\n",
                       begin + "\nno figure here\n" + end):
            status, detail = read("CultureMech", kind, path, selector, lambda url: broken)
            self.assertEqual(status, "CHANGED")
            # #247: it used to say the missing block was "found".
            self.assertIn("missing or states no figure", detail)

    def test_main_exits_by_the_same_rule(self):
        from unittest import mock
        import urllib.error
        with tempfile.TemporaryDirectory() as tmp:
            template, audit = Path(tmp) / "mechs_template.md", Path(tmp) / "site_audit.json"
            template.write_text(self.template())
            self.pinned_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
            audit.write_text(json.dumps(self.audit()))
            with mock.patch.object(self.check_cards, "TEMPLATE", template), \
                 mock.patch.object(self.check_cards, "AUDIT", audit), \
                 mock.patch.object(self.check_cards, "fetch", self.fetch), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.site["AMech"] = 1050
                self.site["BMech"] = urllib.error.URLError("no route")
                self.assertEqual(self.check_cards.main(), 0)
                self.site["AMech"] = 900
                self.assertEqual(self.check_cards.main(), 1)
                # #234: every failing verdict fails the run, not just SHRANK.
                self.site["AMech"] = 1600                                   # STALE
                self.assertEqual(self.check_cards.main(), 1)
                self.site["AMech"] = 1000
                self.at_pin["AMech"] = 1001                                 # WRONG
                audit.write_text(json.dumps(self.audit()))
                self.assertEqual(self.check_cards.main(), 1)
                self.at_pin["AMech"] = 1000
                audit.write_text(json.dumps(self.audit()))
                self.site["AMech"] = self.site["CMech"] = TimeoutError("t")  # UNCHECKED
                self.assertEqual(self.check_cards.main(), 1)
                self.site = {m: 1000 for m in self.NAMES}
                # #249: the remedy WRONG prints is a correction, not a refresh.
                self.at_pin["AMech"] = 1001
                audit.write_text(json.dumps(self.audit()))
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(self.check_cards.main(), 1)
                remedy = out.getvalue().split("WRONG:", 1)[1].split(" GONE or CHANGED:", 1)[0]
                for named in ("every other occurrence", "grepping the tree", "fleet_fragment.html",
                              "extra:", "card_records", "no re-pin"):  # #248, #258, #259
                    self.assertIn(named, remedy)
                self.assertNotIn("update-xmech-page)", remedy)
                self.at_pin["AMech"] = 1000
                # AUDIT alone fails the run, and an unreadable file is AUDIT, not a traceback (#250).
                audit.write_text("{not json")
                self.assertEqual(self.check_cards.main(), 1)
                for body in ("null", "{}", "[1]"):  # #257: none may pass as "no audit"
                    audit.write_text(body)
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        self.assertEqual(self.check_cards.main(), 1, body)
                    self.assertIn("AUDIT", out.getvalue(), body)
                audit.unlink()
                self.assertEqual(self.check_cards.main(), 1)


class RefreshProvenanceTests(unittest.TestCase):
    """The derived numbers must all come from one set of checkouts (#85).

    The census, the card stats and the site audit are written by different
    scripts on what should be the same run. Before any of them recorded a
    revision, a partial refresh left the census at 364 CommunityMech records
    and the stats at 396, and nothing noticed. Each now names the commit it
    read, so a partial rerun shows up here as a disagreement.
    """

    def setUp(self):
        self.census = json.loads((ROOT / "_fleet/data/prefix_census.json").read_text())
        stats = json.loads((ROOT / "_fleet/data/mech_stats.json").read_text())
        self.stats = {m["mech"]: m for m in stats["mechs"]}
        audit = json.loads((ROOT / "_fleet/data/site_audit.json").read_text())
        self.audit = {r["repo"]: r for r in audit["repositories"]}

    def test_every_count_names_a_clean_revision(self):
        for mech, entry in self.stats.items():
            with self.subTest(mech=mech):
                revision = entry.get("source_revision")
                self.assertRegex(revision or "", r"^[0-9a-f]{40}$",
                                 "missing, or read from a checkout with uncommitted changes")

    def test_census_and_stats_read_the_same_revisions(self):
        revisions = self.census.get("_revisions", {})
        for mech in roots.ORDER:
            with self.subTest(mech=mech):
                self.assertEqual(revisions.get(mech), self.stats[mech]["source_revision"])

    def test_census_and_stats_count_the_same_records(self):
        # Same globs, same revision, so the same files. A difference means one
        # of the two was rerun without the other.
        for mech in roots.ORDER:
            with self.subTest(mech=mech):
                self.assertEqual(self.census[mech]["files"], self.stats[mech]["records"])

    def test_the_audit_pins_the_revisions_the_stats_counted(self):
        for mech, entry in self.stats.items():
            with self.subTest(mech=mech):
                self.assertIn(entry["repo"], self.audit, "Mech missing from site_audit.json")
                self.assertEqual(self.audit[entry["repo"]]["sha"], entry["source_revision"])

    def test_every_graph_panel_states_its_card_figure(self):
        # #248: the MECHS block repeats each card's figure as records:, and a
        # correction to one used to leave the other behind unnoticed.
        fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        metadata = fragment.split("var MECHS = {", 1)[1].split("\n  };", 1)[0]
        panels = {m: int(n) for m, n in re.findall(r"^\s+([A-Za-z]+Mech):\s*\{.*?\brecords:\s*(\d+)", metadata, re.M)}
        self.assertEqual(panels, card_figures((ROOT / "_fleet/mechs_template.md").read_text()))

    def test_every_card_equals_the_figure_its_source_stated_at_the_pin(self):
        # #231: the audit builder read card_records from the template, so the
        # audit could only repeat a mistyped card. figure_at_pin is read from the
        # source's committed copy at the pin with check_cards.figure(), and the
        # nightly's WRONG verdict depends on it being there.
        import check_cards
        audit = json.loads((ROOT / "_fleet/data/site_audit.json").read_text())
        pinned = check_cards.pin_time(audit)  # #232: must parse
        # #242: and must fall between the newest pinned commit and the check.
        newest = max(datetime.datetime.fromisoformat(r["commit_date"].replace("Z", "+00:00"))
                     for r in audit["repositories"])
        checked = datetime.datetime.fromisoformat(audit["checked_at_utc"])
        self.assertLessEqual(newest, pinned)
        self.assertLessEqual(pinned, checked)
        entries = {r["repo"].lower(): r for r in audit["repositories"]}
        cards = card_figures((ROOT / "_fleet/mechs_template.md").read_text())
        for mech in check_cards.SOURCES:
            with self.subTest(mech=mech):
                entry = entries[mech.lower()]
                if mech in check_cards.NO_PIN_COPY:
                    # Built in CI, so there is no committed copy at the pin.
                    self.assertNotIn("figure_at_pin", entry)
                    continue
                self.assertIs(type(entry.get("figure_at_pin")), int)  # #260: not 3206.0
                self.assertEqual(entry["figure_at_pin"], cards[mech])

    def test_the_audit_records_this_refresh_and_nothing_else(self):
        # The audit's other fields had no gate at all (#128): its merged PRs,
        # the card figure it read, the CLAW pin, and which repositories it lists.
        cards = card_figures((ROOT / "_fleet/mechs_template.md").read_text())
        manifest = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
        self.assertEqual(set(self.audit), {m["repo"] for m in self.stats.values()} | {"culturebotai-claw"})
        self.assertEqual(self.audit["culturebotai-claw"]["sha"], manifest["source"]["revision"])
        for mech, entry in self.stats.items():
            with self.subTest(mech=mech):
                row = self.audit[entry["repo"]]
                self.assertEqual(row["merged_prs"], entry["merged_prs"])
                self.assertEqual(row["card_records"], cards[mech])

    def test_the_subsets_read_the_same_revisions_as_the_census(self):
        # build_subsets.py is the other scanning pass; a rerun of it alone, or of
        # the census alone, would otherwise go unnoticed (#126).
        subsets = json.loads((ROOT / "_fleet/data/subsets_summary.json").read_text())
        self.assertEqual(subsets.get("_revisions"), self.census.get("_revisions"))

    def test_fleet_data_is_built_from_the_committed_inputs(self):
        # fleet_data.json is what the page embeds. A skipped build_data.py leaves
        # it describing older subsets and census files (#126).
        import build_data
        subsets = json.loads((ROOT / "_fleet/data/subsets_summary.json").read_text())
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            expected = build_data.build(subsets, self.census)
        committed = json.loads((ROOT / "_fleet/data/fleet_data.json").read_text())
        self.assertEqual(committed, json.loads(json.dumps(expected)))


class RevisionTests(unittest.TestCase):
    """roots.revision() must say whether the counted records are the commit's (#121)."""

    MECH = "TraitMech"   # any name in RECORD_GLOBS; its glob is data/traits/**/*.yaml

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.saved = roots.MECHS_ROOT
        self.addCleanup(setattr, roots, "MECHS_ROOT", self.saved)
        roots.MECHS_ROOT = str(self.tmp)
        self.repo = self.tmp / self.MECH
        (self.repo / "data/traits/a").mkdir(parents=True)
        (self.repo / "data/traits/b").mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "data/traits/a/one.yaml").write_text("id: METPO:1\n")
        (self.repo / "data/traits/b/two.yaml").write_text("id: METPO:2\n")
        (self.repo / "src/schema.yaml").write_text("id: s\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "records")
        self.sha = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test",
                               "-c", "commit.gpgsign=false", "-C", str(self.repo), *args],
                              capture_output=True, text=True, check=True).stdout

    def test_a_clean_checkout_names_its_commit(self):
        self.assertEqual(roots.revision(self.MECH), self.sha)

    def test_a_modified_record_is_dirty(self):
        (self.repo / "data/traits/b/two.yaml").write_text("id: METPO:3\n")
        self.assertEqual(roots.revision(self.MECH), self.sha + "+dirty")

    def test_an_untracked_record_is_dirty_even_when_status_hides_it(self):
        self.git("config", "status.showUntrackedFiles", "no")
        (self.repo / "data/traits/three.yaml").write_text("id: METPO:4\n")
        self.assertEqual(roots.revision(self.MECH), self.sha + "+dirty")

    def test_an_ignored_record_is_dirty(self):
        # record_paths() counts it and git status never lists it: the #88 shape.
        (self.repo / ".gitignore").write_text("backups/\n")
        self.git("add", ".gitignore"); self.git("commit", "-q", "-m", "ignore")
        sha = self.git("rev-parse", "HEAD").strip()
        (self.repo / "data/traits/backups").mkdir()
        (self.repo / "data/traits/backups/copy.yaml").write_text("id: METPO:1\n")
        self.assertEqual(roots.revision(self.MECH), sha + "+dirty")

    def test_records_a_sparse_checkout_leaves_out_are_dirty(self):
        # Cone mode keeps files directly in ancestor directories, so the left-out
        # record sits in a sibling subdirectory.
        self.git("sparse-checkout", "set", "--cone", "data/traits/a", "src")
        self.assertFalse((self.repo / "data/traits/b/two.yaml").exists())
        self.assertEqual(roots.revision(self.MECH), self.sha + "+dirty")

    def test_an_unrelated_scratch_file_does_not_make_it_dirty(self):
        (self.repo / "notes.txt").write_text("scratch\n")
        self.assertEqual(roots.revision(self.MECH), self.sha)

    def test_a_directory_inside_another_repository_is_not_that_repository(self):
        # rev-parse walks up; the enclosing repository's HEAD is not this Mech's (#124).
        outer = self.tmp / "outer"
        inner = outer / self.MECH
        (inner / "data/traits").mkdir(parents=True)
        (inner / "data/traits/x.yaml").write_text("id: METPO:9\n")
        subprocess.run(["git", "-C", str(outer), "init", "-q"], check=True)
        roots.MECHS_ROOT = str(outer)
        self.assertIsNone(roots.revision(self.MECH))


class SubsetDeterminismTests(unittest.TestCase):
    """Two build_subsets.py runs over the same records write the same bytes (#107, #129)."""

    # Every Mech gets one record citing the same five shared terms, so every
    # edge has five prefixes tied at one: the case Counter.most_common() orders
    # by set iteration, which follows the per-process hash seed.
    SHARED = "CHEBI:1 GO:2 ENVO:3 NCBITaxon:4 METPO:5 UniProt:P6 PATO:7 UBERON:8"

    def build_fixture(self, root):
        for mech, patterns in roots.RECORD_GLOBS.items():
            base = roots._record_dirs(mech)[0]
            folder = root / mech / base
            folder.mkdir(parents=True, exist_ok=True)
            ident = {"HabitatMech": "habitatmech:0001", "ProteinTraitsMech": "PTM:1"}.get(mech, f"{mech}:1")
            (folder / "rec.yaml").write_text(f"id: {ident}\nlabel: record\nterms: {self.SHARED}\n")
        pages = root / "HabitatMech/pages/habitats"
        pages.mkdir(parents=True)
        (pages / "record-habitatmech-0001.html").write_text("<html></html>")

    def run_once(self, fixture, out, seed):
        driver = ("import build_subsets as b, os; b.OUT=os.environ['OUT']; b.DATA=os.environ['DATA']; "
                  "os.makedirs(b.DATA, exist_ok=True); b.main()")
        env = dict(os.environ, MECHS_ROOT=str(fixture), PYTHONPATH=str(ROOT / "scripts/fleet"),
                   PYTHONHASHSEED=str(seed), OUT=str(out / "fleet"), DATA=str(out / "data"))
        done = subprocess.run([sys.executable, "-c", driver], env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        return {str(p.relative_to(out)): p.read_bytes() for p in sorted(out.rglob("*.json"))}

    def test_a_folded_label_is_read_whole(self):
        # YAML folds a long label onto indented continuation lines; the record
        # link used to carry only the first line (#165).
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.build_fixture(tmp / "mechs")
        folder = tmp / "mechs" / "TaxonMech" / roots._record_dirs("TaxonMech")[0]
        (folder / "folded.yaml").write_text("identifier: NCBITaxon:4\nlabel: Bacterium with a name long enough\n  to fold onto a second line\nterms: " + self.SHARED + "\n")
        run = self.run_once(tmp / "mechs", tmp / "run", 1)
        cells = run["fleet/cells/TaxonMech--NCBITaxon.json"].decode()
        self.assertIn("Bacterium with a name long enough to fold onto a second line", cells)

    def test_output_does_not_depend_on_the_hash_seed(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.build_fixture(tmp / "mechs")
        runs = [self.run_once(tmp / "mechs", tmp / f"run{seed}", seed) for seed in (1, 2, 3, 4)]
        self.assertTrue(runs[0], "the fixture produced no output")
        self.assertTrue(any('"edges"' in k or k.startswith("fleet/edges") for k in runs[0]))
        for seed, run in zip((2, 3, 4), runs[1:]):
            self.assertEqual(run, runs[0], f"output under PYTHONHASHSEED={seed} differs from seed 1")


if __name__ == '__main__':
    unittest.main()
