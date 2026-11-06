import copy
import hashlib
import unittest
from unittest.mock import patch

import sa4_authenticated_authority_v1 as rsa
import sa4_independent_postcheck_receipt_v1 as receipt_module
import sa4_target_registry_v1 as registry


N = "b4ac3f2b2cd6f94e174b0b4eb2f4e63337dd66e8290bd8466a690857fc482b0827b7185d2214478616e497cdf3f553e30c7b27df674e1db4e0446d4604df9a358517cdf738efb2ce3a4521289ba67301592da8bc50feec836cfc94ed269104e2e48d3780e396eb771813b2eee925462cffc0956988a026c981b56596c3584ac04cfafbe5afc68475f300251fcf8db869440b1b9f23493371315bf9ea1cfa048227144477e4f112998a2af83b1571d7215e3bcfb06ad8160f3e157a80fd2a5a0b23595eb2e196aa03bcb24fb00f0d17621007f88b4535049ebea27f74ef65dd065978b1900a7f845eb930bec42f722599fe8a08a31e5e4658d512f834372b326d"
D = "9363d1448f97f059dc76c40ab7c341e896b26fb905833c3475aaa9bbdd7ba25f4cc6f98140c3fa755147baefb10d7a19c79cd0b257bc4a4fbc8516000109c8ebd05fd30ed3cbf7ba759edfa6191478cda8caaed4b1dec563920d9c10bb5da2f6d62cbe12cf97d70f98fcb9045dfea279234b2098af74b72fbc39175f1e8d70ac80028e05504e747cf4ca3b97a156a3fc418d8c2a00528353c30b15f6a4172eab968f253959b4278195b51f49d2671804d4f9c8a0e553dd76907e8c508f424106434e16c256d5936748acda03df7569088c8b93fca47f4337a6d93e37b3a58d759c1186905ba37517d991f90714fddb04e1c62d0e54c44265a75f585b1abf63a1"
KEY = {"kty": "RSA", "n": N, "e": 65537}


class SA4ObserverProductionResolutionTests(unittest.TestCase):
    def test_production_target_resolves_before_schema_fixture(self):
        target = receipt_module._registration("sa4-lxc104-canary-adapter-v1")
        self.assertEqual("lxc104", target.host_id)


def sign(message: bytes) -> str:
    digest_info = rsa.DER_SHA256 + hashlib.sha256(message).digest()
    encoded = (b"\x00\x01" + b"\xff" * (256 - len(digest_info) - 3)
               + b"\x00" + digest_info)
    return pow(int.from_bytes(encoded, "big"), int(D, 16), int(N, 16)).to_bytes(
        256, "big").hex()


def proof_for(receipt_raw):
    proof = {"schema": "aster-sa4-independent-receipt-proof.v1",
             "receipt_sha256": receipt_module.sha256(receipt_raw),
             "observer_id": "sa4-observer",
             "observer_key_sha256": rsa.key_sha256(KEY),
             "signature_algorithm": "rsa-pkcs1v1_5-sha256",
             "authority": "observer-proof-only-no-effect"}
    proof["signature_hex"] = sign(receipt_module.canonical(proof))
    return receipt_module.canonical(proof)


def values(states=("pass", "pass", "pass")):
    target = registry.resolve_schema_fixture("sa4-synthetic-fixture")
    check_set = [{"check_id": check_id,
                  "registered_program_sha256": program}
                 for check_id, program in zip(
                     target.postcheck_ids, target.postcheck_program_sha256)]
    receipt = {
        "schema": "aster-sa4-independent-postcheck-receipt.v1",
        "operation_id": "sa4-synthetic-operation",
        "plan_sha256": "1" * 64, "admission_sha256": "2" * 64,
        "claim_sha256": "3" * 64, "effect_terminal_sha256": "4" * 64,
        "target_id": target.target_id,
        "target_registration_sha256": registry.registration_sha256(target),
        "observed_epoch": 120, "observer_id": "sa4-observer",
        "check_set_sha256": receipt_module.sha256(
            receipt_module.canonical(check_set)),
        "checks": [{"check_id": row["check_id"],
                    "registered_program_sha256": row["registered_program_sha256"],
                    "state": state, "measurement_sha256": str(index) * 64}
                   for index, (row, state) in enumerate(zip(check_set, states), 6)],
        "target_snapshot": {"device": 7, "inode": 8, "uid": 0, "gid": 0,
                            "mode": "0644", "link_count": 1, "size": 25,
                            "regular_file": True, "symlink": False,
                            "bytes_sha256": "9" * 64,
                            "metadata_sha256": "a" * 64},
        "temporary_absent": True, "lock_owner": "sa4-synthetic-operation",
        "maximum_effects": 0, "authority": "independent-observer",
        "automatic_retry": False,
    }
    receipt_raw = receipt_module.canonical(receipt)
    return receipt, receipt_raw, proof_for(receipt_raw)


