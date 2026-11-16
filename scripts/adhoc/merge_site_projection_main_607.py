"""Merge current site main into the reviewed PR603 topic, 2026-11-15.

Inputs: verified CLAW root, exact expected site branch/head; --apply is explicit.
Output: an ordinary merge commit under the short shared site lease for issue607.
Fetch precedes the lease; commit hooks and pushes are separate caller operations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(ROOT), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--cleanup-local", action="store_true",
                        help="After PR603 merges, detach and compare-delete only its local topic ref")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.branch in {"main", "master"} or not re.fullmatch(r"[0-9a-f]{40}", args.head):
        raise ValueError("Require an explicit topic branch and immutable expected head")
    git("check-ref-format", "--branch", args.branch)
    claw = args.claw_root.resolve(strict=True)
    sys.path[:0] = [str(claw), str(claw / "src")]
    from kg_microbe_fleet.roots import resolve_culturebotai_site_root
    from plugins.lock_manager import LockManager
    from plugins.repository_settings import RepositorySettings, RepositoryTarget

    if resolve_culturebotai_site_root(claw_root=claw, environ={"CULTUREBOTAI_SITE_ROOT": str(ROOT)}) != ROOT:
        raise ValueError("Site resolver did not return the exact checkout")
    settings = RepositorySettings({"site": RepositoryTarget(
        "site", ROOT, "CultureBotAI/CultureBotAI.github.io")}, {}, ("site",))

    def verify():
        settings.get_target("site").open()
        if git("branch", "--show-current") != args.branch or git("rev-parse", "HEAD") != args.head:
            raise ValueError("Site branch/head changed")
        if git("status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Site checkout must be clean")

    verify()
    if args.cleanup_local:
        if not (ROOT / ".git").is_dir() or (ROOT / ".git").is_symlink():
            raise ValueError("Cleanup requires this standalone clone, not a linked worktree")
        pr = json.loads(subprocess.check_output([
            "gh", "pr", "view", "603", "--repo", "CultureBotAI/CultureBotAI.github.io",
            "--json", "state,headRefName,headRefOid"], text=True))
        if (pr["state"] != "MERGED" or pr["headRefName"] != args.branch
                or pr["headRefOid"] != args.head):
            raise ValueError("Live PR603 is not merged at the exact expected branch/head")
        if not args.apply:
            print("Dry run: detach HEAD and compare-delete the merged PR603 local topic ref/config.")
            return
        locks = LockManager({"locks_dir": str(claw / "workspace" / "locks")})
        with locks.lock("culturebotai_site", "cleanup-pr603-local-ref", timeout=300):
            verify()
            git("update-ref", "--no-deref", "HEAD", args.head)
            git("update-ref", "-d", "refs/heads/" + args.branch, args.head)
            keys = [entry.split("\n", 1)[0] for entry in git("config", "--local", "--list", "--null").split("\0")]
            if any(key.startswith("branch." + args.branch + ".") for key in keys):
                git("config", "--remove-section", "branch." + args.branch)
            if git("branch", "--show-current") or git("rev-parse", "HEAD") != args.head:
                raise RuntimeError("Detached recovery HEAD verification failed")
            if git("for-each-ref", "--format=%(refname)", "refs/heads/" + args.branch):
                raise RuntimeError("Topic ref deletion verification failed")
            print("Detached recovery HEAD", args.head, "and removed local topic", args.branch)
        return
    if not args.apply:
        print("Dry run: fetch origin/main, verify state, merge normally under the shared site lease.")
        return
    git("fetch", "origin", "main")
    main_head = git("rev-parse", "FETCH_HEAD")
    locks = LockManager({"locks_dir": str(claw / "workspace" / "locks")})
    with locks.lock("culturebotai_site", "merge-pr603-main-607", timeout=300):
        verify()
        # Hooks can acquire their own leases; this metadata merge invokes none.
        git("-c", "core.hooksPath=/dev/null", "merge", "--no-edit", "--no-ff", main_head)
        git("merge-base", "--is-ancestor", main_head, "HEAD")
        if git("status", "--porcelain", "--untracked-files=all"):
            raise RuntimeError("Merge left changes; inspect before continuing")
        print("Merged main", main_head, "at", git("rev-parse", "HEAD"))


if __name__ == "__main__":
    main()
