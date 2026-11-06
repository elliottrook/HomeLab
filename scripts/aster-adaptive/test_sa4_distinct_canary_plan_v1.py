import unittest

import sa4_distinct_canary_plan_v1 as source
import sa4_single_file_repair_contract_v1 as contract


class Tests(unittest.TestCase):
    def test_exact_distinct_plan_is_valid_only_under_binding(self):
        raw = source.build_plan()
        with self.assertRaises(ValueError):
            contract.validate_plan(raw)
        value = contract.decode_unique_json(raw)
        self.assertEqual(source.TARGET_ID, value["target_id"])
        self.assertEqual(source.BEFORE_SHA256,
                         value["precondition"]["expected_sha256"])
        self.assertEqual(source.AFTER_SHA256,
                         value["change"]["artifact_sha256"])

    def test_plan_remains_inert(self):
        value = contract.decode_unique_json(source.build_plan())
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("none", value["authority"])
        self.assertFalse(value["uncertainty"]["automatic_retry"])
        self.assertEqual("off", value["automatic_routing"])


if __name__ == "__main__":
    unittest.main()

