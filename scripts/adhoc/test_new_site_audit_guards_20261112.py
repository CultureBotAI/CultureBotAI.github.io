#!/usr/bin/env python3
"""Offline adversarial regressions for site-audit findings #567/#568, 2026-11-12.

Input: sibling audit helper; output: unittest results only. No network requests.
Transient test fixtures stay under this repository's .temp and are removed by
TemporaryDirectory after the tests; no prior evidence files are touched.
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

import audit_new_mech_sites_20261112 as audit

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://culturebotai.github.io/CofactorMech/"


class SiteAuditGuards(unittest.TestCase):
    def test_asset_url_rejects_escape_and_ambiguous_paths(self):
        for path in ("https://example.org/record.html", "//example.org/a", "/AssayMech/a",
                     "../a", "records/../a", "%2e%2e/a", "records/%2fetc", "a?x=1",
                     "a#frag", "a\\b", "a//b", "./index.html"):
            with self.subTest(path=path), self.assertRaises(AssertionError):
                audit.asset_url(SITE, path)
        self.assertEqual(audit.asset_url(SITE, "records/fad/index.html"), SITE + "records/fad/index.html")

    def test_redirect_rejects_other_host_or_sibling_before_following(self):
        request = urllib.request.Request(SITE + "index.html")
        handler = audit.SiteRedirect(SITE)
        for target in ("https://example.org/a", "https://culturebotai.github.io/AssayMech/",
                       "https://culturebotai.github.io/CofactorMech/../AssayMech/",
                       "https://culturebotai.github.io/CofactorMech/%2e%2e/AssayMech/"):
            with self.subTest(target=target), self.assertRaises(AssertionError):
                handler.redirect_request(request, None, 302, "Found", {}, target)
        redirected = handler.redirect_request(request, None, 302, "Found", {}, SITE)
        self.assertEqual(redirected.full_url, SITE)

    def test_existing_screenshot_directory_refuses_before_network(self):
        scratch = ROOT / ".temp"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="audit-guard-", dir=scratch) as directory:
            root = Path(directory)
            images = root / "screenshots"
            images.mkdir()
            previous = images / "CofactorMech-desktop.png"
            previous.write_bytes(b"existing receipt")
            argv = ["audit", "--mech", "CofactorMech", "--revision", "a" * 40,
                    "--output", str(root / "new.json"), "--screenshots", str(images)]
            with patch("sys.argv", argv), patch.object(audit, "api", side_effect=RuntimeError("Network must not run")) as api:
                with self.assertRaisesRegex(AssertionError, "new screenshot directory"):
                    audit.main()
                api.assert_not_called()
            self.assertEqual(previous.read_bytes(), b"existing receipt")
            self.assertFalse((root / "new.json").exists())


if __name__ == "__main__":
    unittest.main()
