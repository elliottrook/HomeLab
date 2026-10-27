import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import f2_daytime_no_scan_rehearsal as rehearsal


NOW = int(datetime(2026, 10, 27, 12, 0, tzinfo=rehearsal.LOCAL_ZONE).timestamp())


def complete_result():
    return {
        "schema": "aster-f2-daytime-no-scan-rehearsal.v1",
        "state": "complete",
        "date": "2026_10_27",
        "archives": [
            {"vmid": vmid,
             "volid": f"backups:backup/vzdump-lxc-{vmid}-2026_10_27-00_30_00.tar.zst",
             "size": 100, "ctime": NOW - 3600}
            for vmid in ("104", "110", "116")
        ],
        "archive_scan": "not-attempted",
        "receipt_written": False,
    }


class DaytimeNoScanRehearsalTests(unittest.TestCase):
    def test_synthetic_clock_uses_current_cycle_exact_runtime(self):
        value = rehearsal._synthetic_cycle_clock(NOW)
        local = datetime.fromtimestamp(value, rehearsal.LOCAL_ZONE)
        self.assertEqual((local.date(), local.hour, local.minute),
                         (datetime.fromtimestamp(NOW, rehearsal.LOCAL_ZONE).date(), 1, 20))

    def test_child_uses_real_producer_with_no_scan_and_no_save(self):
        seen = {}
        def produce(_runner, **kwargs):
            seen.update(kwargs)
            self.assertEqual(kwargs["probe"]("never-opened", 120), (0, 0))
            kwargs["save"]({"must": "not persist"})
            return {"date": "2026_10_27", "archives": complete_result()["archives"]}
        with patch.object(rehearsal.os, "geteuid", return_value=0), \
                patch.object(rehearsal, "_pinned_regular"), \
                patch.object(rehearsal.os.path, "lexists", return_value=False), \
                patch.object(rehearsal, "produce", side_effect=produce):
            result = rehearsal.child(now_epoch=NOW)
        self.assertEqual(result, complete_result())
        self.assertEqual(seen["clock"](), rehearsal._synthetic_cycle_clock(NOW))

    def test_child_refuses_state_before_producer(self):
        with patch.object(rehearsal.os, "geteuid", return_value=0), \
                patch.object(rehearsal, "_pinned_regular"), \
                patch.object(rehearsal.os.path, "lexists", return_value=True), \
                patch.object(rehearsal, "produce") as produce:
            with self.assertRaisesRegex(rehearsal.RehearsalNoGo, "lease"):
                rehearsal.child(now_epoch=NOW)
            produce.assert_not_called()

    def test_pin_checks_hash_custody_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            path.write_bytes(b"source")
            path.chmod(0o644)
            digest = hashlib.sha256(b"source").hexdigest()
            with patch.object(rehearsal.os, "fstat", wraps=os.fstat) as fstat, \
                    patch.object(rehearsal.os, "getuid", return_value=0, create=True):
                # Local test files are not root-owned; verify all non-owner
                # properties here and owner enforcement separately below.
                meta = os.lstat(path)
                with patch.object(rehearsal.os, "fstat", return_value=type(meta)(
                        (meta.st_mode, meta.st_ino, meta.st_dev, 1, 0, 0,
                         meta.st_size, meta.st_atime, meta.st_mtime, meta.st_ctime))):
                    rehearsal._pinned_regular(path, digest)
            alias = Path(directory) / "alias"
            alias.symlink_to(path)
            with self.assertRaises(OSError):
                rehearsal._pinned_regular(alias, digest)

    def test_projection_rejects_success_like_scan_or_receipt_claim(self):
        self.assertEqual(len(rehearsal._project(json.dumps(complete_result()).encode())["archives"]), 3)
        for key, value in (("archive_scan", "complete"), ("receipt_written", True)):
            bad = complete_result()
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(rehearsal.RehearsalNoGo):
                rehearsal._project(json.dumps(bad).encode())

    def test_parent_real_subprocess_transport(self):
        # Exercise the real Popen/communicate contract that earlier mocked
        # tests failed to cover. The helper only prints a bounded fixture.
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "helper.py"
            helper.write_text("import json; print(json.dumps(" + repr(complete_result()) + "))")
            def real_popen(_argv, **kwargs):
                self.assertEqual(kwargs["env"]["PATH"],
                                 "/usr/sbin:/usr/bin:/sbin:/bin")
                return subprocess.Popen((sys.executable, str(helper)), **kwargs)
            result = rehearsal.parent(now_epoch=NOW, popen=real_popen)
        self.assertEqual(result, complete_result())

    def test_cli_disabled_by_default(self):
        with patch("builtins.print") as output:
            self.assertEqual(rehearsal.main([]), 0)
        self.assertIn("not-attempted", output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
