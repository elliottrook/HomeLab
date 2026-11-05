import copy
import unittest

import sa4_single_file_repair_contract_v1 as contract
import sa4_single_file_repair_receipt_v1 as receipt
from test_sa4_single_file_repair_contract_v1 import evidence, plan


def inputs():
    plan_raw = contract.canonical(plan())
    admission = contract.admit(plan_raw, *evidence(plan_raw), now_epoch=100)
    admission_raw = contract.canonical(admission)
    terminal = {
        "schema": "aster-sa4-single-file-repair-terminal.v1",
        "plan_sha256": contract.sha256(plan_raw),
        "admission_sha256": contract.sha256(admission_raw),
        "state": "no_go", "effect_count": 0, "retry_count": 0,
        "precondition_sha256": "2" * 64,
        "observed_after_sha256": "2" * 64,
        "checkpoint_sha256": "2" * 64,
        "postchecks": {name: "not-run" for name in contract.POSTCHECKS},
        "rollback_performed": False, "final_target_sha256": "2" * 64,
        "evidence_retained": True, "authority": "one-use-consumed",
        "automatic_routing": "off",
    }
    return plan_raw, admission_raw, terminal


class SA4SingleFileRepairReceiptTests(unittest.TestCase):
    def reconcile(self, terminal):
        plan_raw, admission_raw, _ = inputs()
        return receipt.reconcile(plan_raw, admission_raw,
                                 contract.canonical(terminal))

    def test_schema_prototype_rejects_claimed_completion(self):
        _, _, terminal = inputs(); terminal.update(
            state="complete", effect_count=1, observed_after_sha256="3" * 64,
            final_target_sha256="3" * 64)
        terminal["postchecks"] = {name: True for name in contract.POSTCHECKS}
        with self.assertRaisesRegex(ValueError, "cannot authenticate"):
            self.reconcile(terminal)

    def test_pre_effect_no_go_is_not_completion(self):
        _, _, terminal = inputs()
        value = self.reconcile(terminal)
        self.assertFalse(value["completion_accepted"])

    def test_failed_postcheck_requires_rollback_or_uncertain(self):
        _, _, terminal = inputs(); terminal.update(
            state="complete", effect_count=1, observed_after_sha256="3" * 64,
            final_target_sha256="3" * 64)
        terminal["postchecks"] = {name: True for name in contract.POSTCHECKS}
        terminal["postchecks"]["consumer-read-only-health"] = False
        with self.assertRaises(ValueError): self.reconcile(terminal)
        terminal.update(state="rolled_back", rollback_performed=True,
                        final_target_sha256="2" * 64)
        with self.assertRaises(ValueError): self.reconcile(terminal)

    def test_uncertain_never_becomes_success_or_retry(self):
        _, _, terminal = inputs(); terminal.update(state="uncertain", effect_count=1)
        terminal["postchecks"]["consumer-read-only-health"] = "uncertain"
        with self.assertRaises(ValueError): self.reconcile(terminal)

    def test_digest_effect_and_duplicate_drift_fail_closed(self):
        _, _, terminal = inputs(); terminal["effect_count"] = 1
        with self.assertRaises(ValueError): self.reconcile(terminal)
        _, _, terminal = inputs(); terminal["admission_sha256"] = "0" * 64
        with self.assertRaises(ValueError): self.reconcile(terminal)
        plan_raw, admission_raw, terminal = inputs()
        raw = contract.canonical(terminal).replace(
            b'"retry_count":0', b'"retry_count":0,"retry_count":0')
        with self.assertRaises(ValueError):
            receipt.reconcile(plan_raw, admission_raw, raw)
        _, _, terminal = inputs(); terminal["postchecks"]["target-bytes"] = 1
        with self.assertRaises(ValueError): self.reconcile(terminal)


if __name__ == "__main__": unittest.main()
