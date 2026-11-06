import unittest
from unittest import mock

import sa4_fixed_transaction_runner_v7 as previous
import sa4_fixed_transaction_runner_v8 as source


class RunnerV8Tests(unittest.TestCase):
    def test_fresh_paths_are_scoped(self):
        original = (previous.INPUT_DIR, previous.EVIDENCE_DIR,
                    previous.LEDGER_ROOT, previous.OPERATION_ID)
        with mock.patch.object(previous, "execute", return_value={"ok": True}) as run:
            self.assertEqual({"ok": True}, source.execute(17))
            run.assert_called_once_with(17)
            inside = run.call_args
        self.assertEqual(source.EXPECTED_PREDECESSOR, original)
        self.assertEqual(original, (previous.INPUT_DIR, previous.EVIDENCE_DIR,
                                    previous.LEDGER_ROOT, previous.OPERATION_ID))

    def test_rejects_arguments(self):
        with self.assertRaises(ValueError):
            source.main(["unexpected"])


if __name__ == "__main__":
    unittest.main()
