import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_authenticated_authority_v1 as rsa
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_receipt_ledger_reconciler_v1 as reconciler
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_independent_postcheck_receipt_v1 import (
    KEY, proof_for, rollback_value, values)
from test_sa4_single_file_repair_contract_v1 import plan


class SA4ReceiptLedgerReconcilerTests(unittest.TestCase):
    def test_production_target_resolves_before_schema_fixture(self):
        target = reconciler._registration("sa4-lxc104-canary-adapter-v1")
        self.assertEqual("lxc104", target.host_id)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.ledger = ledger_module.OneUseLedger(
            Path(self.temporary.name) / "ledger", expected_uid=os.geteuid())
        self.plan_raw = contract.canonical(plan())
        self.target = registry.resolve_schema_fixture("sa4-synthetic-fixture")
        self.registration = registry.registration_sha256(self.target)
        self.admission = {
            "schema": "aster-sa4-source-preflight-composition.v1",
            "plan_sha256": reconciler.sha256(self.plan_raw),
            "approval_sha256": "1" * 64, "approval_proof_sha256": "2" * 64,
            "grant_id": "synthetic-grant", "grant_sha256": "3" * 64,
            "grant_proof_sha256": "4" * 64,
            "filesystem_evidence_sha256": "5" * 64,
            "target_registration_sha256": self.registration,
            "target_before_sha256": "2" * 64,
            "checkpoint_sha256": "2" * 64,
            "authority_authenticated": True, "ledger_state": "ready",
            "grant_consumed": False, "filesystem_evidence_valid": True,
            "shared_lock_proven": True, "emergency_stop_proven": True,
            "status": "source-complete-pending-real-trust-and-live-measurement",
            "maximum_effects": 0, "preflight_eligible": False,
            "owner_effect_approval_required": True, "automatic_retry": False,
            "automatic_routing": "off"}
        self.admission_raw = contract.canonical(self.admission)
        self.checkpoint = {
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": reconciler.sha256(self.plan_raw),
            "measurement_sha256": "6" * 64,
            "target_id": self.target.target_id,
            "target_registration_sha256": self.registration,
            "checkpoint_epoch": 100,
            "checkpoint_path": "/synthetic/checkpoints/sa4-synthetic-single-file-v1.original",
            "checkpoint_sha256": "2" * 64, "checkpoint_mode": "0600",
            "checkpoint_link_count": 1, "checkpoint_same_filesystem": True,
            "target_unchanged": True,
            "exclusive_owner_lock": "held-during-create",
            "checkpoint_created": True, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False}
        self.checkpoint_raw = contract.canonical(self.checkpoint)
        self.ledger.initialize(
            grant_id="synthetic-grant",
            plan_sha256=reconciler.sha256(self.plan_raw),
            grant_sha256="3" * 64,
            target_registration_sha256=self.registration,
            target_sha256="2" * 64, now_epoch=90, expires_epoch=150)
        self.claim = self.ledger.claim(
            "synthetic-grant", claimant="sa4-synthetic-operation",
            now_epoch=100, deadline_epoch=140)
        self.claim_sha = reconciler.sha256(contract.canonical(self.claim))
        self.terminal = {
            "schema": "aster-sa4-operation-terminal.v1",
            "operation_id": "sa4-synthetic-operation",
            "plan_sha256": reconciler.sha256(self.plan_raw),
            "admission_sha256": reconciler.sha256(self.admission_raw),
            "claim_sha256": self.claim_sha,
            "checkpoint_owner_sha256": reconciler.sha256(self.checkpoint_raw),
            "checkpoint_sha256": "2" * 64,
            "target_id": self.target.target_id,
            "target_registration_sha256": self.registration,
            "state": "effect-attempted-awaiting-observer", "effect_count": 1,
            "retry_count": 0, "target_before_sha256": "2" * 64,
            "target_after_sha256": "3" * 64, "temporary_absent": True,
            "evidence_retained": True,
            "authority": "operation-owner-assertion-only",
            "automatic_retry": False}
        self.terminal_raw = contract.canonical(self.terminal)
        self.trusted = {rsa.key_sha256(KEY): {
            "observer_id": "sa4-observer", "key": KEY}}

    def tearDown(self):
        self.temporary.cleanup()

    def postcheck(self, states=("pass", "pass", "pass")):
        value, _, _ = values(states)
        value.update(
            plan_sha256=reconciler.sha256(self.plan_raw),
            admission_sha256=reconciler.sha256(self.admission_raw),
            claim_sha256=self.claim_sha,
            effect_terminal_sha256=reconciler.sha256(self.terminal_raw),
            target_registration_sha256=self.registration)
        value["target_snapshot"]["bytes_sha256"] = "3" * 64
        raw = contract.canonical(value)
        return value, raw, proof_for(raw)

    def rollback(self, postcheck_raw, *, complete=True):
        value, _, _ = rollback_value(
            state="complete" if complete else "uncertain",
            health="pass" if complete else "uncertain")
        value.update(
            plan_sha256=reconciler.sha256(self.plan_raw),
            admission_sha256=reconciler.sha256(self.admission_raw),
            claim_sha256=self.claim_sha,
            trigger_postcheck_receipt_sha256=reconciler.sha256(postcheck_raw),
            checkpoint_sha256="2" * 64,
            target_registration_sha256=self.registration)
        value["final_target_snapshot"]["bytes_sha256"] = "2" * 64
        value["checkpoint_snapshot"]["bytes_sha256"] = "2" * 64
        raw = contract.canonical(value)
        return value, raw, proof_for(raw)

    def reconcile(self, postcheck_raw, proof_raw, **kwargs):
        with patch.object(observer, "TRUSTED_OBSERVERS", self.trusted):
            return reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                self.terminal_raw, postcheck_raw, proof_raw, self.ledger,
                now_epoch=130, **kwargs)

    def test_passing_receipts_burn_claim_uncertain_without_accepting_effect(self):
        _, raw, proof = self.postcheck()
        result = self.reconcile(raw, proof)
        self.assertEqual("uncertain", result["ledger_terminal_state"])
        self.assertTrue(result["grant_burned"])
        self.assertFalse(result["effect_outcome_accepted"])
        self.assertEqual(0, result["maximum_effects"])
        self.assertFalse(result["automatic_retry"])
        self.assertEqual("uncertain", self.ledger.get(
            "synthetic-grant")["state"])

    def test_failed_postcheck_with_complete_rollback_burns_failed(self):
        _, raw, proof = self.postcheck(("pass", "fail", "pass"))
        _, rollback_raw, rollback_proof = self.rollback(raw)
        result = self.reconcile(
            raw, proof, rollback_receipt_raw=rollback_raw,
            rollback_proof_raw=rollback_proof)
        self.assertEqual("failed", result["ledger_terminal_state"])
        self.assertTrue(result["rollback_evidence_complete"])
        self.assertEqual("failed", self.ledger.get("synthetic-grant")["state"])

    def test_missing_or_uncertain_rollback_never_becomes_success(self):
        _, raw, proof = self.postcheck(("pass", "uncertain", "pass"))
        with patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
                self.assertRaises(ValueError):
            reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                self.terminal_raw, raw, proof, self.ledger, now_epoch=130)
        self.assertEqual("claimed", self.ledger.get("synthetic-grant")["state"])
        _, rollback_raw, rollback_proof = self.rollback(raw, complete=False)
        result = self.reconcile(
            raw, proof, rollback_receipt_raw=rollback_raw,
            rollback_proof_raw=rollback_proof)
        self.assertEqual("uncertain", result["ledger_terminal_state"])

    def test_empty_observer_registry_and_lineage_drift_fail_before_burn(self):
        value, raw, proof = self.postcheck()
        with self.assertRaises(ValueError):
            reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                self.terminal_raw, raw, proof, self.ledger, now_epoch=130)
        value["claim_sha256"] = "0" * 64
        changed = contract.canonical(value)
        with patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
                self.assertRaises(ValueError):
            reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                self.terminal_raw, changed, proof_for(changed), self.ledger,
                now_epoch=130)
        self.assertEqual("claimed", self.ledger.get("synthetic-grant")["state"])

    def test_duplicate_terminal_and_retry_drift_fail_closed(self):
        _, raw, proof = self.postcheck()
        duplicate = self.terminal_raw.replace(
            b'"retry_count":0', b'"retry_count":0,"retry_count":0')
        with patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
                self.assertRaises(ValueError):
            reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                duplicate, raw, proof, self.ledger, now_epoch=130)
        changed = copy.deepcopy(self.terminal); changed["retry_count"] = 1
        with patch.object(observer, "TRUSTED_OBSERVERS", self.trusted), \
                self.assertRaises(ValueError):
            reconciler.reconcile(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                contract.canonical(changed), raw, proof, self.ledger,
                now_epoch=130)


if __name__ == "__main__":
    unittest.main()
