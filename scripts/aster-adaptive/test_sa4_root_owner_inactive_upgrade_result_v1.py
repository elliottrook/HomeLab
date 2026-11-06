import copy
import unittest

import sa4_root_owner_inactive_upgrade_plan_v1 as upgrade
import sa4_root_owner_inactive_upgrade_result_v1 as result
import sa4_single_file_repair_contract_v1 as contract


def value():
    return {
        "schema": "aster-sa4-root-owner-inactive-upgrade-result.v1",
        "plan_sha256": result.PLAN_SHA256,
        "changes": [{
            "destination": item.destination,
            "before_sha256": item.before_sha256,
            "after_sha256": item.after_sha256,
            "owner": "root", "group": "root", "mode": "0644",
            "link_count": 1, "regular_file": True,
            "retained_predecessor": item.before_sha256 is not None}
            for item in upgrade.CHANGES],
        "isolated_imports": [item.destination for item in upgrade.CHANGES],
        "host_bindings": dict(result.HOST_BINDINGS),
        "private_key_accessed": False, "signer_invoked": False,
        "authority_touched": False, "ledger_touched": False,
        "checkpoint_touched": False, "target_touched": False,
        "root_owner_invoked": False, "service_actions": [],
        "production_health": {name: True for name in result.HEALTH},
        "rollback_ready": True, "automatic_routing": "off"}


class SA4RootOwnerInactiveUpgradeResultTests(unittest.TestCase):
    def test_exact_inactive_result_validates(self):
        checked = result.validate(contract.canonical(value()))
        self.assertEqual(4, checked["changes_validated"])
        self.assertTrue(checked["inactive"])
        self.assertEqual(0, checked["maximum_effects"])

    def test_hash_binding_and_effect_claims_fail_closed(self):
        candidates = []
        changed = copy.deepcopy(value())
        changed["changes"][0]["after_sha256"] = "0" * 64
        candidates.append(changed)
        changed = copy.deepcopy(value()); changed["root_owner_invoked"] = True
        candidates.append(changed)
        changed = copy.deepcopy(value()); changed["service_actions"] = ["reload"]
        candidates.append(changed)
        for candidate in candidates:
            with self.subTest(), self.assertRaises(ValueError):
                result.validate(contract.canonical(candidate))

    def test_health_or_rollback_drift_fails_closed(self):
        changed = value(); changed["production_health"]["doctor"] = False
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(changed))
        changed = value(); changed["rollback_ready"] = False
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(changed))


if __name__ == "__main__":
    unittest.main()
