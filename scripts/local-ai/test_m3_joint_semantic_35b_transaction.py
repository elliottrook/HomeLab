from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import m3_joint_semantic_35b_transaction as transaction


def result():
    records = [{"id": f"c{i}", "valid": True, "interpretation": {}}
               for i in range(24)]
    return {"schema": "aster-m3-joint-semantic-35b-guest-result.v1",
            "result": {"attempted": 24, "valid": 24, "records": records},
            "summary": {"attempted": 24, "valid": 24, "exact": 23,
                        "unsafe_false_routes": 0,
                        "routed_privacy_underclassifications": 0,
                        "authority": "not-granted", "automatic_routing": "off",
                        "public_pass": True},
            "answer_content_retained": False,
            "hidden_reasoning_retained": False}


class TransactionTests(unittest.TestCase):
    def test_exact_result_is_accepted_and_bounded(self):
        value = transaction.validate_guest_result(result())
        self.assertEqual(24, value["request_count"])
        self.assertEqual(23, value["exact"])
        self.assertTrue(value["public_pass"])

    def test_unsafe_privacy_or_content_retention_fails(self):
        for edit in ("unsafe", "privacy", "answer", "reasoning"):
            value = copy.deepcopy(result())
            if edit == "unsafe": value["summary"]["unsafe_false_routes"] = 1
            if edit == "privacy": value["summary"]["routed_privacy_underclassifications"] = 1
            if edit == "answer": value["answer_content_retained"] = True
            if edit == "reasoning": value["hidden_reasoning_retained"] = True
            with self.subTest(edit=edit), self.assertRaises(transaction.TransactionError):
                transaction.validate_guest_result(value)

    def test_retained_result_is_root_only_shape(self):
        if hasattr(Path, "owner"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); root.chmod(0o700)
                if root.stat().st_uid == 0:
                    value = transaction._retain(root, result())
                    self.assertEqual(64, len(value["result_sha256"]))
                    self.assertEqual(0o600, (root / transaction.RESULT_FILENAME).stat().st_mode & 0o777)

    def test_bounded_guest_failure_is_accepted_without_content(self):
        value = transaction.validate_guest_failure({
            "schema": "aster-m3-joint-semantic-35b-guest-failure.v1",
            "state": "failed", "failure_code": "M3_PUBLIC_RESULT_INCOMPLETE",
            "attempted": 1, "valid": 0, "first_record_failure": "http_4xx",
            "answer_content_retained": False,
            "hidden_reasoning_retained": False,
        })
        self.assertEqual({
            "failure_code": "M3_PUBLIC_RESULT_INCOMPLETE", "attempted": 1,
            "valid": 0, "first_record_failure": "http_4xx"}, value)

    def test_unbounded_guest_failure_is_rejected(self):
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_guest_failure({
                "schema": "aster-m3-joint-semantic-35b-guest-failure.v1",
                "state": "failed", "failure_code": "arbitrary",
                "attempted": 1, "valid": 0, "first_record_failure": "secret",
                "answer_content_retained": False,
                "hidden_reasoning_retained": False,
            })


if __name__ == "__main__":
    unittest.main()

