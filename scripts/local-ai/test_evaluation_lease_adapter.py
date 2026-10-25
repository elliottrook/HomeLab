import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

from evaluation_lease import (
    ACCEPTED_BACKEND, ACCEPTED_ENDPOINT, ACCEPTED_MODEL, BACKEND_TARGET,
    QUIESCE_STATES, QUIESCE_TARGETS, ProductionBaseline, Admission,
    D4_DIGEST, M3_STAGE_MANIFEST_DIGEST, WorkloadOutcome,
    EvaluationLeaseError,
)
from evaluation_lease_adapter import AdapterError, EvaluationLeaseAdapter, consumer_command, read_state
from evaluation_lease_watchdog import run_once
from evaluation_lease_watchdog import (
    WatchdogInput, run_bound_from_state, run_bound_once, validate_watchdog_input,
)


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
            result = adapter.prepare(self.admission(), now_epoch=1000)
        self.assertEqual(result["effects"], "disabled")
        self.assertEqual(calls, [])

    def test_prepare_is_effect_authorized_but_does_not_quiesce_consumers(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append,
                                              allow_effects=True)
            result = adapter.prepare(self.admission(), now_epoch=1000)
            self.assertEqual(result["effects"], "prepared")
            self.assertEqual(read_state(adapter.state_path).phase, "prepared")
            self.assertEqual(calls, [])
            with self.assertRaises(AdapterError):
                adapter.acquire(self.admission(), now_epoch=1000)

    def test_quiesce_rejects_absent_foreign_and_stale_lease_before_commands(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append,
                                              allow_effects=True)
            with self.assertRaises(AdapterError):
                adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000,
                                heartbeat_timeout=30)
            adapter.prepare(self.admission(), now_epoch=1000)
            with self.assertRaises(AdapterError):
                adapter.quiesce(lease_id="foreign", generation=1, now_epoch=1000,
                                heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=5500,
                                heartbeat_timeout=30)
            self.assertEqual(calls, [])

    def test_partial_quiescence_failure_is_durably_recoverable(self):
        calls = []

        def fail_during_quiescence(command):
            calls.append(command)
            if len(calls) == 3:
                raise RuntimeError("synthetic mid-quiescence failure")

        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, fail_during_quiescence,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            with self.assertRaisesRegex(AdapterError, "quiescence is uncertain"):
                adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000,
                                heartbeat_timeout=30)
            self.assertEqual(read_state(path).phase, "quiescing")
            self.assertTrue(adapter.lock_path.exists())

            recovery_calls = []
            recovered = EvaluationLeaseAdapter(path, recovery_calls.append,
                                                allow_effects=True)
            result = recovered.restore(
                lease_id="eval-1", generation=1,
                restored=self.admission().baseline,
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), recovery=True,
            )
            self.assertEqual(result["effects"], "restored")
            self.assertFalse(path.exists())
            self.assertFalse(recovered.lock_path.exists())
            self.assertEqual(len(recovery_calls), 8)

    def test_clean_prepared_lease_can_recover_without_stranding_state(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, calls.append, allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            self.assertEqual(calls, [])
            result = adapter.restore(
                lease_id="eval-1", generation=1,
                restored=self.admission().baseline,
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), recovery=True,
            )
            self.assertEqual(result["effects"], "restored")
            self.assertFalse(path.exists())
            self.assertFalse(adapter.lock_path.exists())
            self.assertEqual(len(calls), 8)

    def test_post_quiescence_rejects_unhealthy_backend_after_quiesce(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000,
                            heartbeat_timeout=30)
            with self.assertRaises(EvaluationLeaseError):
                adapter.post_quiescence(
                    observed_states=QUIESCE_STATES, admission=self.admission(),
                    backend_active=False, endpoint_authenticated=True,
                    endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                    now_epoch=1000, heartbeat_timeout=30)

    def test_command_allowlist_never_targets_backend(self):
        for target in QUIESCE_TARGETS:
            self.assertEqual(consumer_command(target, "mask")[0:3], ("pct", "exec", target[3:].split(":")[0]))
        with self.assertRaises(AdapterError):
            consumer_command(BACKEND_TARGET, "stop")

    def test_effectful_synthetic_linux_sequence_restores(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", calls.append, allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            self.assertFalse(adapter.workload_allowed(
                lease_id="eval-1", generation=1, workload_name="d4-candidate-g",
                now_epoch=1100, heartbeat_timeout=30,
            ))
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), now_epoch=1100,
                heartbeat_timeout=200,
            )
            self.assertTrue(adapter.workload_allowed(
                lease_id="eval-1", generation=1, workload_name="d4-candidate-g",
                now_epoch=1100, heartbeat_timeout=30,
            ))
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="d4-candidate-g",
                                   now_epoch=1100, heartbeat_timeout=200)
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1150)
            adapter.record_outcome(
                WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                "completed", "a" * 64, "b" * 64, 12, 30, True),
                now_epoch=1200, heartbeat_timeout=100,
            )
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="m3-nlu-calibration",
                                   now_epoch=1200, heartbeat_timeout=100)
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1250)
            adapter.record_outcome(
                WorkloadOutcome("eval-1", 1, "m3-nlu-calibration", M3_STAGE_MANIFEST_DIGEST,
                                "completed", "c" * 64, "d" * 64, 60, 30, True),
                now_epoch=1300, heartbeat_timeout=100,
            )
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
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
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
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
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
            broken.prepare(self.admission(), now_epoch=1000)
            broken.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                broken.restore(lease_id="eval-1", generation=1,
                               restored=self.admission().baseline,
                               backend_active=True, endpoint_authenticated=True,
                               endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), recovery=True)
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
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1100)
            state = read_state(adapter.state_path, expected_lease_id="eval-1",
                               expected_generation=1)
            self.assertEqual(state.heartbeat_epoch, 1100)
            with self.assertRaises(AdapterError):
                adapter.heartbeat(lease_id="foreign", generation=1, now_epoch=1200)

    def test_late_or_stale_transition_and_insufficient_budget_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                adapter.post_quiescence(
                    observed_states=QUIESCE_STATES, admission=self.admission(),
                    backend_active=True, endpoint_authenticated=True,
                    endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                    now_epoch=5500, heartbeat_timeout=30,
                )
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1000)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=3341)
            self.assertFalse(adapter.workload_allowed(
                lease_id="eval-1", generation=1, workload_name="d4-candidate-g",
                now_epoch=3341, heartbeat_timeout=30,
            ))
            self.assertFalse(adapter.workload_allowed(
                lease_id="eval-1", generation=1, workload_name="m3-nlu-calibration",
                now_epoch=4301, heartbeat_timeout=30,
            ))

    def test_workload_sequence_is_lease_bound_one_attempt_and_d4_then_m3(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            with self.assertRaises(AdapterError):
                adapter.start_workload(lease_id="eval-1", generation=1,
                                       workload_name="m3-nlu-calibration",
                                       now_epoch=1000, heartbeat_timeout=30)
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="d4-candidate-g",
                                   now_epoch=1000, heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                adapter.start_workload(lease_id="eval-1", generation=1,
                                       workload_name="d4-candidate-g",
                                       now_epoch=1000, heartbeat_timeout=30)
            foreign = WorkloadOutcome("other", 1, "d4-candidate-g", D4_DIGEST,
                                      "completed", "a" * 64, "b" * 64, 1, 1, True)
            with self.assertRaises(AdapterError):
                adapter.record_outcome(foreign, now_epoch=1001, heartbeat_timeout=30)
            uncertain = WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                        "completed", "a" * 64, "b" * 64, 1, 1, True, True)
            with self.assertRaises(EvaluationLeaseError):
                adapter.record_outcome(uncertain, now_epoch=1001, heartbeat_timeout=30)
            d4 = WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                 "completed", "a" * 64, "b" * 64, 1, 1, True)
            adapter.record_outcome(d4, now_epoch=1001, heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                adapter.record_outcome(d4, now_epoch=1002, heartbeat_timeout=30)
            with self.assertRaises(AdapterError):
                adapter.restore(lease_id="eval-1", generation=1,
                                restored=self.admission().baseline,
                                backend_active=True, endpoint_authenticated=True,
                                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))

    def test_state_mutations_and_valid_inflight_recovery_are_coherent(self):
        mutations = (
            {"completed_outcomes": [("m3-nlu-calibration", "a" * 64, "b" * 64)],
             "next_workload": None, "in_flight_workload": None},
            {"completed_outcomes": [("m3-nlu-calibration", "a" * 64, "b" * 64),
                                     ("d4-candidate-g", "c" * 64, "d" * 64)],
             "next_workload": None, "in_flight_workload": None},
            {"completed_outcomes": [], "next_workload": "d4-candidate-g",
             "in_flight_workload": "m3-nlu-calibration"},
        )
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, lambda command: None, allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            baseline = json.loads(path.read_text())
            for mutation in mutations:
                changed = dict(baseline)
                changed.update(mutation)
                path.write_text(json.dumps(changed) + "\n")
                path.chmod(0o600)
                with self.assertRaises(AdapterError):
                    read_state(path)
            path.write_text(json.dumps(baseline) + "\n")
            path.chmod(0o600)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="d4-candidate-g",
                                   now_epoch=1000, heartbeat_timeout=30)
            self.assertEqual(read_state(path).in_flight_workload, "d4-candidate-g")
            adapter.restore(lease_id="eval-1", generation=1,
                            restored=self.admission().baseline,
                            backend_active=True, endpoint_authenticated=True,
                            endpoint_idle=True, gpu_holders=(BACKEND_TARGET,), recovery=True)

    def test_concurrent_duplicate_start_has_one_admitter(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            barrier = threading.Barrier(2)
            successes, failures = [], []
            def attempt():
                barrier.wait()
                try:
                    adapter.start_workload(lease_id="eval-1", generation=1,
                                           workload_name="d4-candidate-g",
                                           now_epoch=1000, heartbeat_timeout=30)
                    successes.append(True)
                except AdapterError:
                    failures.append(True)
            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(failures), 1)

    def test_heartbeat_and_outcome_cannot_lose_inflight_or_completion(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="d4-candidate-g",
                                   now_epoch=1000, heartbeat_timeout=30)
            outcome = WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                      "completed", "a" * 64, "b" * 64, 1, 1, True)
            barrier = threading.Barrier(2)
            failures = []
            def heartbeat():
                barrier.wait()
                try:
                    adapter.heartbeat(lease_id="eval-1", generation=1, now_epoch=1001)
                except AdapterError as exc:
                    failures.append(exc)
            def outcome_writer():
                barrier.wait()
                try:
                    adapter.record_outcome(outcome, now_epoch=1001, heartbeat_timeout=30)
                except AdapterError as exc:
                    failures.append(exc)
            threads = [threading.Thread(target=heartbeat), threading.Thread(target=outcome_writer)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            state = read_state(adapter.state_path)
            self.assertEqual(tuple(row[0] for row in state.completed_outcomes), ("d4-candidate-g",))
            self.assertIsNone(state.in_flight_workload)
            self.assertLessEqual(len(failures), 1)

    def test_concurrent_duplicate_outcomes_have_one_terminal_writer(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )
            adapter.start_workload(lease_id="eval-1", generation=1,
                                   workload_name="d4-candidate-g",
                                   now_epoch=1000, heartbeat_timeout=30)
            outcome = WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                      "completed", "a" * 64, "b" * 64, 1, 1, True)
            barrier = threading.Barrier(2)
            successes, failures = [], []
            def write_once():
                barrier.wait()
                try:
                    adapter.record_outcome(outcome, now_epoch=1001, heartbeat_timeout=30)
                    successes.append(True)
                except AdapterError:
                    failures.append(True)
            threads = [threading.Thread(target=write_once) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(failures), 1)

    def test_released_operation_guard_does_not_strand_recovery(self):
        with tempfile.TemporaryDirectory() as root:
            adapter = EvaluationLeaseAdapter(Path(root) / "lease.json", lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            with adapter._operation_guard():
                pass
            adapter.post_quiescence(
                observed_states=QUIESCE_STATES, admission=self.admission(),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
                now_epoch=1000, heartbeat_timeout=30,
            )

    def test_operation_lock_rejects_symlink_and_weak_mode(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, lambda command: None,
                                              allow_effects=True)
            target = Path(root) / "target.lock"
            target.write_text("lock\n")
            os.symlink(target, adapter.operation_lock_path)
            with self.assertRaises(AdapterError):
                with adapter._operation_guard():
                    pass
            adapter.operation_lock_path.unlink()
            adapter.operation_lock_path.write_text("lock\n")
            adapter.operation_lock_path.chmod(0o644)
            with self.assertRaises(AdapterError):
                with adapter._operation_guard():
                    pass

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

    def test_watchdog_accepts_healthy_prepared_and_recovers_expired_prepared(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, lambda command: None,
                                              allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            called = []
            healthy = run_bound_from_state(
                path=path, expected_lease_id="eval-1", expected_generation=1,
                now_epoch=1010, heartbeat_timeout=30, owner_present=True,
                effect_authorized=True, recovery=lambda: called.append(True),
            )
            self.assertEqual(healthy["effects"], "not-attempted")
            self.assertEqual(called, [])
            owner_lost = run_bound_from_state(
                path=path, expected_lease_id="eval-1", expected_generation=1,
                now_epoch=1010, heartbeat_timeout=30, owner_present=False,
                effect_authorized=True, recovery=lambda: called.append(True) or "ok",
            )
            self.assertEqual(owner_lost["effects"], "recovered")
            self.assertEqual(called, [True])
            expired = run_bound_from_state(
                path=path, expected_lease_id="eval-1", expected_generation=1,
                now_epoch=5500, heartbeat_timeout=30, owner_present=True,
                effect_authorized=True, recovery=lambda: called.append(True) or "ok",
            )
            self.assertEqual(expired["effects"], "recovered")
            self.assertEqual(called, [True, True])

    def test_watchdog_effect_path_loads_durable_state_and_rejects_duplicate_or_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            adapter = EvaluationLeaseAdapter(path, lambda command: None, allow_effects=True)
            adapter.prepare(self.admission(), now_epoch=1000)
            adapter.quiesce(lease_id="eval-1", generation=1, now_epoch=1000, heartbeat_timeout=30)
            called = []
            result = run_bound_from_state(
                path=path, expected_lease_id="eval-1", expected_generation=1,
                now_epoch=5500, heartbeat_timeout=30, owner_present=True,
                effect_authorized=True, recovery=lambda: called.append(True) or "ok",
            )
            self.assertEqual(result["effects"], "recovered")
            self.assertEqual(called, [True])

        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lease.json"
            path.write_text('{"lease_id":"eval-1","lease_id":"other"}\n')
            path.chmod(0o600)
            with self.assertRaises(AdapterError):
                read_state(path)
            target = Path(root) / "target.json"
            target.write_text('{}\n')
            target.chmod(0o600)
            link = Path(root) / "link.json"
            os.symlink(target, link)
            with self.assertRaises(AdapterError):
                read_state(link)


if __name__ == "__main__":
    unittest.main()
