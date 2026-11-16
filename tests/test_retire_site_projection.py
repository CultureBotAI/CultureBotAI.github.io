"""Cleanup subprocess groups cannot outlive the surrounding site lease (#608)."""
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
from retire_site_projection_603 import run  # noqa: E402 - load the retained standalone helper


class CleanupProcessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="site-cleanup-process-")
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.ready = root / "ready"
        self.marker = root / "late-side-effect"
        self.parent_pid = root / "parent-pid"
        self.child = root / "child.py"
        self.child.write_text(
            "import os, sys, time\nfrom pathlib import Path\n"
            "Path(sys.argv[1]).write_text(str(os.getpid()))\n"
            "time.sleep(0.6)\nPath(sys.argv[2]).write_text('survived')\n"
        )
        self.parent = root / "parent.py"
        self.parent.write_text(
            "import os, subprocess, sys, time\nfrom pathlib import Path\n"
            "Path(sys.argv[4]).write_text(str(os.getpid()))\n"
            "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2], sys.argv[3]])\n"
            "time.sleep(60)\n"
        )
        self.command = (sys.executable, str(self.parent), str(self.child),
                        str(self.ready), str(self.marker), str(self.parent_pid))
        self.addCleanup(self.stop_fixture)

    def stop_fixture(self):
        if self.parent_pid.exists():
            try:
                os.killpg(int(self.parent_pid.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass

    def assert_child_stopped(self):
        self.assertTrue(self.ready.exists(), "Real child must have started before the stop")
        # Past the child's delayed effect: a killed shell alone cannot pass.
        time.sleep(0.8)
        self.assertFalse(self.marker.exists(), "Child survived and wrote after command failure")

    def test_timeout_stops_delayed_child_before_returning(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            run(*self.command, timeout=0.4)
        self.assert_child_stopped()

    def test_interruption_stops_delayed_child_before_returning(self):
        communicate = subprocess.Popen.communicate
        interrupted = False

        def interrupt_once(process, *args, **kwargs):
            nonlocal interrupted
            if not interrupted:
                interrupted = True
                deadline = time.monotonic() + 5
                while not self.ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(self.ready.exists(), "Child startup timed out")
                raise KeyboardInterrupt
            return communicate(process, *args, **kwargs)

        with mock.patch.object(subprocess.Popen, "communicate", interrupt_once):
            with self.assertRaises(KeyboardInterrupt):
                run(*self.command)
        self.assert_child_stopped()

    def test_success_and_nonzero_exit_keep_the_command_contract(self):
        self.assertEqual(run(sys.executable, "-c", "print('finished')"), "finished")
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            run(sys.executable, "-c", "raise SystemExit(7)")
        self.assertEqual(raised.exception.returncode, 7)


if __name__ == "__main__":
    unittest.main()
