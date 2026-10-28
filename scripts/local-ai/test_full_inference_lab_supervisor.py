import unittest
from unittest.mock import patch
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_session import (FullDrainPaths, FullDrainPreflight,
    FullInferenceDrainController)
from full_inference_lab_supervisor import (GpuUser, PersistentFullDrainSupervisor,
    SupervisorError, recovery_only, require_known_gpu_users, watchdog_decision)


class SupervisorTests(unittest.TestCase):
    def preflight(self):
        return FullDrainPreflight("full-inference-drain-v1", "lease-1", 2, "cycle",
            ACCEPTED_BACKEND, True, True, True, True, True, True, True, True, True,
            100, 100, 1900, 2815, 4000)

    def test_watchdog_recovers_hung_or_lost_owner_and_hard_cutoff(self):
        self.assertEqual(watchdog_decision(now_epoch=110, heartbeat_epoch=100,
            heartbeat_timeout=5, hard_deadline_epoch=140, owner_alive=True,
            owner_identity_ok=True).action, "recover")
        self.assertEqual(watchdog_decision(now_epoch=110, heartbeat_epoch=109,
            heartbeat_timeout=5, hard_deadline_epoch=140, owner_alive=False,
            owner_identity_ok=False).reason, "owner-lost")
        self.assertEqual(watchdog_decision(now_epoch=140, heartbeat_epoch=139,
            heartbeat_timeout=5, hard_deadline_epoch=140, owner_alive=True,
            owner_identity_ok=True).reason, "hard-deadline")

    def test_false_new_gpu_consumer_fails_closed(self):
        known = GpuUser(10, 20, "svc", "/bin/known")
        rogue = GpuUser(11, 21, "rogue", "/tmp/rogue")
        with self.assertRaisesRegex(SupervisorError, "unlisted"):
            require_known_gpu_users(frozenset({known, rogue}), frozenset({known}))

    def test_supervisor_requires_masked_production_and_three_receipt(self):
        calls, users = [], frozenset()
        known = GpuUser(10, 20, "svc", "/bin/known")
        def observe(*_): return True
        def runner(command):
            calls.append(tuple(command)); return None
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), runner, observer=observe,
                validator=lambda: True, owner_id="owner", allow_effects=True)
            receipt = '{"schema":"aster-9b-direct-control-smoke.v1","profile":"accepted-9b-direct-control-smoke-v1","lease_id":"lease-1","generation":2,"port":11436,"production_service":"masked-inactive","credential_exported":false,"tool_mode":"disabled","request_count":3,"observation_ids":["a","b","c"],"exit_status":0}'
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda command, timeout: (0, receipt),
                production_masked=lambda: True, lab_absent=lambda: True,
                gpu_users=lambda: frozenset({known}),
                allowed_gpu_users=frozenset({known}), wall_clock=lambda: 110)
            value = supervisor.begin(self.preflight())
            self.assertEqual(supervisor.run_smoke()["request_count"], 3)
            supervisor.restore(now_epoch=120, owner_present=True)
            self.assertFalse(supervisor.active)
            self.assertFalse(controller.paths.lock.exists())

    def test_smoke_refuses_production_or_cutoff(self):
        known = GpuUser(10, 20, "svc", "/bin/known")
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda *_: (1, ""),
                production_masked=lambda: False, lab_absent=lambda: True,
                gpu_users=lambda: frozenset({known}),
                allowed_gpu_users=frozenset({known}), wall_clock=lambda: 110)
            supervisor.begin(self.preflight())
            with self.assertRaisesRegex(SupervisorError, "production"):
                supervisor.run_smoke()

    def test_new_gpu_user_during_smoke_restores_and_retains_no_workload(self):
        known = GpuUser(10, 20, "svc", "/bin/known")
        rogue = GpuUser(11, 21, "rogue", "/tmp/rogue")
        snapshots = iter((frozenset({known}), frozenset({known, rogue})))
        receipt = '{"schema":"aster-9b-direct-control-smoke.v1","profile":"accepted-9b-direct-control-smoke-v1","lease_id":"lease-1","generation":2,"port":11436,"production_service":"masked-inactive","credential_exported":false,"tool_mode":"disabled","request_count":3,"observation_ids":["a","b","c"],"exit_status":0}'
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda *_: (0, receipt),
                production_masked=lambda: True, lab_absent=lambda: True,
                gpu_users=lambda: next(snapshots),
                allowed_gpu_users=frozenset({known}), wall_clock=lambda: 110)
            supervisor.begin(self.preflight())
            with self.assertRaisesRegex(SupervisorError, "unlisted"):
                supervisor.run_smoke()
            self.assertFalse(controller.paths.lock.exists())

    def test_owner_loss_uses_recovery_only_and_never_runs_workload(self):
        with TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            plan = first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            calls = []
            replacement = FullInferenceDrainController(paths, calls.append,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            recovery_only(replacement, lease_id=plan.lease_id, generation=plan.generation,
                          restore_now_epoch=120, cleanup_runner=lambda *_: (0, ""),
                          lab_absent=lambda: True)
            self.assertEqual(len(calls), 14)

    def test_recovery_only_retains_lock_when_lab_absence_is_unproven(self):
        with TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            plan = first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            replacement = FullInferenceDrainController(paths, [],
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            with self.assertRaisesRegex(SupervisorError, "absence is unproven"):
                recovery_only(replacement, lease_id=plan.lease_id, generation=plan.generation,
                              restore_now_epoch=120, cleanup_runner=lambda *_: (0, ""),
                              lab_absent=lambda: False)
            self.assertTrue(paths.lock.exists())

    def test_recovery_only_allows_missing_scope_after_independent_absence_proof(self):
        with TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            plan = first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            calls = []
            replacement = FullInferenceDrainController(paths, calls.append,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            recovery_only(replacement, lease_id=plan.lease_id, generation=plan.generation,
                          restore_now_epoch=120, cleanup_runner=lambda *_: (1, "unit not found"),
                          lab_absent=lambda: True)
            self.assertFalse(paths.lock.exists())

    def test_bounded_deadline_uses_remaining_wall_seconds(self):
        known = GpuUser(10, 20, "svc", "/bin/known")
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda *_: (1, ""),
                production_masked=lambda: True, lab_absent=lambda: True,
                gpu_users=lambda: frozenset({known}),
                allowed_gpu_users=frozenset({known}), wall_clock=lambda: 1800)
            supervisor.begin(self.preflight())
            captured = {}
            def fake_bounded(**kwargs):
                captured.update(kwargs)
                kwargs["heartbeat"]()
                return {"ok": True}
            with patch("full_inference_lab_supervisor.run_fixed_smoke_bounded", fake_bounded):
                self.assertEqual(supervisor.run_smoke_bounded(heartbeat=lambda: None,
                    monotonic=lambda: 1000), {"ok": True})
            self.assertEqual(captured["deadline"], 1100.0)
            supervisor.restore(now_epoch=1810, owner_present=True)

    def test_partial_mask_failure_attempts_recovery(self):
        calls = []
        def runner(command):
            calls.append(command)
            return (1, "mask failed") if len(calls) == 3 else None
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), runner,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda *_: (1, ""),
                production_masked=lambda: True, lab_absent=lambda: True,
                gpu_users=lambda: frozenset(),
                allowed_gpu_users=frozenset(), wall_clock=lambda: 110)
            with self.assertRaisesRegex(Exception, "nonzero"):
                supervisor.begin(self.preflight())
            self.assertFalse(controller.paths.lock.exists())

    def test_orphaned_lab_scope_blocks_production_restore(self):
        known = GpuUser(10, 20, "svc", "/bin/known")
        receipt = '{"schema":"aster-9b-direct-control-smoke.v1","profile":"accepted-9b-direct-control-smoke-v1","lease_id":"lease-1","generation":2,"port":11436,"production_service":"masked-inactive","credential_exported":false,"tool_mode":"disabled","request_count":3,"observation_ids":["a","b","c"],"exit_status":0}'
        with TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(
                FullDrainPaths(Path(tmp) / "state"), lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner", allow_effects=True)
            supervisor = PersistentFullDrainSupervisor(
                controller, workload_runner=lambda *_: (0, receipt),
                production_masked=lambda: True, lab_absent=lambda: False,
                gpu_users=lambda: frozenset({known}), allowed_gpu_users=frozenset({known}),
                wall_clock=lambda: 110)
            supervisor.begin(self.preflight())
            with self.assertRaisesRegex(SupervisorError, "remains"):
                supervisor.run_smoke()
            self.assertTrue(controller.paths.lock.exists())
            controller._exclusion.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
