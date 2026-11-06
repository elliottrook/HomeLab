import json
from pathlib import Path
import tempfile
import unittest

import m3_k2_development_transaction as tx


def valid_result(passed=True):
    records = [{"case_id": f"case-{index}"} for index in range(192)]
    return {
        "schema": "aster-m3-k2-development-guest-result.v1",
        "profile": tx.WORKLOAD_ID,
        "journal_sha256": "a" * 64,
        "run": {
            "schema": "aster-nlu-k2-development-run.v1",
            "engine_sha256": "b" * 64, "attempted": 192, "valid": 192,
            "retries": 0, "response_errors": 0, "records": records,
            "failures": [], "elapsed_seconds": 1.0, "complete": True,
            "authority": "not-granted", "automatic_routing": "off",
        },
        "score": {
            "schema": "aster-nlu-k2-development-score.v1",
            "status": "pass" if passed else "reject", "cases": 192,
            "model_requests": 192, "retries": 0, "response_errors": 0,
            "development_gate_passed": passed,
            "authority": "not-granted", "automatic_routing": "off",
        },
    }


class K2TransactionTests(unittest.TestCase):
    def test_pass_and_reject_are_bounded_development_outcomes(self):
        for passed in (True, False):
            metadata = tx.validate_result(valid_result(passed))
            self.assertEqual(passed, metadata["development_gate_passed"])
            self.assertEqual("pass" if passed else "reject", metadata["status"])

    def test_drift_fails_closed(self):
        value = valid_result()
        value["run"]["attempted"] = 191
        with self.assertRaises(tx.TransactionError):
            tx.validate_result(value)

    def test_retained_result_is_owner_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            saved = tx.retain_result(root, valid_result(), expected_uid=root.stat().st_uid)
            path = root / tx.RESULT_FILENAME
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(saved["result_sha256"],
                             tx.validate_result(json.loads(path.read_text()))["result_sha256"])


if __name__ == "__main__":
    unittest.main()
