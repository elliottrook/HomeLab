import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("cutover_fixed_doctor_response_v2b.sh")


class FixedDoctorResponseV2BCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SCRIPT.read_text()

    def test_pins_predecessor_and_corrected_candidate(self):
        self.assertIn("aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a", self.text)
        self.assertIn("d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48", self.text)
        self.assertIn("4ca8721b1076815de3220dc51a1e499fd6822f3a9a1085bfc561804bea065298", self.text)

    def test_reuses_and_verifies_existing_checkpoint(self):
        self.assertIn("fixed-doctor-response-v2-pre-cutover", self.text)
        self.assertIn('stat -c %a "$checkpoint"', self.text)
        self.assertNotIn("install -d", self.text)

    def test_effect_and_rollback_remain_caller_only(self):
        self.assertEqual(2, self.text.count("restart aster-fixed-doctor-caller.service"))
        self.assertNotIn("restart aster-agent.service", self.text)
        self.assertIn('rm -f "$live_response"', self.text)
        self.assertIn("trap rollback EXIT", self.text)

    def test_canary_requires_schema_two_and_no_authority(self):
        self.assertIn('assert v["schema"]==2', self.text)
        self.assertIn('v["authority"]=="not-granted"', self.text)


if __name__ == "__main__":
    unittest.main()
