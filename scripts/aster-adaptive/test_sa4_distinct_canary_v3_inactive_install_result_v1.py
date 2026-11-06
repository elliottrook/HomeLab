import unittest

import sa4_distinct_canary_v3_inactive_install_plan_v1 as install
import sa4_distinct_canary_v3_inactive_install_result_v1 as result
import sa4_single_file_repair_contract_v1 as contract


def valid_result():
    return {
        "schema": "aster-sa4-distinct-canary-v3-inactive-install-result.v1",
        "rows": [{
            "destination": item.destination,
            "after_sha256": item.after_sha256,
            "owner": "root", "group": "root", "mode": "0644",
            "link_count": 1, "regular_file": True,
        } for item in install.CHANGES],
        "dependencies_exact": True,
        "isolated_imports": True,
        "v1_target_rejected": True,
        "v2_target_resolved": True,
        "runner_invoked": False,
        "transaction_state_absent": True,
        "target_sha256": install.TARGET_SHA256,
        "service_actions": [],
        "production_healthy": True,
        "rollback_ready": True,
        "automatic_routing": "off",
    }


class Tests(unittest.TestCase):
    def test_exact_inactive_result_passes(self):
        value = result.validate(contract.canonical(valid_result()))
        self.assertTrue(value["inactive"])
        self.assertFalse(value["repair_authorized"])

    def test_effect_or_target_drift_fails(self):
        for field, changed in (
                ("runner_invoked", True),
                ("transaction_state_absent", False),
                ("target_sha256", "0" * 64),
                ("service_actions", ["restart"])):
            value = valid_result()
            value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                result.validate(contract.canonical(value))

    def test_row_or_duplicate_key_drift_fails(self):
        value = valid_result()
        value["rows"][0]["mode"] = "0755"
        with self.assertRaises(ValueError):
            result.validate(contract.canonical(value))
        with self.assertRaises(ValueError):
            result.validate(b'{"schema":"x","schema":"x"}\n')


if __name__ == "__main__":
    unittest.main()
