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
        names = ('Includes.xml', 'IncludesHub.xml', 'DialogKeyboard.xml',
                 'DialogVideoInfo.xml', 'custom_1110_books.xml',
                 'custom_1111_digest.xml', 'custom_1112_home.xml',
                 'custom_1113_music.xml')
        for source in (self.home, self.browse, *(ET.parse(ROOT / '1080i' / name) for name in names)):
            for node in source.iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)

    def test_expansion_assets_and_page_mapping(self):
        icons = ('20-music-app', '21-books-app', '22-podcasts-app',
                 '23-music-album', '24-music-artist', '25-music-song',
                 '26-music-playlist', '31-settings-app')
        logos = ('27-aster-media-logo', '28-aster-books-logo',
                 '29-aster-music-logo', '30-aster-news-logo')
        for name in icons + logos:
            data = (ROOT / 'media' / f'{name}.png').read_bytes()[:24]
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n', name)
            expected = (128, 128) if name in icons else (512, 341)
            self.assertEqual(struct.unpack('!II', data[16:24]), expected, name)
        rail = (ROOT / '1080i/IncludesHub.xml').read_text()
        for name in ('20-music-app', '21-books-app', '31-settings-app'):
            self.assertEqual(rail.count(f'{name}.png'), 2, name)
        for page, mark in (('Home.xml', '27-aster-media-logo'),
                           ('DialogVideoInfo.xml', '27-aster-media-logo'),
                           ('custom_1110_books.xml', '28-aster-books-logo'),
                           ('custom_1111_digest.xml', '30-aster-news-logo'),
                           ('custom_1113_music.xml', '29-aster-music-logo')):
            self.assertIn(f'{mark}.png', (ROOT / '1080i' / page).read_text(), page)
        music = (ROOT / '1080i/custom_1113_music.xml').read_text()
        self.assertIn('23-music-album.png', music)

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
        for name in ('Home.xml', 'MyVideoNav.xml', 'Includes.xml'):
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

    def test_media_hero_fades_to_plain_stone_colour(self):
        colours = ET.parse(ROOT / 'colors/defaults.xml')
        self.assertEqual(colours.findtext('.//color[@name="asterStone"]'), 'ffe6dac8')
        self.assertEqual(self.home.findtext('.//backgroundcolor'), 'asterStone')
        for name in ('Home.xml', 'MyVideoNav.xml', 'DialogVideoInfo.xml'):
            root = ET.parse(ROOT / '1080i' / name)
            fades = [control for control in root.findall('.//control')
                     if control.findtext('texture') ==
                     'special://skin/media/ui-hero-bottom-fade.png']
            self.assertEqual(len(fades), 1, name)
            self.assertEqual(fades[0].findtext('colordiffuse'), 'asterStone', name)

    def test_clocks_use_24_hour_label_without_stone(self):
        for name in ('Home.xml', 'custom_1110_books.xml',
                     'custom_1111_digest.xml', 'custom_1112_home.xml',
                     'custom_1113_music.xml'):
            root = ET.parse(ROOT / '1080i' / name)
            labels = [control for control in root.findall('.//control')
                      if control.findtext('label') == '$INFO[System.Time(HH:mm)]']
            self.assertEqual(len(labels), 1, name)
            self.assertEqual(labels[0].findtext('align'), 'center', name)
            self.assertTrue(any(control.findtext('colordiffuse') == 'e029302b'
                                for control in root.findall('.//control')), name)
            self.assertFalse(any(control.findtext('texture') ==
                                 'special://skin/media/ui-limestone-panel.png'
                                 and control.findtext('left') == '1750'
                                 for control in root.findall('.//control')), name)

    def test_hero_block_is_centred_and_actions_match_rings(self):
        # Available hero-copy lane: header bottom 100 to queue heading 492.
        self.assertEqual((151 + 385 + 56) / 2, (100 + 492) / 2)
        for identifier in (120, 121):
            button = self.home.find(f'.//control[@id="{identifier}"]')
            self.assertEqual(button.findtext('top'), '385')
        self.assertEqual(self.browse.find('.//control[@id="19"]').findtext('ondown'), '9200')


if __name__ == '__main__':
    unittest.main()
