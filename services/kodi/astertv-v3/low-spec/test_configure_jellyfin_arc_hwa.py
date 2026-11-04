import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("configure_jellyfin_arc_hwa.py")
SPEC = importlib.util.spec_from_file_location("configure_jellyfin_arc_hwa", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


FIXTURE = b'''<?xml version="1.0" encoding="utf-8"?>
<EncodingOptions>
  <HardwareAccelerationType>qsv</HardwareAccelerationType>
  <VaapiDevice>/dev/dri/renderD128</VaapiDevice>
  <EnableTonemapping>false</EnableTonemapping>
  <EnableVppTonemapping>false</EnableVppTonemapping>
  <EnableHardwareEncoding>true</EnableHardwareEncoding>
  <HardwareDecodingCodecs><string>h264</string><string>vc1</string></HardwareDecodingCodecs>
</EncodingOptions>
'''


class ConfigureTests(unittest.TestCase):
    def test_enables_full_arc_pipeline(self):
        root = ET.fromstring(MODULE.configure(FIXTURE))
        self.assertEqual(root.findtext("EnableTonemapping"), "false")
        self.assertEqual(root.findtext("EnableVppTonemapping"), "true")
        self.assertEqual(
            [node.text for node in root.find("HardwareDecodingCodecs")],
            list(MODULE.CODECS),
        )

    def test_rejects_unexpected_accelerator(self):
        with self.assertRaisesRegex(RuntimeError, "HardwareAccelerationType"):
            MODULE.configure(FIXTURE.replace(b">qsv<", b">none<"))


if __name__ == "__main__":
    unittest.main()
