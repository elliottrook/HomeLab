import unittest

from nlu_deterministic_crossset import guarded_model, leave_one_set_out, summarize


def label(family="general-answer", disposition="route", sensitivity="public"):
    return {"request_family": family, "sensitivity": sensitivity,
            "capability_needs": ["facts.answer"] if family == "general-answer" else ["web.read"],
            "ambiguity": "clear", "disposition": disposition,
            "reason": "understood" if disposition == "route" else "ambiguous"}


class NLUDeterministicCrosssetTests(unittest.TestCase):
    def test_summary_uses_total_case_coverage_and_rejects_error(self):
        good = label()
        wrong = label("external-research")
        result = summarize([(good, good)] * 36 + [(wrong, good)] * 5 +
                           [(dict(good, ambiguity="ambiguous", disposition="clarify", reason="ambiguous"), good)] * 19,
                           attempted=60)
        self.assertAlmostEqual(41 / 60, result["coverage"])
        self.assertFalse(result["eligible"])

    def test_guarded_model_fails_closed_on_nonroute(self):
        target = {**label(disposition="clarify"), "ambiguity": "ambiguous"}
        proposal = {**target, "schema_version": "request-interpretation.v1",
                    "request_id": "r", "principal_ref": "p", "confidence": None,
                    "authorization": "not-granted", "engine_digest": "a" * 64,
                    "policy_digest": "b" * 64}
        result = guarded_model([{"text": "clarify this", "label": target, "proposal": proposal}])
        self.assertEqual(0, result["routed"])

    def test_leave_one_set_out_returns_content_free_counts(self):
        a = [{"text": "answer the factual question", "label": label()} for _ in range(2)]
        b = [{"text": "explain the factual answer", "label": label()} for _ in range(2)]
        result = leave_one_set_out([a, b])
        self.assertEqual(2, len(result))
        self.assertEqual(2, result[0]["attempted"])
        self.assertNotIn("text", result[0])


if __name__ == "__main__":
    unittest.main()
