import copy
import unittest

import sa4_runtime_control_inactive_upgrade_plan_v1 as upgrade
import sa4_runtime_control_inactive_upgrade_result_v1 as result
import sa4_single_file_repair_contract_v1 as contract


def value():
    return {"schema": "aster-sa4-runtime-control-inactive-upgrade-result.v1",
            "plan_sha256": result.PLAN_SHA256,
            "changes": [{"destination": item.destination,
                         "before_sha256": item.before_sha256,
                         "after_sha256": item.after_sha256, "owner": "root",
                         "group": "root", "mode": "0644", "link_count": 1,
                         "regular_file": True,
                         "retained_predecessor": item.before_sha256 is not None}
                        for item in upgrade.CHANGES],
            "isolated_imports": [item.destination for item in upgrade.CHANGES],
            "operation_lock_absent": True, "emergency_stop_absent": True,
            "root_owner_invoked": False, "authority_touched": False,
            "target_touched": False, "service_actions": [],
            "production_healthy": True, "rollback_ready": True,
            "automatic_routing": "off"}


class SA4RuntimeControlInactiveUpgradeResultTests(unittest.TestCase):
    def test_exact_result_validates(self):
        checked = result.validate(contract.canonical(value()))
        self.assertEqual(2, checked["changes_validated"])
        self.assertTrue(checked["inactive"])

    def test_effect_or_control_state_fails(self):
        for field in ("root_owner_invoked", "authority_touched",
                      "target_touched"):
            changed = copy.deepcopy(value()); changed[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                result.validate(contract.canonical(changed))
        changed = value(); changed["operation_lock_absent"] = False
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(changed))

    def test_hash_or_health_drift_fails(self):
        changed = value(); changed["changes"][0]["after_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(changed))
        changed = value(); changed["production_healthy"] = False
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(changed))


if __name__ == "__main__":
    unittest.main()
