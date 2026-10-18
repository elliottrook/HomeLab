import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from application_b60_controller import ApplicationPreLease
from application_b60_lease import ACCEPTED_BACKEND, APPLICATION_MODE
from cooperative_lab_session import LabRuntimePreflight, LabSessionError, plan


class CooperativeLabSessionTests(unittest.TestCase):
    def prelease(self):
        epoch = lambda hour, minute: int(datetime(2026, 10, 18, hour, minute,
                                                  tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        return ApplicationPreLease(APPLICATION_MODE, "lab-1", 3, "application-chain:1",
                                   ACCEPTED_BACKEND, True, True, True,
                                   epoch(10, 0), epoch(10, 5), epoch(11, 0), epoch(11, 15))

    def runtime(self):
        return LabRuntimePreflight(ACCEPTED_BACKEND, True, True, True, True)

    def test_plan_preserves_backend_and_quiesces_allowlisted_consumers(self):
        value = plan(self.prelease(), self.runtime())
        self.assertTrue(value.preserve_backend)
        self.assertEqual(value.lab_seconds, 2700)
        self.assertEqual(len(value.stop_commands), 4)
        self.assertEqual(value.stop_commands[2][2:5], ("114", "--", "systemctl"))
        self.assertEqual(value.restore_reserve_seconds, 900)

    def test_rejects_incomplete_runtime_or_overlong_budget(self):
        with self.assertRaisesRegex(LabSessionError, "runtime"):
            plan(self.prelease(), LabRuntimePreflight(ACCEPTED_BACKEND, False, True, True, True))
        with self.assertRaisesRegex(LabSessionError, "budget"):
            plan(self.prelease(), self.runtime(), lab_seconds=2701)

    def test_rejects_missing_restore_reserve(self):
        bad = self.prelease().__class__(**{**self.prelease().__dict__, "restore_start_epoch": self.prelease().restore_deadline_epoch - 899})
        with self.assertRaisesRegex(LabSessionError, "reserve"):
            plan(bad, self.runtime())


if __name__ == "__main__":
    unittest.main()
