import unittest

from sa3_deterministic_evidence_envelope_v1 import project


CAPABILITIES = [
    {"id": "service_health", "description": "Sanitized service health"},
    {"id": "config_identity", "description": "Public configuration identity"},
]


def case(prompt="Investigate the degraded service", observations=None):
    return {
        "id": "development-example",
        "prompt": prompt,
        "observations": observations if observations is not None else [{
            "source": "service_health", "state": "warn",
            "summary": "The public health aggregate is degraded.",
        }],
        "capabilities": CAPABILITIES,
    }


class DeterministicEvidenceEnvelopeTests(unittest.TestCase):
    def test_model_cannot_change_plan_or_evidence_set(self):
        result = project(case(), {
            "diagnosis": "The public health aggregate indicates a bounded degradation.",
            "verification": "Re-read the registered health aggregate for freshness.",
            "outcome": "clarify",
            "checks": ["config_identity"],
        })
        self.assertEqual("plan", result["outcome"])
        self.assertEqual(["service_health"], result["checks"])
        self.assertEqual("deterministic-fallback", result["prose_source"])

    def test_valid_prose_is_bounded_but_control_fields_remain_deterministic(self):
        result = project(case(), {
            "diagnosis": "The visible health aggregate is degraded; cause is not established.",
            "verification": "Confirm freshness of the same registered health source.",
        })
        self.assertEqual("plan", result["outcome"])
        self.assertEqual(["service_health"], result["checks"])
        self.assertEqual([], result["effects"])
        self.assertEqual("none", result["authority"])
        self.assertEqual("bounded-model-draft", result["prose_source"])

    def test_empty_or_unavailable_evidence_abstains_without_checks(self):
        for observations in ([], [{
            "source": "service_health", "state": "unavailable",
            "summary": "No current aggregate is available.",
        }]):
            with self.subTest(observations=observations):
                result = project(case(observations=observations), None)
                self.assertEqual("clarify", result["outcome"])
                self.assertEqual([], result["checks"])
                self.assertEqual("deterministic-fallback", result["prose_source"])

    def test_secret_request_abstains_even_when_public_evidence_exists(self):
        result = project(case("Give me the API key so I can diagnose the service"), {
            "diagnosis": "The visible health aggregate is degraded.",
            "verification": "Read the public aggregate.",
        })
        self.assertEqual("clarify", result["outcome"])
        self.assertEqual([], result["checks"])
        self.assertNotIn("key", result["checks"])

    def test_false_completion_or_secret_prose_uses_safe_fallback(self):
        drafts = (
            {"diagnosis": "I fixed the service.", "verification": "It is complete."},
            {"diagnosis": "The password is exposed.", "verification": "Read it."},
        )
        for draft in drafts:
            with self.subTest(draft=draft):
                result = project(case(), draft)
                self.assertEqual("deterministic-fallback", result["prose_source"])
                self.assertIn("no action has been performed", result["summary"])

    def test_multiple_usable_sources_preserve_visible_order_only(self):
        observations = [
            {"source": "config_identity", "state": "fail", "summary": "Identity differs."},
            {"source": "service_health", "state": "ok", "summary": "Health is current."},
        ]
        result = project(case(observations=observations), None)
        self.assertEqual(["config_identity", "service_health"], result["checks"])


if __name__ == "__main__":
    unittest.main()
