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

    def test_sa3_guardian_deadline_uses_registered_2700_second_budget(self):
        booking={"booking_id":"sa3-booking-01","end_epoch":4600,
                 "workload":"sa3-expanded-source-quality-v1"}
        _,_,guardian,_=runner.commands(booking,"lh-12345678",1000)
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"3700")
        self.assertEqual(guardian[guardian.index("--hard-deadline")+1],"5500")

    def test_m3_uses_mount_aware_guardian_and_exact_profile(self):
        booking={"booking_id":"m3-booking-01","end_epoch":5500,
                 "workload":"m3-joint-semantic-35b-public-v1"}
        _,_,guardian,owner=runner.commands(booking,"lh-12345678",1000)
        self.assertTrue(any(str(item).endswith("m3_joint_semantic_35b_guardian.py")
                            for item in guardian))
        self.assertFalse(any(str(item).endswith("full_inference_lab_deadline_guardian.py")
                             for item in guardian))
        self.assertEqual(guardian[guardian.index("--rescue-at")+1],"4600")
        self.assertEqual(owner[owner.index("--workload-profile")+1],
                         "m3-joint-semantic-35b-public-v1")

if __name__=="__main__": unittest.main()
