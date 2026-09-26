#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b60_guard", HERE / "guard.py")
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def snapshot():
    return {
        "collected_at": "2026-09-27T00:24:00-07:00",
        "backup_completed_at": "2026-09-26T02:39:00-07:00",
        "mirror_completed_at": "2026-09-26T04:24:00-07:00",
        "mirror_state": "SUCCESS", "service_health": "ok", "driver": "xe",
        "vulkan_device": "Intel BMG G21", "binary_sha256": guard.ACCEPTED_BINARY_SHA256,
        "unit_sha256": guard.ACCEPTED_UNIT_SHA256, "disk_free_bytes": 30 * 1024**3,
        "ram_available_bytes": 8 * 1024**3, "vram_headroom_bytes": 3 * 1024**3,
    }


class GuardTests(unittest.TestCase):
    def test_preflight_sets_0140_and_0200_deadlines(self):
        result = guard.validate_preflight(snapshot(), datetime.fromisoformat("2026-09-27T00:25:00-07:00"), 60)
        self.assertIn("01:40:00", result["experiment_deadline"])
        self.assertIn("02:00:00", result["restoration_deadline"])

    def test_preflight_rejects_wrong_time_stale_mirror_hash_and_headroom(self):
        cases = []
        cases.append((snapshot(), datetime.fromisoformat("2026-09-27T00:10:00-07:00")))
        for key, value in (("mirror_state", "FAILED"), ("binary_sha256", "0" * 64),
                           ("vram_headroom_bytes", 1)):
            item = snapshot(); item[key] = value; cases.append((item, datetime.fromisoformat("2026-09-27T00:25:00-07:00")))
        for item, now in cases:
            with self.assertRaises(guard.GuardError):
                guard.validate_preflight(item, now, 30)

    def test_finalizer_order_and_validation(self):
        outputs = ["", "", "", guard.ACCEPTED_BINARY_SHA256, guard.ACCEPTED_UNIT_SHA256,
                   "/sys/bus/pci/drivers/xe\n", "Intel BMG G21", '{"status":"ok"}']
        seen = []
        def fake_run(command, **kwargs):
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, outputs[len(seen)-1], "")
        guard.execute_finalizer(fake_run)
        self.assertEqual(seen, guard.commands())
        self.assertEqual(seen[0][-2:], ["stop", guard.CANDIDATE_UNIT])
        self.assertEqual(seen[1][-2:], ["restart", "aster-llama.service"])

    def test_finalizer_fails_closed_on_validation_error(self):
        count = 0
        def fake_run(command, **kwargs):
            nonlocal count
            count += 1
            return subprocess.CompletedProcess(command, 1 if count == 3 else 0, "", "")
        with self.assertRaises(guard.GuardError):
            guard.execute_finalizer(fake_run)


if __name__ == "__main__":
    unittest.main()
