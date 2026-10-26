import json
import unittest

import nlu_ensemble_candidate_v1 as candidate


def label(disposition="route", sensitivity="public"):
    reason = "understood" if disposition == "route" else "policy-denied"
    return {
        "request_family": "general-answer", "sensitivity": sensitivity,
        "capability_needs": ["facts.answer"], "ambiguity": "clear",
        "disposition": disposition, "reason": reason,
    }


class NluEnsembleCandidateV1Tests(unittest.TestCase):
    def test_payloads_are_deterministic_distinct_and_tool_free(self):
        payloads = [candidate.build_payload("What is rain?", index) for index in range(3)]
        self.assertEqual(3, len(set(payloads)))
        for raw in payloads:
            value = json.loads(raw)
            self.assertEqual(0, value["temperature"])
            self.assertNotIn("tools", value)

    def test_unanimous_vote_has_full_confidence_without_authority(self):
        result = candidate.aggregate([label(), label(), label()])
        self.assertEqual(label(), result["proposal"])
        self.assertEqual(1.0, result["decision_score"])
        self.assertEqual(1.0, result["route_score"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_disagreement_reduces_decision_and_route_confidence(self):
        result = candidate.aggregate([label(), label(), label("deny", "personal")])
        self.assertEqual(label(), result["proposal"])
        self.assertEqual(2 / 3, result["decision_score"])
        self.assertEqual(2 / 3, result["route_score"])

    def test_incomplete_or_invalid_votes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "every perspective"):
            candidate.aggregate([label(), label()])
        invalid = label()
        invalid["reason"] = "unsupported"
        with self.assertRaises(ValueError):
            candidate.aggregate([label(), label(), invalid])


if __name__ == "__main__":
    unittest.main()
