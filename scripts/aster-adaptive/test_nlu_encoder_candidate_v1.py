import unittest

import nlu_encoder_candidate_v1 as candidate


def label(disposition="route"):
    return {
        "request_family": "general-answer", "sensitivity": "public",
        "capability_needs": [], "ambiguity": "clear",
        "disposition": disposition,
        "reason": "routable" if disposition == "route" else "unsupported",
    }


class EncoderCandidateTests(unittest.TestCase):
    def test_unanimous_neighbours_accept_exact_proposal_without_authority(self):
        training = [([1.0, 0.0], label()) for _ in range(5)]
        result = candidate.propose([1.0, 0.0], training)
        self.assertTrue(result["accepted"])
        self.assertEqual(label(), result["proposal"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_route_needs_separate_route_support(self):
        route = label()
        stop = label("abstain")
        training = [([1.0, 0.0], route)] * 3 + [([0.99, 0.01], stop)] * 2
        result = candidate.propose([1.0, 0.0], training)
        self.assertEqual("route", result["proposal"]["disposition"])
        self.assertFalse(result["accepted"])

    def test_summary_separates_decision_coverage_from_route_effect(self):
        exact = {"proposal": label(), "accepted": True}
        held = {"proposal": label(), "accepted": False}
        result = candidate.summarize([(exact, label()), (held, label("abstain"))])
        self.assertEqual(0.5, result["decision_coverage"])
        self.assertEqual(1, result["routed"])
        self.assertEqual(0, result["unsafe_false_routes"])

    def test_rejects_nonfinite_vector(self):
        with self.assertRaises(ValueError):
            candidate.propose([float("nan"), 0.0], [([1.0, 0.0], label())] * 5)


if __name__ == "__main__":
    unittest.main()
