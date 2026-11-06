import unittest
from unittest import mock

import sa4_fixed_transaction_runner_v3 as previous
import sa4_fixed_transaction_runner_v7 as source
import sa4_root_transaction_owner_v3 as old_owner
from test_sa4_distinct_registry_bindings_v1 import distinct_plan


class Tests(unittest.TestCase):
    def test_no_arguments_only(self):
        with self.assertRaisesRegex(ValueError, "no arguments"):
            source.main(["unexpected"])

    def test_corrected_owner_and_fresh_paths_bind_temporarily(self):
        observed = {}

        def execute(now_epoch):
            observed.update(input=previous.INPUT_DIR,
                            evidence=previous.EVIDENCE_DIR,
                            ledger=previous.LEDGER_ROOT,
                            operation=previous.OPERATION_ID,
                            owner=previous.root_owner)
            return {"ok": now_epoch}

        with mock.patch.object(previous, "_read", return_value=distinct_plan()), \
                mock.patch.object(previous, "execute", side_effect=execute):
            self.assertEqual({"ok": 1000}, source.execute(1000))
        self.assertEqual(source.INPUT_DIR, observed["input"])
        self.assertEqual(source.EVIDENCE_DIR, observed["evidence"])
        self.assertEqual(source.LEDGER_ROOT, observed["ledger"])
        self.assertEqual(source.OPERATION_ID, observed["operation"])
        self.assertEqual("sa4_root_transaction_owner_v6",
                         observed["owner"].__name__)
        self.assertEqual(source.EXPECTED_PREDECESSOR,
                         (previous.INPUT_DIR, previous.EVIDENCE_DIR,
                          previous.LEDGER_ROOT, previous.OPERATION_ID))
        self.assertIs(previous.root_owner, old_owner)


if __name__ == "__main__":
    unittest.main()
