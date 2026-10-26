import json
import math
import unittest

import nlu_ensemble_candidate_v7 as candidate


LABEL = {
    "request_family": "general-answer", "sensitivity": "public",
    "capability_needs": ["facts.answer"], "ambiguity": "clear",
    "disposition": "route", "reason": "understood",
}


def response(label=LABEL, values=(-0.1, -0.3)):
    return json.dumps({"choices": [{
        "message": {"role": "assistant", "content": json.dumps(label)},
        "finish_reason": "stop",
        "logprobs": {"content": [{"logprob": value} for value in values]},
    }]}).encode()


class NluEnsembleCandidateV7Tests(unittest.TestCase):
    def test_payload_requests_logprobs_without_tools(self):
        value = json.loads(candidate.build_payload("Explain lunar phases", 0))
        self.assertIs(value["logprobs"], True)
        self.assertEqual(1, value["top_logprobs"])
        self.assertNotIn("tools", value)

    def test_parser_derives_geometric_token_confidence(self):
        label = candidate.parse_response(response())
        self.assertEqual(LABEL, label)
        self.assertAlmostEqual(math.exp(-0.2), label.model_confidence)

    def test_missing_or_positive_logprob_fails_closed(self):
        for raw in (json.dumps({"choices": [{"message": {}, "finish_reason": "stop",
                                              "logprobs": None}]}).encode(),
                    response(values=(0.1,))):
            with self.assertRaises(ValueError):
                candidate.parse_response(raw)

    def test_aggregate_multiplies_agreement_by_independent_confidence(self):
        labels = [candidate.ScoredLabel(LABEL, value) for value in (0.9, 0.8, 0.7)]
        result = candidate.aggregate_available(labels)
        self.assertAlmostEqual(0.8, result["decision_score"])
        self.assertAlmostEqual(0.8, result["route_score"])
        self.assertEqual("not-granted", result["authority"])


if __name__ == "__main__":
    unittest.main()
