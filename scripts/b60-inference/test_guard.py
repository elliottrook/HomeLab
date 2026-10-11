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
        "collected_at": "2026-09-27T22:04:00-07:00",
        "backup_completed_at": "2026-09-27T02:39:00-07:00",
        "mirror_completed_at": "2026-09-27T04:24:00-07:00",
        "mirror_state": "SUCCESS", "service_health": "ok", "driver": "xe",
        "vulkan_device": "Intel BMG G21", "binary_sha256": guard.ACCEPTED_BINARY_SHA256,
        "unit_sha256": guard.ACCEPTED_UNIT_SHA256, "disk_free_bytes": 30 * 1024**3,
        "ram_available_bytes": 8 * 1024**3, "vram_headroom_bytes": 3 * 1024**3,
    }


class GuardTests(unittest.TestCase):
    def test_exclusive_session_has_rolling_bounds_not_calendar_cutoff(self):
        item = snapshot()
        item.update(collected_at='2026-10-10T23:25:00-07:00',
                    backup_completed_at='2026-10-10T02:44:00-07:00',
                    mirror_completed_at='2026-10-10T04:24:00-07:00')
        now = datetime.fromisoformat('2026-10-10T23:26:00-07:00')
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item,now,20)
        result=guard.validate_preflight(item,now,20,approved_exclusive_session=True)
        self.assertIn('23:56:00',result['experiment_deadline'])
        self.assertIn('00:01:00',result['restoration_deadline'])
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item,now,31,approved_exclusive_session=True)
        item['mirror_state']='FAILED'
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item,now,20,approved_exclusive_session=True)

    def test_instrumented_extension_still_enforces_freshness_and_2320(self):
        item = snapshot()
        item.update(collected_at='2026-10-10T23:01:00-07:00',
                    backup_completed_at='2026-10-10T02:44:00-07:00',
                    mirror_completed_at='2026-10-10T04:24:00-07:00')
        now = datetime.fromisoformat('2026-10-10T23:02:00-07:00')
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item, now, 16)
        guard.validate_preflight(item, now, 16, approved_instrumented_run=True)
        for value in ['2026-10-10T23:07:00-07:00','2026-10-10T23:20:00-07:00','2026-10-11T23:02:00-07:00']:
            with self.assertRaises(guard.GuardError):
                guard.validate_preflight(item,datetime.fromisoformat(value),16,approved_instrumented_run=True)

    def test_loader_exception_is_fresh_date_limited_and_opt_in(self):
        item = snapshot()
        item.update(collected_at='2026-10-10T22:47:00-07:00',
                    backup_completed_at='2026-10-10T02:44:00-07:00',
                    mirror_completed_at='2026-10-10T04:24:00-07:00')
        now = datetime.fromisoformat('2026-10-10T22:48:00-07:00')
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item, now, 9)
        guard.validate_preflight(item, now, 9, approved_loader_retry=True)
        for value in ['2026-10-10T22:53:00-07:00', '2026-10-10T22:55:00-07:00', '2026-10-11T22:48:00-07:00']:
            with self.assertRaises(guard.GuardError):
                guard.validate_preflight(item, datetime.fromisoformat(value), 9, approved_loader_retry=True)

    def test_one_time_fusion_preflight_exception_keeps_freshness_and_date(self):
        item = snapshot()
        item.update(collected_at='2026-10-10T22:28:00-07:00',
                    backup_completed_at='2026-10-10T02:44:00-07:00',
                    mirror_completed_at='2026-10-10T04:24:00-07:00')
        now = datetime.fromisoformat('2026-10-10T22:29:00-07:00')
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item, now, 25)
        result = guard.validate_preflight(item, now, 25, approved_fusion_retry=True)
        self.assertIn('23:20:00', result['experiment_deadline'])
        self.assertIn('23:40:00', result['restoration_deadline'])
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item, datetime.fromisoformat('2026-10-10T22:34:00-07:00'), 25, approved_fusion_retry=True)
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(item, datetime.fromisoformat('2026-10-11T22:29:00-07:00'), 25, approved_fusion_retry=True)

    def test_retired_production_hashes_are_rejected(self):
        old = snapshot()
        old['binary_sha256'] = '47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693'
        old['unit_sha256'] = '7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013'
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(old, datetime.fromisoformat('2026-09-27T22:05:00-07:00'), 30)
        self.assertIn(guard.ACCEPTED_BINARY_PATH, guard.commands()[5])
        old['binary_sha256']='5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d'
        old['unit_sha256']='6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e'
        with self.assertRaises(guard.GuardError):
            guard.validate_preflight(old,datetime.fromisoformat('2026-09-27T22:05:00-07:00'),30)

    def test_preflight_sets_2320_and_2340_deadlines(self):
        result = guard.validate_preflight(snapshot(), datetime.fromisoformat("2026-09-27T22:05:00-07:00"), 60)
        self.assertIn("23:20:00", result["experiment_deadline"])
        self.assertIn("23:40:00", result["restoration_deadline"])

    def test_preflight_rejects_wrong_time_stale_mirror_hash_and_headroom(self):
        cases = []
        cases.append((snapshot(), datetime.fromisoformat("2026-09-27T00:10:00-07:00")))
        for key, value in (("mirror_state", "FAILED"), ("binary_sha256", "0" * 64),
                           ("vram_headroom_bytes", 1)):
            item = snapshot(); item[key] = value; cases.append((item, datetime.fromisoformat("2026-09-27T22:05:00-07:00")))
        for item, now in cases:
            with self.assertRaises(guard.GuardError):
                guard.validate_preflight(item, now, 30)

    def test_finalizer_order_and_validation(self):
        outputs = ["", "", "", "", '{"status":"ok"}', guard.ACCEPTED_BINARY_SHA256,
                   guard.ACCEPTED_UNIT_SHA256, "/sys/bus/pci/drivers/xe\n", "Intel BMG G21"]
        seen = []
        def fake_run(command, **kwargs):
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, outputs[len(seen)-1], "")
        guard.execute_finalizer(fake_run, sleep=lambda _: None, quiesce_seconds=0,
                                readiness_attempts=1, readiness_interval=0)
        self.assertEqual(seen, guard.commands())
        self.assertEqual(seen[0][-2:], ["stop", guard.CANDIDATE_UNIT])
        self.assertEqual(seen[1][-2:], ["stop", "aster-llama.service"])
        self.assertEqual(seen[2][-3:], ["start", "--no-block", "aster-llama.service"])

    def test_explicit_rollback_profile_is_independent_of_current_acceptance(self):
        seen=[]
        outputs=['','','','', '{"status":"ok"}','old-binary','old-unit','/sys/bus/pci/drivers/xe','BMG G21']
        def fake(command,**kw):
            seen.append(command);return subprocess.CompletedProcess(command,0,outputs[len(seen)-1],'')
        guard.execute_finalizer(fake,sleep=lambda _:None,readiness_attempts=1,
                                accepted_binary_path='/retained/vulkan',
                                accepted_binary_sha256='old-binary',accepted_unit_sha256='old-unit')
        self.assertEqual(seen[5][-1],'/retained/vulkan')

    def test_finalizer_fails_closed_on_validation_error(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(command, 1 if "is-active" in command else 0, "", "")
        with self.assertRaises(guard.GuardError):
            guard.execute_finalizer(fake_run, sleep=lambda _: None, quiesce_seconds=0,
                                    readiness_attempts=2, readiness_interval=0)


if __name__ == "__main__":
    unittest.main()
