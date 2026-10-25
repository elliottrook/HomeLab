import tempfile
import unittest
from pathlib import Path

from evaluation_lease import (
    ACCEPTED_BACKEND, ACCEPTED_ENDPOINT, ACCEPTED_MODEL, BACKEND_TARGET,
    QUIESCE_STATES, QUIESCE_TARGETS, ProductionBaseline, Admission,
)
from evaluation_lease_adapter import AdapterError, EvaluationLeaseAdapter, consumer_command, read_state
from evaluation_lease_watchdog import run_once
from evaluation_lease_watchdog import WatchdogInput, run_bound_once, validate_watchdog_input


class AdapterTests(unittest.TestCase):
    def admission(self):
        return Admission(
            "eval-1", 1, "backup", "f2", "f3", ACCEPTED_MODEL,
            ACCEPTED_BACKEND, ACCEPTED_ENDPOINT, True, True, True,
            (BACKEND_TARGET,), QUIESCE_TARGETS, (),
            ProductionBaseline(
                (("lxc104:aster-agent.service", "enabled+active"),
                 ("lxc116:aster-speech.service", "enabled+active")),
                (("lxc114:news-aggregator-ingest.timer", "enabled+active"),
                 ("lxc114:news-aggregator-digest.timer", "enabled+active")),
            ), True, 5500, 6400,
        )

    def test_disabled_acquire_makes_no_commands(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append)
            result = adapter.acquire(self.admission(), now_epoch=1000)
        self.assertEqual(result["effects"], "disabled")
        self.assertEqual(calls, [])

    def test_command_allowlist_never_targets_backend(self):
        for target in QUIESCE_TARGETS:
            self.assertEqual(consumer_command(target, "mask")[0:3], ("pct", "exec", target[3:].split(":")[0]))
        with self.assertRaises(AdapterError):
            consumer_command(BACKEND_TARGET, "stop")

    def test_effectful_synthetic_linux_sequence_restores(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append, allow_effects=True)
            adapter.acquire(self.admission(), now_epoch=1000)
            self.assertFalse(adapter.workload_allowed(lease_id="eval-1", generation=1))
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), now_epoch=1100,
            )
            self.assertTrue(adapter.workload_allowed(lease_id="eval-1", generation=1))
            result = adapter.restore(
                lease_id="eval-1", generation=1,
                restored=self.admission().baseline,
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
            )
            self.assertEqual(result["effects"], "restored")
            self.assertEqual(len(calls), 16)

    def test_restore_failure_retains_lock(self):
        calls = []
        def failing(command):
            calls.append(command)
            if command[-2:] == ("start", "aster-speech.service"):
                raise RuntimeError("synthetic start failure")
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", failing, allow_effects=True)
            adapter.acquire(self.admission(), now_epoch=1000)
            with self.assertRaises(AdapterError):
                adapter.restore(
                    lease_id="eval-1", generation=1,
                    restored=self.admission().baseline,
                    backend_active=True, endpoint_authenticated=True,
                    endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                )
            self.assertTrue(adapter.state_path.exists())
            self.assertTrue(adapter.lock_path.exists())

    def test_restore_is_idempotent_from_quiescing_and_restoring(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, calls.append, allow_effects=True)
            adapter.acquire(self.admission(), now_epoch=1000)
            adapter.restore(lease_id="eval-1", generation=1,
                            restored=self.admission().baseline,
                            backend_active=True, endpoint_authenticated=True,
                            endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))
            self.assertFalse(path.exists())

        calls = []
        def failing(command):
            calls.append(command)
            if command[-1] == "aster-speech.service" and command[-2] == "start":
                raise RuntimeError("crash during restore")
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            broken = EvaluationLeaseAdapter(path, failing, allow_effects=True)
            broken.acquire(self.admission(), now_epoch=1000)
            with self.assertRaises(AdapterError):
                broken.restore(lease_id="eval-1", generation=1,
                               restored=self.admission().baseline,
                               backend_active=True, endpoint_authenticated=True,
                               endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))
            self.assertEqual(read_state(path).phase, "restoring")
            recovered = EvaluationLeaseAdapter(path, lambda command: None, allow_effects=True)
            recovered.restore(lease_id="eval-1", generation=1,
                              restored=self.admission().baseline,
                              backend_active=True, endpoint_authenticated=True,
                              endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))

    def test_heartbeat_uses_the_same_identity_bound_schema(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.acquire(self.admission(), now_epoch=1000)
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1100)
            state = read_state(adapter.state_path, expected_lease_id="eval-1",
                               expected_generation=1)
            self.assertEqual(state.heartbeat_epoch, 1100)
            with self.assertRaises(AdapterError):
                adapter.heartbeat(lease_id="foreign", generation=1, now_epoch=1200)

    def test_watchdog_is_inert_without_effect_authority(self):
        called = []
        result = run_once(now_epoch=6500, heartbeat_epoch=1000,
                          heartbeat_timeout=30, hard_deadline_epoch=5500,
                          restore_deadline_epoch=6400, owner_present=True,
                          effect_authorized=True, recovery=called.append)
        self.assertEqual(result["effects"], "disabled")
        self.assertEqual(called, [])

    def test_watchdog_binds_identity_and_fixed_deadlines(self):
        value = WatchdogInput("eval-1", 1, "running", 1100, 1000, 5500, 6400)
        validate_watchdog_input(value, expected_lease_id="eval-1", expected_generation=1)
        with self.assertRaises(ValueError):
            validate_watchdog_input(value, expected_lease_id="foreign", expected_generation=1)
        stale = WatchdogInput("eval-1", 1, "running", 1100, 1000, 5501, 6400)
        with self.assertRaises(ValueError):
            validate_watchdog_input(stale, expected_lease_id="eval-1", expected_generation=1)
        result = run_bound_once(value=value, expected_lease_id="eval-1",
                                expected_generation=1, now_epoch=6500,
                                heartbeat_timeout=30, owner_present=True,
                                effect_authorized=False)
        self.assertEqual(result["effects"], "disabled")


if __name__ == "__main__":
    unittest.main()
