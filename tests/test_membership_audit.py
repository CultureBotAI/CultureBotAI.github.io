"""Membership-only audit provenance and retained-data exclusion (#552, #553)."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from membership_audit import refresh_membership_audit, validate_membership_observation


class MembershipAuditTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {"source": {"revision": "a" * 40}, "mechs": {
            "PublicLab": {"key": "public_lab", "github": "Example/PublicLab"}}}
        self.audit = {
            "checked_at_utc": "2026-11-09T17:40:28+00:00",
            "local_date": "2026-11-09", "pinned_at_utc": "2026-11-09T12:41:41+00:00",
            "scope": "Earlier public and private_lab corpus observation.",
            "repositories": [
                {"repo": "PublicLab", "sha": "b" * 40, "commit_date": "2026-11-09T10:00:00Z",
                 "card_records": 2, "merged_prs": 3},
                {"repo": "private_lab", "sha": "c" * 40, "commit_date": "2026-11-09T11:00:00Z",
                 "card_records": 11, "merged_prs": 19, "notes": "PRIVATE_MARKER"},
                {"repo": "culturebotai-claw", "sha": "d" * 40,
                 "commit_date": "2026-11-09T09:00:00Z"},
            ],
        }
        self.notes = {"scope": self.audit["scope"], "notes": {
            "PublicLab": "Public evidence.", "private_lab": "PRIVATE_MARKER",
            "culturebotai-claw": "Membership-only observation.",
        }}
        self.commit_date = "2026-11-10T05:02:46Z"
        self.observed_at = "2026-11-10T06:00:00Z"

    def refresh(self, observed=None):
        return refresh_membership_audit(self.audit, self.notes, self.snapshot,
                                        self.commit_date, observed or self.observed_at)

    def test_public_projection_precedes_retained_audit_and_note_serialization(self):
        original = deepcopy((self.audit, self.notes))
        audit, notes = self.refresh()
        self.assertEqual([row["repo"] for row in audit["repositories"]],
                         ["PublicLab", "culturebotai-claw"])
        self.assertEqual(set(notes["notes"]), {"PublicLab", "culturebotai-claw"})
        self.assertEqual(sum(row.get("card_records", 0) for row in audit["repositories"]), 2)
        self.assertEqual(sum(row.get("merged_prs", 0) for row in audit["repositories"]), 3)
        output = json.dumps((audit, notes))
        self.assertNotIn("private_lab", output)
        self.assertNotIn("PRIVATE_MARKER", output)
        self.assertEqual(audit["repositories"][0], self.audit["repositories"][0])
        self.assertEqual((self.audit, self.notes), original)

    def test_membership_observation_is_separate_from_preserved_corpus_dates(self):
        audit, notes = self.refresh()
        for field in ("checked_at_utc", "pinned_at_utc", "local_date"):
            self.assertEqual(audit[field], self.audit[field])
        self.assertEqual(audit["membership_checked_at_utc"], "2026-11-10T06:00:00+00:00")
        self.assertIn("checked separately", audit["scope"])
        self.assertIn(audit["checked_at_utc"], audit["scope"])
        self.assertEqual(audit["scope"], notes["scope"])
        validate_membership_observation(audit)

    def test_observation_before_new_claw_commit_is_refused(self):
        with self.assertRaisesRegex(ValueError, "predates"):
            self.refresh("2026-11-09T18:00:00Z")

    def test_naive_membership_timestamp_is_refused(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            self.refresh("2026-11-10T06:00:00")

    def test_published_audit_has_a_valid_membership_observation(self):
        audit = json.loads((ROOT / "_fleet/data/site_audit.json").read_text())
        self.assertIn("membership_checked_at_utc", audit)
        validate_membership_observation(audit)


if __name__ == "__main__":
    unittest.main()
