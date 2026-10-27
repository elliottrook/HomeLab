import re
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_sa2_registered_producer.sh")


class Sa2RegisteredProducerInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_pins_predecessor_and_two_candidate_files(self):
        self.assertEqual(3, len(re.findall(r"(?m)^[a-z_]+_sha=[0-9a-f]{64}$", self.source)))
        self.assertIn("3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a", self.source)
        self.assertIn("28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703", self.source)
        self.assertIn("5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931", self.source)

    def test_effect_is_two_files_and_only_aster_agent_restart(self):
        self.assertIn("aster_agent.py", self.source)
        self.assertIn("sysadmin_registered_producer.py", self.source)
        self.assertNotIn("aster-llama.service", self.source)
        self.assertNotIn("systemctl daemon-reload", self.source)
        self.assertEqual(2, self.source.count("systemctl restart aster-agent.service"))

    def test_checkpoint_precedes_install_and_rollback_removes_addition(self):
        checkpoint = self.source.index('cp -p "$target_root/aster_agent.py"')
        install = self.source.index('install -o root -g root -m 0644 "$packet/aster_agent.py"')
        self.assertLess(checkpoint, install)
        self.assertIn('rm -f "$target_root/sysadmin_registered_producer.py"', self.source)
        self.assertIn('test ! -e "$target_root/sysadmin_registered_producer.py"', self.source)

    def test_postcheck_preserves_authentication_boundary(self):
        self.assertIn("http://192.168.70.10:9120/v1/models", self.source)
        self.assertIn(')" = 401', self.source)


if __name__ == "__main__":
    unittest.main()
