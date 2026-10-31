"""Behavioral regression checks for Pages audit review findings #531 and #532."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/adhoc/audit_mech_pages_20261030.py"
SPEC = importlib.util.spec_from_file_location("pages_refresh_audit", SOURCE)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PagesRefreshAuditTests(unittest.TestCase):
    def test_latest_status_controls_deployment_success(self):
        for state in ("inactive", "failure", "error", "pending"):
            with self.subTest(state=state):
                self.assertFalse(AUDIT.deployment_succeeded([
                    {"state": state}, {"state": "success"},
                ]))
        self.assertFalse(AUDIT.deployment_succeeded([]))
        self.assertTrue(AUDIT.deployment_succeeded([
            {"state": "success"}, {"state": "in_progress"},
        ]))

    def test_incomplete_evidence_cannot_pass_audit(self):
        for row in (
            {"successful_deployment": {"sha": "abc"}, "live": {"error": "HTTP 404"}},
            {"successful_deployment": None, "live": {"status": 200}},
            {"successful_deployment": {"sha": "abc"}},
            {"error": "API failed"},
        ):
            with self.subTest(row=row):
                self.assertFalse(AUDIT.audit_verified(row))
        self.assertTrue(AUDIT.audit_verified({
            "successful_deployment": {"sha": "abc"}, "live": {"status": 200},
        }))
