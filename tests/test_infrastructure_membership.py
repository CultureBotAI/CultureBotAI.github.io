"""Infrastructure admission must not invent corpus counts or website evidence (#540)."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from assemble_page import assemble, infrastructure_markup
from card_markup import card_figures, card_names


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


if __name__ == "__main__":
    unittest.main()
