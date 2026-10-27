from __future__ import annotations

import json
import unittest

import nlu_whole_label_choice_v1 as v1
import nlu_whole_label_choice_v2 as v2


class WholeLabelChoiceV2Tests(unittest.TestCase):
    def test_revision_changes_only_public_rubric(self):
        self.assertIs(v1.CATALOGUE, v2.CATALOGUE)
        self.assertIs(v1.RESPONSE_SCHEMA, v2.RESPONSE_SCHEMA)
        self.assertIs(v1.interpret, v2.interpret)
        self.assertNotEqual(v1.SYSTEM_POLICY, v2.SYSTEM_POLICY)
        self.assertIn("Doctor diagnostic status", v2.RUBRIC)
        self.assertIn("impossible, unknowable or unobservable", v2.RUBRIC)

    def test_payload_remains_selection_only_and_tool_free(self):
        payload = json.loads(v2.build_payload("Restart the news service"))
        self.assertNotIn("tools", payload)
        self.assertEqual({"label_id"}, set(payload["response_format"]["schema"]["properties"]))
        self.assertEqual(32, payload["max_tokens"])
        self.assertEqual(0, payload["temperature"])

    def test_parser_and_safety_boundary_are_unchanged(self):
        label_id = next(
            key for key, value in v2.CATALOGUE.items()
            if value["request_family"] == "general-answer"
            and value["disposition"] == "route"
        )
        raw = json.dumps({"choices": [{
            "message": {"role": "assistant", "content": json.dumps({"label_id": label_id})},
            "finish_reason": "stop",
        }]}).encode()
        result = v2.interpret("Read another person's thoughts", raw)
        self.assertEqual(("unsupported", "abstain"), (
            result["request_family"], result["disposition"],
        ))


if __name__ == "__main__":
    unittest.main()
