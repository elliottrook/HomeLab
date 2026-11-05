from contextlib import redirect_stderr
import io
import json
import unittest
from unittest.mock import patch

import aster_llama_sa3_candidate_j_quality_wrapper as wrapper


def valid_result():
    return {"schema": "aster-sa3-evidence-matrix-quality-result.v1",
        "candidate_alias": "candidate-j", "model": wrapper.MODEL,
        "packet_id": wrapper.PROFILE, "packet_sha256": wrapper.PACKET_SHA256,
        "case_count": 20, "model_request_count": 14, "retry_count": 0,
        "predictions": [{"effects": [], "authority": "none",
            "error_class": None, "prose_source": "deterministic-evidence-matrix",
            "model_requested": index < 14} for index in range(20)],
        "errors": [], "authority": "none", "automatic_routing": "off"}


class CandidateJQualityGuestWrapperTests(unittest.TestCase):
    def test_exact_runtime_boundary_is_key_free(self):
        self.assertEqual(4, len(wrapper.PINS))
        self.assertEqual(20, wrapper.CASES)
        self.assertEqual(14, wrapper.MODEL_REQUESTS)
        self.assertEqual(2700, wrapper.DEADLINE)
        self.assertFalse(any("keys" in name or "review" in name or "scorer" in name
                             for name in wrapper.PINS))
        self.assertIn("sa3_evidence_matrix_candidate_j_quality_runtime.py", wrapper.PINS)
        self.assertEqual(wrapper.PACKET_SHA256, wrapper.PINS[
            "sa3-evidence-matrix-candidate-j-quality-v1.json"])

    def test_valid_result_accepts_only_no_effect_zero_error_batch(self):
        wrapper.validate_result(valid_result())
        value = valid_result(); value["predictions"][0]["effects"] = ["restart"]
        with self.assertRaisesRegex(wrapper.GuestError, "control boundary"):
            wrapper.validate_result(value)
        value = valid_result(); value["predictions"][14]["model_requested"] = True
        with self.assertRaisesRegex(wrapper.GuestError, "control boundary"):
            wrapper.validate_result(value)
        value = valid_result(); value["errors"] = [{"id": "x", "class": "TimeoutError"}]
        with self.assertRaisesRegex(wrapper.GuestError, "count=1;classes=TimeoutError"):
            wrapper.validate_result(value)

    def test_packet_identity_and_invocation_drift_fail(self):
        value = valid_result(); value["packet_sha256"] = "0" * 64
        with self.assertRaisesRegex(wrapper.GuestError, "identity or count"):
            wrapper.validate_result(value)
        with self.assertRaisesRegex(wrapper.GuestError, "invocation mismatch"):
            wrapper.run(profile="wrong", port=wrapper.PORT, requests=wrapper.CASES,
                per_request_timeout=wrapper.PER_REQUEST_TIMEOUT,
                deadline=wrapper.DEADLINE, lease_id="lease-1", generation=1,
                scope_unit="wrong", production_check=lambda: True)

    def test_unhandled_exception_retains_only_bounded_class(self):
        output = io.StringIO()
        arguments = ["--profile", wrapper.PROFILE, "--port", str(wrapper.PORT),
            "--requests", str(wrapper.CASES), "--per-request-timeout",
            str(wrapper.PER_REQUEST_TIMEOUT), "--deadline", str(wrapper.DEADLINE),
            "--lease-id", "lease-1", "--generation", "1",
            "--scope-unit", "fixed-scope"]
        with patch.object(wrapper, "run", side_effect=KeyError("private-value")), \
                redirect_stderr(output):
            self.assertEqual(1, wrapper.main(arguments))
        value = json.loads(output.getvalue())
        self.assertEqual("candidate-j quality guest exception-class:KeyError", value["code"])
        self.assertNotIn("private-value", output.getvalue())


if __name__ == "__main__": unittest.main()
