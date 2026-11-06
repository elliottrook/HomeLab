import hashlib
import json
import unittest
from unittest.mock import patch

import nlu_k2_sealed_evaluation_admission_v1 as admission


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def development(passed=True):
    return canonical({
        "schema": "aster-m3-k2-development-reconciliation.v1",
        "state": "complete",
        "booking_id": admission.BOOKING_ID,
        "requests": 192,
        "retries": 0,
        "errors": 0,
        "production_restored": True,
        "development_gate_passed": passed,
        "status": "pass" if passed else "reject",
        "result_sha256": "a" * 64,
    })


class K2SealedEvaluationAdmissionTests(unittest.TestCase):
    def test_complete_pass_and_exact_custody_are_review_eligible(self):
        files = [b"receipt", b"proof", b"disjoint", b"disjoint-proof"]
        constants = ["EVALUATION_RECEIPT_SHA256", "EVALUATION_PROOF_SHA256",
                     "DISJOINTNESS_RECEIPT_SHA256", "DISJOINTNESS_PROOF_SHA256"]
        patches = [patch.object(admission, name, hashlib.sha256(raw).hexdigest())
                   for name, raw in zip(constants, files)]
        for active in patches:
            active.start()
        self.addCleanup(lambda: [active.stop() for active in reversed(patches)])
        with patch.object(admission.custody, "evaluation_receipt", return_value={
                "custodian_id": "independent-j2-evaluation-custodian",
                "evaluation_sha256": "b" * 64,
                "normalized_text_set_sha256": "c" * 64,
             }), patch.object(admission.external, "verify", return_value={
                "signer_key_sha256": admission.EVALUATION_KEY_SHA256,
             }), patch.object(admission.disjointness, "verify", return_value={
                "evaluation_sha256": "b" * 64,
                "evaluation_normalized_text_set_sha256": "c" * 64,
                "intersection_count": 0,
             }):
            result = admission.admit(
                development_raw=development(),
                evaluation_receipt_raw=files[0],
                evaluation_proof_raw=files[1],
                evaluation_key={},
                disjointness_receipt_raw=files[2],
                disjointness_proof_raw=files[3])
        self.assertEqual("eligible-for-sealed-evaluation-effect-review",
                         result["status"])
        self.assertFalse(result["evaluation_effect_authorized"])
        self.assertFalse(result["sealed_evaluation_access"])

    def test_reject_or_unrestored_development_cannot_open_gate(self):
        with self.assertRaisesRegex(ValueError, "development gate"):
            admission._development(development(False))
        value = json.loads(development())
        value["production_restored"] = False
        with self.assertRaisesRegex(ValueError, "development gate"):
            admission._development(canonical(value))

    def test_duplicate_key_development_fails_closed(self):
        with self.assertRaises(ValueError):
            admission._development(
                b'{"schema":"aster-m3-k2-development-reconciliation.v1",'
                b'"schema":"changed"}\n')


if __name__ == "__main__":
    unittest.main()
