import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_authenticated_authority_v1 as authority
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_preflight_composition_v1 as composition
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as target_registry
from test_sa4_authenticated_authority_v1 import inputs as authority_inputs
from test_sa4_filesystem_evidence_v1 import evidence as filesystem_evidence


class SA4PreflightCompositionTests(unittest.TestCase):
    def test_real_target_registration_resolves_before_schema_fixture(self):
        value = composition._registration("sa4-lxc104-canary-adapter-v1")
        self.assertEqual("lxc104", value.host_id)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = ledger_module.OneUseLedger(
            Path(self.temporary.name) / "ledger", expected_uid=os.geteuid())
        values = authority_inputs()
        self.plan_raw, self.approval_raw, self.approval_proof_raw = values[:3]
        self.grant_raw, self.grant_proof_raw, self.trusted = values[3:]
        self.evidence_raw = contract.canonical(
            filesystem_evidence(self.plan_raw))
        grant = contract.decode_unique_json(self.grant_raw)
        self.store.initialize(
            grant_id=grant["grant_id"],
            plan_sha256=authority.sha256(self.plan_raw),
            grant_sha256=authority.sha256(self.grant_raw),
            target_registration_sha256=target_registry.registration_sha256(
                target_registry.resolve_schema_fixture(
                    "sa4-synthetic-fixture")),
            target_sha256=grant["target_sha256"],
            now_epoch=100, expires_epoch=grant["expires_epoch"])

    def tearDown(self):
        self.temporary.cleanup()

    def compose(self):
        with patch.object(authority, "TRUSTED_KEYS", self.trusted):
            return composition.compose(
                self.plan_raw, self.approval_raw, self.approval_proof_raw,
                self.grant_raw, self.grant_proof_raw, self.evidence_raw,
                self.store, 100)

    def test_exact_chain_cross_binds_but_authorizes_zero_effects(self):
        value = self.compose()
        self.assertTrue(value["authority_authenticated"])
        self.assertEqual("ready", value["ledger_state"])
        self.assertTrue(value["filesystem_evidence_valid"])
        self.assertEqual(0, value["maximum_effects"])
        self.assertFalse(value["preflight_eligible"])
        self.assertTrue(value["owner_effect_approval_required"])

    def test_consumed_or_mismatched_ledger_fails_closed(self):
        self.store.claim("synthetic-grant", claimant="synthetic-owner",
                         now_epoch=101, deadline_epoch=120)
        with self.assertRaises(ValueError):
            self.compose()

    def test_empty_trust_registry_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "not compiled"):
            composition.compose(
                self.plan_raw, self.approval_raw, self.approval_proof_raw,
                self.grant_raw, self.grant_proof_raw, self.evidence_raw,
                self.store, 100)

    def test_filesystem_or_grant_drift_fails_closed(self):
        changed = contract.decode_unique_json(self.evidence_raw)
        changed["target"]["bytes_sha256"] = "4" * 64
        with patch.object(authority, "TRUSTED_KEYS", self.trusted), self.assertRaises(ValueError):
            composition.compose(
                self.plan_raw, self.approval_raw, self.approval_proof_raw,
                self.grant_raw, self.grant_proof_raw,
                contract.canonical(changed), self.store, 100)

    def live_values(self):
        target = target_registry.SCHEMA_FIXTURES[0]
        measurement = {
            "schema": "aster-sa4-inactive-target-measurement.v1",
            "plan_sha256": authority.sha256(self.plan_raw),
            "target_id": target.target_id,
            "target_registration_sha256": target_registry.registration_sha256(target),
            "measurement_epoch": 100, "host_id": target.host_id,
            "path": target.path,
            "open_flags": ["O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC"],
            "path_descriptor_stable": True,
            "target_snapshot": {"device": 7, "inode": 8, "uid": 0,
                "gid": 0, "mode": "0644", "link_count": 1, "size": 25,
                "mtime_ns": 9, "ctime_ns": 10, "regular_file": True,
                "bytes_sha256": "2" * 64, "metadata_sha256": "3" * 64},
            "checkpoint_created": False, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False}
        measurement_raw = contract.canonical(measurement)
        checkpoint = {
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": authority.sha256(self.plan_raw),
            "measurement_sha256": authority.sha256(measurement_raw),
            "target_id": target.target_id,
            "target_registration_sha256": target_registry.registration_sha256(target),
            "checkpoint_epoch": 100,
            "checkpoint_path": "/synthetic/checkpoints/sa4-synthetic-single-file-v1.original",
            "checkpoint_sha256": "2" * 64, "checkpoint_mode": "0600",
            "checkpoint_link_count": 1, "checkpoint_same_filesystem": True,
            "target_unchanged": True, "exclusive_owner_lock": "held-during-create",
            "checkpoint_created": True, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False}
        controls = {
            "schema": "aster-sa4-live-runtime-controls.v1",
            "plan_sha256": authority.sha256(self.plan_raw),
            "observed_epoch": 100, "shared_operation_lock": "held",
            "lock_path": "/run/aster-sa4-operation.lock",
            "lock_owner": "sa4-synthetic-single-file-v1",
            "lock_regular_file": True, "lock_link_count": 1,
            "emergency_stop": "armed",
            "emergency_stop_owner": "sa4-synthetic-single-file-v1",
            "automatic_retry": False, "automatic_routing": "off"}
        return target, measurement_raw, contract.canonical(checkpoint), controls

    def test_live_composition_requires_measurement_checkpoint_and_controls(self):
        target, measurement, checkpoint, controls = self.live_values()
        with patch.object(authority, "TRUSTED_KEYS", self.trusted), \
             patch.object(target_registry, "PRODUCTION_TARGETS", (target,)):
            value = composition.compose_live(
                self.plan_raw, self.approval_raw, self.approval_proof_raw,
                self.grant_raw, self.grant_proof_raw, measurement, checkpoint,
                contract.canonical(controls), self.store, 100)
        self.assertEqual("live-measurement-checkpoint-complete", value["status"])
        self.assertTrue(value["shared_lock_proven"])
        self.assertFalse(value["preflight_eligible"])

    def test_live_composition_rejects_disarmed_or_checkpoint_drift(self):
        target, measurement, checkpoint, controls = self.live_values()
        controls["emergency_stop"] = "disarmed"
        with patch.object(authority, "TRUSTED_KEYS", self.trusted), \
             patch.object(target_registry, "PRODUCTION_TARGETS", (target,)), \
             self.assertRaises(ValueError):
            composition.compose_live(
                self.plan_raw, self.approval_raw, self.approval_proof_raw,
                self.grant_raw, self.grant_proof_raw, measurement, checkpoint,
                contract.canonical(controls), self.store, 100)


if __name__ == "__main__":
    unittest.main()
