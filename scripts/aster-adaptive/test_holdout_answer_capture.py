import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import holdout_answer_capture as module


def fixture() -> bytes:
    rows = [{"id": f"fiction-{i:02}", "class": "stable fact",
             "fictional_user_request": "Fictional request",
             "frozen_clock": "2026-01-01T00:00:00Z",
             "synthetic_source_records": [],
             "private_context_locality_constraint": None,
             "permitted_capability_set": [], "maximum_tool_scope": "none"}
            for i in range(20)]
    return b"".join((json.dumps(row) + "\n").encode() for row in rows)


class HoldoutCaptureTests(unittest.TestCase):
    def test_digest_and_label_blind_capture(self):
        raw = fixture()
        seen = []
        with patch.object(module, "CASE_SHA256", hashlib.sha256(raw).hexdigest()):
            result = module.capture(raw, "a" * 64,
                                    lambda case: seen.append(set(case)) or "Fictional answer")
        self.assertEqual(len(seen), 20)
        self.assertTrue(all("rubric_checks" not in keys for keys in seen))
        self.assertTrue(all(row["status"] == "completed" for row in result["attempts"]))
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            module.load_cases(raw + b" ")

    def test_failed_attempt_stops_and_preserves_remaining_rows(self):
        raw = fixture()
        calls = []
        def invoke(case):
            calls.append(case["id"])
            raise TimeoutError()
        with patch.object(module, "CASE_SHA256", hashlib.sha256(raw).hexdigest()):
            result = module.capture(raw, "b" * 64, invoke)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["attempts"][0]["error_code"], "timeout")
        self.assertEqual([r["status"] for r in result["attempts"][1:]],
                         ["not_attempted"] * 19)

    def test_private_save_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as dirname:
            parent = Path(dirname)
            result = {"attempts": [{"status": "completed", "answer": "fiction"}]}
            dest = parent / "one"
            summary = module.save_private(dest, result)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual((dest / "raw-attempts.json").stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                module.save_private(dest, result)


if __name__ == "__main__":
    unittest.main()
