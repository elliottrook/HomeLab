import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from voice_keymap import (SELECT_ACTION, SELECT_CODE, VOICE_ACTION, VOICE_CODE,
                          build)


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'remote' / 'g20s-pro-plus.xml'


class VoiceKeymapTests(unittest.TestCase):
    def test_separates_select_and_voice_by_observed_linux_codes(self):
        root = ET.fromstring(build(SOURCE.read_bytes()))
        keyboard = root.find('./global/keyboard')
        self.assertEqual(keyboard.find("key[@id='" + SELECT_CODE + "']").text,
                         SELECT_ACTION)
        self.assertEqual(keyboard.find("key[@id='" + VOICE_CODE + "']").text,
                         VOICE_ACTION)
        self.assertIsNone(keyboard.find('select'))
        for name in ('FullscreenVideo', 'FullscreenGame', 'Visualisation'):
            self.assertEqual(root.find('./' + name + "/keyboard/key[@id='582']").text,
                             'noop')

    def test_refuses_reapplication_or_changed_predecessor(self):
        value = build(SOURCE.read_bytes())
        with self.assertRaises(ValueError):
            build(value)
        with self.assertRaises(ValueError):
            build(b'<keymap><global><keyboard/></global></keymap>')


if __name__ == '__main__':
    unittest.main()
