import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from voice_search_patch import controller, window


HERE = Path(__file__).resolve().parent


class VoiceSearchPatchTests(unittest.TestCase):
    def test_controller_accepts_voice_query_and_back_cancels_capture(self):
        raw = controller((HERE / 'search_native/default.py').read_bytes())
        self.assertIn(b"command=='voice'", raw)
        self.assertIn(b"PREFIX+'VoiceQuery'", raw)
        self.assertIn(b"PREFIX+'VoiceCancel'", raw)
        with self.assertRaises(ValueError):
            controller(raw)

    def test_window_has_focused_voice_pill_and_keeps_keyboard(self):
        raw = window((HERE / 'search_native/overlay/custom_1127_search.xml').read_bytes())
        root = ET.fromstring(raw)
        field = root.find(".//control[@id='10']")
        voice = root.find(".//control[@id='11']")
        self.assertEqual(field.findtext('width'), '1190')
        self.assertEqual(field.findtext('onright'), '11')
        self.assertEqual(voice.findtext('onclick'), 'RunScript(script.astervoice.v2lab)')
        self.assertEqual(voice.findtext('onleft'), '10')
        self.assertIn('asterGreen', ET.tostring(voice).decode())
        with self.assertRaises(ValueError):
            window(raw)


if __name__ == '__main__':
    unittest.main()
