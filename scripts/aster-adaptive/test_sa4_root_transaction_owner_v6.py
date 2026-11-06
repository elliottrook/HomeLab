import unittest

import sa4_root_transaction_owner_v2 as previous
import sa4_root_transaction_owner_v6 as source
from test_sa4_distinct_registry_bindings_v1 import distinct_plan


class Ledger:
    pass


class Tests(unittest.TestCase):
    def test_successor_preserves_target_interface(self):
        self.assertTrue(issubclass(source.RootTransactionOwner,
                                   previous.RootTransactionOwner))
        self.assertEqual("sa4-lxc104-canary-adapter-v2",
                         source.BOUND_TARGET_ID)

    def test_prepare_reaches_candidate_gate(self):
        owner = object.__new__(source.RootTransactionOwner)
        owner.phase = "new"
        owner._values = {}
        owner.controls = None
        owner.ledger = Ledger()
        owner.operation_id = "sa4-canary-v2-third-operation-v1"
        with self.assertRaisesRegex(ValueError, "candidate"):
            owner.prepare(distinct_plan(), b"", b"", b"", b"", b"bad",
                          measurement_epoch=1000, checkpoint_epoch=1001)


if __name__ == "__main__":
    unittest.main()
