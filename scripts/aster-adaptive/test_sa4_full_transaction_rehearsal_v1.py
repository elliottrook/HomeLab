from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_atomic_repair_owner_v1 as repair_owner
import sa4_atomic_rollback_owner_v1 as rollback_owner
import sa4_authenticated_authority_v1 as rsa
import sa4_effect_admission_v1 as effect_admission
import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_independent_receipt_producer_v1 as postcheck_producer
import sa4_independent_rollback_receipt_producer_v1 as rollback_producer
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_receipt_ledger_reconciler_v1 as reconciler
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_independent_postcheck_receipt_v1 import KEY, sign
from test_sa4_single_file_repair_contract_v1 import plan


def proof_for(raw: bytes) -> bytes:
    value = {
        "schema": "aster-sa4-independent-receipt-proof.v1",
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "observer_id": "aster-observer",
        "observer_key_sha256": rsa.key_sha256(KEY),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "observer-proof-only-no-effect"}
    value["signature_hex"] = sign(contract.canonical(value))
    return contract.canonical(value)


class SA4FullTransactionRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.before = b'{"adapter":"sa4-canary","schema":"old","state":"drifted"}\n'
        self.healthy = (Path(__file__).with_name("fixtures") /
                        "sa4-canary-adapter-healthy-v1.json").read_bytes()
        self.path = root / "canary-adapter.json"
        self.path.write_bytes(self.before); os.chmod(self.path, 0o644)
        checkpoint_parent = root / "checkpoints"; checkpoint_parent.mkdir(mode=0o700)
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(
            base, host_id="sa4-full-rehearsal-host", path=str(self.path),
            checkpoint_parent=str(checkpoint_parent),
            temporary_path=str(root / ".canary-adapter.sa4-tmp"))
        self.ledger = ledger_module.OneUseLedger(
            root / "ledger", expected_uid=os.geteuid())
        self.trusted = {rsa.key_sha256(KEY): {
            "observer_id": "aster-observer", "key": KEY}}

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _root_snapshot(function):
        def wrapped(value, raw):
            result = function(value, raw); result.update(uid=0, gid=0)
            fields = dict(result); fields.pop("metadata_sha256")
            result["metadata_sha256"] = hashlib.sha256(
                contract.canonical(fields)).hexdigest()
            return result
        return wrapped

    def run_transaction(self, candidate: bytes) -> tuple[dict, bytes]:
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {
            "host_id": self.target.host_id, "path": self.target.path,
            "type": "regular-file", "follow_symlinks": False,
            "owner": "root", "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = hashlib.sha256(self.before).hexdigest()
        value["change"]["artifact_sha256"] = hashlib.sha256(candidate).hexdigest()
        plan_raw = contract.canonical(value); plan_sha = hashlib.sha256(plan_raw).hexdigest()
        registration = registry.registration_sha256(self.target)
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.multiple(measurement_owner, LOCAL_HOST_ID=self.target.host_id,
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()):
            measurement = measurement_owner.measure(plan_raw, measurement_epoch=100)
        measurement_raw = contract.canonical(measurement)
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.multiple(checkpoint_owner, LOCAL_HOST_ID=self.target.host_id,
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()):
            checkpoint = checkpoint_owner.create(
                plan_raw, measurement_raw, checkpoint_epoch=105)
        checkpoint_raw = contract.canonical(checkpoint)
        grant_id = "sa4-full-rehearsal-grant"
        grant_sha = "1" * 64
        self.ledger.initialize(
            grant_id=grant_id, plan_sha256=plan_sha, grant_sha256=grant_sha,
            target_registration_sha256=registration,
            target_sha256=hashlib.sha256(self.before).hexdigest(),
            now_epoch=90, expires_epoch=180)
        claim = self.ledger.claim(
            grant_id, claimant="sa4-full-rehearsal-operation",
            now_epoch=110, deadline_epoch=170)
        claim_raw = contract.canonical(claim)
        source_admission_raw = contract.canonical({
            "schema": "aster-sa4-source-preflight-composition.v1",
            "plan_sha256": plan_sha, "approval_sha256": "2" * 64,
            "approval_proof_sha256": "3" * 64, "grant_id": grant_id,
            "grant_sha256": grant_sha, "grant_proof_sha256": "4" * 64,
            "filesystem_evidence_sha256": "5" * 64,
            "target_registration_sha256": registration,
            "target_before_sha256": hashlib.sha256(self.before).hexdigest(),
            "checkpoint_sha256": hashlib.sha256(self.before).hexdigest(),
            "authority_authenticated": True, "ledger_state": "ready",
            "grant_consumed": False, "filesystem_evidence_valid": True,
            "shared_lock_proven": True, "emergency_stop_proven": True,
            "status": "live-measurement-checkpoint-complete",
            "maximum_effects": 0, "preflight_eligible": False,
            "owner_effect_approval_required": True,
            "automatic_retry": False, "automatic_routing": "off"})
        authenticated = {
            "approval_sha256": "2" * 64,
            "approval_proof_sha256": "3" * 64,
            "grant_id": grant_id, "grant_sha256": grant_sha,
            "grant_proof_sha256": "4" * 64,
            "approval_expires_epoch": 180, "grant_expires_epoch": 180,
            "grant_consumed": False, "maximum_effects": 0,
            "preflight_eligible": False}
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(effect_admission.authority, "verify",
                          return_value=authenticated):
            effect_admission_raw = effect_admission.admit(
                plan_raw, b"approval\n", b"approval-proof\n",
                b"grant\n", b"grant-proof\n", source_admission_raw,
                checkpoint_raw, claim_raw, candidate, effect_epoch=120)
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.multiple(repair_owner, LOCAL_HOST_ID=self.target.host_id,
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()):
            terminal = repair_owner.execute(
                plan_raw, effect_admission_raw, checkpoint_raw, claim_raw,
                candidate, operation_id="sa4-full-rehearsal-operation",
                effect_epoch=120)
        terminal_raw = contract.canonical(terminal)

        original_metadata = postcheck_producer.metadata_check.check
        def metadata(value):
            return original_metadata(dict(value, uid=0, gid=0))
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.multiple(postcheck_producer,
                            LOCAL_HOST_ID=self.target.host_id,
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.object(postcheck_producer, "_snapshot",
                          side_effect=self._root_snapshot(
                              postcheck_producer._snapshot)), \
             patch.object(postcheck_producer.metadata_check, "check",
                          side_effect=metadata):
            postcheck_raw = postcheck_producer.observe(
                plan_raw, effect_admission_raw, claim_raw, terminal_raw,
                observed_epoch=130)
        postcheck_proof = proof_for(postcheck_raw)
        postcheck = contract.decode_unique_json(postcheck_raw)

        rollback_terminal_raw = rollback_receipt_raw = rollback_proof = None
        if any(row["state"] != "pass" for row in postcheck["checks"]):
            with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
                 patch.multiple(rollback_owner,
                                LOCAL_HOST_ID=self.target.host_id,
                                EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
                 patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
                rollback_terminal = rollback_owner.restore(
                    plan_raw, checkpoint_raw, terminal_raw,
                    postcheck_raw, postcheck_proof,
                    rollback_attempt_id="sa4-full-rehearsal-rollback",
                    not_before_epoch=110, deadline_epoch=170,
                    rollback_epoch=140)
            rollback_terminal_raw = contract.canonical(rollback_terminal)
            with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
                 patch.multiple(rollback_producer,
                                LOCAL_HOST_ID=self.target.host_id,
                                EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
                 patch.object(rollback_producer, "_snapshot",
                              side_effect=self._root_snapshot(
                                  rollback_producer._snapshot)), \
                 patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
                rollback_receipt_raw = rollback_producer.observe(
                    plan_raw, effect_admission_raw, claim_raw, checkpoint_raw,
                    postcheck_raw, postcheck_proof, rollback_terminal_raw,
                    observed_epoch=150)
            rollback_proof = proof_for(rollback_receipt_raw)

        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
            result = reconciler.reconcile(
                plan_raw, source_admission_raw, effect_admission_raw,
                checkpoint_raw, terminal_raw, postcheck_raw, postcheck_proof,
                self.ledger, now_epoch=155,
                rollback_terminal_raw=rollback_terminal_raw,
                rollback_receipt_raw=rollback_receipt_raw,
                rollback_proof_raw=rollback_proof)
        return result, self.path.read_bytes()

    def test_success_branch_repairs_once_observes_and_burns_uncertain(self):
        result, final = self.run_transaction(self.healthy)
        self.assertEqual(self.healthy, final)
        self.assertTrue(result["postchecks_complete"])
        self.assertIsNone(result["rollback_evidence_complete"])
        self.assertEqual("uncertain", result["ledger_terminal_state"])
        self.assertTrue(result["grant_burned"])
        self.assertFalse(result["effect_outcome_accepted"])

    def test_failure_branch_rolls_back_once_and_burns_failed(self):
        result, final = self.run_transaction(b'{"invalid":"candidate"}\n')
        self.assertEqual(self.before, final)
        self.assertFalse(result["postchecks_complete"])
        self.assertTrue(result["rollback_evidence_complete"])
        self.assertEqual("failed", result["ledger_terminal_state"])
        self.assertTrue(result["grant_burned"])
        self.assertFalse(result["automatic_retry"])


if __name__ == "__main__":
    unittest.main()
