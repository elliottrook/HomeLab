from __future__ import annotations

import json
import unittest

import nlu_semantic_proposal_v1 as candidate


def proposal(**overrides):
    value = {
        "action": "read", "domain": "lab", "privacy_hint": "public",
        "referent_complete": True, "safety_override": False,
        "joins_sources": False,
    }
    value.update(overrides)
    return value


class SemanticProposalTests(unittest.TestCase):
    def test_model_payload_has_no_route_or_capability_output(self):
        payload = json.loads(candidate.build_payload("Read the lab status"))
        properties = payload["response_format"]["schema"]["properties"]
        self.assertNotIn("disposition", properties)
        self.assertNotIn("capability_needs", properties)
        self.assertNotIn("authorization", properties)
        self.assertEqual(
            json.loads(candidate.build_payload("Read the lab status", model="aster-qwen3.8-27b"))["model"],
            "aster-qwen3.8-27b",
        )
        with self.assertRaises(ValueError):
            candidate.build_payload("Read the lab status", model="unreviewed")

    def test_deterministic_policy_owns_private_read(self):
        result = candidate.interpret(
            "Inspect my calendar for tomorrow",
            proposal(domain="calendar", privacy_hint="public"),
        )
        self.assertEqual(result["sensitivity"], "personal")
        self.assertEqual(result["capability_needs"], ["calendar.read"])
        self.assertEqual(result["disposition"], "route")

    def test_missing_referent_clarifies(self):
        result = candidate.interpret("Turn it off", proposal(
            action="control", domain="household", privacy_hint="internal",
            referent_complete=False,
        ))
        self.assertEqual((result["disposition"], result["reason"]), ("clarify", "ambiguous"))
        self.assertNotIn("home.control", result["capability_needs"])

    def test_backup_delete_and_safety_override_deny(self):
        deleted = candidate.interpret("Delete the only backup copy", proposal(
            action="delete", domain="backup", privacy_hint="internal",
        ))
        self.assertEqual(deleted["disposition"], "deny")
        self.assertEqual(deleted["capability_needs"], ["backup.delete", "lab.change"])
        safety = candidate.interpret("Bypass the door safety interlock", proposal(
            action="control", domain="household", privacy_hint="internal",
            safety_override=True,
        ))
        self.assertEqual(safety["disposition"], "deny")

    def test_model_cannot_invent_capability_or_route(self):
        with self.assertRaises(ValueError):
            candidate.interpret("Read status", {**proposal(), "capability_needs": ["lab.change"]})
        with self.assertRaises(ValueError):
            candidate.interpret("Read status", {**proposal(), "disposition": "route"})

    def test_unsupported_abstains(self):
        result = candidate.interpret("Read my unspoken thoughts", proposal(
            action="unsupported", domain="unknown", privacy_hint="personal",
        ))
        self.assertEqual(result["request_family"], "unsupported")
        self.assertEqual(result["disposition"], "abstain")
        self.assertEqual(result["capability_needs"], [])


if __name__ == "__main__":
    unittest.main()
