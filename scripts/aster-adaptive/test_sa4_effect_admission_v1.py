from dataclasses import replace
import copy
import hashlib
import unittest
from unittest.mock import patch

import sa4_effect_admission_v1 as admission
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4EffectAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.candidate = b"candidate bytes\n"
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(base, host_id="effect-admission-test-host",
                              path="/synthetic/admission.json")
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {"host_id": self.target.host_id,
                           "path": self.target.path, "type": "regular-file",
                           "follow_symlinks": False, "owner": "root",
                           "group": "root", "mode": "0644"}
        value["change"]["artifact_sha256"] = hashlib.sha256(self.candidate).hexdigest()
        self.plan_raw = contract.canonical(value); plan_sha = admission.sha256(self.plan_raw)
        self.approval_raw = b"approval\n"; self.approval_proof = b"approval-proof\n"
        self.grant_raw = b"grant\n"; self.grant_proof = b"grant-proof\n"
        self.authenticated = {
            "approval_sha256": admission.sha256(self.approval_raw),
            "approval_proof_sha256": admission.sha256(self.approval_proof),
            "grant_id": "sa4-test-grant",
            "grant_sha256": admission.sha256(self.grant_raw),
            "grant_proof_sha256": admission.sha256(self.grant_proof),
            "approval_expires_epoch": 200, "grant_expires_epoch": 180,
            "grant_consumed": False, "maximum_effects": 0,
            "preflight_eligible": False}
        registration = registry.registration_sha256(self.target)
        self.source = {
            "schema": "aster-sa4-source-preflight-composition.v1",
            "plan_sha256": plan_sha,
            "approval_sha256": self.authenticated["approval_sha256"],
            "approval_proof_sha256": self.authenticated["approval_proof_sha256"],
            "grant_id": self.authenticated["grant_id"],
            "grant_sha256": self.authenticated["grant_sha256"],
            "grant_proof_sha256": self.authenticated["grant_proof_sha256"],
            "filesystem_evidence_sha256": "1" * 64,
            "target_registration_sha256": registration,
            "target_before_sha256": "2" * 64, "checkpoint_sha256": "2" * 64,
            "authority_authenticated": True, "ledger_state": "ready",
            "grant_consumed": False, "filesystem_evidence_valid": True,
            "shared_lock_proven": True, "emergency_stop_proven": True,
            "status": "source-complete-pending-real-trust-and-live-measurement",
            "maximum_effects": 0, "preflight_eligible": False,
            "owner_effect_approval_required": True,
            "automatic_retry": False, "automatic_routing": "off"}
        self.checkpoint = {
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": plan_sha, "measurement_sha256": "3" * 64,
            "target_id": self.target.target_id,
            "target_registration_sha256": registration,
            "checkpoint_epoch": 100, "checkpoint_path": "/synthetic/original",
            "checkpoint_sha256": "2" * 64, "checkpoint_mode": "0600",
            "checkpoint_link_count": 1, "checkpoint_same_filesystem": True,
            "target_unchanged": True, "exclusive_owner_lock": "held-during-create",
            "checkpoint_created": True, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False}
        self.claim = {
            "schema": "aster-sa4-one-use-grant-ledger.v1",
            "grant_id": self.authenticated["grant_id"], "plan_sha256": plan_sha,
            "grant_sha256": self.authenticated["grant_sha256"],
            "target_registration_sha256": registration, "target_sha256": "2" * 64,
            "created_epoch": 90, "expires_epoch": 180, "state": "claimed",
            "use_count": 1, "automatic_retry": False,
            "authority": "one-use-ledger-only", "effect_authorized": False,
            "claimant": "sa4-test-operation", "claimed_epoch": 110,
            "claim_deadline_epoch": 160}

    def admit(self, source=None, claim=None, candidate=None):
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             patch.object(admission.authority, "verify",
                          return_value=self.authenticated):
            return contract.decode_unique_json(admission.admit(
                self.plan_raw, self.approval_raw, self.approval_proof,
                self.grant_raw, self.grant_proof,
                contract.canonical(self.source if source is None else source),
                contract.canonical(self.checkpoint),
                contract.canonical(self.claim if claim is None else claim),
                self.candidate if candidate is None else candidate,
                effect_epoch=120))

    def test_fresh_cross_bound_authority_emits_one_short_lived_effect(self):
        value = self.admit()
        self.assertTrue(value["effect_authorized"])
        self.assertEqual(1, value["maximum_effects"])
        self.assertEqual(160, value["expires_epoch"])
        self.assertFalse(value["automatic_retry"])

    def test_source_claim_or_candidate_drift_fails(self):
        source = copy.deepcopy(self.source); source["approval_sha256"] = "0" * 64
        with self.assertRaises(ValueError): self.admit(source=source)
        claim = copy.deepcopy(self.claim); claim["use_count"] = 0
        with self.assertRaises(ValueError): self.admit(claim=claim)
        with self.assertRaises(ValueError): self.admit(candidate=b"changed\n")

    def test_real_authority_verifier_is_required(self):
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             self.assertRaises(ValueError):
            admission.admit(
                self.plan_raw, self.approval_raw, self.approval_proof,
                self.grant_raw, self.grant_proof, contract.canonical(self.source),
                contract.canonical(self.checkpoint), contract.canonical(self.claim),
                self.candidate, effect_epoch=120)


if __name__ == "__main__":
    unittest.main()
