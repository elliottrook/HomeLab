import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("activate_fixed_doctor_capability.sh")


class FixedDoctorActivationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.text = SCRIPT.read_text()

    def test_exact_identity_capability_and_single_read_are_pinned(self):
        self.assertIn(
            '[ "$(sha "$core")" = 2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99 ]',
            self.text,
        )
        self.assertIn(
            '[ "$(sha "$doctor_adapter")" = c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db ]',
            self.text,
        )
        self.assertIn(
            '[ "$(sha "$investigation")" = bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe ]',
            self.text,
        )
        self.assertIn("enable-fixed-doctor --agent-uid 978", self.text)
        self.assertEqual(1, self.text.count('s.sendall(b\'{"method":"doctor.aster-inference.latest"'))
        self.assertIn('assert rows == [("consumed",)]', self.text)
        self.assertIn('observation["state"] == "ok"', self.text)

    def test_rollback_removes_activation_and_restores_database_custody(self):
        self.assertIn('systemctl disable --now "$caller" "$gateway"', self.text)
        self.assertIn('install -o hlabroker -g hlabroker -m 0600', self.text)
        self.assertIn('wait_for_broker', self.text)
        self.assertNotIn('systemctl restart aster-agent', self.text)

    def test_no_model_forgejo_schedule_or_other_effect_path(self):
        for forbidden in ("llama", "model", "forgejo", "LaunchAgent", "timer", "cron"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
