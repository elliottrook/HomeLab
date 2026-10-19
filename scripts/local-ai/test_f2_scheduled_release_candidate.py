import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import f2_scheduled_release_candidate as candidate


class Result:
    returncode = 0


class F2ScheduledReleaseTests(unittest.TestCase):
    def epoch(self, hour, minute):
        return datetime(2026, 10, 19, hour, minute, tzinfo=ZoneInfo("America/Vancouver")).timestamp()

    def runner(self, epoch):
        def run(command, timeout):
            if command == candidate.CLOCK:
                return 0, str(int(epoch))
            return 0, ""
        return run

    def test_prepare_owns_cycle_and_writes_only_prepared_state(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "capture_fixed_preflight", return_value=object()) as capture:
            value = candidate.prepare(self.runner(self.epoch(1, 7)), clock=lambda: self.epoch(1, 7))
            self.assertEqual(value["state"], "prepared")
            capture.assert_called_once()

    def test_prepare_rejects_outside_window_without_capture(self):
        with patch.object(candidate, "capture_fixed_preflight") as capture:
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "outside"):
                candidate.prepare(self.runner(self.epoch(1, 20)), clock=lambda: self.epoch(1, 20))
            capture.assert_not_called()

    def test_final_is_one_shot_and_hard_deadline_bound(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "run_fixed_final_guard") as gate:
            candidate._write_state("2026-10-19", "prepare", "prepared")
            process = Result()
            with patch.object(candidate, "subprocess"):
                value = candidate.final(self.runner(self.epoch(1, 11)), popen=lambda *a, **k: process, clock=lambda: self.epoch(1, 11))
            self.assertEqual(value["state"], "complete")
            gate.assert_called_once()
            self.assertEqual(candidate._existing_state("2026-10-19")["state"], "complete")

    def test_final_failure_is_terminal_and_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "run_fixed_final_guard", side_effect=candidate.ScheduledF2Error("drift")):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaises(candidate.ScheduledF2Error):
                candidate.final(self.runner(self.epoch(1, 11)), clock=lambda: self.epoch(1, 11))
            self.assertEqual(candidate._existing_state("2026-10-19")["state"], "no_go")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "prepared state"):
                candidate.final(self.runner(self.epoch(1, 11)), clock=lambda: self.epoch(1, 11))


if __name__ == "__main__":
    unittest.main()
