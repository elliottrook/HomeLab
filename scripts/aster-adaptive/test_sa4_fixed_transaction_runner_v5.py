import unittest
from unittest import mock

import sa4_fixed_transaction_runner_v3 as previous
import sa4_fixed_transaction_runner_v5 as source
import sa4_root_transaction_owner_v3 as old_owner
import sa4_root_transaction_owner_v5 as new_owner
from test_sa4_distinct_registry_bindings_v1 import distinct_plan


class Tests(unittest.TestCase):
    def test_no_arguments_only(self):
        with self.assertRaisesRegex(ValueError, "no arguments"):
            source.main(["unexpected"])

    def test_complete_binding_wraps_predecessor_execution(self):
        with mock.patch.object(previous, "_read", return_value=distinct_plan()), \
                mock.patch.object(previous, "execute", return_value={"ok": True}):
            self.assertEqual({"ok": True}, source.execute(1000))
        self.assertIs(previous.root_owner, old_owner)

    def test_bad_time_rejected_before_input(self):
        for value in (0, -1, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.execute(value)

    def test_new_owner_preserves_runner_target_contract(self):
        self.assertEqual(old_owner.BOUND_TARGET_ID,
                         new_owner.BOUND_TARGET_ID)


if __name__ == "__main__":
    unittest.main()
