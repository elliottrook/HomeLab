import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("cutover_fixed_doctor_response_v2.sh")


class FixedDoctorResponseV2CutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SCRIPT.read_text()

    def test_pins_predecessor_and_two_candidate_hashes(self):
        self.assertIn("aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a", self.text)
        self.assertIn("d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48", self.text)
        self.assertIn("c7855a76da7f9a060dac4d4230c06703cd8be043b78a38445c47854b3fac70ff", self.text)

    def test_only_caller_is_restarted_and_aster_is_postchecked(self):
        self.assertEqual(2, self.text.count("restart aster-fixed-doctor-caller.service"))
        self.assertNotIn("restart aster-agent.service", self.text)
        self.assertIn("agent_restarts", self.text)

    def test_canary_requires_schema_two_and_no_authority(self):
        self.assertIn('assert v["schema"]==2', self.text)
        self.assertIn('v["authority"]=="not-granted"', self.text)
        self.assertIn('/run/aster-fixed-doctor-caller/caller.sock', self.text)

    def test_rollback_restores_old_caller_and_removes_new_module(self):
        self.assertIn('$checkpoint/fixed_doctor_caller.py', self.text)
        self.assertIn('rm -f "$live_response"', self.text)
        self.assertIn('trap rollback EXIT', self.text)


if __name__ == "__main__":
    unittest.main()
