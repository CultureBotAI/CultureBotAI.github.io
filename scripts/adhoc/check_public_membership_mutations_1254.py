"""Check site public-membership regressions in fresh pytest processes, 2026-11-15.

Inputs: this topic checkout's sources/tests; output: a new JSON receipt path.
Serves CLAW #1254/site #551 successor. --only supports one end-to-end canary.
Each changed file is restored in finally; no repository or network mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = (
    ("canonical_projection", "scripts/fleet/refresh_manifest.py", "public = manifest.public()", "public = manifest",
     "tests/test_public_projection.py::PublicProjectionTests::test_shared_projection_removes_identity_and_distinct_artifact_contributions"),
    ("identity_guard", "scripts/fleet/roots.py", "    lowered = value.strip().lower()", "    return False\n    lowered = value.strip().lower()",
     "tests/test_public_projection.py::PublicProjectionTests::test_guard_uses_public_allowlist_instead_of_a_named_private_repository"),
    ("aggregate_guard", "scripts/fleet/build_data.py", '    if any(not name.startswith("_") and name not in ORDER for name in cen):', "    if False:",
     "tests/test_public_projection.py::PublicProjectionTests::test_unprojected_nonzero_census_is_refused_before_aggregation"),
    ("graph_guard", "scripts/fleet/assemble_page.py", "            if any(identity not in names for identity in identities):", "            if False:",
     "tests/test_public_projection.py::PublicProjectionTests::test_arbitrary_private_graph_endpoint_is_refused"),
    ("audit_rows", "scripts/fleet/membership_audit.py", 'if row["repo"].lower() in allowed]', "if True]",
     "tests/test_membership_audit.py::MembershipAuditTests::test_public_projection_precedes_retained_audit_and_note_serialization"),
    ("audit_notes", "scripts/fleet/membership_audit.py", "if name.lower() in allowed}", "if True}",
     "tests/test_membership_audit.py::MembershipAuditTests::test_public_projection_precedes_retained_audit_and_note_serialization"),
    ("audit_time", "scripts/fleet/membership_audit.py", '    if observed < timestamp(rows[0]["commit_date"]):', "    if False:",
     "tests/test_membership_audit.py::MembershipAuditTests::test_observation_before_new_claw_commit_is_refused"),
    ("infrastructure_scope_evidence", "scripts/adhoc/refresh_public_membership_1254.py",
     '    infrastructure = read("_fleet/infrastructure.json")',
     '    infrastructure = read("_fleet/infrastructure.json")\n    for member in infrastructure["members"].values():\n        member["evidence_url"] = snapshot["source"]["url"]',
     "tests/test_membership_refresh.py::MembershipRefreshTests::test_new_membership_pin_retains_historical_infrastructure_evidence"),
)


def run(test: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="site-public-bytecode-") as cache:
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "tests"), PYTHONPYCACHEPREFIX=cache)
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-c", "/dev/null", test, "-q"],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", choices=[case[0] for case in CASES])
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; preserve prior evidence")
    receipts = []
    for label, relative, old, new, test in CASES:
        if args.only and args.only != label:
            continue
        path = ROOT / relative
        before = path.read_bytes()
        text = before.decode()
        if old not in text:
            raise RuntimeError(f"Mutation target changed: {label}")
        green = run(test)
        if green.returncode or "1 passed" not in green.stdout:
            raise RuntimeError(green.stdout + green.stderr)
        try:
            path.write_text(text.replace(old, new))
            red = run(test)
            if red.returncode != 1 or "1 failed" not in red.stdout or "ERROR collecting" in red.stdout:
                raise RuntimeError(f"Mutation not distinguished: {label}\n{red.stdout}\n{red.stderr}")
        finally:
            path.write_bytes(before)
        restored = run(test)
        if restored.returncode or "1 passed" not in restored.stdout or path.read_bytes() != before:
            raise RuntimeError(f"Restoration failed: {label}\n{restored.stdout}\n{restored.stderr}")
        receipts.append({"mutation": label, "test": test, "source_sha256": hashlib.sha256(before).hexdigest(),
                         "before_exit": green.returncode, "mutation_exit": red.returncode,
                         "restored_exit": restored.returncode, "restored_bytes": True})
    with args.output.open("x") as handle:
        json.dump(receipts, handle, indent=2)
        handle.write("\n")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
