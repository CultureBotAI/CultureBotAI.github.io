"""A membership-only refresh cannot rewrite a dated scope observation (#604)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
from refresh_public_membership_1254 import prepare_refresh


class MembershipRefreshTests(unittest.TestCase):
    def test_new_membership_pin_retains_historical_infrastructure_evidence(self):
        snapshot = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
        infrastructure_path = ROOT / "_fleet/infrastructure.json"
        before = infrastructure_path.read_bytes()
        infrastructure = json.loads(before)
        member = infrastructure["members"]["EdgeMech"]
        original = member["evidence_url"]
        snapshot["source"]["revision"] = "f" * 40
        snapshot["source"]["url"] = (
            "https://github.com/CultureBotAI/culturebotai-claw/blob/"
            + "f" * 40 + "/src/kg_microbe_fleet/fleet.yaml"
        )
        self.assertNotEqual(original, snapshot["source"]["url"])
        changes = prepare_refresh(snapshot, "2026-11-20T08:00:00Z", "2026-11-20T09:00:00Z")
        self.assertEqual(set(changes), {
            "_fleet/data/manifest.json", "_fleet/audit_notes.json",
            "_fleet/data/site_audit.json", "mechs.md",
        })
        self.assertEqual(json.loads(changes["_fleet/data/manifest.json"])["source"], snapshot["source"])
        self.assertIn(original, changes["mechs.md"])
        self.assertIn(member["checked_on"], changes["mechs.md"])
        self.assertIn(snapshot["source"]["url"], changes["mechs.md"])
        self.assertEqual(infrastructure_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
