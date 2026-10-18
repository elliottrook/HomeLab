import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_session import (FullDrainPaths, FullDrainPreflight,
    FullInferenceDrainController)
from full_inference_lab_supervisor import (GpuUser, PersistentFullDrainSupervisor,
    SupervisorError, require_known_gpu_users, watchdog_decision)


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
                production_masked=lambda: True, gpu_users=lambda: frozenset({known}),
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
                production_masked=lambda: False, gpu_users=lambda: frozenset({known}),
                allowed_gpu_users=frozenset({known}), wall_clock=lambda: 110)
            supervisor.begin(self.preflight())
            with self.assertRaisesRegex(SupervisorError, "production"):
                supervisor.run_smoke()


if __name__ == "__main__":
    unittest.main()
