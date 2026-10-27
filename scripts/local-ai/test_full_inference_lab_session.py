import tempfile
import unittest
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import full_inference_lab_session as session

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_session import (FULL_DRAIN_CONSUMERS, FullDrainError,
    FullDrainPaths, FullDrainPreflight, FullInferenceDrainController, plan)


class FullInferenceLabSessionTests(unittest.TestCase):
    def epoch(self, hour, minute):
        return int(datetime(2026, 10, 18, hour, minute, tzinfo=ZoneInfo("America/Vancouver")).timestamp())

    def preflight(self):
        return FullDrainPreflight("full-inference-drain-v1", "drain-1", 1, "application-chain:1",
            ACCEPTED_BACKEND, True, True, True, True, True, True, True, True, True,
            self.epoch(10, 0), self.epoch(10, 0), self.epoch(10, 30), self.epoch(10, 45), self.epoch(11, 30))

    def test_plan_contains_five_effect_inventory_and_backend_baseline(self):
        value = plan(self.preflight())
        self.assertEqual(len(value.drain_commands), len(FULL_DRAIN_CONSUMERS))
        self.assertEqual(value.lab_seconds, 1800)
        self.assertEqual(value.restore_reserve_seconds, 900)
        self.assertIn("aster-llama.service", value.drain_commands[2])

    def test_news_overlap_requires_the_explicit_narrow_override(self):
        value = self.preflight()
        overlapping = FullDrainPreflight(**{
            **value.__dict__, "next_news_ingest_epoch": self.epoch(10, 40)})
        with self.assertRaisesRegex(FullDrainError, "overlaps"):
            plan(overlapping)
        self.assertEqual(plan(overlapping, allow_news_overlap=True).lease_id, "drain-1")

    def test_advisory_mode_does_not_run_commands(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            controller = FullInferenceDrainController(FullDrainPaths(Path(tmp) / "state"), calls.append)
            with self.assertRaisesRegex(FullDrainError, "advisory"):
                controller.begin(self.preflight())
        self.assertEqual(calls, [])

    def test_effectful_drain_and_overdue_restore_are_fixed_and_journaled(self):
        calls, observations = [], []
        def observe(phase, command):
            observations.append((phase, tuple(command)))
            return True
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            controller = FullInferenceDrainController(paths, calls.append, observer=observe,
                                                       validator=lambda: True,
                                                       owner_id="owner-1", allow_effects=True)
            value = controller.begin(self.preflight())
            self.assertEqual(len(calls), 5)
            controller.require_work_window(self.epoch(10, 29))
            with self.assertRaisesRegex(FullDrainError, "window has ended"):
                controller.require_work_window(self.epoch(10, 30))
            controller.restore(value, now_epoch=self.epoch(10, 50), owner_present=True)
            self.assertEqual(len(calls), 16)
            self.assertEqual(len(observations), 16)
            self.assertFalse(paths.lock.exists())
            self.assertIn("restore-overdue", paths.journal.read_text())

    def test_controller_locks_the_exact_state_root(self):
        seen = []
        @contextmanager
        def exact_root(path):
            seen.append(path)
            yield
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            original = session.host_exclusion
            session.host_exclusion = exact_root
            try:
                controller = FullInferenceDrainController(
                    paths, lambda _: None, observer=lambda *_: True,
                    validator=lambda: True, owner_id="owner-1", allow_effects=True)
                value = controller.begin(self.preflight())
                controller.restore(value, now_epoch=self.epoch(10, 20), owner_present=True)
            finally:
                session.host_exclusion = original
        self.assertEqual(seen, [paths.root])

    def test_restore_replays_a_safe_command_when_prior_observation_drifted(self):
        calls = []
        checks = 0
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            controller = FullInferenceDrainController(
                paths, calls.append, observer=lambda *_: True,
                validator=lambda: True, owner_id="owner-1", allow_effects=True)
            value = controller.begin(self.preflight())
            first = value.restore_commands[0]
            with paths.journal.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "restore-observed",
                                         "lease_id": value.lease_id,
                                         "unit": first[-1],
                                         "command": list(first)}) + "\n")
            def observe(phase, command):
                nonlocal checks
                if tuple(command) == first:
                    checks += 1
                    return checks > 1
                return True
            controller.observer = observe
            controller.restore(value, now_epoch=self.epoch(10, 20), owner_present=True)
            self.assertEqual(calls.count(first), 1)
            self.assertIn("restore-replay-required", paths.journal.read_text())

    def test_failed_drain_retains_lock(self):
        calls = []
        def fail(command):
            calls.append(command)
            if len(calls) == 3:
                raise RuntimeError("synthetic drain failure")
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            controller = FullInferenceDrainController(paths, fail, observer=lambda *_: True,
                                                       owner_id="owner-1", allow_effects=True)
            with self.assertRaises(RuntimeError):
                controller.begin(self.preflight())
            self.assertTrue(paths.lock.exists())
            self.assertTrue(paths.state.exists())
            controller._exclusion.__exit__(None, None, None)

    def test_partial_drain_owner_loss_can_resume_by_exact_identity(self):
        calls = []
        def fail_on_third(command):
            calls.append(command)
            if len(calls) == 3:
                raise RuntimeError("synthetic owner loss during drain")
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, fail_on_third,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            with self.assertRaises(RuntimeError):
                first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            resumed_calls = []
            resumed = FullInferenceDrainController(paths, resumed_calls.append,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            value = resumed.resume_existing(lease_id="drain-1", generation=1)
            resumed.restore(value, now_epoch=self.epoch(10, 20), owner_present=True)
            self.assertEqual(len(resumed_calls), 11)
            self.assertFalse(paths.lock.exists())

    def test_resume_rejects_wrong_owner_or_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            wrong = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-2", allow_effects=True)
            with self.assertRaisesRegex(FullDrainError, "identity"):
                wrong.resume_existing(lease_id="drain-1", generation=1)

    def test_final_validator_failure_retains_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            controller = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: False,
                owner_id="owner-1", allow_effects=True)
            value = controller.begin(self.preflight())
            with self.assertRaisesRegex(FullDrainError, "validation"):
                controller.restore(value, now_epoch=self.epoch(10, 40), owner_present=True)
            self.assertTrue(paths.lock.exists())
            controller._exclusion.__exit__(None, None, None)

    def test_nonzero_mask_result_is_not_observed_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            controller = FullInferenceDrainController(paths, lambda _: (1, "command failed"),
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            with self.assertRaisesRegex(FullDrainError, "nonzero"):
                controller.begin(self.preflight())
            self.assertTrue(paths.lock.exists())
            self.assertNotIn('"event": "drain-observed"', paths.journal.read_text())
            controller._exclusion.__exit__(None, None, None)

    def test_nonzero_restore_result_retains_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = FullDrainPaths(Path(tmp) / "state")
            first = FullInferenceDrainController(paths, lambda _: None,
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            value = first.begin(self.preflight())
            first._exclusion.__exit__(None, None, None)
            restored = FullInferenceDrainController(paths, lambda _: (1, "command failed"),
                observer=lambda *_: True, validator=lambda: True,
                owner_id="owner-1", allow_effects=True)
            value = restored.resume_existing(lease_id=value.lease_id, generation=value.generation)
            with self.assertRaisesRegex(FullDrainError, "nonzero"):
                restored.restore(value, now_epoch=self.epoch(10, 40), owner_present=True)
            self.assertTrue(paths.lock.exists())
            restored._exclusion.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
