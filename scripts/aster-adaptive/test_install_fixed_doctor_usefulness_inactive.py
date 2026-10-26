import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_fixed_doctor_usefulness_inactive.sh")


class InstallFixedDoctorUsefulnessInactiveTests(unittest.TestCase):
    def test_transaction_is_inactive_exact_and_rollback_safe(self):
        text = SCRIPT.read_text()
        self.assertIn("vmid=104", text)
        self.assertIn("target=/var/lib/aster/fixed-doctor-usefulness-v1", text)
        self.assertIn("local-ai-lease status", text)
        self.assertIn("systemctl is-active aster-agent.service", text)
        self.assertIn("test ! -e \"$target\"", text)
        self.assertIn("rm -rf \"$temporary\" \"$target\"", text)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", text)
        self.assertIn("--help", text)
        for forbidden in (
            "systemctl start", "systemctl enable", "local-ai-lease acquire",
            "--execute", "curl ", "Authorization:", "aster.env",
        ):
            self.assertNotIn(forbidden, text)

    def test_all_transport_hashes_are_full_sha256(self):
        text = SCRIPT.read_text()
        values = re.findall(r"^(?:archive|validator|manifest)_sha=([0-9a-f]+)$", text, re.M)
        self.assertEqual(3, len(values))
        self.assertTrue(all(len(value) == 64 for value in values))


if __name__ == "__main__":
    unittest.main()
