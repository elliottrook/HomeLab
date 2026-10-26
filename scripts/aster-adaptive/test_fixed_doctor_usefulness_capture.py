import json
import tempfile
import unittest
from pathlib import Path

import fixed_doctor_usefulness_capture as capture


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"
PROFILE = "1" * 64


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 0.01
        return self.value


class FixedDoctorUsefulnessCaptureTests(unittest.TestCase):
    def test_complete_capture_is_tool_free_and_non_authoritative(self):
        result = capture.capture(
            FIXTURE.read_bytes(), PROFILE, lambda case: f"answer {case['id']}",
            clock=Clock(),
        )
        self.assertEqual(8, len(result["attempts"]))
        self.assertTrue(all(row["status"] == "completed" for row in result["attempts"]))
        self.assertEqual("disabled", result["tool_mode"])
        self.assertEqual("not-granted", result["authority"])

    def test_failure_stops_subsequent_attempts(self):
        calls = []

        def invoke(case):
            calls.append(case["id"])
            if len(calls) == 2:
                raise TimeoutError
            return "bounded answer"

        result = capture.capture(FIXTURE.read_bytes(), PROFILE, invoke, clock=Clock())
        self.assertEqual(["fd-use-01", "fd-use-02"], calls)
        self.assertEqual("failed", result["attempts"][1]["status"])
        self.assertTrue(all(
            row["status"] == "not_attempted" for row in result["attempts"][2:]
        ))

    def test_fixture_and_profile_drift_fail_closed(self):
        with self.assertRaises(ValueError):
            capture.capture(FIXTURE.read_bytes() + b"\n", PROFILE, lambda case: "answer")
        with self.assertRaises(ValueError):
            capture.capture(FIXTURE.read_bytes(), "short", lambda case: "answer")

    def test_private_save_rejects_git_and_creates_owner_only_file(self):
        result = capture.capture(
            FIXTURE.read_bytes(), PROFILE, lambda case: "answer", clock=Clock()
        )
        with self.assertRaises(ValueError):
            capture.save_private(Path(__file__).resolve().parent / "forbidden", result)
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            parent.chmod(0o700)
            destination = parent / "capture"
            summary = capture.save_private(destination, result)
            self.assertEqual(8, summary["completed"])
            self.assertEqual(0o600, (destination / "raw-attempts.json").stat().st_mode & 0o777)
            stored = json.loads((destination / "raw-attempts.json").read_text())
            self.assertEqual(result, stored)


if __name__ == "__main__":
    unittest.main()
