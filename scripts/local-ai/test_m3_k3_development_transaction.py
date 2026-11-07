import json
from pathlib import Path
import tempfile
import unittest

import m3_k3_development_transaction as tx


def valid_result(passed=True):
    records = [{"case_id": f"case-{index}"} for index in range(192)]
    return {
        "schema": "aster-m3-k3-development-guest-result.v1",
        "profile": tx.WORKLOAD_ID,
        "journal_sha256": "a" * 64,
        "run": {
            "schema": "aster-nlu-k3-development-run.v1",
            "engine_sha256":
                "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13",
            "attempted": 384, "valid": 192, "retries": 0,
            "response_errors": 0, "records": records, "failures": [],
            "elapsed_seconds": 1.0, "complete": True,
            "authority": "not-granted", "automatic_routing": "off",
        },
        "score": {
            "schema": "aster-nlu-k3-development-score.v1",
            "status": "pass" if passed else "reject", "cases": 192,
            "model_requests": 384, "retries": 0, "response_errors": 0,
            "development_gate_passed": passed,
            "sealed_evaluation_access": False,
            "authority": "not-granted", "automatic_routing": "off",
        },
    }


class K3TransactionTests(unittest.TestCase):
    def test_pass_and_reject_are_bounded_development_outcomes(self):
        for passed in (True, False):
            metadata = tx.validate_result(valid_result(passed))
            self.assertEqual(passed, metadata["development_gate_passed"])
            self.assertEqual("pass" if passed else "reject", metadata["status"])

    def test_engine_and_request_drift_fail_closed(self):
        for field, value in (("engine_sha256", "b" * 64),
                             ("attempted", 383)):
            result = valid_result()
            result["run"][field] = value
            with self.assertRaises(tx.TransactionError):
                tx.validate_result(result)

    def test_retained_result_is_owner_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            saved = tx.retain_result(
                root, valid_result(), expected_uid=root.stat().st_uid)
            path = root / tx.RESULT_FILENAME
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(
                saved["result_sha256"],
                tx.validate_result(json.loads(path.read_text()))["result_sha256"])


if __name__ == "__main__":
    unittest.main()
