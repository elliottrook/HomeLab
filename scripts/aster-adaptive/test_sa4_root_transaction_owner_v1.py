import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import nullcontext

import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_root_transaction_owner_v1 as owner_module
import sa4_single_file_repair_contract_v1 as contract
from test_sa4_single_file_repair_contract_v1 import plan


class SA4RootTransactionOwnerTests(unittest.TestCase):
    class Controls:
        def __init__(self, _plan): self.retained = False
        def acquire(self): pass
        def observe(self, _epoch): return b"fresh-controls\n"
        def ensure_armed(self): pass
        def retain_uncertain(self): self.retained = True
        def release_terminal(self): pass

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.ledger = ledger_module.OneUseLedger(
            Path(self.temporary.name) / "ledger", expected_uid=os.geteuid())
        self.candidate = b"candidate\n"
        value = plan()
        value["change"]["artifact_sha256"] = hashlib.sha256(
            self.candidate).hexdigest()
        self.plan_raw = contract.canonical(value)
        self.ledger.initialize(
            grant_id="root-owner-grant",
            plan_sha256=hashlib.sha256(self.plan_raw).hexdigest(),
            grant_sha256="1" * 64,
            target_registration_sha256="2" * 64,
            target_sha256=value["precondition"]["expected_sha256"],
            now_epoch=90, expires_epoch=180)
        self.owner = owner_module.RootTransactionOwner(
            self.ledger, operation_id="root-owner-operation")

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self):
        with patch.object(owner_module.authority, "verify",
                          return_value={"authenticated": True}), \
             patch.object(owner_module.measurement_owner, "measure",
                          return_value={"measurement": "fixed"}), \
             patch.object(owner_module.checkpoint_owner, "create",
                          return_value={"checkpoint": "fixed"}), \
             patch.object(owner_module.runtime_owner, "RuntimeControlOwner",
                          self.Controls), \
             patch.object(owner_module, "_fixed_bindings",
                          side_effect=lambda _plan: nullcontext()):
            return self.owner.prepare(
                self.plan_raw, b"approval\n", b"approval-proof\n",
                b"grant\n", b"grant-proof\n", self.candidate,
                measurement_epoch=99,
                checkpoint_epoch=100)

    def execute(self):
        with patch.object(owner_module.preflight, "compose_live",
                          return_value={"grant_id": "root-owner-grant"}), \
             patch.object(owner_module.effect_admission, "admit",
                          return_value=b"admission\n"), \
             patch.object(owner_module.repair_owner, "execute",
                          return_value={"terminal": "fixed"}), \
             patch.object(owner_module, "_fixed_bindings",
                          side_effect=lambda _plan: nullcontext()):
            return self.owner.execute_once(
                claim_epoch=110, claim_deadline_epoch=170,
                effect_epoch=120)

    def test_success_path_is_ordered_and_has_no_retry(self):
        self.prepare(); self.execute()
        with patch.object(owner_module.receipt_producer, "observe",
                          return_value=b"postcheck\n"), \
             patch.object(owner_module, "_fixed_bindings",
                          side_effect=lambda _plan: nullcontext()):
            self.assertEqual(b"postcheck\n",
                             self.owner.observe(observed_epoch=130))
        with patch.object(owner_module.receipt_validator, "validate",
                          return_value={"postchecks_complete": True}):
            self.assertEqual("ready-to-reconcile",
                             self.owner.accept_postcheck_proof(b"proof\n"))
        with patch.object(owner_module.reconciler, "reconcile",
                          return_value={"grant_burned": True}) as called:
            self.assertEqual({"grant_burned": True},
                             self.owner.finish(now_epoch=140))
        self.assertEqual("terminal", self.owner.phase)
        self.assertEqual(1, called.call_count)
        self.assertFalse(hasattr(self.owner, "retry"))

    def test_phase_skips_and_second_effect_fail_closed(self):
        with self.assertRaises(ValueError):
            self.owner.execute_once(
                claim_epoch=110, claim_deadline_epoch=170,
                effect_epoch=120)
        self.prepare(); self.execute()
        with self.assertRaises(ValueError):
            self.execute()

    def test_effect_exception_becomes_manual_uncertainty(self):
        self.prepare()
        with patch.object(owner_module.preflight, "compose_live",
                          return_value={"grant_id": "root-owner-grant"}), \
             patch.object(owner_module.effect_admission, "admit",
                          side_effect=RuntimeError("injected")), \
             self.assertRaises(RuntimeError):
            self.owner.execute_once(
                claim_epoch=110, claim_deadline_epoch=170,
                effect_epoch=120)
        self.assertEqual("uncertain-manual-reconciliation-required",
                         self.owner.phase)
        with self.assertRaises(ValueError):
            self.owner.finish(now_epoch=140)


if __name__ == "__main__":
    unittest.main()
