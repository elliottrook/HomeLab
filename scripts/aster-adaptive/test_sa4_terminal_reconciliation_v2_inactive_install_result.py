import unittest

import sa4_single_file_repair_contract_v1 as contract
import sa4_terminal_reconciliation_v2_inactive_install_plan as install
import sa4_terminal_reconciliation_v2_inactive_install_result as result


def valid():
    return {
        "schema":
            "aster-sa4-terminal-reconciliation-v2-inactive-install-result.v1",
        "rows": [{
            "destination": item.destination,
            "after_sha256": item.after_sha256,
            "owner": "root", "group": "root", "mode": "0644",
            "link_count": 1, "regular_file": True,
            "isolated_import": True,
        } for item in install.CHANGES],
        "v1_dependencies_unchanged": True,
        "runner_invoked": False,
        "authority_touched": False,
        "ledger_touched": False,
        "target_touched": False,
        "runtime_state_absent": True,
        "service_actions": [],
        "production_healthy": True,
        "rollback_ready": True,
        "automatic_routing": "off",
    }


class Tests(unittest.TestCase):
    def test_exact_result_passes(self):
        checked = result.validate(contract.canonical(valid()))
        self.assertTrue(checked["inactive"])
        self.assertFalse(checked["effect_authorized"])

    def test_effect_or_hash_drift_fails(self):
        variants = []
        value = valid(); value["runner_invoked"] = True; variants.append(value)
        value = valid(); value["ledger_touched"] = True; variants.append(value)
        value = valid(); value["rows"][0]["after_sha256"] = "0" * 64; variants.append(value)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError):
                result.validate(contract.canonical(value))


if __name__ == "__main__":
    unittest.main()
