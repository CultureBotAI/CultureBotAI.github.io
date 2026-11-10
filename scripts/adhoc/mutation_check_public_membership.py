"""Prove public-membership regression tests detect removed gates, 2026-11-10.

Inputs: site sources/tests. Output: public-membership-mutations.json beside this
script. Run under the site lease; each mutation runs in a fresh interpreter.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
mutations = [
    ('canonical_projection', 'scripts/fleet/refresh_manifest.py',
     'public = manifest.public()', 'public = manifest',
     'test_public_projection.PublicProjectionTests.test_shared_projection_removes_identity_and_distinct_artifact_contributions'),
    ('identity_guard', 'scripts/fleet/roots.py',
     '    lowered = value.strip().lower()', '    return False\n    lowered = value.strip().lower()',
     'test_public_projection.PublicProjectionTests.test_guard_uses_public_allowlist_instead_of_a_named_private_repository'),
    ('aggregate_guard', 'scripts/fleet/build_data.py',
     '    if any(not name.startswith("_") and name not in ORDER for name in cen):',
     '    if False:',
     'test_public_projection.PublicProjectionTests.test_unprojected_nonzero_census_is_refused_before_aggregation'),
    ('graph_guard', 'scripts/fleet/assemble_page.py',
     '            if any(identity not in names for identity in identities):',
     '            if False:',
     'test_public_projection.PublicProjectionTests.test_arbitrary_private_graph_endpoint_is_refused'),
]
receipts = []
for label, name, old, new, test in mutations:
    path = root / name
    before = path.read_text()
    assert old in before
    try:
        path.write_text(before.replace(old, new))
        with tempfile.TemporaryDirectory(prefix='site-public-mutation-') as cache:
            env = dict(os.environ, PYTHONPATH=str(root / 'tests'), PYTHONPYCACHEPREFIX=cache)
            run = subprocess.run([sys.executable, '-m', 'pytest', '-c', '/dev/null', 'tests/test_public_projection.py::' + test.split('.', 1)[1].replace('.', '::'), '-q'], cwd=root, env=env, capture_output=True, text=True)
        assert run.returncode != 0, label + ' survived'
        assert '1 failed' in run.stdout and 'ERROR collecting' not in run.stdout, run.stdout + run.stderr
        receipts.append({'mutation': label, 'test': test, 'exit_code': run.returncode, 'detected': True})
    finally:
        path.write_text(before)
(root / 'scripts/adhoc/public-membership-mutations.json').write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps(receipts, indent=2))
