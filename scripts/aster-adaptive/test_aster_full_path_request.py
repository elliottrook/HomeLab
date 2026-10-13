import json
import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from aster_full_path_request import frozen_request_hashes, payload_for, wire_bytes_for


def fixture():
    return {"id": "fictional-00", "class": "calendar_web",
            "fictional_user_request": "Can I attend the fictional gala?",
            "frozen_clock": "2026-10-12T12:00:00Z",
            "synthetic_source_records": [{"type": "fictional", "value": "private fixture"}],
            "private_context_locality_constraint": "local",
            "permitted_capability_set": [], "maximum_tool_scope": "none"}


class AsterFullPathRequestTests(unittest.TestCase):
    def test_exact_no_tool_payload_contains_only_candidate_visible_context(self):
        payload = payload_for(fixture())
        self.assertEqual(payload["enabled_tools"], [])
        self.assertEqual(payload["persona"], "sysadmin")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["max_tokens"], 256)
        self.assertEqual(len(payload["messages"]), 1)
        user = json.loads(payload["messages"][0]["content"])
        self.assertEqual(user["context"], fixture()["synthetic_source_records"])
        self.assertNotIn("id", user)
        self.assertNotIn("class", user)
        self.assertNotIn("expected_answer", str(payload))

    def test_rejects_hidden_key_and_nonzero_tool_scope(self):
        case = fixture()
        case["expected_answer"] = "secret label"
        with self.assertRaises(ValueError):
            payload_for(case)
        case = fixture()
        case["maximum_tool_scope"] = "read_only"
        with self.assertRaises(ValueError):
            payload_for(case)

    def test_private_manifest_hashes_exact_wire_bytes_without_labels(self):
        cases = []
        for i in range(20):
            case = fixture()
            case["id"] = f"fictional-{i:02d}"
            case["fictional_user_request"] += f" ({i})"
            cases.append(case)
        with patch("aster_full_path_request.load_cases", return_value=cases) as loader:
            digests = frozen_request_hashes(b"sealed fixture")
        loader.assert_called_once_with(b"sealed fixture")
        self.assertEqual(len(digests), 20)
        self.assertIn(hashlib.sha256(wire_bytes_for(cases[0])).hexdigest(), digests)
        self.assertNotIn(cases[0]["fictional_user_request"], str(digests))

    def test_private_manifest_rejects_duplicate_wire_requests(self):
        cases = [fixture() for _ in range(20)]
        for i, case in enumerate(cases):
            case["id"] = f"fictional-{i:02d}"
        with patch("aster_full_path_request.load_cases", return_value=cases):
            with self.assertRaisesRegex(ValueError, "duplicate serialized request"):
                frozen_request_hashes(b"sealed fixture")

    def test_private_manifest_rejects_invalid_case_before_hashing(self):
        bad = fixture()
        bad["maximum_tool_scope"] = "read_only"
        with patch("aster_full_path_request.load_cases", return_value=[bad] * 20):
            with self.assertRaisesRegex(ValueError, "invalid frozen no-tool case"):
                frozen_request_hashes(b"sealed fixture")


if __name__ == "__main__":
    unittest.main()
