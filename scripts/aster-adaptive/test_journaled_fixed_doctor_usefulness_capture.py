import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import journaled_fixed_doctor_usefulness_capture as journaled


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"
PROFILE = "a" * 64


class JournaledFixedDoctorUsefulnessCaptureTests(unittest.TestCase):
    def test_interrupted_call_is_durable_and_never_retried(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []

            def interrupted(case):
                calls.append(case["id"])
                raise SystemExit("synthetic interruption")

            with self.assertRaises(SystemExit):
                journaled.capture_journaled(
                    FIXTURE.read_bytes(), PROFILE, interrupted, directory
                )
            events = [json.loads(line) for line in (
                directory / "attempt-journal.jsonl"
            ).read_text().splitlines()]
            self.assertEqual(
                ["run_started", "attempt_started"],
                [event["event"] for event in events],
            )
            with self.assertRaises(FileExistsError):
                journaled.capture_journaled(
                    FIXTURE.read_bytes(), PROFILE, interrupted, directory
                )
            self.assertEqual(["fd-use-01"], calls)

    def test_return_evidence_failure_stops_before_next_request(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []
            original = journaled._write_event

            def fail_return(stream, event):
                if event["event"] == "attempt_returned":
                    raise journaled.EvidenceWriteFailure("synthetic failure")
                return original(stream, event)

            with patch.object(journaled, "_write_event", side_effect=fail_return):
                with self.assertRaises(journaled.EvidenceWriteFailure):
                    journaled.capture_journaled(
                        FIXTURE.read_bytes(), PROFILE,
                        lambda case: calls.append(case["id"]) or "answer", directory,
                    )
            self.assertEqual(["fd-use-01"], calls)
            self.assertFalse((directory / "raw-attempts.json").exists())

    def test_success_seals_capture_and_content_free_summary(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            summary = journaled.capture_journaled(
                FIXTURE.read_bytes(), PROFILE, lambda case: "synthetic answer", directory
            )
            stored = json.loads((directory / "raw-attempts.json").read_text())
            self.assertEqual(8, len(stored["attempts"]))
            self.assertEqual(8, summary["completed"])
            self.assertNotIn("synthetic answer", str(summary))
            self.assertEqual(0o700, directory.stat().st_mode & 0o777)
            self.assertEqual(
                0o600, (directory / "attempt-journal.jsonl").stat().st_mode & 0o777
            )

    def test_adapter_error_is_allowlisted_without_exception_text(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"

            def broken(_case):
                raise ConnectionError("secret-bearing-message")

            summary = journaled.capture_journaled(
                FIXTURE.read_bytes(), PROFILE, broken, directory
            )
            journal = (directory / "attempt-journal.jsonl").read_text()
            self.assertEqual(1, summary["failed"])
            self.assertEqual(7, summary["not_attempted"])
            self.assertIn('"error_code": "unavailable"', journal)
            self.assertNotIn("secret-bearing-message", journal)

    def test_delayed_start_journal_prevents_transport_open(self):
        with tempfile.TemporaryDirectory() as root:
            reads = [0]

            def clock():
                reads[0] += 1
                return 0.0 if reads[0] <= 2 else 550.0

            calls = []

            def answer(case, *, timeout_s):
                calls.append((case["id"], timeout_s))
                return "answer"

            summary = journaled.capture_journaled(
                FIXTURE.read_bytes(), PROFILE, answer, Path(root) / "run",
                clock=clock,
            )
            self.assertEqual([], calls)
            self.assertEqual(0, summary["completed"])
            self.assertEqual(8, summary["not_attempted"])

    def test_invalid_deadline_fails_before_directory_or_call(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            for deadline in (0, float("nan"), 601, True):
                with self.subTest(deadline=deadline):
                    directory = Path(root) / f"run-{str(deadline)}"
                    with self.assertRaises(ValueError):
                        journaled.capture_journaled(
                            FIXTURE.read_bytes(), PROFILE,
                            lambda case: calls.append(case["id"]), directory,
                            max_wall_s=deadline,
                        )
                    self.assertFalse(directory.exists())
            self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()
