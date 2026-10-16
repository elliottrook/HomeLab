import io
import json
import os
import tempfile
import unittest
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import retained_archive_timing_observer as observer
from host_exclusion import HostExclusionError, host_exclusion


class ReadOnlyTimingTests(unittest.TestCase):
    def test_observer_disables_receipt_writer_and_projects_only_timing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(observer, "RECEIPT_PATH", Path(directory) / "archive-integrity.json"), \
                    patch.object(observer.os, "geteuid", return_value=0), \
                    patch.object(observer, "host_exclusion", return_value=nullcontext()) as exclusion, \
                    patch.object(observer, "produce", return_value={
                        "date": "2026_10_17", "archives": [{
                            "vmid": vmid, "volid": f"backups:backup/vzdump-lxc-{vmid}.tar.zst",
                            "size": 100, "ctime": 10, "test_started_epoch": 20,
                            "test_finished_epoch": 30, "test_elapsed_ms": 10000,
                            "test_exit": 0, "path": "must-not-print",
                        } for vmid in ("104", "110", "116")],
                    }) as scan:
                result = observer.observe(clock=lambda: 20)
                scan.call_args.kwargs["save"]({"synthetic": True})
                exclusion.assert_called_once_with(Path(directory))
            self.assertEqual(len(result["archives"]), 3)
            self.assertFalse(result["admission_receipt_written"])
            self.assertNotIn("must-not-print", json.dumps(result))
            self.assertFalse((Path(directory) / "archive-integrity.json").exists())

    def test_nonroot_or_any_lease_refuses_before_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(observer, "RECEIPT_PATH", root / "archive-integrity.json"), \
                    patch.object(observer, "host_exclusion", return_value=nullcontext()), \
                    patch.object(observer, "produce") as scan:
                with patch.object(observer.os, "geteuid", return_value=501), \
                        self.assertRaises(PermissionError):
                    observer.observe()
                for path in (
                    root / "lease.json", root / "lease.lock",
                    root / "application-b60" / "application-b60.json",
                    root / "application-b60" / "application-b60.lock",
                ):
                    with self.subTest(path=path.name):
                        path.parent.mkdir(exist_ok=True)
                        path.write_text("synthetic")
                        with patch.object(observer.os, "geteuid", return_value=0), \
                                self.assertRaises(RuntimeError):
                            observer.observe()
                        path.unlink()
                (root / "lease.lock").symlink_to("missing-lock")
                with patch.object(observer.os, "geteuid", return_value=0), \
                        self.assertRaises(RuntimeError):
                    observer.observe()
                scan.assert_not_called()

    def test_failed_observation_prints_only_bounded_error_class(self):
        output = io.StringIO()
        with patch.object(observer, "observe", side_effect=RuntimeError("private-path")), \
                redirect_stdout(output):
            self.assertEqual(observer.main(), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["state"], "no_go")
        self.assertEqual(result["error_class"], "RuntimeError")
        self.assertNotIn("private-path", output.getvalue())

    def test_scan_holds_common_exclusion_until_produce_returns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def scan(*_args, **_kwargs):
                with self.assertRaises(HostExclusionError):
                    with host_exclusion(root):
                        pass
                return {"date": "2026_10_16", "archives": []}
            gate_os = SimpleNamespace(geteuid=lambda: 0, path=os.path)
            with patch.object(observer, "RECEIPT_PATH", root / "archive-integrity.json"), \
                    patch.object(observer, "os", gate_os), \
                    patch.object(observer, "produce", side_effect=scan):
                self.assertEqual(observer.observe()["archives"], [])


if __name__ == "__main__":
    unittest.main()
