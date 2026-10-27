import re
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("install_sa2_doctor_producer.sh").read_text()


class Sa2DoctorProducerInstallerTests(unittest.TestCase):
    def test_fixed_packet_and_three_exact_replacements(self):
        self.assertIn('test "$#" -eq 0', SOURCE)
        self.assertIn('packet=/tmp/aster-sa2-doctor-producer-20261027', SOURCE)
        self.assertEqual(3, len(re.findall(r"(?m)^  [0-9a-f]{64}$", SOURCE.split("before=(",1)[1].split(")",1)[0])))
        self.assertEqual(3, len(re.findall(r"(?m)^  [0-9a-f]{64}$", SOURCE.split("after=(",1)[1].split(")",1)[0])))

    def test_checkpoint_precedes_staging_and_rollback_restores_all(self):
        self.assertLess(SOURCE.index('cp -p "$target/$name"'), SOURCE.index('install -o root -g root -m 0644 "$packet/$name"'))
        restore = SOURCE.split("restore()",1)[1].split("rollback()",1)[0]
        self.assertIn('mv -f "$target/$name.new"', restore)
        self.assertIn('if [ "$changed" -eq 1 ]', SOURCE)
        self.assertIn('if [ "$staged" -eq 1 ]', SOURCE)

    def test_only_aster_agent_restart_and_no_model_effect(self):
        self.assertEqual(2, SOURCE.count("systemctl restart aster-agent.service"))
        self.assertNotIn("aster-llama.service", SOURCE)
        self.assertNotIn("daemon-reload", SOURCE)
        self.assertNotIn("/completion", SOURCE)
        self.assertIn("/v1/models", SOURCE)

    def test_preinstall_requires_fixed_doctor_path_and_claim_api(self):
        check = SOURCE.index("PYTHONDONTWRITEBYTECODE=1")
        install = SOURCE.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(check, install)
        self.assertIn('/var/lib/aster/health/latest.json', SOURCE)
        self.assertIn('pending_follow_up_claim', SOURCE)


if __name__ == "__main__":
    unittest.main()
