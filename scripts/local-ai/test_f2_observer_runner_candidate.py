import json
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import f2_observer_runner_candidate as f2


ZONE = ZoneInfo("America/Vancouver")
START = datetime(2026, 10, 17, 1, 10, tzinfo=ZONE).timestamp()


def result():
    return {
        "schema": "aster-read-only-archive-timing.v1", "state": "complete",
        "date": "2026_10_17", "admission_receipt_written": False,
        "archives": [{"vmid": vmid, "volid": f"backups:backup/vzdump-lxc-{vmid}.tar.zst",
                      "size": 100, "ctime": 1, "test_started_epoch": 2,
                      "test_finished_epoch": 3, "test_elapsed_ms": 1000, "test_exit": 0}
                     for vmid in ("104", "110", "116")],
    }


class F2ObserverRunnerTests(unittest.TestCase):
    def test_fixed_start_window_and_deadline(self):
        self.assertEqual(f2._window(START), 1200)
        with self.assertRaises(f2.F2NoGo):
            f2._window(START - 60)
        with self.assertRaises(f2.F2NoGo):
            f2._window(START + 600)
        self.assertLessEqual(f2._window(START + 9 * 60), 1200)

    def test_truenas_schedules_and_busy_state(self):
        tasks = [{"id": i, "enabled": True,
                  "schedule": {"hour": h, "minute": m},
                  "job": {"state": "SUCCESS"}}
                 for i, (h, m) in f2.TRUENAS_SCHEDULES.items()]
        runner = lambda _command, _timeout: (0, json.dumps(tasks))
        f2._quiet_truenas(runner)
        tasks[1]["job"]["state"] = "RUNNING"
        with self.assertRaises(f2.F2NoGo):
            f2._quiet_truenas(runner)
        tasks[1]["job"]["state"] = "SUCCESS"
        tasks[0]["schedule"]["hour"] = 2
        with self.assertRaises(f2.F2NoGo):
            f2._quiet_truenas(runner)

    def test_pinned_file_custody_hash_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manual"
            path.write_bytes(b"candidate")
            path.chmod(0o750)
            digest = hashlib.sha256(b"candidate").hexdigest()
            owner = {"expected_uid": os.getuid(), "expected_gid": os.getgid()}
            f2._pinned_regular(path, digest, 0o750, 1024, **owner)
            path.chmod(0o777)
            with self.assertRaises(f2.F2NoGo):
                f2._pinned_regular(path, digest, 0o750, 1024, **owner)
            path.chmod(0o750)
            with self.assertRaises(f2.F2NoGo):
                f2._pinned_regular(path, "0" * 64, 0o750, 1024, **owner)
            alias = Path(directory) / "alias"
            alias.symlink_to(path)
            with self.assertRaises(OSError):
                f2._pinned_regular(alias, digest, 0o750, 1024, **owner)

    def test_host_load_and_competing_process_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(f2.os, "getloadavg", return_value=(4.1, 0, 0)):
                with self.assertRaisesRegex(f2.F2NoGo, "load"):
                    f2._quiet_host(root)
            process = root / "123"
            process.mkdir()
            (process / "comm").write_text("vzdump\n")
            with patch.object(f2.os, "getloadavg", return_value=(0.5, 0, 0)):
                with self.assertRaisesRegex(f2.F2NoGo, "competing"):
                    f2._quiet_host(root)

    def test_lease_gate_refuses_before_child_launch(self):
        with patch.object(f2.os, "geteuid", return_value=0), \
                patch.object(f2, "_pinned_regular"), \
                patch.object(f2, "_no_lease_or_receipt", side_effect=f2.F2NoGo("active lease")), \
                patch.object(f2.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(f2.F2NoGo, "active lease"):
                f2.observe_once(runner=lambda *_: (0, "[]"), clock=lambda: START, popen=popen)
            popen.assert_not_called()

    def test_projection_rejects_receipt_claim_and_extra_data(self):
        self.assertEqual(len(f2._project(json.dumps(result()))["archives"]), 3)
        bad = result()
        bad["admission_receipt_written"] = True
        with self.assertRaises(f2.F2NoGo):
            f2._project(json.dumps(bad))
        bad = result()
        bad["archives"][0]["path"] = "private"
        with self.assertRaises(f2.F2NoGo):
            f2._project(json.dumps(bad))
        bad = result()
        bad["archives"][1]["test_exit"] = 1
        with self.assertRaises(f2.F2NoGo):
            f2._project(json.dumps(bad))

    def test_no_child_spawn_without_source_and_job_gates(self):
        with patch.object(f2.os, "geteuid", return_value=0), \
                patch.object(f2, "_pinned_regular", side_effect=f2.F2NoGo("old manual")), \
                patch.object(f2, "_no_lease_or_receipt"), \
                patch.object(f2, "_quiet_host"), \
                patch.object(f2, "_quiet_truenas"), \
                patch.object(f2.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(f2.F2NoGo, "old manual"):
                f2.observe_once(runner=lambda *_: (0, "[]"), clock=lambda: START, popen=popen)
            popen.assert_not_called()

    def test_one_shot_passes_isolated_child_and_no_receipt(self):
        class FakeProcess:
            returncode = 0
            def communicate(self, timeout):
                self.timeout = timeout
                return json.dumps(result()).encode(), b""
        created = []
        def popen(*args, **kwargs):
            created.append((args, kwargs))
            return FakeProcess()
        with patch.object(f2.os, "geteuid", return_value=0), \
                patch.object(f2, "_pinned_regular"), \
                patch.object(f2, "_no_lease_or_receipt"), \
                patch.object(f2, "_quiet_host"), \
                patch.object(f2, "_quiet_truenas"):
            output = f2.observe_once(runner=lambda *_: (0, "[]"), clock=lambda: START, popen=popen)
        self.assertFalse(output["admission_receipt_written"])
        self.assertEqual(len(created), 1)
        self.assertTrue(created[0][1]["start_new_session"])
        self.assertEqual(created[0][1]["stderr"], subprocess.DEVNULL)

    def test_timeout_kills_child_group_and_returns_no_go(self):
        class FakeProcess:
            pid = 1904
            returncode = None
            def communicate(self, timeout):
                raise subprocess.TimeoutExpired("observer", timeout)
        with patch.object(f2.os, "geteuid", return_value=0), \
                patch.object(f2, "_pinned_regular"), \
                patch.object(f2, "_no_lease_or_receipt"), \
                patch.object(f2, "_quiet_host"), \
                patch.object(f2, "_quiet_truenas"), \
                patch.object(f2, "_terminate_group") as kill:
            with self.assertRaisesRegex(f2.F2NoGo, "external wall deadline"):
                f2.observe_once(runner=lambda *_: (0, "[]"), clock=lambda: START, popen=lambda *_a, **_k: FakeProcess())
            kill.assert_called_once()

    def test_failed_child_reaps_its_group_before_no_go(self):
        class FakeProcess:
            pid = 1904
            returncode = 1
            def communicate(self, timeout):
                return b"{\"state\":\"no_go\"}", b""
        with patch.object(f2.os, "geteuid", return_value=0), \
                patch.object(f2, "_pinned_regular"), \
                patch.object(f2, "_no_lease_or_receipt"), \
                patch.object(f2, "_quiet_host"), \
                patch.object(f2, "_quiet_truenas"), \
                patch.object(f2, "_terminate_group") as kill:
            with self.assertRaisesRegex(f2.F2NoGo, "observer failed"):
                f2.observe_once(runner=lambda *_: (0, "[]"), clock=lambda: START,
                                popen=lambda *_a, **_k: FakeProcess())
            kill.assert_called_once()

    def test_real_process_group_termination_stops_child_heartbeat(self):
        # Safe synthetic process only. Re-run on target Linux before release;
        # the live archive observer and zstd are never started by this test.
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / "heartbeat"
            child_code = (
                "import pathlib,time; p=pathlib.Path(" + repr(str(heartbeat)) + "); "
                "\nwhile True: p.write_text(str(time.time_ns())); time.sleep(.05)"
            )
            parent_code = (
                "import subprocess,sys,time; "
                "subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "], "
                "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
                "print('ready',flush=True); time.sleep(30)"
            )
            parent = subprocess.Popen(
                [sys.executable, "-c", parent_code], stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, start_new_session=True,
            )
            try:
                self.assertEqual(parent.stdout.readline().strip(), b"ready")
                for _ in range(40):
                    if heartbeat.exists():
                        break
                    time.sleep(.025)
                self.assertTrue(heartbeat.exists())
                f2._terminate_group(parent)
                before = heartbeat.read_text()
                time.sleep(.2)
                self.assertEqual(heartbeat.read_text(), before)
            finally:
                try:
                    os.killpg(parent.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                parent.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
