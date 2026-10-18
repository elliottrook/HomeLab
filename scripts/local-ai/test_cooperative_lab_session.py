import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from application_b60_lease import ACCEPTED_BACKEND
from cooperative_lab_session import (ALLOWED_CONSUMERS, CooperativeLabController,
    CooperativeLabPaths, CooperativeLabPreflight, LabSessionError, plan)


class CooperativeLabSessionTests(unittest.TestCase):
    def epoch(self, hour, minute):
        return int(datetime(2026, 10, 18, hour, minute, tzinfo=ZoneInfo("America/Vancouver")).timestamp())

    def preflight(self):
        return CooperativeLabPreflight("cooperative-lab-v1", "lab-1", 3, "backup-1",
            ACCEPTED_BACKEND, True, True, True, True, True, True,
            self.epoch(10, 0), self.epoch(10, 0), self.epoch(10, 30), self.epoch(10, 45), self.epoch(11, 30))

    def test_plan_is_source_bound_and_preserves_backend(self):
        value = plan(self.preflight())
        self.assertTrue(value.preserve_backend)
        self.assertEqual(len(value.stop_commands), len(ALLOWED_CONSUMERS))
        self.assertIn("mask", value.stop_commands[0])
        self.assertIn("--runtime", value.stop_commands[0])
        self.assertEqual(value.restore_reserve_seconds, 900)

    def test_rejects_incomplete_runtime_or_bad_chronology(self):
        bad = self.preflight().__class__(**{**self.preflight().__dict__, "news_timers_active": False})
        with self.assertRaisesRegex(LabSessionError, "runtime"):
            plan(bad)
        bad = self.preflight().__class__(**{**self.preflight().__dict__, "next_news_ingest_epoch": self.epoch(10, 49)})
        with self.assertRaisesRegex(LabSessionError, "News ingest"):
            plan(bad)
        bad = self.preflight().__class__(**{**self.preflight().__dict__, "lab_end_epoch": self.epoch(11, 1)})
        with self.assertRaisesRegex(LabSessionError, "chronology|duration"):
            plan(bad)

    def test_advisory_controller_never_runs_commands(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            controller = CooperativeLabController(CooperativeLabPaths(Path(tmp) / "state"), calls.append)
            with self.assertRaisesRegex(LabSessionError, "advisory"):
                controller.begin(self.preflight())
        self.assertEqual(calls, [])

    def test_effectful_begin_journals_fixed_effects_and_restore_releases(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            paths = CooperativeLabPaths(Path(tmp) / "state")
            observations = []
            def observer(phase, command):
                observations.append((phase, tuple(command)))
                return True
            controller = CooperativeLabController(paths, calls.append, allow_effects=True,
                                                   observer=observer, owner_id="test-owner")
            value = controller.begin(self.preflight())
            self.assertEqual(len(calls), 4)
            self.assertTrue(paths.lock.exists())
            controller.require_work_window(self.epoch(10, 29))
            with self.assertRaisesRegex(LabSessionError, "window has ended"):
                controller.require_work_window(self.epoch(10, 30))
            controller.restore(value, now_epoch=self.epoch(10, 50), owner_present=True)
            self.assertEqual(len(calls), 12)
            self.assertEqual(len(observations), 12)
            self.assertFalse(paths.lock.exists())
            self.assertIn("restore-verified", paths.journal.read_text())

    def test_failed_effect_keeps_lock_and_does_not_auto_restore(self):
        calls = []
        def fail_on_third(command):
            calls.append(command)
            if len(calls) == 3:
                raise RuntimeError("synthetic failure")
        with tempfile.TemporaryDirectory() as tmp:
            paths = CooperativeLabPaths(Path(tmp) / "state")
            controller = CooperativeLabController(paths, fail_on_third, allow_effects=True,
                                                   observer=lambda *_: True, owner_id="test-owner")
            with self.assertRaises(RuntimeError):
                controller.begin(self.preflight())
            self.assertTrue(paths.lock.exists())
            self.assertTrue(paths.state.exists())
            self.assertEqual(len(calls), 3)
            controller.restore(plan(self.preflight()), now_epoch=self.epoch(10, 50), owner_present=True)
            self.assertFalse(paths.lock.exists())


if __name__ == "__main__":
    unittest.main()
