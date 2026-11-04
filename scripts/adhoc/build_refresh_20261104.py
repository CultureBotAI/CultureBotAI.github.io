#!/usr/bin/env python3
"""Pin and reproduce the November 4 X-Mech refresh; PR assigned after checks.

Inputs: published fleet inventory, identity-validated checkout paths, Git objects.
Outputs: isolated snapshot/revisions.json and the existing fleet pipeline products.
The shared Mech worktrees and their Git metadata are never written. 2026-11-04.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import roots


def command(args, **kwargs):
    return subprocess.check_output([str(arg) for arg in args], text=True, **kwargs).strip()


def pin(args):
    destination = args.snapshot / "revisions.json"
    if destination.exists():
        raise ValueError("pins already exist; refusing to repin")
    inventory = json.loads(args.inventory.read_text())
    if {m['display_name'] for m in inventory} != set(roots.ORDER):
        raise ValueError("manifest membership differs from the unchanged census scope")
    queries = []
    for index, item in enumerate(inventory):
        owner, repo = item['github'].split('/')
        queries.append(f'r{index}:repository(owner:{json.dumps(owner)},name:{json.dumps(repo)})'
                       '{nameWithOwner defaultBranchRef{name target{oid ... on Commit{committedDate}}}}')
    queries.append('claw:repository(owner:"CultureBotAI",name:"culturebotai-claw")'
                   '{nameWithOwner defaultBranchRef{name target{oid ... on Commit{committedDate}}}}')
    query = 'query {' + ' '.join(queries) + '}'
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    response = json.loads(command(['gh', 'api', 'graphql', '-f', 'query=' + query]))
    acquired = dt.datetime.now(dt.timezone.utc).isoformat()
    if response.get('errors'):
        raise ValueError(response['errors'])
    data = response['data']
    claw_sha = command(['git', '-C', args.snapshot / 'claw', 'rev-parse', 'HEAD'])
    if data['claw']['defaultBranchRef']['target']['oid'] != claw_sha:
        raise ValueError('CLAW moved during setup; choose its current manifest before pinning')
    revisions = {'pinned_at_utc': acquired, 'claw': claw_sha, 'mechs': {}}
    for index, item in enumerate(inventory):
        row = data[f'r{index}']
        if row['nameWithOwner'].lower() != item['github'].lower() or row['defaultBranchRef']['name'] != 'main':
            raise ValueError(f"unexpected identity/default branch: {item['github']}")
        commit = row['defaultBranchRef']['target']
        revisions['mechs'][item['display_name']] = {
            'repo': item['github'].split('/')[1], 'sha': commit['oid'], 'commit_date': commit['committedDate']}
    destination.write_text(json.dumps(revisions, indent=2) + '\n')
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / 'pin-acquisition.json').write_text(json.dumps({
        'started_at_utc': started, 'completed_at_utc': acquired, 'query': query,
        'response': response, 'manifest_sha256': hashlib.sha256(
            (args.snapshot / 'claw/src/kg_microbe_fleet/fleet.yaml').read_bytes()).hexdigest()}, indent=2) + '\n')
    print(json.dumps(revisions, indent=2), flush=True)


def snapshot(args):
    revisions = json.loads((args.snapshot / 'revisions.json').read_text())
    targets = {}
    for line in args.targets.read_text().splitlines():
        key, name, github, env_var, path = line.split('\t')
        if not path:
            raise ValueError(f'unconfigured source: {name}')
        targets[name] = (github, Path(path))
    names = [args.only] if args.only else list(revisions['mechs'])
    for name in names:
        info = revisions['mechs'][name]
        github, source = targets[name]
        origin = command(['git', '-C', source, 'remote', 'get-url', 'origin'])
        expected = 'https://github.com/' + github
        if origin.removesuffix('.git') not in (expected, 'git@github.com:' + github):
            raise ValueError(f'identity mismatch: {name}')
        destination = args.snapshot / 'mechs' / name
        print(f"{name}: {source} -> {destination} @ {info['sha']}", flush=True)
        if args.plan:
            continue
        if destination.exists():
            if command(['git', '-C', destination, 'rev-parse', 'HEAD']) != info['sha']:
                raise ValueError(f'existing snapshot at different revision: {name}')
            print(f'{name}: already at pin', flush=True)
            continue
        subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(source), str(destination)], check=True)
        present = subprocess.run(['git', '-C', str(destination), 'cat-file', '-e', info['sha'] + '^{commit}'], capture_output=True)
        if present.returncode:
            subprocess.run(['git', '-C', str(destination), 'fetch', '-q', expected + '.git', info['sha']], check=True)
        sparse = roots._record_dirs(name) + ['src']
        if name == 'HabitatMech':
            sparse.append('pages/habitats')
        subprocess.run(['git', '-C', str(destination), 'sparse-checkout', 'set', '--cone', *sparse], check=True)
        subprocess.run(['git', '-C', str(destination), 'checkout', '-q', '--detach', info['sha']], check=True)
        actual = roots.revision(name)
        if actual != info['sha']:
            raise ValueError(f'{name}: expected {info["sha"]}, got {actual}')
        print(f'VERIFIED {name}: {roots.record_count(name):,} logical records at clean pin', flush=True)


def worker(args):
    module = importlib.import_module(args.stage)
    if args.only:
        if args.stage != 'prefix_census':
            raise ValueError('single-unit canary supported only for the census')
        module.ORDER = [args.only]
    raise SystemExit(module.main())


def history(args):
    """Complete clone-only history before deriving record addition dates."""
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    for name, row in pins.items():
        if args.only and name != args.only:
            continue
        clone = args.snapshot / 'mechs' / name
        if command(['git', '-C', clone, 'rev-parse', '--is-shallow-repository']) == 'true':
            subprocess.run(['git', '-C', str(clone), 'fetch', '-q', '--unshallow',
                            'https://github.com/CultureBotAI/' + row['repo'] + '.git', row['sha']], check=True)
        if command(['git', '-C', clone, 'rev-parse', '--is-shallow-repository']) != 'false':
            raise ValueError(f'{name}: incomplete history')
        if command(['git', '-C', clone, 'rev-parse', 'HEAD']) != row['sha']:
            raise ValueError(f'{name}: moved pin')
        print(f'VERIFIED full history at unchanged {name} pin', flush=True)


def stage(args):
    outputs = {'prefix_census': 'prefix_census', 'build_subsets': 'subsets_summary',
               'build_cells': 'cells_summary', 'recent_terms': 'recent_terms',
               'build_data': 'fleet_data', 'mech_stats': 'mech_stats'}
    if args.stage not in outputs:
        raise ValueError('unknown pipeline stage')
    log = args.snapshot / (args.stage + ('-canary' if args.only else '') + '.log')
    invocation = [sys.executable, str(Path(__file__).resolve()), 'worker', '--snapshot', str(args.snapshot), '--stage', args.stage]
    if args.only:
        invocation += ['--only', args.only]
    with log.open('w') as handle:
        result = subprocess.run(invocation, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join(log.read_text().splitlines()[-30:]))
        raise SystemExit(result.returncode)
    path = ROOT / '_fleet/data' / (outputs[args.stage] + '.json')
    payload = json.loads(path.read_text())
    pins = json.loads((args.snapshot / 'revisions.json').read_text())['mechs']
    expected = {name: row['sha'] for name, row in pins.items() if not args.only or name == args.only}
    if '_revisions' in payload and payload['_revisions'] != expected:
        raise ValueError(f'{args.stage}: revision mismatch')
    if args.stage in ('mech_stats', 'recent_terms'):
        if {m['mech']: m['source_revision'] for m in payload['mechs']} != expected:
            raise ValueError(f'{args.stage}: statistics revision mismatch')
    if args.stage == 'build_cells':
        for key, row in payload['cells'].items():
            asset = ROOT / 'assets/fleet/cells' / (key.replace('|', '--') + '.json')
            if hashlib.sha256(asset.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'cell asset differs: {key}')
    print(f'VERIFIED {args.stage}: {path.stat().st_size:,} bytes; log {log}', flush=True)
    print('\n'.join(log.read_text().splitlines()[-5:]), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['pin', 'snapshot', 'worker', 'stage', 'verify', 'history'])
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--targets', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--only')
    parser.add_argument('--stage')
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    os.environ['MECHS_ROOT'] = str(args.snapshot / 'mechs')
    os.environ['GIT_CONFIG_GLOBAL'] = '/dev/null'
    os.environ['GIT_CONFIG_NOSYSTEM'] = '1'
    os.environ['PYTHONUNBUFFERED'] = '1'
    roots.MECHS_ROOT = os.environ['MECHS_ROOT']
    if args.operation == 'verify':
        for name, row in json.loads((args.snapshot / 'revisions.json').read_text())['mechs'].items():
            actual = roots.revision(name)
            if actual != row['sha']:
                raise ValueError(f'{name}: {actual} != {row["sha"]}')
            print(f'VERIFIED {name} {actual} {roots.record_count(name):,} records', flush=True)
    else:
        globals()[args.operation](args)


if __name__ == '__main__':
    main()
