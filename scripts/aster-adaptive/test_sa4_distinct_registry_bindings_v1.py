import unittest

import sa4_distinct_registry_bindings_v1 as source
import sa4_first_signed_ceremony_v1 as old_plan
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v2 as registry_v2


def distinct_plan():
    value = contract.decode_unique_json(old_plan.build_unsigned(1000)["plan"])
    target = registry_v2.resolve_production(source.TARGET_ID)
    value["plan_id"] = "sa4-canary-v2-first-repair-v1"
    value["target_id"] = target.target_id
    value["target"] = {
        "host_id": target.host_id, "path": target.path,
        "type": "regular-file", "follow_symlinks": False,
        "owner": target.owner, "group": target.group, "mode": target.mode,
    }
    value["precondition"]["expected_sha256"] = (
        "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")
    value["change"]["artifact_sha256"] = (
        "fae178a1558199b66f4dc9abec18690ed22a7cbee398f411b47f93daf1d3a0c2")
    return contract.canonical(value)


class Tests(unittest.TestCase):
    def test_v1_rejects_and_complete_binding_accepts_then_restores(self):
        raw = distinct_plan()
        with self.assertRaises(ValueError):
            contract.validate_plan(raw)
        with source.accepted_registry(raw) as value:
            self.assertEqual(source.TARGET_ID, value["target_id"])
            self.assertIs(contract.target_registry, registry_v2)
            self.assertTrue(all(
                getattr(module, name) is registry_v2
                for module, name in source._BINDINGS))
            with source.accepted_registry(raw) as nested:
                self.assertEqual(source.TARGET_ID, nested["target_id"])
                self.assertTrue(all(
                    getattr(module, name) is registry_v2
                    for module, name in source._BINDINGS))
        self.assertIs(contract.target_registry, registry_v1)
        self.assertTrue(all(
            getattr(module, name) is registry_v1
            for module, name in source._BINDINGS))

    def test_other_target_rejected_without_mutation(self):
        raw = old_plan.build_unsigned(1000)["plan"]
        with self.assertRaises(ValueError):
            with source.accepted_registry(raw):
                pass
        self.assertTrue(all(
            getattr(module, name) is registry_v1
            for module, name in source._BINDINGS))


if __name__ == "__main__":
    unittest.main()

