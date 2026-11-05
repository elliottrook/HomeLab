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


if __name__ == "__main__":
    unittest.main()
