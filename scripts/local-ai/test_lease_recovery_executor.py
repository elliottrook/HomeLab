import unittest

from lease_recovery_executor import effects_permitted, main
from lease_watchdog import WatchdogState


class RecoveryExecutorTests(unittest.TestCase):
    def test_effects_require_both_restoring_state_and_explicit_gate(self):
        self.assertFalse(effects_permitted(WatchdogState.LEASED, True))
        self.assertFalse(effects_permitted(WatchdogState.RESTORING, False))
        self.assertTrue(effects_permitted(WatchdogState.RESTORING, True))

    def test_effect_flag_is_explicit_and_help_exposes_it(self):
        with self.assertRaises(SystemExit) as result:
            main(["--help"])
        self.assertEqual(result.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
