from contextlib import redirect_stderr
import io
import json
import unittest
from unittest.mock import patch

import aster_llama_sa3_candidate_j_evidence_matrix_wrapper as wrapper


def valid_result():
    return {
        "schema": "aster-sa3-evidence-matrix-public-result.v1",
        "candidate_alias": "candidate-j", "model": wrapper.MODEL,
        "fixture_sha256": wrapper.PINS[
            "sa3-evidence-matrix-candidate-j-public-v1.json"],
        "case_count": 6, "model_request_count": 2, "retry_count": 0,
        "predictions": [{
            "effects": [], "authority": "none", "error_class": None,
            "prose_source": "deterministic-evidence-matrix",
            "model_requested": index < 2,
        } for index in range(6)],
        "errors": [], "authority": "none", "automatic_routing": "off",
    }


class CandidateJGuestWrapperTests(unittest.TestCase):
    def test_exact_runtime_boundary_excludes_predecessors_and_review(self):
        self.assertEqual(5, len(wrapper.PINS))
        self.assertEqual(6, wrapper.CASES)
        self.assertEqual(2, wrapper.MODEL_REQUESTS)
        self.assertFalse(any("keys" in name or "review" in name
                             for name in wrapper.PINS))

    def test_valid_result_accepts_only_no_effect_zero_error_batch(self):
        wrapper.validate_result(valid_result())
        value = valid_result()
        value["predictions"][0]["effects"] = ["restart"]
        with self.assertRaisesRegex(wrapper.GuestError, "control boundary"):
            wrapper.validate_result(value)
        value = valid_result()
        value["predictions"][2]["model_requested"] = True
        with self.assertRaisesRegex(wrapper.GuestError, "control boundary"):
            wrapper.validate_result(value)
        value = valid_result()
        value["errors"] = [{"id": "x", "class": "TimeoutError"}]
        with self.assertRaisesRegex(
                wrapper.GuestError,
                "result errors:count=1;classes=TimeoutError"):
            wrapper.validate_result(value)

    def test_invocation_mismatch_fails_before_effect(self):
        with self.assertRaisesRegex(wrapper.GuestError, "invocation mismatch"):
            wrapper.run(profile="wrong", port=wrapper.PORT,
                        requests=wrapper.CASES,
                        per_request_timeout=wrapper.PER_REQUEST_TIMEOUT,
                        deadline=wrapper.DEADLINE, lease_id="lease-1",
                        generation=1, scope_unit="wrong",
                        production_check=lambda: True)

    def test_unhandled_exception_retains_only_bounded_class(self):
        output = io.StringIO()
        arguments = ["--profile", wrapper.PROFILE, "--port", str(wrapper.PORT),
                     "--requests", str(wrapper.CASES), "--per-request-timeout",
                     str(wrapper.PER_REQUEST_TIMEOUT), "--deadline",
                     str(wrapper.DEADLINE), "--lease-id", "lease-1",
                     "--generation", "1", "--scope-unit", "fixed-scope"]
        with patch.object(wrapper, "run", side_effect=KeyError("private-value")), \
                redirect_stderr(output):
            self.assertEqual(1, wrapper.main(arguments))
        value = json.loads(output.getvalue())
        self.assertEqual("candidate-j guest exception-class:KeyError",
                         value["code"])
        self.assertNotIn("private-value", output.getvalue())


if __name__ == "__main__":
    unittest.main()
