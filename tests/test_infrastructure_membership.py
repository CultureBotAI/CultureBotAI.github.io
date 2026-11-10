"""Infrastructure admission must not invent corpus counts or website evidence (#540)."""

import datetime
import json
import re
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import build_site_audit
import check_cards
import check_updates
import mech_stats
import roots
from assemble_page import assemble, infrastructure_markup, pr_activity, validate_recent_terms, validate_site_features
from card_markup import card_figures, card_names
from refresh_manifest import project, semantic, validate


class InfrastructureMembershipTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json",
                        "site_features.json", "recent_terms.json")]
        self.infrastructure = json.loads((ROOT / "_fleet/infrastructure.json").read_text())

    def render(self):
        return assemble(self.template, self.fragment, *self.inputs, infrastructure=self.infrastructure)

    def test_member_gets_capabilities_without_a_numeric_card_or_scientific_corpus(self):
        before = deepcopy(self.inputs)
        page = self.render()
        self.assertIn('data-infrastructure="EdgeMech"', page)
        self.assertIn('<tr><th scope="row">EdgeMech</th>', page)
        self.assertIn("The manifest also declares one infrastructure member: EdgeMech.", page)
        self.assertIn("No published scientific corpus or Pages browser", page)
        self.assertIn("not independent scientific approvals", page)
        self.assertEqual(len(card_names(page)), 14)
        self.assertNotIn("EdgeMech", card_figures(page))
        self.assertNotIn("EdgeMech", self.inputs[0]["order"])
        self.assertNotIn("EdgeMech", self.inputs[4]["mechs"])
        self.assertEqual(self.inputs, before)
        self.assertIn("Across 16 repositories: the fourteen Mechs, CLAW and this website", page)

    def test_admission_is_not_inferred_from_infrastructure_description(self):
        self.inputs[1]["mechs"].pop("EdgeMech")
        page = self.render()
        self.assertIn("Separately listed projects without a declaration: EdgeMech.", page)
        self.assertIn("No infrastructure member has a manifest declaration.", page)
        self.assertIn('<span class="badge">not yet in fleet manifest</span>', page)
        self.assertNotIn("All projects shown here have a manifest declaration.", page)

    def test_omitted_infrastructure_representation_still_fails_closed(self):
        self.infrastructure["members"] = {}
        with self.assertRaisesRegex(ValueError, "cards must match"):
            self.render()

    def test_corpus_cannot_be_hidden_as_infrastructure(self):
        self.infrastructure["members"]["TraitMech"] = self.infrastructure["members"].pop("EdgeMech")
        with self.assertRaisesRegex(ValueError, "separate from corpus"):
            self.render()

    def test_invented_corpus_or_site_requires_separate_review(self):
        for key, value in (("corpus", 0), ("site", "https://example.org")):
            with self.subTest(key=key):
                changed = deepcopy(self.infrastructure)
                changed["members"]["EdgeMech"][key] = value
                with self.assertRaisesRegex(ValueError, "separate reviewed admission"):
                    infrastructure_markup(changed, self.inputs[1])

    def test_repository_and_scope_fields_fail_closed(self):
        for mutation in (lambda item: item.update(repository="CultureBotAI/WrongMech"),
                         lambda item: item.pop("scope_note"),
                         lambda item: item.update(description=""),
                         lambda item: item.update(checked_on="yesterday")):
            changed = deepcopy(self.infrastructure)
            mutation(changed["members"]["EdgeMech"])
            with self.assertRaises(ValueError):
                infrastructure_markup(changed, self.inputs[1])

    def test_committed_infrastructure_claw_evidence_url_matches_manifest_source(self):
        manifest_url = self.inputs[1]["source"]["url"]
        for name, item in self.infrastructure["members"].items():
            url = item.get("evidence_url", "")
            if "/culturebotai-claw/blob/" in url and url.endswith("/src/kg_microbe_fleet/fleet.yaml"):
                self.assertEqual(url, manifest_url, f"{name} evidence_url does not match manifest.json source.url")


