#!/usr/bin/env python3
"""Pin and reproduce the November 9 X-Mech refresh; PR assigned after checks.

Inputs: published fleet manifest, identity-validated checkout paths, Git objects.
Outputs: isolated snapshot/revisions.json and the existing fleet pipeline products.
The shared Mech worktrees and their Git metadata are never written. 2026-11-09.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = Path.home() / "Documents/VIMSS/ontology/Mechs"
sys.path.insert(0, str(ROOT / "scripts/fleet"))
import roots


def command(args, **kwargs):
    return subprocess.check_output([str(arg) for arg in args], text=True, **kwargs).strip()


def setup_claw(args):
    claw_dir = args.snapshot / "claw"
    info = json.loads(command(["gh", "api", "repos/CultureBotAI/culturebotai-claw/commits/main"]))
    claw_sha = info["sha"]
    if not claw_dir.exists():
        subprocess.run(["git", "init", "-q", str(claw_dir)], check=True)
    subprocess.run(
        ["git", "-C", str(claw_dir), "fetch", "-q", "--depth", "1",
         "https://github.com/CultureBotAI/culturebotai-claw.git", claw_sha],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(claw_dir), "checkout", "-q", "--detach", "FETCH_HEAD"],
        check=True,
    )
    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts/fleet/refresh_manifest.py"),
         "--claw-root", str(claw_dir), "--check"],
        capture_output=True, text=True,
    )
    print(f"CLAW pinned at {claw_sha}; refresh_manifest --check exit={check.returncode}")
    if check.stdout:
        print(check.stdout.strip())
    if check.stderr:
        print(check.stderr.strip())
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/fleet/refresh_manifest.py"),
         "--claw-root", str(claw_dir)],
        check=True,
    )


def _fetch_head(github: str) -> dict:
    payload = json.loads(command(["gh", "api", f"repos/{github}/commits/main"]))
    return {
        "github": github,
        "sha": payload["sha"],
        "commit_date": payload["commit"]["committer"]["date"],
    }


def pin(args):
    destination = args.snapshot / "revisions.json"
    if destination.exists():
        raise ValueError("pins already exist; refusing to repin")
    manifest = json.loads((ROOT / "_fleet/data/manifest.json").read_text())
    mechs_map = manifest["mechs"]
    infrastructure = json.loads((ROOT / "_fleet/infrastructure.json").read_text())["members"]
    if set(mechs_map.keys()) - set(infrastructure) != set(roots.ORDER):
        raise ValueError("manifest membership differs from the unchanged census scope")

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    repos = {name: item["github"] for name, item in mechs_map.items() if name in roots.ORDER}
    repos["__claw__"] = "CultureBotAI/culturebotai-claw"

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(_fetch_head, gh): name for name, gh in repos.items()}
        for fut in concurrent.futures.as_completed(futs):
            results[futs[fut]] = fut.result()
    acquired = dt.datetime.now(dt.timezone.utc).isoformat()

    claw_sha = command(["git", "-C", args.snapshot / "claw", "rev-parse", "HEAD"])
    if results["__claw__"]["sha"] != claw_sha:
        raise ValueError("CLAW moved during setup; choose its current manifest before pinning")

    revisions = {"pinned_at_utc": acquired, "claw": claw_sha, "mechs": {}}
    for name in roots.ORDER:
        row = results[name]
        repo_name = row["github"].split("/")[1]
        revisions["mechs"][name] = {
            "repo": repo_name,
            "sha": row["sha"],
            "commit_date": row["commit_date"],
        }

    destination.write_text(json.dumps(revisions, indent=2) + "\n")
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / "pin-acquisition.json").write_text(
        json.dumps(
            {
                "started_at_utc": started,
                "completed_at_utc": acquired,
                "results": results,
                "manifest_sha256": hashlib.sha256(
                    (args.snapshot / "claw/src/kg_microbe_fleet/fleet.yaml").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(revisions, indent=2), flush=True)


def snapshot(args):
    revisions = json.loads((args.snapshot / "revisions.json").read_text())
    manifest = json.loads((ROOT / "_fleet/data/manifest.json").read_text())["mechs"]
    src_root = args.src or DEFAULT_SRC
    prev_mechs = args.snapshot.parent / "xmech-refresh-20261108" / "mechs"
    names = [args.only] if args.only else list(revisions["mechs"])
    for name in names:
        info = revisions["mechs"][name]
        github = manifest[name]["github"]
        source = src_root / name
        origin = command(["git", "-C", source, "remote", "get-url", "origin"])
        expected = "https://github.com/" + github
        if origin.removesuffix(".git") not in (expected, "git@github.com:" + github):
            raise ValueError(f"identity mismatch: {name} ({origin})")
        destination = args.snapshot / "mechs" / name
        print(f"{name}: {source} -> {destination} @ {info['sha']}", flush=True)
        if args.plan:
            continue
        if destination.exists():
            head_proc = subprocess.run(
                ["git", "-C", str(destination), "rev-parse", "--verify", "-q", "HEAD"],
                capture_output=True,
                text=True,
            )
            current_head = head_proc.stdout.strip() if head_proc.returncode == 0 else None
            if current_head == info["sha"] and roots.revision(name) == info["sha"]:
                print(f"{name}: already at pin", flush=True)
                continue
        else:
            subprocess.run(
                ["git", "clone", "-q", "--shared", "--no-checkout", str(source), str(destination)],
                check=True,
            )
            prev_obj = prev_mechs / name / ".git" / "objects"
            alt_file = destination / ".git" / "objects" / "info" / "alternates"
            if prev_obj.exists() and alt_file.exists():
                existing = alt_file.read_text().splitlines()
                if str(prev_obj) not in existing:
                    alt_file.write_text("\n".join(existing + [str(prev_obj)]) + "\n")
                prev_clone = prev_mechs / name
                if command(["git", "-C", prev_clone, "rev-parse", "--is-shallow-repository"]) == "false":
                    shallow_file = destination / ".git" / "shallow"
                    if shallow_file.exists():
                        subprocess.run(
                            ["git", "-C", str(destination), "fetch", "-q", "--unshallow", str(prev_clone)],
                            check=True,
                        )
        present = subprocess.run(
            ["git", "-C", str(destination), "cat-file", "-e", info["sha"] + "^{commit}"],
            capture_output=True,
        )
        if present.returncode:
            subprocess.run(
                ["git", "-C", str(destination), "fetch", "-q", expected + ".git", info["sha"]],
                check=True,
            )
        sparse = roots._record_dirs(name) + ["src"]
        if name == "HabitatMech":
            sparse.append("pages/habitats")
        subprocess.run(
            ["git", "-C", str(destination), "sparse-checkout", "set", "--cone", *sparse],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(destination), "checkout", "-q", "--detach", info["sha"]],
            check=True,
        )
        actual = roots.revision(name)
        if actual != info["sha"]:
            raise ValueError(f"{name}: expected {info['sha']}, got {actual}")
        print(
            f"VERIFIED {name}: {roots.record_count(name):,} logical records at clean pin",
            flush=True,
        )


def worker(args):
    module = importlib.import_module(args.stage)
    if args.only:
        if args.stage != "prefix_census":
            raise ValueError("single-unit canary supported only for the census")
        module.ORDER = [args.only]
    raise SystemExit(module.main())


def history(args):
    """Complete clone-only history before deriving record addition dates."""
    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]
    for name, row in pins.items():
        if args.only and name != args.only:
            continue
        clone = args.snapshot / "mechs" / name
        if command(["git", "-C", clone, "rev-parse", "--is-shallow-repository"]) == "true":
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(clone),
                    "fetch",
                    "-q",
                    "--unshallow",
                    "https://github.com/CultureBotAI/" + row["repo"] + ".git",
                    row["sha"],
                ],
                check=True,
            )
        if command(["git", "-C", clone, "rev-parse", "--is-shallow-repository"]) != "false":
            raise ValueError(f"{name}: incomplete history")
        if command(["git", "-C", clone, "rev-parse", "HEAD"]) != row["sha"]:
            raise ValueError(f"{name}: moved pin")
        print(f"VERIFIED full history at unchanged {name} pin", flush=True)


def stage(args):
    outputs = {
        "prefix_census": "prefix_census",
        "build_subsets": "subsets_summary",
        "build_cells": "cells_summary",
        "recent_terms": "recent_terms",
        "build_data": "fleet_data",
        "mech_stats": "mech_stats",
    }
    if args.stage not in outputs:
        raise ValueError("unknown pipeline stage")
    log = args.snapshot / (args.stage + ("-canary" if args.only else "") + ".log")
    invocation = [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--snapshot",
        str(args.snapshot),
        "--stage",
        args.stage,
    ]
    if args.only:
        invocation += ["--only", args.only]
    with log.open("w") as handle:
        result = subprocess.run(invocation, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        print("\n".join(log.read_text().splitlines()[-30:]))
        raise SystemExit(result.returncode)
    path = ROOT / "_fleet/data" / (outputs[args.stage] + ".json")
    payload = json.loads(path.read_text())
    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]
    expected = {name: row["sha"] for name, row in pins.items() if not args.only or name == args.only}
    if "_revisions" in payload and payload["_revisions"] != expected:
        raise ValueError(f"{args.stage}: revision mismatch")
    if args.stage in ("mech_stats", "recent_terms"):
        if {m["mech"]: m["source_revision"] for m in payload["mechs"]} != expected:
            raise ValueError(f"{args.stage}: statistics revision mismatch")
    if args.stage == "build_cells":
        for key, row in payload["cells"].items():
            asset = ROOT / "assets/fleet/cells" / (key.replace("|", "--") + ".json")
            if hashlib.sha256(asset.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"cell asset differs: {key}")
    print(f"VERIFIED {args.stage}: {path.stat().st_size:,} bytes; log {log}", flush=True)
    print("\n".join(log.read_text().splitlines()[-5:]), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=["setup_claw", "pin", "snapshot", "worker", "stage", "verify", "history"],
    )
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--only")
    parser.add_argument("--stage")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    os.environ["MECHS_ROOT"] = str(args.snapshot / "mechs")
    os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"
    os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
    if args.stage != "mech_stats" and args.operation not in ("setup_claw", "pin"):
        os.environ["XDG_CONFIG_HOME"] = "/tmp"
    os.environ["PYTHONUNBUFFERED"] = "1"
    roots.MECHS_ROOT = os.environ["MECHS_ROOT"]
    if args.operation == "verify":
        for name, row in json.loads((args.snapshot / "revisions.json").read_text())["mechs"].items():
            actual = roots.revision(name)
            if actual != row["sha"]:
                raise ValueError(f"{name}: {actual} != {row['sha']}")
            print(f"VERIFIED {name} {actual} {roots.record_count(name):,} records", flush=True)
    else:
        globals()[args.operation](args)


if __name__ == "__main__":
    main()
