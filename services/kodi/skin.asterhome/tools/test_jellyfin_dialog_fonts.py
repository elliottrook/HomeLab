"""Keep upstream Jellyfin setup dialogs legible under the Aster skin."""

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


FONT_XML = Path(__file__).resolve().parents[1] / '1080i' / 'Font.xml'


class JellyfinDialogFontTests(unittest.TestCase):
    def test_standard_dialog_aliases_exist(self):
        root = ET.parse(FONT_XML).getroot()
        fonts = {node.findtext('name'): node for node in root.findall('.//font')}
        for name in ('font12', 'font13'):
            self.assertIn(name, fonts)
            self.assertTrue(fonts[name].findtext('filename'))
            self.assertGreater(int(fonts[name].findtext('size')), 0)


if __name__ == '__main__':
    unittest.main()
