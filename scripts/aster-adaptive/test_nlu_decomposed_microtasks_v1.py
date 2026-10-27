import json
import unittest

import nlu_decomposed_microtasks_v1 as candidate


def response(task, value):
    return json.dumps({"choices": [{"message": {"role": "assistant", "content": json.dumps({task: value})}, "finish_reason": "stop"}]}).encode()


class DecomposedMicrotaskTests(unittest.TestCase):
    def test_each_payload_exposes_only_one_non_authorizing_field(self):
        for task in candidate.TASKS:
            payload = json.loads(candidate.build_payload("Inspect the server", task))
            self.assertEqual({task}, set(payload["response_format"]["schema"]["properties"]))
            self.assertNotIn("tools", payload)
            self.assertNotIn("authority", json.dumps(payload["response_format"]))

    def test_strict_parser_accepts_only_expected_value(self):
        self.assertEqual("read", candidate.parse_response("action", response("action", "read")))
        self.assertIs(False, candidate.parse_response("referent_complete", response("referent_complete", False)))
        with self.assertRaises(ValueError): candidate.parse_response("action", response("action", "route"))
        with self.assertRaises(ValueError): candidate.parse_response("action", response("domain", "lab"))

    def test_deterministic_policy_assembles_no_authority_label(self):
        answers = {"action": "read", "domain": "calendar", "privacy_hint": "public", "referent_complete": True, "safety_override": False, "joins_sources": False}
        result = candidate.interpret("Inspect my calendar", answers)
        self.assertEqual("personal", result["sensitivity"])
        self.assertEqual(["calendar.read"], result["capability_needs"])
        self.assertEqual("route", result["disposition"])

    def test_incomplete_and_unsupported_fail_closed(self):
        incomplete = {"action": "change", "domain": "lab", "privacy_hint": "internal", "referent_complete": False, "safety_override": False, "joins_sources": False}
        self.assertEqual(("clarify", []), (candidate.interpret("Fix it", incomplete)["disposition"], candidate.interpret("Fix it", incomplete)["capability_needs"]))
        unsupported = dict(incomplete, action="unsupported", domain="unknown", privacy_hint="public", referent_complete=True)
        self.assertEqual("abstain", candidate.interpret("Predict the impossible", unsupported)["disposition"])


if __name__ == "__main__": unittest.main()
