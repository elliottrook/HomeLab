import copy
import unittest

import sa4_single_file_repair_contract_v1 as contract
import sa4_transaction_inactive_install_result_v1 as result


def value():
    return {
        "schema": "aster-sa4-transaction-inactive-install-result.v1",
        "plan_sha256": result.plan_sha256(),
        "changes": [{
            "host_id": item[0], "destination": item[1],
            "before_state": "present" if item[2] else "absent",
            "before_sha256": item[2],
            "after_sha256": item[3], "owner": "root",
            "group": "root", "mode": "0644", "link_count": 1,
            "regular_file": True,
            "retained_predecessor": item[2] is not None}
            for item in result.INSTALLED_CHANGES],
        "proxmox_parent_created": True,
        "isolated_imports": [item[1] for item in result.INSTALLED_CHANGES],
        "host_bindings": dict(result.HOST_BINDINGS),
        "signer_fake_self_test": "pass", "private_key_accessed": False,
        "signer_invoked": False, "grant_touched": False,
        "checkpoint_owner_invoked": False, "target_touched": False,
        "service_actions": [],
        "production_health": {name: True for name in result.HEALTH},
        "rollback_ready": True, "automatic_routing": "off"}


class SA4TransactionInactiveInstallResultTests(unittest.TestCase):
    def test_exact_result_is_inactive_and_rollback_ready(self):
        checked = result.validate(contract.canonical(value()))
        self.assertEqual(7, checked["changes_validated"])
        self.assertTrue(checked["inactive"])
        self.assertEqual(0, checked["maximum_effects"])

    def test_hash_binding_or_predecessor_drift_fails(self):
        for mutation in ("hash", "predecessor"):
            candidate = copy.deepcopy(value())
            if mutation == "hash":
                candidate["changes"][0]["after_sha256"] = "0" * 64
            else:
                candidate["changes"][4]["retained_predecessor"] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                result.validate(contract.canonical(candidate))

    def test_any_effect_signer_or_health_claim_fails(self):
        for field in ("private_key_accessed", "signer_invoked",
                      "grant_touched", "checkpoint_owner_invoked",
                      "target_touched"):
            candidate = copy.deepcopy(value()); candidate[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                result.validate(contract.canonical(candidate))
        candidate = value(); candidate["production_health"]["doctor"] = False
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(candidate))


if __name__ == "__main__":
    unittest.main()
