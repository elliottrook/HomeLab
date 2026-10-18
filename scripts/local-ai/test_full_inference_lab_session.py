import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

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
            self.assertEqual(len(calls), 15)
            self.assertEqual(len(observations), 15)
            self.assertFalse(paths.lock.exists())
            self.assertIn("restore-overdue", paths.journal.read_text())

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


if __name__ == "__main__":
    unittest.main()
