import hashlib
import unittest

import sa4_distinct_canary_plan_v1 as previous
import sa4_distinct_canary_plan_v2 as source
import sa4_single_file_repair_contract_v1 as contract


class UniquePlanTests(unittest.TestCase):
    def test_only_plan_identity_changes(self):
        old = contract.decode_unique_json(previous.build_plan())
        new = contract.decode_unique_json(source.build_plan())
        self.assertEqual("sa4-canary-v2-second-repair-v1", new.pop("plan_id"))
        old.pop("plan_id")
        self.assertEqual(old, new)

    def test_digest_is_exact(self):
        self.assertEqual(source.PLAN_SHA256,
                         hashlib.sha256(source.build_plan()).hexdigest())


if __name__ == "__main__":
    unittest.main()
