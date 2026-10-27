import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa1_sa2_incident_modules.sh")


class Sa1Sa2IncidentModuleInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_gateway_and_three_live_candidate_pairs(self):
        self.assertIn(
            "gateway_sha=e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116",
            self.source,
        )
        self.assertEqual(3, len(re.findall(r"(?m)^  [0-9a-f]{64}$", self.source.split("live_shas=(", 1)[1].split(")", 1)[0])))
        self.assertEqual(3, len(re.findall(r"(?m)^  [0-9a-f]{64}$", self.source.split("candidate_shas=(", 1)[1].split(")", 1)[0])))

    def test_effect_is_three_modules_and_one_service(self):
        for name in (
            "sysadmin_incident_store.py",
            "sysadmin_incident_stream.py",
            "sysadmin_investigation.py",
        ):
            self.assertIn(name, self.source)
        self.assertNotIn("systemctl restart aster-llama", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))

    def test_checkpoint_and_rollback_precede_effect(self):
        checkpoint = self.source.index('cp -p "$target_root/$name" "$checkpoint/$name"')
        install = self.source.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(checkpoint, install)
        self.assertIn("restore_checkpoint", self.source)
        self.assertIn('install -o root -g root -m 0644 "$checkpoint/$name"', self.source)

    def test_health_retry_is_quiet_and_bounded(self):
        self.assertIn("http://192.168.70.10:9120/health", self.source)
        self.assertIn('2>/dev/null; then', self.source)
        self.assertIn('[ "$attempts" -lt 50 ]', self.source)
        self.assertIn('{"status":"ok","service":"aster-agent"}', self.source)


if __name__ == "__main__":
    unittest.main()