class WithheldMechExclusionTests(unittest.TestCase):
    """ScaleupMech must stay excluded from public view, pages, and all statistics."""

    def setUp(self):
        self.template = (ROOT / "_fleet/mechs_template.md").read_text()
        self.fragment = (ROOT / "_fleet/fleet_fragment.html").read_text()
        self.inputs = [json.loads((ROOT / "_fleet/data" / name).read_text()) for name in
                       ("fleet_data.json", "manifest.json", "mech_stats.json", "prefix_census.json",
                        "site_features.json", "recent_terms.json")]
        self.infrastructure = json.loads((ROOT / "_fleet/infrastructure.json").read_text())

    def render(self):
        return assemble(self.template, self.fragment, *self.inputs, infrastructure=self.infrastructure)

    def test_withheld_identifier_matching_and_root_rejection(self):
        for token in ("ScaleupMech", "scaleupmech", "CultureBotAI/ScaleupMech",
                      "https://github.com/CultureBotAI/ScaleupMech/",
                      "https://github.com/CultureBotAI/ScaleupMech/blob/main/README.md",
                      "https://culturebotai.github.io/ScaleupMech/pages/index.html",
                      "ScaleupMech/pages/index.html",
                      "scaleupmech_export",
                      "ScaleupMech--CHEBI",
                      "ScaleupMech|CHEBI"):
            self.assertTrue(roots.is_withheld(token), token)
        for allowed in ("CultureMech", "CofactorMech", "AssayMech", "EdgeMech", None, ""):
            self.assertFalse(roots.is_withheld(allowed), allowed)
        self.assertNotIn("ScaleupMech", roots.RECORD_GLOBS)
        self.assertNotIn("ScaleupMech", roots.ORDER)
        self.assertNotIn("ScaleupMech", check_cards.SOURCES)
        self.assertNotIn("ScaleupMech", mech_stats.MEMBERS)
        self.assertNotIn("ScaleupMech", mech_stats.ADDITIONAL_REPOS)
        with self.assertRaisesRegex(SystemExit, "withheld"):
            roots.mech_root("ScaleupMech")

    def test_manifest_projection_strips_scaleupmech_and_preserves_public_snapshot(self):
        snapshot = self.inputs[1]
        manifest = {
            "capability_catalogue": deepcopy(snapshot["capability_catalogue"]),
            "mechs": {
                mech["key"]: {
                    "display_name": name,
                    "github": mech["github"],
                    "capabilities": deepcopy(mech["capabilities"]),
                }
                for name, mech in snapshot["mechs"].items()
            },
        }
        manifest["mechs"]["scaleupmech"] = {
            "display_name": "ScaleupMech",
            "github": "CultureBotAI/ScaleupMech",
            "capabilities": {
                key: {"status": "disabled", "reason": "Withheld private bootstrap."}
                for key in snapshot["capability_catalogue"]
            },
        }
        registry = {
            "canonical_repository": "CultureBotAI/culturebotai-claw",
            "artifacts": (
                [{"id": f"shared-{i}", "consumers": ["culturemech", "scaleupmech"]}
                 for i in range(snapshot["artifact_count"])]
                + [{"id": "scaleup-only", "consumers": ["scaleupmech"]}]
                + [{"id": "scaleupmech_schema", "source": "ScaleupMech/schema.yaml", "consumers": []}]
            ),
        }
        projected = project(manifest, registry, snapshot["source"]["revision"])
        self.assertNotIn("ScaleupMech", projected["mechs"])
        self.assertEqual(projected["artifact_count"], snapshot["artifact_count"])
        self.assertEqual(semantic(projected), semantic(snapshot))

    def test_manifest_validation_rejects_withheld_mech(self):
        bad = deepcopy(self.inputs[1])
        bad["mechs"]["ScaleupMech"] = deepcopy(bad["mechs"]["EdgeMech"])
        bad["mechs"]["ScaleupMech"].update(key="scaleupmech", github="CultureBotAI/ScaleupMech")
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            validate(bad)

        bad_reason = deepcopy(self.inputs[1])
        first_mech = next(iter(bad_reason["mechs"].values()))
        first_cap = next(iter(first_mech["capabilities"]))
        first_mech["capabilities"][first_cap] = {
            "status": "disabled",
            "reason": "Deferred until ScaleupMech integration lands.",
        }
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            validate(bad_reason)

    def test_stats_and_pr_activity_reject_withheld_mech(self):
        with self.assertRaisesRegex(SystemExit, "withheld Mech"):
            mech_stats.review_slot("ScaleupMech")
        with self.assertRaisesRegex(SystemExit, "withheld Mech"):
            mech_stats.review_census("ScaleupMech")
        with self.assertRaisesRegex(SystemExit, "withheld Mech"):
            mech_stats.merged_prs("ScaleupMech")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stats.json"
            bad_cache = deepcopy(self.inputs[2])
            bad_cache["mechs"].append({"mech": "ScaleupMech", "repo": "ScaleupMech", "merged_prs": 5})
            out.write_text(json.dumps(bad_cache))
            with mock.patch.object(mech_stats, "OUT", str(out)):
                with self.assertRaisesRegex(SystemExit, "withheld Mech"):
                    mech_stats.cached_prs()

        bad_stats = deepcopy(self.inputs[2])
        bad_stats["mechs"].append({"mech": "ScaleupMech", "repo": "ScaleupMech", "merged_prs": 5})
        bad_stats["merged_prs_total"] += 5
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            pr_activity(bad_stats)

    def test_assemble_and_audit_helpers_reject_withheld_mech_everywhere(self):
        bad_infra = deepcopy(self.infrastructure)
        bad_infra["members"]["ScaleupMech"] = deepcopy(bad_infra["members"]["EdgeMech"])
        bad_infra["members"]["ScaleupMech"]["repository"] = "CultureBotAI/ScaleupMech"
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            infrastructure_markup(bad_infra, self.inputs[1])

        bad_features = deepcopy(self.inputs[4])
        bad_features["mechs"]["ScaleupMech"] = {
            "repository": "https://github.com/CultureBotAI/ScaleupMech",
            "site": None,
            "note": "Private repository.",
        }
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            validate_site_features(bad_features, list(bad_features["mechs"]))
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            check_updates.site_feature_check(bad_features)
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            check_updates.drift({"repo": "ScaleupMech", "sha": "a" * 40}, "ScaleupMech", set())

        bad_recent = deepcopy(self.inputs[5])
        bad_recent["mechs"].append({"mech": "ScaleupMech", "repo": "ScaleupMech", "source_revision": "a" * 40, "records": []})
        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            validate_recent_terms(bad_recent, list(roots.ORDER) + ["ScaleupMech"])

        orig_template = self.template
        self.template = orig_template + "\n<!-- scaleupmech_export -->"
        with self.assertRaisesRegex(ValueError, "Withheld Mech ScaleupMech"):
            self.render()
        self.template = orig_template

        with self.assertRaisesRegex(ValueError, "withheld Mech"):
            check_cards.check(
                orig_template,
                audit={"pinned_at_utc": "2026-11-09T12:00:00Z", "repositories": [{"repo": "ScaleupMech"}]},
            )

        pins = {"pinned_at_utc": "2026-11-09T12:00:00Z",
                "mechs": {"ScaleupMech": {"repo": "ScaleupMech", "sha": "a" * 40, "commit_date": "2026-11-09T12:00:00Z"}},
                "claw": "b" * 40}
        notes = json.loads((ROOT / "_fleet/audit_notes.json").read_text())
        with self.assertRaisesRegex(SystemExit, "withheld Mech"):
            build_site_audit.build(pins, notes, (ROOT / "_fleet/mechs_template.md").read_text(),
                                   self.inputs[2], lambda _: b"", lambda *_: lambda _: None,
                                   "2026-11-09T12:00:00Z", datetime.datetime.now(datetime.timezone.utc))

        pins_alias = {"pinned_at_utc": "2026-11-09T12:00:00Z",
                      "mechs": {"CultureMech": {"repo": "ScaleupMech", "sha": "a" * 40, "commit_date": "2026-11-09T12:00:00Z"}},
                      "claw": "b" * 40}
        with self.assertRaisesRegex(SystemExit, "withheld Mech"):
            build_site_audit.build(pins_alias, notes, (ROOT / "_fleet/mechs_template.md").read_text(),
                                   self.inputs[2], lambda _: b"", lambda *_: lambda _: None,
                                   "2026-11-09T12:00:00Z", datetime.datetime.now(datetime.timezone.utc))

    def test_no_public_page_or_fleet_data_file_mentions_scaleupmech(self):
        checked_paths = (
            list(ROOT.glob("*.md"))
            + list(ROOT.glob("*.html"))
            + list((ROOT / "_includes").glob("*.html"))
            + list((ROOT / "_layouts").glob("*.html"))
            + list((ROOT / "_fleet").glob("*.md"))
            + list((ROOT / "_fleet").glob("*.html"))
            + list((ROOT / "_fleet").glob("*.json"))
            + list((ROOT / "_fleet/data").glob("*.json"))
            + list((ROOT / "assets/fleet").rglob("*.json"))
        )
        self.assertGreater(len(checked_paths), 100)
        for path in checked_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"scaleupmech", text, re.I), f"{path.relative_to(ROOT)} mentions ScaleupMech")


if __name__ == "__main__":
    unittest.main()
