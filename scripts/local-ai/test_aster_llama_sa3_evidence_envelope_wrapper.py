import unittest

import aster_llama_sa3_evidence_envelope_wrapper as wrapper


def valid_result():
    return {
        "schema": "aster-sa3-evidence-envelope-result.v1",
        "packet_id": wrapper.PROFILE,
        "packet_sha256": wrapper.PINS["sa3-evidence-envelope-quality-v1.json"],
        "candidate_alias": "candidate-g", "model": wrapper.MODEL,
        "case_count": 20, "model_request_count": 14, "retry_count": 0,
        "predictions": [{"effects": [], "authority": "none", "error_class": None}
                        for _ in range(20)],
        "errors": [], "authority": "none", "automatic_routing": "off",
    }


class CandidateGGuestWrapperTests(unittest.TestCase):
    def test_exact_runtime_boundary_excludes_keys_and_review(self):
        self.assertEqual(5, len(wrapper.PINS))
        self.assertEqual(20, wrapper.CASES)
        self.assertEqual(14, wrapper.MODEL_REQUESTS)
        self.assertFalse(any("keys" in name or "review" in name for name in wrapper.PINS))

    def test_valid_result_accepts_only_no_effect_zero_error_batch(self):
        wrapper.validate_result(valid_result())
        value = valid_result(); value["predictions"][0]["effects"] = ["restart"]
        with self.assertRaisesRegex(wrapper.GuestError, "control boundary"):
            wrapper.validate_result(value)
        value = valid_result(); value["errors"] = [{"id": "x", "error_class": "TimeoutError"}]
        with self.assertRaisesRegex(
                wrapper.GuestError,
                "result errors:count=1;classes=TimeoutError"):
            wrapper.validate_result(value)
        value = valid_result(); value["errors"] = [
            {"id": "x", "error_class": "ValueError"},
            {"id": "y", "error_class": "TimeoutError"},
        ]
        with self.assertRaisesRegex(
                wrapper.GuestError,
                "count=2;classes=TimeoutError,ValueError"):
            wrapper.validate_result(value)

    def test_invocation_mismatch_fails_before_effect(self):
        with self.assertRaisesRegex(wrapper.GuestError, "invocation mismatch"):
            wrapper.run(profile="wrong", port=wrapper.PORT, requests=wrapper.CASES,
                        per_request_timeout=wrapper.PER_REQUEST_TIMEOUT,
                        deadline=wrapper.DEADLINE, lease_id="lease-1", generation=1,
                        scope_unit="wrong", production_check=lambda: True)


if __name__ == "__main__":
    unittest.main()
