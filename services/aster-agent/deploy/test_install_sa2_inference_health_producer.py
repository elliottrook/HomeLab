import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa2_inference_health_producer.sh")


class Sa2InferenceHealthInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_two_live_and_two_candidate_files(self):
        live = self.source.split("live_shas=(", 1)[1].split(")", 1)[0]
        candidates = self.source.split("candidate_shas=(", 1)[1].split(")", 1)[0]
        self.assertEqual(2, len(re.findall(r"(?m)^  [0-9a-f]{64}$", live)))
        self.assertEqual(2, len(re.findall(r"(?m)^  [0-9a-f]{64}$", candidates)))

    def test_effect_is_two_replacements_and_only_aster_agent_restart(self):
        files = self.source.split("files=(", 1)[1].split(")", 1)[0].split()
        self.assertEqual(["aster_agent.py", "sysadmin_registered_producer.py"], files)
        self.assertNotIn("aster-llama.service", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))

    def test_checkpoint_covers_both_files_before_install(self):
        checkpoint = self.source.index('cp -p "$target_root/$name" "$checkpoint/$name"')
        install = self.source.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(checkpoint, install)
        self.assertIn('for name in "${files[@]}"; do', self.source)

    def test_postcheck_preserves_authentication_boundary(self):
        self.assertIn("http://192.168.70.10:9120/v1/models", self.source)
        self.assertIn(')" = 401', self.source)


if __name__ == "__main__":
    unittest.main()
