from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_authenticated_authority_v1 as rsa
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_independent_rollback_receipt_producer_v1 as producer
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_independent_postcheck_receipt_v1 import KEY, sign
from test_sa4_single_file_repair_contract_v1 import plan


def proof_for(raw: bytes) -> bytes:
    value = {
        "schema": "aster-sa4-independent-receipt-proof.v1",
        "receipt_sha256": producer.sha256(raw),
        "observer_id": producer.OBSERVER_ID,
        "observer_key_sha256": rsa.key_sha256(KEY),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "observer-proof-only-no-effect",
    }
    value["signature_hex"] = sign(contract.canonical(value))
    return contract.canonical(value)


class SA4IndependentRollbackReceiptProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.before = b'{"adapter":"sa4-canary","schema":"old","state":"drifted"}\n'
        self.path = root / "canary.json"
        self.path.write_bytes(self.before); os.chmod(self.path, 0o644)
        checkpoint_parent = root / "checkpoints"; checkpoint_parent.mkdir(mode=0o700)
        self.checkpoint_path = checkpoint_parent / "sa4-test-plan.original"
        self.checkpoint_path.write_bytes(self.before); os.chmod(self.checkpoint_path, 0o600)
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(
            base, host_id="rollback-observer-test-host", path=str(self.path),
            checkpoint_parent=str(checkpoint_parent),
            temporary_path=str(root / ".canary.tmp"))
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {
            "host_id": self.target.host_id, "path": self.target.path,
            "type": "regular-file", "follow_symlinks": False,
            "owner": "root", "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = hashlib.sha256(self.before).hexdigest()
        value["change"]["artifact_sha256"] = "a" * 64
        self.plan_raw = contract.canonical(value)
        plan_sha = producer.sha256(self.plan_raw)
        self.admission_raw = contract.canonical({
            "schema": "aster-sa4-effect-admission.v1", "plan_sha256": plan_sha,
            "effect_authorized": True, "maximum_effects": 1,
            "automatic_retry": False})
        self.claim_raw = contract.canonical({
            "state": "claimed", "use_count": 1, "plan_sha256": plan_sha,
            "claimant": "sa4-test-operation", "claimed_epoch": 100,
            "claim_deadline_epoch": 150})
        registration = registry.registration_sha256(self.target)
        self.checkpoint_raw = contract.canonical({
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": plan_sha, "target_id": self.target.target_id,
            "target_registration_sha256": registration,
            "checkpoint_path": str(self.checkpoint_path),
            "checkpoint_sha256": hashlib.sha256(self.before).hexdigest(),
            "checkpoint_created": True})
        check_set = [{"check_id": check_id,
                      "registered_program_sha256": program}
                     for check_id, program in zip(
                         self.target.postcheck_ids,
                         self.target.postcheck_program_sha256)]
        snapshot = {"device": 7, "inode": 8, "uid": 0, "gid": 0,
                    "mode": "0644", "link_count": 1, "size": 12,
                    "regular_file": True, "symlink": False,
                    "bytes_sha256": "b" * 64, "metadata_sha256": "c" * 64}
        trigger = {
            "schema": "aster-sa4-independent-postcheck-receipt.v1",
            "operation_id": "sa4-test-operation", "plan_sha256": plan_sha,
            "admission_sha256": producer.sha256(self.admission_raw),
            "claim_sha256": producer.sha256(self.claim_raw),
            "effect_terminal_sha256": "d" * 64,
            "target_id": self.target.target_id,
            "target_registration_sha256": registration,
            "observed_epoch": 115, "observer_id": producer.OBSERVER_ID,
            "check_set_sha256": producer.sha256(contract.canonical(check_set)),
            "checks": [{"check_id": row["check_id"],
                        "registered_program_sha256": row["registered_program_sha256"],
                        "state": "fail" if index == 0 else "pass",
                        "measurement_sha256": str(index + 2) * 64}
                       for index, row in enumerate(check_set)],
            "target_snapshot": snapshot, "temporary_absent": True,
            "lock_owner": "sa4-test-operation", "maximum_effects": 0,
            "authority": "independent-observer", "automatic_retry": False}
        self.trigger_raw = contract.canonical(trigger)
        self.trigger_proof = proof_for(self.trigger_raw)
        self.rollback_terminal_raw = contract.canonical({
            "schema": "aster-sa4-rollback-terminal.v1",
            "operation_id": "sa4-test-operation",
            "rollback_attempt_id": "sa4-test-rollback",
            "plan_sha256": plan_sha,
            "trigger_postcheck_receipt_sha256": producer.sha256(self.trigger_raw),
            "checkpoint_sha256": hashlib.sha256(self.before).hexdigest(),
            "target_id": self.target.target_id,
            "target_registration_sha256": registration,
            "rollback_epoch": 120, "rollback_effect_count": 1,
            "retry_count": 0, "temporary_absent": True,
            "checkpoint_retained": True,
            "authority": "rollback-owner-assertion-only",
            "automatic_retry": False})
        self.trusted = {rsa.key_sha256(KEY): {
            "observer_id": producer.OBSERVER_ID, "key": KEY}}

    def tearDown(self):
        self.temporary.cleanup()

    def observe(self) -> bytes:
        original_snapshot = producer._snapshot
        def root_snapshot(value, raw):
            result = original_snapshot(value, raw)
            result.update(uid=0, gid=0)
            fields = dict(result); fields.pop("metadata_sha256")
            result["metadata_sha256"] = producer.sha256(
                contract.canonical(fields))
            return result
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(producer, "LOCAL_HOST_ID", self.target.host_id), \
             patch.object(producer, "EXPECTED_UID", os.geteuid()), \
             patch.object(producer, "EXPECTED_GID", os.getegid()), \
             patch.object(producer, "_snapshot", side_effect=root_snapshot), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
            return producer.observe(
                self.plan_raw, self.admission_raw, self.claim_raw,
                self.checkpoint_raw, self.trigger_raw, self.trigger_proof,
                self.rollback_terminal_raw, observed_epoch=130)

    def test_complete_restoration_produces_valid_cross_bound_receipt(self):
        raw = self.observe(); value = contract.decode_unique_json(raw)
        self.assertEqual("complete", value["rollback_state"])
        self.assertEqual("pass", value["consumer_health_state"])
        self.assertEqual(producer.sha256(self.rollback_terminal_raw),
                         value["rollback_terminal_sha256"])
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
            checked = observer.validate_rollback(
                raw, proof_for(raw), not_before_epoch=115, deadline_epoch=150)
        self.assertTrue(checked["rollback_evidence_complete"])

    def test_changed_target_is_retained_as_failed_not_complete(self):
        self.path.write_bytes(b"changed\n")
        raw = self.observe(); value = contract.decode_unique_json(raw)
        self.assertEqual("failed", value["rollback_state"])
        self.assertEqual("fail", value["consumer_health_state"])
        self.assertEqual(0, value["maximum_effects"])

    def test_committed_source_is_inactive_and_terminal_drift_fails(self):
        self.assertEqual("unconfigured", producer.LOCAL_HOST_ID)
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
             self.assertRaises(ValueError):
            producer.observe(
                self.plan_raw, self.admission_raw, self.claim_raw,
                self.checkpoint_raw, self.trigger_raw, self.trigger_proof,
                self.rollback_terminal_raw, observed_epoch=130)
        changed = self.rollback_terminal_raw.replace(
            b'"retry_count":0', b'"retry_count":1')
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(producer, "LOCAL_HOST_ID", self.target.host_id), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
             self.assertRaises(ValueError):
            producer.observe(
                self.plan_raw, self.admission_raw, self.claim_raw,
                self.checkpoint_raw, self.trigger_raw, self.trigger_proof,
                changed, observed_epoch=130)


if __name__ == "__main__":
    unittest.main()
