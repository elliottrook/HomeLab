from __future__ import annotations

import json
import unittest

import nlu_joint_semantic_35b_v1 as candidate


class JointSemantic35BTests(unittest.TestCase):
    def test_payload_is_one_joint_reasoning_request_without_authority(self):
        payload = json.loads(candidate.build_payload("Turn on the kitchen light"))
        self.assertEqual(candidate.MODEL, payload["model"])
        self.assertEqual(0, payload["temperature"])
        self.assertEqual(192, payload["reasoning_budget_tokens"])
        self.assertTrue(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(candidate.RESPONSE_SCHEMA, payload["response_format"]["schema"])
        serialized = json.dumps(payload).lower()
        for forbidden in ("tool_choice", '"tools"', "permission granted"):
            self.assertNotIn(forbidden, serialized)

    def test_policy_contains_no_public_examples_or_private_sets(self):
        policy = candidate.SYSTEM_POLICY.lower()
        for forbidden in (
            "turn on the kitchen light", "pride and prejudice", "lottery",
            "calibration", "holdout", "private cross-set",
        ):
            self.assertNotIn(forbidden, policy)
        self.assertIn("one coherent semantic decision", policy)
        self.assertIn("do not classify fields separately", policy)

    def test_exact_selection_uses_existing_tightening_guard(self):
        label_id = next(
            key for key, value in candidate.CATALOGUE.items()
            if value["capability_needs"] == ["home.control"]
        )
        response = json.dumps({"choices": [{
            "message": {"role": "assistant", "content": json.dumps({"label_id": label_id})},
            "finish_reason": "stop",
        }]}).encode()
        value = candidate.interpret("Turn on the kitchen light", response)
        self.assertEqual(["home.control"], value["capability_needs"])
        self.assertEqual("route", value["disposition"])

    def test_model_identity_is_exact(self):
        with self.assertRaisesRegex(ValueError, "model identity differs"):
            candidate.build_payload("hello", model="other")


if __name__ == "__main__":
    unittest.main()

