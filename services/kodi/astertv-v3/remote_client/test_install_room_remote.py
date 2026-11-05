import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INSTALLER = (ROOT / "install_room_remote.py").read_text()
APPLY = (ROOT / "apply_room_remote.py").read_text()
CLIENT = (ROOT / "addon/service.asterremote/service.py").read_text()


class InstallRoomRemoteTests(unittest.TestCase):
    def test_sources_parse_and_scope_only_family_and_bedroom(self):
        for source in (INSTALLER, APPLY, CLIENT): ast.parse(source)
        self.assertIn('"AsterTV-Family"', INSTALLER + APPLY)
        self.assertIn('"AsterTV-Bedroom"', INSTALLER + APPLY)
        self.assertNotIn('"AsterTV-Guest"', INSTALLER + APPLY)

    def test_identity_and_key_are_private_and_independent(self):
        self.assertIn("asterremote-client.json", INSTALLER + APPLY + CLIENT)
        self.assertIn("asterremote-client.key", INSTALLER + APPLY + CLIENT)
        self.assertIn("os.chmod(KEY, 0o600)", INSTALLER)
        self.assertIn("os.chmod(CONFIG, 0o600)", INSTALLER)
        self.assertIn('"credential_output": False', INSTALLER + APPLY)

    def test_checkpoint_and_idle_guards_precede_kodi_restart(self):
        self.assertIn('rpc("Player.GetActivePlayers")', INSTALLER)
        self.assertIn('"database": DATABASE', INSTALLER)
        self.assertIn('"config": CONFIG', INSTALLER)
        self.assertIn("restore(saved)", INSTALLER)
        self.assertIn('run("systemctl", "stop", "kodi")', INSTALLER)

    def test_client_remains_semantic_and_outbound_only(self):
        self.assertIn('BASE = "http://192.168.70.10:9120/v1/remote"', CLIENT)
        self.assertNotIn("HTTPServer", CLIENT)
        self.assertNotIn("subprocess", CLIENT)
        for forbidden in ("volumeup", "volumedown", '"mute"', '"power"'):
            self.assertNotIn(forbidden, CLIENT.casefold())


if __name__ == "__main__": unittest.main()
