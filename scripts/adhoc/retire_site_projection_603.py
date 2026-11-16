"""Retire only the isolated PR603 clone after merge, 2026-11-16.

Inputs: explicit CLAW root and reviewed PR head; previously preserved Git recovery.
Output: existing safe-delete tool's durable deletion receipt, or a dry-run plan.
Serves PR603 cleanup. Preserving ignored files/Git state and preflight are separate
operator steps. This wrapper never removes the archive or another checkout.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path


def stop_group_and_reap(process: subprocess.Popen) -> None:
    """Stop the owned command group and reap its leader before releasing the lease."""
    while True:
        try:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            return
        except KeyboardInterrupt:
            # A second interrupt cannot abandon an active deletion child (#608).
            continue


def run(*command: str, timeout: float = 60) -> str:
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command, output)
        return output.strip()
    except BaseException:
        stop_group_and_reap(process)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", required=True, type=Path)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    claw = args.claw_root.resolve(strict=True)
    root = Path(__file__).resolve().parents[2]
    expected = claw / ".temp/coordination-20261115/site-projection"
    if root != expected or expected.is_symlink() or root in Path.cwd().resolve().parents or Path.cwd().resolve() == root:
        raise SystemExit("Use the exact isolated task clone, from a working directory outside it")
    if not (root / ".git").is_dir() or (root / ".git").is_symlink():
        raise SystemExit("Only the standalone task clone is supported")
    archive = claw / ".temp/coordination-closeout-20261115/site-projection"
    recovery = archive / "site-recovery.git"
    if not recovery.is_dir() or recovery.is_symlink():
        raise SystemExit("Preserved Git recovery is required")
    helpers = Path.home() / ".codex/skills/safe-delete/scripts"
    sys.path[:0] = [str(claw), str(claw / "src")]
    from plugins.lock_manager import LockManager
    from plugins.repository_settings import RepositoryTarget

    with LockManager({"locks_dir": str(claw / "workspace/locks")}).lock(
        "culturebotai_site", "retire-merged-site-projection-603", timeout=300,
    ):
        RepositoryTarget("site", root, "CultureBotAI/CultureBotAI.github.io").open()
        pr = json.loads(run("gh", "pr", "view", "603", "--repo", "CultureBotAI/CultureBotAI.github.io",
                            "--json", "state,headRefOid,headRefName,isCrossRepository"))
        if (pr["state"] != "MERGED" or pr["isCrossRepository"]
                or pr["headRefOid"] != args.expected_head
                or pr["headRefName"] != "feat/public-fleet-projection-1254-20261115"):
            raise SystemExit("Exact reviewed PR merge proof is required")
        if run("git", "-C", str(root), "rev-parse", "HEAD") != args.expected_head:
            raise SystemExit("Task clone HEAD changed")
        if len(run("git", "-C", str(root), "worktree", "list", "--porcelain").split("worktree ")) != 2:
            raise SystemExit("Other linked worktrees require separate review")
        if (run("git", "-C", str(root), "status", "--porcelain", "--untracked-files=all")
                or run("git", "-C", str(root), "ls-files", "--others")):
            raise SystemExit("Preserve every untracked/ignored byte and resolve tracked changes first")
        if any(not row.startswith("H ") for row in run("git", "-C", str(root), "ls-files", "-v").splitlines()):
            raise SystemExit("Hidden index entries require separate review")
        print(run(str(helpers / "git_clone_check.sh"), str(root), str(recovery)))
        command = [str(helpers / "guarded_rm.sh"), "--expect-parent", str(root.parent),
                   "--expect-git-head", args.expected_head, "--log", str(archive / "deletions.tsv"),
                   "--note", "PR603 merged; Git and all ignored evidence preserved"]
        if not args.apply:
            command.append("--dry-run")
        print(run(*command, str(root)))
        if args.apply and root.exists():
            raise RuntimeError("Task clone remains after guarded removal")


if __name__ == "__main__":
    main()
