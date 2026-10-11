"""AIMech measures imported and maintained concepts without conflating them."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import build_cells
import build_site_audit
import build_subsets
import check_cards
import check_updates
import mech_stats
import prefix_census
import roots

PIN = "a" * 40


class AIMechTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "AIMech"
        self.imported = "id: AIO:Example\nname: Example\nparents:\n- AIO:Model\nreview_status: NOT_REVIEWED\n"
        self.curated = ("name: Example\ndefinition: A maintained concept.\nid: AIMech:Example\n"
                        "aio_mappings:\n- target: AIO:Model\nreview_status: DRAFT\n"
                        "persistent_id: arXiv:1234.56789v1\n")
        for part, text in (("aio", self.imported), ("curated", self.curated)):
            path = self.root / "data" / part / "Example.yaml"
            path.parent.mkdir(parents=True)
            path.write_text(text)

    def tree(self, paths):
        return json.dumps({"truncated": False, "tree": [
            {"path": path, "mode": "100644", "type": "blob", "sha": PIN}
            for path in paths]})

    def test_census_and_card_inventory_count_both_native_corpora_only(self):
        extra = ("data/aio/nested/not-a-record.yaml", "data/aio/.hidden.yaml",
                 "data/aio/example.yml", "reviews/structured/review.yaml",
                 "history/concept.yaml", "data/aio-full.owl", "sources/aio/source.json")
        for relative in extra:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("reference or sidecar")
        with mock.patch.object(roots, "MECHS_ROOT", str(self.root.parent)):
            paths = roots.record_paths("AIMech")
            self.assertEqual(roots.record_count("AIMech", paths), 2)
        relative = [Path(path).relative_to(self.root).as_posix() for path in paths]
        self.assertEqual(relative, ["data/aio/Example.yaml", "data/curated/Example.yaml"])
        kind, _, selector = check_cards.SOURCES["AIMech"]
        self.assertEqual(check_cards.figure("AIMech", kind, self.tree([*relative, *extra]), selector), 2)
        for path in relative:
            self.assertTrue(check_updates.is_record("AIMech", path))

    def test_external_aio_and_arxiv_count_without_new_shared_term_indexes(self):
        text = self.imported + self.curated + "external: arxiv:9999.00001\nreference: DOI:10.1/example\n"
        counts = collections.Counter(prefix_census.norm.get(p, p) for p in prefix_census.rx.findall(text))
        self.assertEqual(counts, {"AIO": 3, "arXiv": 2, "DOI": 1})
        self.assertIn("arXiv", roots.CITATION)
        self.assertNotIn("AIO", roots.CITATION)
        self.assertNotIn("AIO", build_subsets.PREF)
        self.assertNotIn("arXiv", build_subsets.PREF)
        self.assertEqual(build_subsets.terms_in(self.imported + self.curated), set())

    def test_same_named_import_and_curated_concept_keep_distinct_labels_and_links(self):
        base = "https://github.com/CultureBotAI/AIMech/blob/" + PIN + "/data/"
        cfg = {"root": str(self.root), "base": base}
        with (mock.patch.object(roots, "MECHS_ROOT", str(self.root.parent)),
              mock.patch.dict(build_subsets.MECHS, {"AIMech": cfg})):
            cells = build_cells.scan("AIMech", source_revision=PIN)
        aio = cells["AIO"]
        self.assertEqual((aio["total"], aio["occurrences"]), (2, 3))
        self.assertEqual(aio["base"], base)
        self.assertEqual(aio["records"], [
            ["aio/Example.yaml", "Example · AIO:Example"],
            ["curated/Example.yaml", "Example · AIMech:Example"],
        ])
        with self.assertRaisesRegex(ValueError, "native concept identity"):
            build_subsets.record_identity("bad.yaml", "name: Missing identity\n", "AIMech")

    def test_source_links_are_pinned_during_prepare(self):
        with (mock.patch.object(build_subsets, "ORDER", ["CMMMech", "AIMech"]),
              mock.patch.object(build_subsets, "mech_root", side_effect=lambda name: "/fixture/" + name),
              mock.patch.object(build_subsets, "revision", return_value=PIN),
              mock.patch.object(build_subsets.glob, "glob", return_value=["/fixture/HabitatMech/pages/habitats/a.html"]),
              mock.patch.dict(build_subsets.MECHS, clear=True),
              mock.patch.object(build_subsets, "hab_pages", set()),
              mock.patch.object(build_subsets, "hab_by_suffix", collections.defaultdict(list))):
            build_subsets.prepare()
            self.assertEqual(build_subsets.MECHS["AIMech"]["base"],
                             "https://github.com/CultureBotAI/AIMech/blob/" + PIN + "/data/")
            self.assertEqual(build_subsets.MECHS["CMMMech"]["base"],
                             "https://github.com/CultureBotAI/CMMMech/blob/" + PIN + "/data/records/")

    def test_native_draft_and_import_statuses_do_not_claim_review_coverage(self):
        schema = self.root / "src/aimech/schema"
        schema.mkdir(parents=True)
        for filename, cls, status in (("aimech", "AIConcept", "NOT_REVIEWED"),
                                       ("curated_concept", "CuratedAIConcept", "DRAFT")):
            (schema / (filename + ".yaml")).write_text(
                f"classes:\n  {cls}:\n    tree_root: true\n    attributes:\n"
                f"      review_status: {{range: {cls}Status}}\n"
                f"enums:\n  {cls}Status:\n    permissible_values:\n      {status}: {{}}\n")
        with (mock.patch.object(roots, "MECHS_ROOT", str(self.root.parent)),
              mock.patch.object(mech_stats, "revision", return_value=PIN),
              mock.patch.object(mech_stats, "unchanged")):
            self.assertEqual(mech_stats.review_census("AIMech"), (2, None, None, PIN))

    def test_audit_hashes_only_both_concept_inventories_and_links_their_common_directory(self):
        payload = self.tree(["data/aio/Example.yaml", "data/curated/Example.yaml"]).encode()
        source = check_cards.SOURCES["AIMech"]
        row = build_site_audit.build_entry(
            "AIMech", source, {"sha": PIN, "commit_date": "2026-10-11T00:00:00Z"},
            {"source_revision": PIN, "repo": "AIMech", "merged_prs": 3},
            2, "Imported and maintained concepts.", lambda _: payload, lambda _: payload)
        self.assertEqual(row["figure_at_pin"], 2)
        self.assertEqual(row["site"], "https://github.com/CultureBotAI/AIMech/tree/" + PIN + "/data")
        self.assertEqual(row["data_url"], source[1])
        digest = hashlib.sha256(check_cards.record_inventory(payload.decode(), source[2])).hexdigest()
        self.assertEqual(row["data_sha256"], digest)
        self.assertEqual(row["data_sha256_at_pin"], digest)
        self.assertIn("data inventory", row["notes"])


if __name__ == "__main__":
    unittest.main()