def rollback_value(state="complete", health="pass"):
    target = registry.resolve_schema_fixture("sa4-synthetic-fixture")
    snapshot = {"device": 7, "inode": 8, "uid": 0, "gid": 0,
                "mode": "0644", "link_count": 1, "size": 25,
                "regular_file": True, "symlink": False,
                "bytes_sha256": "9" * 64, "metadata_sha256": "a" * 64}
    checkpoint = dict(snapshot, inode=9, mode="0600",
                      metadata_sha256="b" * 64)
    value = {
        "schema": "aster-sa4-independent-rollback-receipt.v1",
        "operation_id": "sa4-synthetic-operation",
        "plan_sha256": "1" * 64, "admission_sha256": "2" * 64,
        "claim_sha256": "3" * 64,
        "trigger_postcheck_receipt_sha256": "4" * 64,
        "rollback_terminal_sha256": "5" * 64,
        "checkpoint_sha256": "9" * 64,
        "rollback_attempt_id": "sa4-synthetic-rollback",
        "target_id": target.target_id,
        "target_registration_sha256": registry.registration_sha256(target),
        "rollback_program_sha256": target.rollback_program_sha256,
        "observed_epoch": 130, "observer_id": "sa4-observer",
        "rollback_state": state, "final_target_snapshot": snapshot,
        "checkpoint_snapshot": checkpoint, "temporary_absent": True,
        "checkpoint_retained": True, "consumer_health_state": health,
        "evidence_retained": True, "maximum_effects": 0,
        "authority": "independent-observer", "automatic_retry": False,
    }
    raw = receipt_module.canonical(value)
    return value, raw, proof_for(raw)


class SA4IndependentPostcheckReceiptTests(unittest.TestCase):
    def validate(self, receipt_raw, proof_raw):
        trusted = {rsa.key_sha256(KEY): {
            "observer_id": "sa4-observer", "key": KEY}}
        with patch.object(receipt_module, "TRUSTED_OBSERVERS", trusted):
            return receipt_module.validate(
                receipt_raw, proof_raw, not_before_epoch=100,
                deadline_epoch=150)

    def test_exact_authenticated_receipt_remains_zero_effect_evidence(self):
        _, receipt_raw, proof_raw = values()
        result = self.validate(receipt_raw, proof_raw)
        self.assertTrue(result["observer_authenticated"])
        self.assertTrue(result["postchecks_complete"])
        self.assertFalse(result["effect_outcome_accepted"])
        self.assertEqual(0, result["maximum_effects"])

    def test_empty_production_observer_registry_fails_closed(self):
        _, receipt_raw, proof_raw = values()
        with self.assertRaisesRegex(ValueError, "not compiled"):
            receipt_module.validate(receipt_raw, proof_raw,
                                    not_before_epoch=100, deadline_epoch=150)

    def test_fail_or_uncertain_is_retained_not_accepted(self):
        _, receipt_raw, proof_raw = values(("pass", "fail", "uncertain"))
        result = self.validate(receipt_raw, proof_raw)
        self.assertFalse(result["postchecks_complete"])
        self.assertTrue(result["postcheck_failure_or_uncertainty"])
        self.assertFalse(result["automatic_retry"])

    def test_order_program_registration_and_snapshot_drift_fail_closed(self):
        original, _, _ = values()
        variants = []
        value = copy.deepcopy(original); value["checks"].reverse(); variants.append(value)
        value = copy.deepcopy(original); value["checks"][0]["registered_program_sha256"] = "0" * 64; variants.append(value)
        value = copy.deepcopy(original); value["target_registration_sha256"] = "0" * 64; variants.append(value)
        value = copy.deepcopy(original); value["target_snapshot"]["link_count"] = 2; variants.append(value)
        for value in variants:
            raw = receipt_module.canonical(value)
            _, _, proof = values()
            with self.subTest(), self.assertRaises(ValueError):
                self.validate(raw, proof)

    def test_stale_duplicate_and_signature_drift_fail_closed(self):
        value, receipt_raw, proof_raw = values()
        value["observed_epoch"] = 151
        with self.assertRaises(ValueError):
            self.validate(receipt_module.canonical(value), proof_raw)
        duplicate = receipt_raw.replace(
            b'"maximum_effects":0', b'"maximum_effects":0,"maximum_effects":0')
        with self.assertRaises(ValueError):
            self.validate(duplicate, proof_raw)
        proof = bytearray(proof_raw); proof[-3] ^= 1
        with self.assertRaises(ValueError):
            self.validate(receipt_raw, bytes(proof))

    def test_exact_rollback_observation_remains_zero_effect_evidence(self):
        _, raw, proof = rollback_value()
        trusted = {rsa.key_sha256(KEY): {
            "observer_id": "sa4-observer", "key": KEY}}
        with patch.object(receipt_module, "TRUSTED_OBSERVERS", trusted):
            result = receipt_module.validate_rollback(
                raw, proof, not_before_epoch=100, deadline_epoch=150)
        self.assertTrue(result["rollback_evidence_complete"])
        self.assertFalse(result["effect_outcome_accepted"])
        self.assertEqual(0, result["maximum_effects"])

    def test_failed_or_drifted_rollback_requires_manual_reconciliation(self):
        _, raw, proof = rollback_value(state="uncertain", health="uncertain")
        trusted = {rsa.key_sha256(KEY): {
            "observer_id": "sa4-observer", "key": KEY}}
        with patch.object(receipt_module, "TRUSTED_OBSERVERS", trusted):
            result = receipt_module.validate_rollback(
                raw, proof, not_before_epoch=100, deadline_epoch=150)
        self.assertTrue(result["manual_reconciliation_required"])
        self.assertFalse(result["automatic_retry"])

        value, _, _ = rollback_value()
        value["rollback_program_sha256"] = "0" * 64
        changed = receipt_module.canonical(value)
        with patch.object(receipt_module, "TRUSTED_OBSERVERS", trusted), self.assertRaises(ValueError):
            receipt_module.validate_rollback(
                changed, proof_for(changed), not_before_epoch=100,
                deadline_epoch=150)


if __name__ == "__main__":
    unittest.main()
