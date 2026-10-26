import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("remove_fixed_doctor_usefulness_inactive.sh")


class RemoveFixedDoctorUsefulnessInactiveTests(unittest.TestCase):
    def test_removal_is_exact_and_fail_closed(self):
        text = SCRIPT.read_text()
        self.assertIn("vmid=104", text)
        self.assertIn("target=/var/lib/aster/fixed-doctor-usefulness-v1", text)
        self.assertIn("local-ai-lease status", text)
        self.assertIn("systemctl is-active aster-agent.service", text)
        self.assertIn("-maxdepth 1 ! -type f", text)
        self.assertIn("rmdir \"$target\"", text)
        self.assertNotIn("rm -rf", text)
        self.assertNotIn("systemctl stop", text)
        self.assertNotIn("systemctl start", text)
        self.assertNotIn("--execute", text)

    def test_all_eight_installed_hashes_are_pinned(self):
        text = SCRIPT.read_text()
        values = re.findall(r"^  \[[^]]+\]=([0-9a-f]+)$", text, re.M)
        self.assertEqual(8, len(values))
        self.assertTrue(all(len(value) == 64 for value in values))


if __name__ == "__main__":
    unittest.main()
