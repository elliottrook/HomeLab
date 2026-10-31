from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


SOURCE = Path(__file__).parent / "payload/skin.asterhome/1080i/DialogBusy.xml"


class ProductionBusyLogoR36Tests(unittest.TestCase):
    def test_busy_dialog_is_static_full_screen_astertv_art(self):
        root = ET.fromstring(SOURCE.read_bytes())
        self.assertEqual(root.findtext("backgroundcolor"), "ff1a211c")
        image = root.find("./controls/control")
        self.assertIsNotNone(image)
        self.assertEqual(image.attrib.get("type"), "image")
        self.assertEqual(image.findtext("width"), "1920")
        self.assertEqual(image.findtext("height"), "1080")
        self.assertEqual(image.findtext("texture"),
                         "special://home/media/Splash.png")
        self.assertEqual(image.findtext("aspectratio"), "stretch")

    def test_busy_dialog_has_no_working_text_or_animation(self):
        text = SOURCE.read_text()
        self.assertNotIn("Working", text)
        self.assertNotIn("animation", text.lower())
        self.assertNotIn("RunScript", text)


if __name__ == "__main__":
    unittest.main()
