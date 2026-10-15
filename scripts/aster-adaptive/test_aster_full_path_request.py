import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aster_full_path_request import payload_for


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


if __name__ == "__main__":
    unittest.main()
