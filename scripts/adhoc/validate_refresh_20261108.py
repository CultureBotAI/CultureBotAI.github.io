#!/usr/bin/env python3
"""Run every requested local gate and retain receipts for the Nov 8 refresh PR.

Inputs: final assembled worktree and immutable CLAW snapshot. Outputs: compact
validation JSON in the repository and full command logs in a supplied log dir.
2026-11-08. Commands are read-only apart from these validation artifacts.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--logs', type=Path, required=True)
    args = parser.parse_args()
    args.logs.mkdir(parents=True, exist_ok=True)
    commands = {
        'unit-tests': [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        'assembled-page': [sys.executable, 'scripts/fleet/assemble_page.py', '--check'],
        'pinned-manifest': [sys.executable, 'scripts/fleet/refresh_manifest.py', '--claw-root', str(args.snapshot / 'claw'), '--check'],
        'cards': [sys.executable, 'scripts/fleet/check_cards.py'],
        'updates': [sys.executable, 'scripts/fleet/check_updates.py'],
        'diff-whitespace': ['git', 'diff', '--check'],
    }
    receipt = {'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'snapshot': str(args.snapshot), 'commands': {}, 'production_sha256': {}}
    env = dict(os.environ, PYTHONUNBUFFERED='1')
    try:
        Path.home().joinpath('.gitconfig').read_bytes()
    except OSError:
        env['GIT_CONFIG_GLOBAL'] = '/dev/null'
        env['GIT_CONFIG_NOSYSTEM'] = '1'
    for name, command in commands.items():
        log = args.logs / (name + '.log')
        print('RUN ' + name, flush=True)
        with log.open('w') as handle:
            done = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
        content = log.read_text()
        receipt['commands'][name] = {'argv': command, 'exit_code': done.returncode,
                                     'log': str(log), 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
                                     'tail': content.splitlines()[-18:]}
        print(f'{name}: exit {done.returncode}\n' + '\n'.join(content.splitlines()[-4:]), flush=True)
    tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], env=env, text=True).split('\0')
    for name in tracked:
        if name and (name.startswith(('_fleet/data/', 'assets/fleet/')) or name in
                     ('mechs.md', '_fleet/mechs_template.md', '_fleet/fleet_fragment.html', '_fleet/audit_notes.json')):
            path = ROOT / name
            if path.is_file():
                receipt['production_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt['completed_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    destination = ROOT / '_fleet/reviews/refresh-20261108/validation.json'
    destination.write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(any(row['exit_code'] != 0 for row in receipt['commands'].values()))


if __name__ == '__main__':
    main()
