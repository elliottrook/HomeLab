import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import holdout_answer_9b_adapter as adapter


CASE = {"id": "fiction-1", "fictional_user_request": "What is the fictional answer?",
        "frozen_clock": "2026-01-01T00:00:00Z",
        "synthetic_source_records": [{"source_id": "F1", "content": "fictional"}],
        "private_context_locality_constraint": None,
        "maximum_tool_scope": "none",
        "rubric_checks": ["must never be transmitted"]}


class AdapterTests(unittest.TestCase):
    def test_payload_is_label_blind_and_tool_free(self):
        req = adapter.request_for(CASE, "test-only-key")
        body = json.loads(req.data)
        self.assertEqual(req.full_url, adapter.ENDPOINT)
        self.assertEqual(body["model"], adapter.MODEL)
        self.assertNotIn("tools", body)
        self.assertNotIn("rubric_checks", req.data.decode())
        self.assertNotIn("must never be transmitted", req.data.decode())
        self.assertEqual(body["max_tokens"], 256)

    def test_rejects_tool_scope_and_invalid_response(self):
        with self.assertRaisesRegex(ValueError, "connected tools"):
            adapter.request_for({**CASE, "maximum_tool_scope": "read"}, "test-only-key")
        def mock_request(_request, timeout):
            self.assertEqual(timeout, 60)
            return io.BytesIO(json.dumps({"choices": [{"message": {"content": "fictional"},
                                                       "finish_reason": "length"}]}).encode())
        with self.assertRaisesRegex(ValueError, "terminal"):
            adapter.invoke(CASE, "test-only-key", mock_request)


if __name__ == "__main__":
    unittest.main()
