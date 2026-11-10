"""Stage a membership-only X-Mech refresh at an immutable CLAW candidate.

Inputs: committed CLAW root and preserved site census pins. Outputs: public
manifest, infrastructure descriptions, CLAW audit pin, and assembled mechs.md.
Fleet integration PR, 2026-11-10. Default validates without writing; --apply
uses the shared transactional writer under the site's repository lease.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--claw-root', type=Path, required=True)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
claw = args.claw_root.resolve()
sys.path[:0] = [str(ROOT / 'scripts/fleet'), str(claw), str(claw / 'src')]
from kg_microbe_write import ValidatedWriteTransaction
from plugins.lock_manager import LockManager
from plugins.repository_settings import RepositorySettings, RepositoryTarget
from kg_microbe_fleet.roots import resolve_culturebotai_site_root
import roots
from refresh_manifest import read_canonical, validate
from assemble_page import assemble

resolved = resolve_culturebotai_site_root(claw_root=claw, environ={'CULTUREBOTAI_SITE_ROOT': str(ROOT)})
assert resolved == ROOT
settings = RepositorySettings({'site': RepositoryTarget('site', ROOT, 'CultureBotAI/CultureBotAI.github.io')}, {}, ('site',))
settings.get_target('site').open()


def read(name):
    return json.loads((ROOT / name).read_text())


def encoded(document):
    return json.dumps(document, indent=2, ensure_ascii=False) + '\n'


def prepare():
    snapshot = read_canonical(claw)
    revision = snapshot['source']['revision']
    infrastructure = read('_fleet/infrastructure.json')
    for name in ('CofactorMech', 'AssayMech'):
        entry = snapshot['mechs'][name]
        infrastructure['members'][name] = {
            'repository': entry['github'],
            'description': 'Newly registered repository awaiting its initial implementation.',
            'scope_note': 'The inspected default branch is empty. No scientific corpus, numeric card, graph node or Pages browser is included in this audit; corpus counts and historical repository statistics await a separate reviewed admission.',
            'corpus': None, 'site': None, 'checked_on': '2026-11-10',
            'evidence_url': snapshot['source']['url'],
        }
    notes = read('_fleet/audit_notes.json')
    notes['notes']['culturebotai-claw'] = (
        'Membership-only refresh at ' + revision + '. The public canonical projection declares '
        + str(len(snapshot['mechs'])) + ' members. CofactorMech and AssayMech have no committed corpus '
        'at their inspected default-branch tips and enter only the infrastructure listing. '
        'Existing corpus pins, figures and statistics are retained unchanged.'
    )
    audit = read('_fleet/data/site_audit.json')
    date = subprocess.check_output(['git', '-C', str(claw), 'show', '-s', '--format=%cI', revision], text=True).strip()
    for row in audit['repositories']:
        if row['repo'] == 'culturebotai-claw':
            row.update(sha=revision, commit_date=date,
                       readme_url=f'https://github.com/CultureBotAI/culturebotai-claw/blob/{revision}/README.md',
                       notes=notes['notes']['culturebotai-claw'])
    # Generate against the candidate public snapshot before promoting any file.
    previous = roots.public_names
    roots.public_names = lambda: frozenset(token.lower() for name, row in snapshot['mechs'].items()
                                          for token in (name, row['key'], row['github'], row['github'].rsplit('/', 1)[-1]))
    try:
        validate(snapshot)
        page = assemble((ROOT / '_fleet/mechs_template.md').read_text(),
                        (ROOT / '_fleet/fleet_fragment.html').read_text(),
                        read('_fleet/data/fleet_data.json'), snapshot,
                        read('_fleet/data/mech_stats.json'), read('_fleet/data/prefix_census.json'),
                        read('_fleet/data/site_features.json'), read('_fleet/data/recent_terms.json'),
                        infrastructure=infrastructure)
    finally:
        roots.public_names = previous
    return {
        '_fleet/data/manifest.json': encoded(snapshot),
        '_fleet/infrastructure.json': encoded(infrastructure),
        '_fleet/audit_notes.json': encoded(notes),
        '_fleet/data/site_audit.json': json.dumps(audit, indent=1, ensure_ascii=False) + '\n',
        'mechs.md': page,
    }


with LockManager().lock('culturebotai-site', 'refresh-public-membership'):
    changes = prepare()
    transaction = ValidatedWriteTransaction(ROOT)
    for path, text in changes.items():
        transaction.stage(path, text)
    result = transaction.commit(apply=args.apply)
    print(result)
    if args.apply:
        for path, text in changes.items():
            assert (ROOT / path).read_text() == text
        print('Verified every promoted artifact against staged bytes.')
