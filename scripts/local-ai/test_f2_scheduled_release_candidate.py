import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import f2_scheduled_release_candidate as candidate


class Result:
    returncode = 0
    kwargs = None

    def communicate(self, timeout=None):
        return (b'{"schema":"aster-read-only-archive-timing.v1","state":"complete",'
                b'"date":"2026_10_19","archives":['
                b'{"vmid":"104","volid":"backups:backup/vzdump-lxc-104-2026_10_19-00_00_00.tar.zst","size":1,"ctime":1,"test_started_epoch":1,"test_finished_epoch":2,"test_elapsed_ms":1,"test_exit":0},'
                b'{"vmid":"110","volid":"backups:backup/vzdump-lxc-110-2026_10_19-00_00_00.tar.zst","size":1,"ctime":1,"test_started_epoch":1,"test_finished_epoch":2,"test_elapsed_ms":1,"test_exit":0},'
                b'{"vmid":"116","volid":"backups:backup/vzdump-lxc-116-2026_10_19-00_00_00.tar.zst","size":1,"ctime":1,"test_started_epoch":1,"test_finished_epoch":2,"test_elapsed_ms":1,"test_exit":0}],'
                b'"admission_receipt_written":false}', None)


class TimeoutResult(Result):
    calls = 0
    pid = 12345

    def communicate(self, timeout=None):
        self.calls += 1
        if self.calls == 1:
            import subprocess
            raise subprocess.TimeoutExpired("observer", timeout)
        return (b"", None)


class OversizedResult(Result):
    def communicate(self, timeout=None):
        return (b"{" + b"x" * 8192, None)


class NonzeroResult(Result):
    returncode = 1


class CommunicationFailureResult(Result):
    def communicate(self, timeout=None):
        raise RuntimeError("synthetic communication failure")


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
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "capture_fixed_preflight", return_value=object()) as capture:
            value = candidate.prepare(self.runner(self.epoch(1, 15)), clock=lambda: self.epoch(1, 15))
            self.assertEqual(value["state"], "prepared")
            capture.assert_called_once()

    def test_prepare_rejects_outside_window_without_capture(self):
        with patch.object(candidate, "capture_fixed_preflight") as capture:
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "outside"):
                candidate.prepare(self.runner(self.epoch(1, 16)), clock=lambda: self.epoch(1, 16))
            capture.assert_not_called()

    def test_final_is_one_shot_and_hard_deadline_bound(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard") as gate:
            candidate._write_state("2026-10-19", "prepare", "prepared")
            process = Result()
            value = candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: process, clock=lambda: self.epoch(1, 20))
            self.assertEqual(value["state"], "complete")
            self.assertEqual(value["result"]["archives"][1]["vmid"], "110")
            gate.assert_called_once()
            saved = candidate._existing_state("2026-10-19")
            self.assertEqual(saved["state"], "complete")
            self.assertEqual(saved["result"]["archives"][2]["test_exit"], 0)

    def test_final_failure_is_terminal_and_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard", side_effect=candidate.ScheduledF2Error("drift")):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaises(candidate.ScheduledF2Error):
                candidate.final(self.runner(self.epoch(1, 20)), clock=lambda: self.epoch(1, 20))
            self.assertEqual(candidate._existing_state("2026-10-19")["state"], "no_go")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "prepared state"):
                candidate.final(self.runner(self.epoch(1, 20)), clock=lambda: self.epoch(1, 20))

    def test_final_guard_subcheck_records_bounded_code(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard", side_effect=candidate.ScheduledF2Error("drift")):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaises(candidate.ScheduledF2Error):
                candidate.final(self.runner(self.epoch(1, 20)), clock=lambda: self.epoch(1, 20))
            self.assertEqual(candidate._existing_state("2026-10-19")["failure_class"], "FINAL_GUARD_SUBCHECK_FAILED")

    def test_final_observer_exit_records_bounded_code(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "no-go"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: NonzeroResult(), clock=lambda: self.epoch(1, 20))
            self.assertEqual(candidate._existing_state("2026-10-19")["failure_class"], "OBSERVER_EXIT_NONZERO")

    def test_final_observer_launch_records_bounded_code(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "launch failed"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: (_ for _ in ()).throw(OSError("hidden")), clock=lambda: self.epoch(1, 20))
            self.assertEqual(candidate._existing_state("2026-10-19")["failure_class"], "OBSERVER_LAUNCH_FAILED")

    def test_final_observer_communication_records_bounded_code(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "communication failed"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: CommunicationFailureResult(), clock=lambda: self.epoch(1, 20))
            saved = candidate._existing_state("2026-10-19")
            self.assertEqual(saved["first_failure_phase"], "final")
            self.assertEqual(saved["failure_class"], "OBSERVER_COMMUNICATION_FAILED")

    def test_first_prepare_failure_survives_final_attempt(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "capture_fixed_preflight", side_effect=candidate.ScheduledF2Error("fixed source failed")):
            with self.assertRaises(candidate.ScheduledF2Error):
                candidate.prepare(self.runner(self.epoch(1, 15)), clock=lambda: self.epoch(1, 15))
            before = candidate._existing_state("2026-10-19")
            self.assertEqual(before["phase"], "prepare")
            self.assertEqual(before["first_failure_phase"], "prepare")
            self.assertEqual(before["failure_class"], "PREFLIGHT_FAILED")
            with self.assertRaises(candidate.ScheduledF2Error):
                candidate.final(self.runner(self.epoch(1, 20)), clock=lambda: self.epoch(1, 20))
            self.assertEqual(candidate._existing_state("2026-10-19"), before)

    def test_final_timeout_records_bounded_class_and_first_phase(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "hard deadline"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: TimeoutResult(), clock=lambda: self.epoch(1, 20))
            saved = candidate._existing_state("2026-10-19")
            self.assertEqual(saved["phase"], "final")
            self.assertEqual(saved["first_failure_phase"], "final")
            self.assertEqual(saved["failure_class"], "OBSERVER_TIMEOUT")
            self.assertIn(saved["failure_class"], candidate.FAILURE_CLASSES)

    def test_final_kills_process_group_on_early_deadline(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"), patch.object(candidate.os, "killpg") as killpg:
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "hard deadline"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: TimeoutResult(), clock=lambda: self.epoch(1, 20))
            killpg.assert_called_once()
            self.assertEqual(candidate._existing_state("2026-10-19")["state"], "no_go")

    def test_final_rejects_oversized_projection_before_parse(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True), patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "oversized"):
                candidate.final(self.runner(self.epoch(1, 20)), popen=lambda *a, **k: OversizedResult(), clock=lambda: self.epoch(1, 20))

    def test_state_rejects_wrong_mode_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(candidate, "STATE_ROOT", Path(tmp)), patch.object(candidate, "_state_root", return_value=Path(tmp)), patch.object(candidate, "_root_custody", return_value=True):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            path = Path(tmp) / "2026-10-19.json"
            path.chmod(0o644)
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "custody"):
                candidate._existing_state("2026-10-19")
            path.unlink()
            path.symlink_to("/etc/hosts")
            with self.assertRaises((candidate.ScheduledF2Error, OSError)):
                candidate._existing_state("2026-10-19")

    def test_state_root_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "real"
            real.mkdir(mode=0o700)
            link = Path(tmp) / "link"
            link.symlink_to(real, target_is_directory=True)
            with patch.object(candidate, "STATE_ROOT", link):
                with self.assertRaisesRegex(candidate.ScheduledF2Error, "symlink"):
                    candidate._state_root()


if __name__ == "__main__":
    unittest.main()
