import unittest

import nlu_encoder_candidate_v2 as candidate


def label(*, disposition="route", sensitivity="public", capability=None, reason=None):
    return {
        "request_family": "general-answer",
        "sensitivity": sensitivity,
        "capability_needs": [] if capability is None else capability,
        "ambiguity": "clear",
        "disposition": disposition,
        "reason": reason or ("routable" if disposition == "route" else "unsupported"),
    }


class EncoderCandidateV2Tests(unittest.TestCase):
    def test_votes_for_one_reviewed_coherent_label(self):
        left = label(capability=["knowledge.read"])
        right = label(disposition="abstain", sensitivity="personal")
        result = candidate.propose(
            [1.0, 0.0],
            [([1.0, 0.0], left)] * 3 + [([0.8, 0.2], right)] * 2,
            k=5, power=2,
        )
        self.assertIn(result["proposal"], (left, right))
        self.assertEqual(left, result["proposal"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_route_score_uses_weakest_route_safety_support(self):
        public_route = label(capability=["knowledge.read"])
        personal_route = label(sensitivity="personal", capability=["knowledge.read"])
        nonroute = label(disposition="abstain")
        result = candidate.propose(
            [1.0, 0.0],
            [([1.0, 0.0], public_route)] * 3
            + [([0.9, 0.1], personal_route), ([0.8, 0.2], nonroute)],
            k=5, power=1,
        )
        self.assertEqual(public_route, result["proposal"])
        self.assertLess(result["route_score"], 1.0)
        self.assertLessEqual(result["route_score"], result["decision_score"] + 0.4)

    def test_content_free_score_row_separates_decision_and_effect(self):
        expected = label(disposition="abstain", sensitivity="personal")
        result = {
            "proposal": label(sensitivity="public"),
            "decision_score": 0.8,
            "route_score": 0.7,
        }
        row = candidate.score_row(result, expected)
        self.assertFalse(row["accepted_decision_correct"])
        self.assertTrue(row["unsafe_false_route_if_routed"])
        self.assertTrue(row["privacy_underclassified_if_routed"])

    def test_tie_break_is_stable_and_training_order_is_preserved(self):
        first = label(reason="alpha")
        second = label(reason="beta")
        result = candidate.propose(
            [1.0, 0.0],
            [([1.0, 0.0], first), ([1.0, 0.0], second)],
            k=2, power=1,
        )
        self.assertEqual(second, result["proposal"])

    def test_rejects_malformed_inputs(self):
        with self.assertRaises(ValueError):
            candidate.propose([float("nan")], [([1.0], label())], k=1, power=1)
        with self.assertRaises(ValueError):
            candidate.propose([1.0], [([1.0], {"bad": "label"})], k=1, power=1)
        with self.assertRaises(ValueError):
            candidate.propose([1.0], [([1.0], label())], k=0, power=1)

    def test_precomputed_similarity_matches_direct_proposal(self):
        training = [([1.0, 0.0], label(reason="alpha"))] * 3 + [
            ([0.5, 0.5], label(disposition="abstain", reason="beta"))
        ] * 2
        direct = candidate.propose([1.0, 0.0], training, k=5, power=2)
        scored = [
            (candidate._dot([1.0, 0.0], vector), index, candidate._label_key(value))
            for index, (vector, value) in enumerate(training)
        ]
        self.assertEqual(direct, candidate.propose_scored(scored, k=5, power=2))


if __name__ == "__main__":
    unittest.main()
