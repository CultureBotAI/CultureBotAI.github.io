"""Exercise pinned gap research inputs/output for #574/#575; 2026-11-14.

Inputs: temporary committed Git records and mocked GitHub metadata. Outputs:
temporary evidence JSON, verified without network access or corpus mutations.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
import research_gap_browser_20261113 as research


DISCUSSION = """id: trait:test
discussions:
- discussion_id: test-gap
  prompt: Which mechanism explains this observation?
  kind: KNOWLEDGE_GAP
  status: OPEN
"""


class GapBrowserResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "TraitMech"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "fixture")
        self.git("remote", "add", "origin", "https://github.com/CultureBotAI/TraitMech.git")

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True,
            stderr=subprocess.PIPE,
        ).strip()

    def fixture(self, files, globs):
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "Record fixture")
        self.sha = self.git("rev-parse", "HEAD")
        self.mech = {
            "display_name": "TraitMech", "github": "CultureBotAI/TraitMech",
            "record_globs": globs,
            "capabilities": {"knowledge_gap_scan": {"status": "enabled"}},
        }

    def api(self, endpoint):
        if endpoint == "repos/CultureBotAI/TraitMech":
            return {"full_name": "CultureBotAI/TraitMech", "private": False,
                    "default_branch": "main"}
        if endpoint == "repos/CultureBotAI/TraitMech/commits/main":
            return {"sha": self.sha}
        self.fail(f"Unexpected API request: {endpoint}")

    def collect(self):
        with patch.object(research, "api", side_effect=self.api):
            result = research.collect("TraitMech", self.mech, self.root)
        self.assertEqual(result["revision"], self.sha)
        return result

    def test_recursive_glob_includes_zero_and_multiple_directories_at_pin(self):
        paths = ["data/traits/root.yaml", "data/traits/ecology/deep/record.yaml"]
        self.fixture({**{p: DISCUSSION for p in paths}, "notes/outside.yaml": DISCUSSION},
                     ["data/traits/**/*.yaml"])
        # The collector must inspect the pinned commit, not these local edits.
        (self.repo / paths[0]).write_text("id: no-local-discussions\n")
        (self.repo / "data/traits/untracked.yaml").write_text(DISCUSSION)
        result = self.collect()
        self.assertEqual({s["path"] for s in result["discussion_samples"]}, set(paths))

    def test_single_star_does_not_include_nested_records(self):
        self.fixture({"data/traits/root.yaml": DISCUSSION,
                      "data/traits/nested/outside.yaml": DISCUSSION},
                     ["data/traits/*.yaml"])
        result = self.collect()
        self.assertEqual([s["path"] for s in result["discussion_samples"]],
                         ["data/traits/root.yaml"])

    def test_declared_yml_extension_is_probed(self):
        paths = ["data/traits/root.yml", "data/traits/ecology/record.yml"]
        self.fixture({**{p: DISCUSSION for p in paths},
                      "data/traits/ecology/not-declared.yaml": DISCUSSION},
                     ["data/traits/**/*.yml"])
        result = self.collect()
        self.assertEqual({s["path"] for s in result["discussion_samples"]}, set(paths))

    def test_empty_record_globs_do_not_run_a_global_probe(self):
        self.fixture({"data/traits/ecology/record.yaml": DISCUSSION}, [])
        with patch.object(research.subprocess, "run", wraps=subprocess.run) as calls:
            result = self.collect()
        self.assertEqual(result["discussion_samples"], [])
        self.assertEqual(result["sample_probe"], "not performed")
        self.assertFalse(any("grep" in call.args[0] for call in calls.call_args_list))

    def test_main_persists_native_yaml_dates_and_timestamps_as_iso_text(self):
        self.fixture({
            "data/traits/ecology/record.yaml": DISCUSSION +
                "  posed_date: 2026-11-13\n  resolved_date: 2026-11-14\n",
            "conf/kgscan_config.yaml": "generated_at: 2026-11-14T12:30:00Z\n",
        }, ["data/traits/**/*.yaml"])
        manifest = self.root / "fleet.yaml"
        manifest.write_text(yaml.safe_dump({"mechs": {"traitmech": self.mech}}))
        output = self.root / "evidence"
        argv = ["research", "--manifest", str(manifest), "--local-root", str(self.root),
                "--output", str(output), "--repo", "TraitMech"]
        with patch.object(sys, "argv", argv), patch.object(research, "api", side_effect=self.api):
            research.main()
        target = output / "TraitMech.json"
        self.assertGreater(target.stat().st_size, 0)
        result = json.loads(target.read_text())
        discussion = result["discussion_samples"][0]["discussions"][0]
        self.assertEqual(discussion["posed_date"], "2026-11-13")
        self.assertEqual(discussion["resolved_date"], "2026-11-14")
        self.assertEqual(result["configs"]["conf/kgscan_config.yaml"]["generated_at"],
                         "2026-11-14T12:30:00+00:00")

    def test_main_does_not_stringify_unsupported_yaml_values(self):
        self.fixture({"data/traits/ecology/record.yaml": DISCUSSION,
                      "conf/kgscan_config.yaml": "unexpected: !!set {a: null}\n"},
                     ["data/traits/**/*.yaml"])
        manifest = self.root / "fleet.yaml"
        manifest.write_text(yaml.safe_dump({"mechs": {"traitmech": self.mech}}))
        output = self.root / "evidence"
        argv = ["research", "--manifest", str(manifest), "--local-root", str(self.root),
                "--output", str(output), "--repo", "TraitMech"]
        with patch.object(sys, "argv", argv), patch.object(research, "api", side_effect=self.api):
            with self.assertRaises(TypeError):
                research.main()
        self.assertFalse((output / "TraitMech.json").exists())
