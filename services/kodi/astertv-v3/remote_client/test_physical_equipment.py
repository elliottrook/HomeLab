import ast
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


PATH = Path(__file__).parent / "addon/service.asterremote/equipment.py"
SOURCE = PATH.read_text(encoding="utf-8")
SPEC = importlib.util.spec_from_file_location("physical_equipment", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PhysicalEquipmentTests(unittest.TestCase):
    def test_source_is_narrow_and_parses(self):
        ast.parse(SOURCE)
        self.assertEqual(MODULE.ALLOWED, {
            "volume_up", "volume_down", "mute_toggle", "power_toggle",
            "power_on", "power_off",
        })
        for forbidden in ("subprocess", "jsonrpc", "homeassistant", "volume_set"):
            self.assertNotIn(forbidden, SOURCE.casefold())

    def test_identity_and_key_require_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            key = Path(directory) / "key"
            config.write_text(json.dumps({"client_id": "AsterTV-Bedroom",
                                          "room_id": "bedroom"}))
            key.write_text("k" * 40)
            config.chmod(stat.S_IRUSR | stat.S_IWUSR)
            key.chmod(stat.S_IRUSR | stat.S_IWUSR)
            with mock.patch.object(MODULE, "CONFIG", config), mock.patch.object(MODULE, "KEY", key):
                self.assertEqual(MODULE.identity(), ("AsterTV-Bedroom", "bedroom"))
                self.assertEqual(MODULE.private_key(), "k" * 40)

    def test_unknown_control_is_denied_before_network(self):
        with mock.patch.object(MODULE.urllib.request, "urlopen") as request:
            with self.assertRaisesRegex(RuntimeError, "control-denied"):
                MODULE.send("arbitrary")
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
