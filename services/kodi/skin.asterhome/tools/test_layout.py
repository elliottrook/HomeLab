"""Offline geometry and asset regression checks for the Aster Kodi shell."""
from pathlib import Path
import struct
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.home = ET.parse(ROOT / '1080i/Home.xml')
        self.browse = ET.parse(ROOT / '1080i/MyVideoNav.xml')

    def test_top_category_lane(self):
        previous_right = 0
        for identifier in range(130, 135):
            button = self.home.find(f'.//control[@id="{identifier}"]')
            self.assertEqual(button.findtext('top'), '26')
            left = int(button.findtext('left'))
            self.assertGreater(left, previous_right)
            previous_right = left + 248
        self.assertLess(previous_right, 1750)  # clock begins here

    def test_search_and_portraits_do_not_overlap(self):
        panel = self.browse.find('.//control[@id="50"]')
        search = self.browse.find('.//control[@id="19"]')
        self.assertGreater(int(panel.findtext('left')), int(search.findtext('left')) + int(search.findtext('width')))
        for layout in ('itemlayout', 'focusedlayout'):
            art = next(control for control in panel.find(layout).findall('control')
                       if control.find('texture') is not None
                       and control.find('texture').get('diffuse'))
            self.assertEqual(int(art.findtext('width')) * 3, int(art.findtext('height')) * 2)
            self.assertEqual(art.find('aspectratio').get('scalediffuse'), 'false')

    def test_runtime_assets_exist(self):
        for source in (self.home, self.browse, ET.parse(ROOT / '1080i/Includes.xml'), ET.parse(ROOT / '1080i/DialogKeyboard.xml'), ET.parse(ROOT / '1080i/DialogVideoInfo.xml')):
            for node in source.iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)

    def test_poster_masks_are_native_size(self):
        for name in ('ui-poster-mask.png', 'ui-poster-ring.png'):
            header = (ROOT / 'media' / name).read_bytes()[:24]
            self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('!II', header[16:24]), (220, 330))

    def test_limestone_surface_is_button_sized_and_reused(self):
        panel = ROOT / 'media/ui-limestone-panel.png'
        header = panel.read_bytes()[:24]
        self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('!II', header[16:24]), (280, 56))
        for name in ('Home.xml', 'MyVideoNav.xml', 'Includes.xml',
                     'custom_1110_books.xml', 'custom_1111_digest.xml',
                     'custom_1112_home.xml', 'custom_1113_music.xml'):
            self.assertIn('ui-limestone-panel.png', (ROOT / '1080i' / name).read_text())

    def test_expanded_menu_preserves_dimmed_artwork(self):
        fanart = self.home.find('.//control[@id="12"]')
        self.assertIsNone(fanart.find('visible'))
        fade = self.home.find('.//control[@id="13"]')
        self.assertIn('!Control.HasFocus(8999)', fade.findtext('visible'))
        overlays = [control for control in self.home.findall('.//control')
                    if control.findtext('colordiffuse') == 'b91f211e']
        self.assertEqual(len(overlays), 1)
        self.assertIn('Control.HasFocus(8999)', overlays[0].findtext('visible'))
        self.assertEqual(overlays[0].findtext('texture'), 'special://skin/media/ui-solid.png')

    def test_filter_heading_uses_small_stone_surface(self):
        panels = [control for control in self.browse.findall('.//control')
                  if control.findtext('texture') == 'special://skin/media/ui-limestone-panel.png']
        self.assertTrue(any(control.findtext('width') == '280' and
                            control.findtext('height') == '56' and
                            control.findtext('top') == '502' for control in panels))

    def test_hero_block_is_centred_and_actions_match_rings(self):
        # Available hero-copy lane: header bottom 100 to queue heading 492.
        self.assertEqual((151 + 385 + 56) / 2, (100 + 492) / 2)
        for identifier in (120, 121):
            button = self.home.find(f'.//control[@id="{identifier}"]')
            self.assertEqual(button.findtext('top'), '385')
        self.assertEqual(self.browse.find('.//control[@id="19"]').findtext('ondown'), '9200')


if __name__ == '__main__':
    unittest.main()
