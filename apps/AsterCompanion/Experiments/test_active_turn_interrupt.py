"""Offline checks for the one-shot, content-free interruption watcher."""

import importlib.util
from pathlib import Path
import signal
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("active_turn_interrupt.py")
SPEC = importlib.util.spec_from_file_location("active_turn_interrupt", SCRIPT)
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)
REQUEST = "request-11111111-2222-3333-4444-555555555555"


class DecisionTests(unittest.TestCase):
    def test_only_new_running_turn_with_id_is_eligible(self):
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("running", "turn-1")}), "signal")
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("running", None)}), "wait")
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("dispatch_unknown", None)}), "wait")

    def test_completed_or_uncertain_turn_is_not_signalled(self):
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("completed", "turn-1")}),
                         "completed_before_interrupt")
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("unknown", "turn-1")}),
                         "abort_uncertain_state")

    def test_preexisting_or_unrelated_job_aborts(self):
        self.assertEqual(watcher.decision({REQUEST}, REQUEST,
                                          {REQUEST: ("running", "turn-1")}),
                         "abort_unexpected_job")
        self.assertEqual(watcher.decision(set(), None,
                                          {REQUEST: ("running", "turn-1")}),
                         "abort_unexpected_job")
        self.assertEqual(watcher.decision(set(), REQUEST,
                                          {REQUEST: ("running", "turn-1"),
                                           "other": ("running", "turn-2")}),
                         "abort_unexpected_job")


class RuntimeTests(unittest.TestCase):
    def run_fixture(self, armed):
        with patch.object(watcher, "private_directory"), \
             patch.object(watcher, "read_pending", side_effect=[None, REQUEST]), \
             patch.object(watcher, "read_rows", side_effect=[{},
                         {REQUEST: ("running", "turn-1")}]), \
             patch.object(watcher, "process_matches", return_value=True), \
             patch.object(watcher, "executable_matches", return_value=True), \
             patch.object(watcher.os, "kill") as kill:
            result = watcher.run(Path("/unused"), 12345, 1, armed)
        return result, kill

    def test_default_dry_run_cannot_signal(self):
        result, kill = self.run_fixture(False)
        self.assertEqual(result["outcome"], "would_signal")
        self.assertFalse(result["signal_sent"])
        kill.assert_not_called()

    def test_armed_run_signals_only_exact_pid_once(self):
        result, kill = self.run_fixture(True)
        self.assertEqual(result["outcome"], "signalled_on_observed_running")
        self.assertTrue(result["signal_sent"])
        kill.assert_called_once_with(12345, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
