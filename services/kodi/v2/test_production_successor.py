from pathlib import Path
import tempfile
import unittest

from tools.build_production_successor import (YOUTUBE_BACK_ACTION,
                                              add_youtube_back_navigation,
                                              adapt_youtube_entry_timing,
                                              rewrite_embedded_pin)


class ProductionSuccessorTests(unittest.TestCase):
    def test_rewrite_embedded_pin_is_exact(self):
        old = 'a' * 64
        new = 'b' * 64
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'launcher.py'
            target.write_text("PIN = '" + old + "'\n")
            rewrite_embedded_pin(target, old, new)
            self.assertEqual(target.read_text(), "PIN = '" + new + "'\n")
            with self.assertRaisesRegex(RuntimeError, 'unexpected-embedded-pin'):
                rewrite_embedded_pin(target, old, new)

    def test_youtube_root_focus_waits_for_kodi_22_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'MyVideoNav.xml'
            target.write_text('<window><onload>AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)</onload></window>')
            adapt_youtube_entry_timing(target)
            raw = target.read_text()
            self.assertIn('00:03,silent)', raw)
            self.assertIn('SetFocus(9530)', raw)
            self.assertNotIn('00:01,silent)', raw)

    def test_youtube_back_navigation_is_window_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skin = root / '.kodi/addons/skin.asterhome'
            (skin / '1080i').mkdir(parents=True)
            (skin / 'tools').mkdir()
            (skin / '1080i/MyVideoNav.xml').write_text(
                '<window><controls>'
                '<control id="9305"><onclick>Action(Back)</onclick></control>'
                '<control id="9404"><onclick>Action(Back)</onclick></control>'
                '</controls></window>')
            keymap = root / '.kodi/userdata/keymaps/g20s-pro-plus.xml'
            keymap.parent.mkdir(parents=True)
            keymap.write_text('<keymap><global /></keymap>')
            target = add_youtube_back_navigation(root)
            self.assertTrue(target.is_file())
            nav = (skin / '1080i/MyVideoNav.xml').read_text()
            self.assertEqual(nav.count(YOUTUBE_BACK_ACTION), 2)
            mapped = keymap.read_text()
            self.assertIn('<MyVideoNav>', mapped)
            self.assertEqual(mapped.count(YOUTUBE_BACK_ACTION), 4)


if __name__ == '__main__':
    unittest.main()
