import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).with_name("install_aster_remote_rooms.py")).read_text()


class InstallAsterRemoteRoomsTests(unittest.TestCase):
    def test_source_parses_and_is_additive(self):
        ast.parse(SOURCE)
        self.assertIn('clients = json.loads(values["ASTER_REMOTE_CLIENTS"])', SOURCE)
        self.assertIn('assignments[owner] = sorted(set(assignments[owner])', SOURCE)
        self.assertNotIn("clients = {}", SOURCE)

    def test_exact_rooms_and_private_input(self):
        self.assertIn('"AsterTV-Family": {"room_id": "family"', SOURCE)
        self.assertIn('"AsterTV-Bedroom": {"room_id": "bedroom"', SOURCE)
        self.assertIn("private-room-keys-required", SOURCE)
        self.assertIn("INPUT.unlink", SOURCE)
        self.assertIn('"credential_output": False', SOURCE)

    def test_checkpoint_restore_and_real_protocol_validation(self):
        self.assertIn("shutil.copy2(ENVIRONMENT", SOURCE)
        self.assertIn("shutil.copy2(saved / \"asterremote.env\"", SOURCE)
        self.assertIn("/v1/remote/client/poll", SOURCE)
        self.assertIn("timeout=25", SOURCE)


if __name__ == "__main__": unittest.main()
