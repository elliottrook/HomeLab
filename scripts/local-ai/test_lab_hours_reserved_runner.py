import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
import lab_hours_reserved_runner as runner

class ReservedRunnerTests(unittest.TestCase):
    def test_commands_bind_exact_booking_identity_and_deadline(self):
        booking={"booking_id":"test-booking-01","end_epoch":4600,
                 "workload":"accepted-9b-direct-control-smoke-v1"}
        guardian_unit,owner_unit,guardian,owner=runner.commands(booking,"lh-12345678",1000)
        self.assertIn("lh-12345678",guardian_unit)
        self.assertIn("lh-12345678",owner_unit)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"2800")
        self.assertEqual(guardian[guardian.index("--hard-deadline")+1],"5500")
        self.assertEqual(owner[owner.index("--admin-path-evidence")+1],"reserved:test-booking-01")
        self.assertIn("--effect-authorized",owner)

    def test_owner_loss_exercise_has_early_bounded_rescue(self):
        booking={"booking_id":"loss-booking-01","end_epoch":4600,
                 "workload":"accepted-9b-owner-loss-exercise-v1"}
        _,_,guardian,_=runner.commands(booking,"lh-12345678",1000)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"1120")

if __name__=="__main__": unittest.main()
