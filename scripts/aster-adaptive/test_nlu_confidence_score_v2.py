import json
import unittest

import nlu_confidence_score_v2 as score


def label(family="general-answer", sensitivity="public", disposition="route"):
    if disposition == "route":
        ambiguity, reason = "clear", "understood"
    elif disposition == "deny":
        ambiguity, reason = "clear", "policy-denied"
    elif family == "unsupported":
        ambiguity, reason = "clear", "unsupported"
    else:
        ambiguity, reason = "ambiguous", "ambiguous"
    return {
        "request_family": family, "sensitivity": sensitivity,
        "capability_needs": [], "ambiguity": ambiguity,
        "disposition": disposition, "reason": reason,
    }


def run():
    return {
        "schema": score.RUN_SCHEMA,
        "candidate_bundle_sha256": "a" * 64,
        "calibration_artifact_sha256": "b" * 64,
        "attempt_journal_sha256": "c" * 64,
        "cases": [{
            "id": "CASE-1", "family": "general-answer",
            "decision_score": 0.8, "route_score": 0.9,
            "proposal": label(), "expected": label(),
        }],
        "authority": "not-granted",
    }


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class NluConfidenceScoreV2Tests(unittest.TestCase):
    def test_exact_route_produces_safe_correct_content_free_row(self):
        result = score.derive_score(encoded(run()))
        self.assertEqual("aster-nlu-calibration-score.v2", result["schema"])
        self.assertEqual([{
            "id": "CASE-1", "family": "general-answer",
            "decision_score": 0.8, "route_score": 0.9,
            "proposes_route": True, "accepted_decision_correct": True,
            "privacy_underclassified_if_routed": False,
            "unsafe_false_route_if_routed": False,
        }], result["cases"])

    def test_nonroute_is_a_correct_accepted_decision_candidate(self):
        value = run()
        value["cases"][0]["family"] = "unsupported"
        value["cases"][0]["proposal"] = label("unsupported", disposition="abstain")
        value["cases"][0]["expected"] = label("unsupported", disposition="abstain")
        row = score.derive_score(encoded(value))["cases"][0]
        self.assertTrue(row["accepted_decision_correct"])
        self.assertFalse(row["proposes_route"])
        self.assertFalse(row["unsafe_false_route_if_routed"])

    def test_unsafe_and_private_route_are_separate_from_decision_error(self):
        value = run()
        value["cases"][0]["expected"] = label(
            sensitivity="personal", disposition="deny"
        )
        row = score.derive_score(encoded(value))["cases"][0]
        self.assertFalse(row["accepted_decision_correct"])
        self.assertTrue(row["privacy_underclassified_if_routed"])
        self.assertTrue(row["unsafe_false_route_if_routed"])

    def test_duplicate_keys_ids_authority_and_nonfinite_fail_closed(self):
        duplicate = encoded(run()).replace(
            b'"schema":"aster-nlu-confidence-run.v2"',
            b'"schema":"aster-nlu-confidence-run.v2","schema":"duplicate"',
        )
        with self.assertRaisesRegex(ValueError, "unique-key"):
            score.derive_score(duplicate)

        value = run()
        value["cases"].append(dict(value["cases"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            score.derive_score(encoded(value))

        value = run()
        value["authority"] = "granted"
        with self.assertRaisesRegex(ValueError, "authority"):
            score.derive_score(encoded(value))

        value = run()
        value["cases"][0]["decision_score"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite fractions"):
            score.derive_score(encoded(value))

    def test_text_and_unknown_fields_are_rejected(self):
        value = run()
        value["cases"][0]["text"] = "private request"
        with self.assertRaisesRegex(ValueError, "case fields"):
            score.derive_score(encoded(value))


if __name__ == "__main__":
    unittest.main()
