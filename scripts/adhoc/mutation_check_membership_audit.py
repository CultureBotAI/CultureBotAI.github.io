"""Mutation-check audit timestamp and retained-data exclusion (#552, #553).

Input: maintained membership_audit.py and regressions. Output: mutation receipt
beside this script. Run under the site lease; fresh pytest per case. 2026-11-10.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / 'scripts/fleet/membership_audit.py'
mutations = [
    ('audit_rows', 'if row["repo"].lower() in allowed]', 'if True]',
     'test_public_projection_precedes_retained_audit_and_note_serialization'),
    ('audit_notes', 'if name.lower() in allowed}', 'if True}',
     'test_public_projection_precedes_retained_audit_and_note_serialization'),
    ('membership_timestamp', 'if observed < timestamp(rows[0]["commit_date"]):', 'if False:',
     'test_observation_before_new_claw_commit_is_refused'),
]
receipts = []
for label, old, new, test in mutations:
    before = path.read_text()
    assert old in before
    try:
        path.write_text(before.replace(old, new))
        with tempfile.TemporaryDirectory(prefix='site-audit-mutation-') as cache:
            env = dict(os.environ, PYTHONPYCACHEPREFIX=cache)
            test_id = 'tests/test_membership_audit.py::MembershipAuditTests::' + test
            run = subprocess.run([sys.executable, '-m', 'pytest', '-c', '/dev/null', test_id, '-q'],
                                 cwd=root, env=env, capture_output=True, text=True)
        assert run.returncode != 0 and '1 failed' in run.stdout and 'ERROR collecting' not in run.stdout, run.stdout + run.stderr
        receipts.append({'mutation': label, 'test': test_id, 'exit_code': run.returncode, 'detected': True})
    finally:
        path.write_text(before)
(root / 'scripts/adhoc/membership-audit-mutations.json').write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps(receipts, indent=2))
