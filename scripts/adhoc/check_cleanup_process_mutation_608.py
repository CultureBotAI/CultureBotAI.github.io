"""Verify cleanup stops a real delayed child on timeout for site #608, 2026-11-16.

Input: cleanup wrapper and subprocess regression; output: a new JSON receipt.
Temporarily restore the old check_output behavior, then restore exact source bytes.
Only disposable test subprocesses run; no checkout or real file cleanup is invoked.
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
RELATIVE = "scripts/adhoc/retire_site_projection_603.py"
TEST = "tests/test_retire_site_projection.py::CleanupProcessTests::test_timeout_stops_delayed_child_before_returning"


def check() -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="cleanup-mutation-bytecode-") as cache:
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-c", "/dev/null", "-q", TEST],
            cwd=ROOT, env={**os.environ, "PYTHONPYCACHEPREFIX": cache},
            capture_output=True, text=True, timeout=60,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve prior receipts; choose a new path")
    path = ROOT / RELATIVE
    original = path.read_bytes()
    text = original.decode()
    start = text.index("    process = subprocess.Popen(", text.index("def run("))
    end = text.index("\n\ndef main()", start)
    old = text[:start] + "    return subprocess.check_output(command, text=True, timeout=timeout).strip()\n" + text[end:]
    green = check()
    if green.returncode or "1 passed" not in green.stdout:
        raise RuntimeError(green.stdout + green.stderr)
    try:
        path.write_text(old)
        red = check()
        if (red.returncode != 1 or "1 failed" not in red.stdout
                or "Child survived and wrote after command failure" not in red.stdout):
            raise RuntimeError("Old behavior was not distinguished: " + red.stdout + red.stderr)
    finally:
        path.write_bytes(original)
    restored = check()
    if restored.returncode or "1 passed" not in restored.stdout or path.read_bytes() != original:
        raise RuntimeError("Restoration failed: " + restored.stdout + restored.stderr)
    receipt = {
        "source": RELATIVE, "test": TEST,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "old_behavior_sha256": hashlib.sha256(old.encode()).hexdigest(),
        "green_exit": green.returncode, "red_exit": red.returncode,
        "restored_exit": restored.returncode, "restored_bytes": True,
        "failure": red.stdout,
    }
    with args.output.open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print("Verified cleanup child shutdown: green/red/green and exact source restoration")


if __name__ == "__main__":
    main()
