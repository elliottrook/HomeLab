import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


PATH = Path(__file__).with_name("build_physical_equipment_keymap.py")
SPEC = importlib.util.spec_from_file_location("physical_keymap", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    return {
        "schema_version": 1,
        "kind": "astertv-physical-equipment-keys",
        "hostname": "AsterTV-Bedroom",
        "bindings": {
            "volume_up": {"kind": "named", "value": "volume_up"},
            "volume_down": {"kind": "named", "value": "volume_down"},
            "mute_toggle": {"kind": "id", "value": 113},
            "power_toggle": {"kind": "id", "value": 116},
        },
    }


class PhysicalKeymapTests(unittest.TestCase):
    def test_renders_only_four_bounded_runscript_actions(self):
        root = ET.fromstring(MODULE.render(fixture()))
        nodes = list(root.findall("./global/keyboard/*"))
        self.assertEqual(len(nodes), 4)
        self.assertEqual({node.text for node in nodes}, {
            MODULE.RUN.format(control) for control in MODULE.CONTROLS
        })
        self.assertEqual(root.findtext("./global/keyboard/volume_up"),
                         MODULE.RUN.format("volume_up"))
        self.assertEqual({node.attrib["id"] for node in root.findall("./global/keyboard/key")},
                         {"113", "116"})

    def test_rejects_reserved_navigation_and_duplicate_keys(self):
        value = fixture()
        value["bindings"]["volume_up"] = {"kind": "named", "value": "select"}
        with self.assertRaisesRegex(ValueError, "reserved"):
            MODULE.render(value)
        value = fixture()
        value["bindings"]["mute_toggle"] = value["bindings"]["power_toggle"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MODULE.render(value)

    def test_rejects_unknown_host_or_missing_control(self):
        value = fixture(); value["hostname"] = "AsterTV-Guest"
        with self.assertRaisesRegex(ValueError, "host"):
            MODULE.render(value)
        value = fixture(); value["bindings"].pop("power_toggle")
        with self.assertRaisesRegex(ValueError, "controls"):
            MODULE.render(value)


if __name__ == "__main__":
    unittest.main()
