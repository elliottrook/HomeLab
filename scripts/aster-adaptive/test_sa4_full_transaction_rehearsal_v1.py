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
import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_independent_receipt_producer_v1 as postcheck_producer
import sa4_independent_rollback_receipt_producer_v1 as rollback_producer
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_root_transaction_owner_v1 as root_owner
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
        root = Path(self.temporary.name); self.root = root
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
        grant_id = "sa4-full-rehearsal-grant"
        grant_sha = "1" * 64
        self.ledger.initialize(
            grant_id=grant_id, plan_sha256=plan_sha, grant_sha256=grant_sha,
            target_registration_sha256=registration,
            target_sha256=hashlib.sha256(self.before).hexdigest(),
            now_epoch=90, expires_epoch=180)
        authenticated = {
            "approval_sha256": "2" * 64,
            "approval_proof_sha256": "3" * 64,
            "grant_id": grant_id, "grant_sha256": grant_sha,
            "grant_proof_sha256": "4" * 64,
            "approval_expires_epoch": 180, "grant_expires_epoch": 180,
            "grant_consumed": False, "maximum_effects": 0,
            "preflight_eligible": False}
        original_metadata = postcheck_producer.metadata_check.check
        def metadata(value):
            return original_metadata(dict(value, uid=0, gid=0))
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(rsa, "verify", return_value=authenticated), \
             patch.object(root_owner, "BOUND_HOST_ID", self.target.host_id), \
             patch.multiple(root_owner.runtime_owner,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(),
                            EXPECTED_GID=os.getegid(),
                            LOCK_PATH=str(self.root / "operation.lock"),
                            STOP_PATH=str(self.root / "emergency-stop")), \
             patch.multiple(measurement_owner,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.multiple(checkpoint_owner,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.multiple(repair_owner,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.multiple(postcheck_producer,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.multiple(rollback_owner,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.multiple(rollback_producer,
                            LOCAL_HOST_ID="unconfigured",
                            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid()), \
             patch.object(postcheck_producer, "_snapshot",
                          side_effect=self._root_snapshot(
                              postcheck_producer._snapshot)), \
             patch.object(rollback_producer, "_snapshot",
                          side_effect=self._root_snapshot(
                              rollback_producer._snapshot)), \
             patch.object(postcheck_producer.metadata_check, "check",
                          side_effect=metadata), \
             patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
            owner = root_owner.RootTransactionOwner(
                self.ledger, operation_id="sa4-full-rehearsal-operation")
            owner.prepare(
                plan_raw, b"approval\n", b"approval-proof\n",
                b"grant\n", b"grant-proof\n", candidate,
                measurement_epoch=100, checkpoint_epoch=105)
            owner.execute_once(
                claim_epoch=110, claim_deadline_epoch=170,
                effect_epoch=120)
            postcheck_raw = owner.observe(observed_epoch=130)
            branch = owner.accept_postcheck_proof(proof_for(postcheck_raw))
            if branch == "rollback-required":
                rollback_receipt_raw = owner.rollback_once(
                    rollback_attempt_id="sa4-full-rehearsal-rollback",
                    rollback_epoch=140, observed_epoch=150)
                owner.accept_rollback_proof(proof_for(rollback_receipt_raw))
            result = owner.finish(now_epoch=155)
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
