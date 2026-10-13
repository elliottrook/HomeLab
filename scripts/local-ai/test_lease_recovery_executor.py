import unittest
from pathlib import Path

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

    def test_candidate_timer_is_periodic_and_disabled_by_installation_policy(self):
        root = Path(__file__).parents[2] / "services/local-ai-lease"
        unit = (root / "local-ai-lease-watchdog.service").read_text()
        timer = (root / "local-ai-lease-watchdog.timer").read_text()
        self.assertIn("RefuseManualStart=yes", unit)
        self.assertIn("OnUnitActiveSec=1min", timer)
        self.assertIn("RandomizedDelaySec=10s", timer)


if __name__ == "__main__":
    unittest.main()
