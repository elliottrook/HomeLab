import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).with_name("acquisition_native")


class AcquisitionNativeTests(unittest.TestCase):
    def test_controller_is_discovery_only_and_compiles(self):
        raw = (ROOT / "default.py").read_text()
        ast.parse(raw)
        self.assertIn("DiscoveryFeedClient", raw)
        self.assertIn("RunScript(script.asterseerr)", raw)
        self.assertNotIn("RequestWriter", raw)
        self.assertNotIn("/v1/request", raw)
        self.assertNotIn(":5055", raw)
        self.assertNotIn("API_KEY", raw)

    def test_page_has_remote_complete_focus_and_no_music_books_write(self):
        root = ET.parse(ROOT / "overlay/custom_1133_acquisition.xml").getroot()
        controls = {node.get("id"): node for node in root.findall(".//control[@id]")}
        for identity in ("10", "11", "12", "30", "50", "51"):
            self.assertIn(identity, controls)
        self.assertEqual(root.findtext("defaultcontrol"), "10")
        self.assertEqual(controls["50"].findtext("onclick"),
                         "SetProperty(AsterAcquisition.Command,action,home)")
        for identity, control in controls.items():
            if control.get("type") in ("button", "list"):
                for direction in ("onup", "ondown", "onleft", "onright"):
                    self.assertIsNotNone(control.find(direction),
                                         identity + ":" + direction)

    def test_page_uses_current_aster_materials_without_stone_controls(self):
        raw = (ROOT / "overlay/custom_1133_acquisition.xml").read_text()
        self.assertIn("ui-compact-card-ring.png", raw)
        self.assertIn("ui-hero-bottom-fade.png", raw)
        self.assertNotIn("ui-limestone-panel.png", raw)
        self.assertNotIn("Dialog().yesno", (ROOT / "default.py").read_text())


if __name__ == "__main__":
    unittest.main()
