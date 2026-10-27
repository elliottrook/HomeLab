import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa0_current_composite.sh")


class Sa0CompositeInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_live_candidate_and_unchanged_dependencies(self):
        expected = {
            "live_sha": "7edc7ff9776357d62f6eff45de2093aab5749bb38317251b404df88012c6b50c",
            "candidate_sha": "e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116",
            "knowledge_sha": "900a7fccad9c6e665297e3655e01844ca976705f69b45fac689858a00ccbfb55",
            "unit_sha": "530b3918e08e8a9e27ce2f651b18fd4967bdba8c453eecc40b37788b4c9b1a15",
        }
        for name, digest in expected.items():
            self.assertRegex(self.source, rf"(?m)^{name}={digest}$")

    def test_effect_is_one_runtime_file_and_one_service_restart(self):
        installed_targets = re.findall(r'install -o root -g root -m 0644 .*? "(\$[a-z]+(?:\.new)?)"', self.source)
        self.assertEqual(["$target.new", "$target.new"], installed_targets)
        self.assertNotIn("systemctl restart aster-llama", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))

    def test_checkpoint_precedes_install_and_rollback_restores_it(self):
        checkpoint = self.source.index('cp -p "$target" "$checkpoint/aster_agent.py"')
        install = self.source.index('install -o root -g root -m 0644 "$candidate" "$target.new"')
        self.assertLess(checkpoint, install)
        self.assertIn('install -o root -g root -m 0644 "$checkpoint/aster_agent.py" "$target.new"', self.source)
        self.assertIn('mv -f "$target.new" "$target"', self.source)

    def test_requires_health_and_zero_restart_loop_after_restart(self):
        self.assertIn("wait_for_health", self.source)
        self.assertIn("http://192.168.70.10:9120/health", self.source)
        self.assertIn('{"status":"ok","service":"aster-agent"}', self.source)
        self.assertGreaterEqual(
            self.source.count('test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0'),
            2,
        )


if __name__ == "__main__":
    unittest.main()
