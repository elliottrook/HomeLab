import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).with_name("acquisition_native")


class AcquisitionNativeTests(unittest.TestCase):
    def test_property_updates_repaint_only_this_page_without_looping(self):
        root = ET.parse(ROOT / "overlay/custom_1133_acquisition.xml").getroot()
        animation = root.find("controls/control[@id='600']/animation")
        self.assertEqual(animation.attrib, {
            'effect': 'fade', 'start': '100', 'end': '100', 'time': '50',
            'condition': 'String.IsEqual(Window(Home).Property(AsterAcquisition.Revision),odd)'})
        self.assertEqual(animation.text, 'Conditional')
        raw = (ROOT / 'default.py').read_text()
        self.assertIn('revision = not revision', raw)
        self.assertIn('prop("Revision", "odd" if revision else "even")', raw)
        self.assertNotIn('ReloadSkin', raw)

    def test_controller_uses_only_the_restricted_acquisition_writer(self):
        raw = (ROOT / "default.py").read_text()
        ast.parse(raw)
        self.assertIn("DiscoveryFeedClient", raw)
        self.assertIn("RunScript(script.asterseerr)", raw)
        self.assertIn("RequestWriter", raw)
        self.assertIn("acquisition-token", raw)
        self.assertNotIn(":5055", raw)
        self.assertNotIn("API_KEY", raw)

    def test_page_has_remote_complete_focus(self):
        root = ET.parse(ROOT / "overlay/custom_1133_acquisition.xml").getroot()
        controls = {node.get("id"): node for node in root.findall(".//control[@id]")}
        for identity in ("10", "11", "12", "30", "50", "51"):
            self.assertIn(identity, controls)
        self.assertEqual(root.findtext("defaultcontrol"), "10")
        self.assertEqual(controls["50"].findtext("onclick"),
                         "SetProperty(AsterAcquisition.Command,action,home)")
        self.assertEqual(controls["50"].findtext("label"), "")
        self.assertEqual(controls["50"].findtext("texturefocus"), "")
        self.assertEqual(controls["50"].findtext("texturenofocus"), "")
        self.assertIn("AsterAcquisition.PrimaryAction",
                      controls["50"].findtext("visible"))
        self.assertIn('prop("PrimaryAction",', (ROOT / "default.py").read_text())
        action_labels = [node for node in root.findall(".//control")
                         if node.get("type") == "label"
                         and node.findtext("label") == "Request"]
        self.assertEqual(len(action_labels), 1)
        self.assertEqual(action_labels[0].findtext("font"), "font20")
        self.assertIn("AsterAcquisition.PrimaryAction",
                      action_labels[0].findtext("visible"))
        action_images = [node for node in root.findall(".//control")
                         if node.get("type") == "image"
                         and node.findtext("left") == "455"
                         and node.findtext("top") == "640"]
        self.assertEqual(len(action_images), 2)
        self.assertTrue(any("Control.HasFocus(50)" in node.findtext("visible")
                            for node in action_images))
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
