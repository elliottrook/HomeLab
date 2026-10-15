"""Offline fictional capture fixtures; no socket or model call."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import holdout_answer_capture as holdout
from a1_full_path_capture import capture_full_path
from a1_headless_client import A1TransportError


def fictional_cases():
    cases = [{"id": f"fictional-{i:02d}", "class": "synthetic",
              "fictional_user_request": "Name the fictional item",
              "frozen_clock": "2026-10-12T12:00:00Z", "synthetic_source_records": [],
              "private_context_locality_constraint": "local",
              "permitted_capability_set": [], "maximum_tool_scope": "none"}
             for i in range(20)]
    return b"".join((json.dumps(case, sort_keys=True) + "\n").encode()
                    for case in cases)


def timing(*, displayed=True):
    return {"schema_version": "aster-client-clock.v0",
            "observation_id": "a" * 32 if displayed else None,
            "http_status": 200 if displayed else None,
            "accepted_to_displayed_ms": 24.0 if displayed else None,
            "terminal_displayed": displayed}


class FullPathCaptureTests(unittest.TestCase):
    def setUp(self):
        self.cases = fictional_cases()
        pin = patch.object(holdout, "CASE_SHA256", hashlib.sha256(self.cases).hexdigest())
        pin.start()
        self.addCleanup(pin.stop)

    def test_success_preserves_answers_privately_and_exports_only_clock_digest(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            timeouts = []

            def successful(case, **kwargs):
                timeouts.append(kwargs["timeout_s"])
                return "fictional answer", timing()

            summary = capture_full_path(self.cases, "a" * 64, directory,
                                        successful)
            rows = [json.loads(line) for line in
                    (directory / "client-clock.jsonl").read_text().splitlines()]
            self.assertEqual(summary["completed"], 20)
            self.assertEqual(summary["client_clock_rows"], 20)
            self.assertEqual(len(rows), 20)
            self.assertEqual(rows[0]["clock"]["accepted_to_displayed_ms"], 24.0)
            self.assertNotIn("fictional answer", str(summary))
            self.assertNotIn("fictional answer", str(rows))
            self.assertIn("fictional answer", (directory / "raw-attempts.json").read_text())
            self.assertEqual((directory / "client-clock.jsonl").stat().st_mode & 0o777, 0o600)
            self.assertEqual(timeouts, [60.0] * 20)

    def test_uncertain_transport_keeps_censored_clock_and_stops_batch(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []

            def uncertain(case, **_):
                calls.append(case["id"])
                raise A1TransportError("unavailable_or_uncertain", timing(displayed=False))

            summary = capture_full_path(self.cases, "b" * 64, directory, uncertain)
            self.assertEqual(calls, ["fictional-00"])
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["not_attempted"], 19)
            row = json.loads((directory / "client-clock.jsonl").read_text())
            self.assertFalse(row["clock"]["terminal_displayed"])
            self.assertEqual(row["error_code"], "unavailable_or_uncertain")

    def test_invalid_clock_stops_before_second_request(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "run"
            calls = []

            def invalid(case, **_):
                calls.append(case["id"])
                return "fictional answer", {**timing(), "secret": "must-not-write"}

            summary = capture_full_path(self.cases, "c" * 64, directory, invalid)
            self.assertEqual(calls, ["fictional-00"])
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["client_clock_rows"], 0)
            self.assertNotIn("must-not-write", (directory / "attempt-journal.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
