import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import holdout_answer_capture as holdout
import journaled_holdout_capture as journaled


def fictional_cases():
    cases = [{"id": f"fictional-{i:02d}", "class": "synthetic",
              "fictional_user_request": "Name the fictional item",
              "frozen_clock": "2026-10-12T12:00:00Z", "synthetic_source_records": [],
              "private_context_locality_constraint": "local",
              "permitted_capability_set": [], "maximum_tool_scope": "none"}
             for i in range(20)]
    return b"".join((json.dumps(case, sort_keys=True) + "\n").encode() for case in cases)


class JournaledCaptureTests(unittest.TestCase):
    def setUp(self):
        self.cases = fictional_cases()
        self.fixture_pin = patch.object(holdout, "CASE_SHA256", hashlib.sha256(self.cases).hexdigest())
        self.fixture_pin.start()
        self.addCleanup(self.fixture_pin.stop)
        self.profile = "a" * 64

    def test_interrupted_call_is_durable_and_never_retried(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []

            def interrupted(case):
                calls.append(case["id"])
                raise SystemExit("synthetic process interruption")

            with self.assertRaises(SystemExit):
                journaled.capture_journaled(self.cases, self.profile, interrupted, directory)
            events = [json.loads(line) for line in (directory / "attempt-journal.jsonl").read_text().splitlines()]
            self.assertEqual([event["event"] for event in events], ["run_started", "attempt_started"])
            self.assertEqual(calls, ["fictional-00"])
            self.assertFalse((directory / "raw-attempts.json").exists())
            with self.assertRaises(FileExistsError):
                journaled.capture_journaled(self.cases, self.profile, interrupted, directory)
            self.assertEqual(calls, ["fictional-00"])

    def test_post_call_evidence_failure_stops_before_next_request(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []
            write_event = journaled._write_event

            def fail_returned(stream, event):
                if event["event"] == "attempt_returned":
                    raise journaled.EvidenceWriteFailure("synthetic storage failure")
                return write_event(stream, event)

            def answer(case):
                calls.append(case["id"])
                return "fictional answer"

            with patch.object(journaled, "_write_event", side_effect=fail_returned):
                with self.assertRaises(journaled.EvidenceWriteFailure):
                    journaled.capture_journaled(self.cases, self.profile, answer, directory)
            self.assertEqual(calls, ["fictional-00"])
            self.assertFalse((directory / "raw-attempts.json").exists())
            self.assertEqual((directory / "attempt-journal.jsonl").stat().st_mode & 0o777, 0o600)

    def test_success_seals_same_capture_envelope_without_answer_in_summary(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            summary = journaled.capture_journaled(
                self.cases, self.profile, lambda case: "fictional answer", directory)
            capture = json.loads((directory / "raw-attempts.json").read_text())
            self.assertEqual(capture["schema_version"], "aster-answer-holdout-capture.v1")
            self.assertEqual(len(capture["attempts"]), 20)
            self.assertEqual(summary["completed"], 20)
            self.assertNotIn("fictional answer", str(summary))
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual((directory / "raw-attempts.json").stat().st_mode & 0o777, 0o600)

    def test_adapter_error_is_allowlisted_without_secret_bearing_message(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []

            def broken(case):
                calls.append(case["id"])
                raise ConnectionError("synthetic-token-do-not-record")

            summary = journaled.capture_journaled(self.cases, self.profile, broken, directory)
            journal = (directory / "attempt-journal.jsonl").read_text()
            capture = json.loads((directory / "raw-attempts.json").read_text())
            self.assertEqual(calls, ["fictional-00"])
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["not_attempted"], 19)
            self.assertIn('"error_code": "unavailable"', journal)
            self.assertNotIn("synthetic-token-do-not-record", journal)
            self.assertEqual(capture["attempts"][0]["error_code"], "unavailable")

    def test_invalid_deadline_is_rejected_before_evidence_or_model_call(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []
            for deadline in (0, float("nan"), 901, True):
                with self.subTest(deadline=deadline):
                    with self.assertRaisesRegex(ValueError, "deadline"):
                        journaled.capture_journaled(
                            self.cases, self.profile,
                            lambda case: calls.append(case["id"]),
                            directory, max_wall_s=deadline)
                    self.assertFalse(directory.exists())
            self.assertEqual(calls, [])

    def test_final_envelope_write_failure_preserves_all_returned_answers(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            with patch.object(journaled.os, "replace", side_effect=OSError("synthetic rename failure")):
                with self.assertRaises(journaled.EvidenceWriteFailure):
                    journaled.capture_journaled(
                        self.cases, self.profile, lambda case: "fictional answer", directory)
            events = [json.loads(line) for line in (directory / "attempt-journal.jsonl").read_text().splitlines()]
            self.assertEqual(sum(event["event"] == "attempt_returned" for event in events), 20)
            self.assertFalse((directory / "raw-attempts.json").exists())
            self.assertFalse((directory / "raw-attempts.json.tmp").exists())

    def test_full_path_deadline_never_starts_case_without_full_call_budget(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            reads = [0]

            def clock():
                reads[0] += 1
                return 0.0 if reads[0] <= 2 else 1150.0
            calls = []

            def answer(case, *, timeout_s):
                calls.append((case["id"], timeout_s))
                return "fictional answer"

            summary = journaled.capture_journaled(
                self.cases, self.profile, answer, directory,
                clock=clock, max_wall_s=1200,
                allow_full_path_20m=True)
            self.assertEqual(calls, [])
            self.assertEqual(summary["completed"], 0)
            self.assertEqual(summary["not_attempted"], 20)

    def test_extended_deadline_requires_explicit_full_path_flag(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "deadline"):
                journaled.capture_journaled(self.cases, self.profile,
                                            lambda case: "fictional answer",
                                            Path(root) / "run", max_wall_s=1200)


if __name__ == "__main__":
    unittest.main()
