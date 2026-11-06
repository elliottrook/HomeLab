import unittest

import sa4_distinct_postcheck_receipt_producer_v1 as distinct_receipt
import sa4_distinct_registry_bindings_v2 as source
import sa4_root_transaction_owner_v2 as root_owner
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v3 as registry_v3
from test_sa4_distinct_registry_bindings_v1 import distinct_plan


class Tests(unittest.TestCase):
    def test_complete_binding_includes_observer_and_restores(self):
        plan = distinct_plan()
        with source.accepted_registry(plan):
            self.assertIs(registry_v3, root_owner.registry)
            self.assertIs(distinct_receipt, root_owner.receipt_producer)
            with source.accepted_registry(plan):
                self.assertIs(registry_v3, root_owner.registry)
                self.assertIs(distinct_receipt, root_owner.receipt_producer)
        self.assertIs(registry_v1, root_owner.registry)
        self.assertIsNot(distinct_receipt, root_owner.receipt_producer)


if __name__ == "__main__":
    unittest.main()
