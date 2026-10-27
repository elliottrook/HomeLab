import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa1_followup_gateway.sh")


class Sa1FollowupGatewayInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_three_live_files_and_four_candidate_files(self):
        live = self.source.split("live_shas=(", 1)[1].split(")", 1)[0]
        candidates = self.source.split("candidate_shas=(", 1)[1].split(")", 1)[0]
        self.assertEqual(3, len(re.findall(r"(?m)^  [0-9a-f]{64}$", live)))
        self.assertEqual(4, len(re.findall(r"(?m)^  [0-9a-f]{64}$", candidates)))

    def test_effect_is_four_files_and_only_aster_agent_restart(self):
        for name in (
            "aster_agent.py",
            "sysadmin_incident_store.py",
            "sysadmin_incident_stream.py",
            "sysadmin_followup_selector.py",
        ):
            self.assertIn(name, self.source)
        self.assertNotIn("systemctl restart aster-llama", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))

    def test_checkpoint_and_rollback_cover_old_and_new_paths(self):
        checkpoint = self.source.index('cp -p "$target_root/$name" "$checkpoint/$name"')
        install = self.source.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(checkpoint, install)
        self.assertIn('rm -f "$target_root/sysadmin_followup_selector.py"', self.source)
        self.assertIn('test ! -e "$target_root/sysadmin_followup_selector.py"', self.source)

    def test_postcheck_keeps_auth_boundary_and_excludes_model_control(self):
        self.assertNotIn("aster-llama.service", self.source)
        self.assertIn('http://192.168.70.10:9120/v1/models', self.source)
        self.assertIn(')" = 401', self.source)


if __name__ == "__main__":
    unittest.main()
