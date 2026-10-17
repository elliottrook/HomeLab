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

    def test_media_logo_is_centered_and_enlarged_in_header_gutter(self):
        logo = next(control for control in self.home.findall('.//control')
                    if control.findtext('texture') ==
                    'special://skin/media/27-aster-media-logo.png')
        self.assertEqual((logo.findtext('left'), logo.findtext('top'),
                          logo.findtext('width'), logo.findtext('height')),
                         ('110', '0', '240', '160'))
        self.assertEqual(110 + 240 // 2, (85 + 375) // 2)

    def test_product_logos_share_one_header_slot(self):
        for name, mark in (('Home.xml', '27-aster-media-logo.png'),
                           ('DialogVideoInfo.xml', '27-aster-media-logo.png'),
                           ('IncludesBooks.xml', '28-aster-books-logo.png'),
                           ('IncludesMusic.xml', '29-aster-music-logo.png'),
                           ('custom_1111_digest.xml', '30-aster-news-logo.png'),
                           ('custom_1122_breaking.xml', '30-aster-news-logo.png')):
            root = ET.parse(ROOT / '1080i' / name)
            logo = next(control for control in root.findall('.//control')
                        if control.findtext('texture') ==
                        'special://skin/media/' + mark)
            self.assertEqual(tuple(logo.findtext(key) for key in
                                   ('left', 'top', 'width', 'height')),
                             ('110', '0', '240', '160'), name)

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
                 'custom_1113_music.xml', 'custom_1122_breaking.xml')
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
                           ('IncludesBooks.xml', '28-aster-books-logo'),
                           ('custom_1111_digest.xml', '30-aster-news-logo'),
                           ('custom_1122_breaking.xml', '30-aster-news-logo'),
                           ('IncludesMusic.xml', '29-aster-music-logo')):
            self.assertIn(f'{mark}.png', (ROOT / '1080i' / page).read_text(), page)
        music = (ROOT / '1080i/IncludesMusic.xml').read_text()
        self.assertIn('23-music-album.png', music)

    def test_poster_masks_are_native_size(self):
        for name in ('ui-poster-mask.png', 'ui-poster-ring.png'):
            header = (ROOT / 'media' / name).read_bytes()[:24]
            self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('!II', header[16:24]), (220, 330))

    def test_limestone_surface_is_button_sized_and_reserved_for_major_actions(self):
        panel = ROOT / 'media/ui-limestone-panel.png'
        header = panel.read_bytes()[:24]
        self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('!II', header[16:24]), (280, 56))
        for name in ('Home.xml', 'Includes.xml', 'custom_1112_home.xml'):
            self.assertIn('ui-limestone-panel.png', (ROOT / '1080i' / name).read_text())
        self.assertNotIn('ui-limestone-panel.png',
                         (ROOT / '1080i/MyVideoNav.xml').read_text())

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

    def test_search_controls_use_quiet_charcoal_and_gold_language(self):
        includes = ET.parse(ROOT / '1080i/Includes.xml')
        filter_button = includes.find('.//include[@name="AsterFilterButton"]')
        self.assertEqual(filter_button.findtext('textcolor'), 'asterIvory')
        self.assertEqual(filter_button.findtext('texturenofocus'), 'none')
        backplate = includes.find('.//include[@name="AsterQuietFieldBackplate"]/definition')
        self.assertEqual([node.findtext('colordiffuse') for node in backplate.findall('control')],
                         ['b0c2a06b', 'e029302b'])
        search_entry = self.browse.find('.//control[@id="19"]')
        self.assertEqual(search_entry.findtext('textoffsetx'), '16')
        self.assertEqual(search_entry.findtext('align'), 'left')
        self.assertEqual(search_entry.findtext('aligny'), 'center')
        for name, minimum in (('MyVideoNav.xml', 5), ('IncludesBooks.xml', 2),
                              ('IncludesMusic.xml', 2), ('DialogKeyboard.xml', 1)):
            root = ET.parse(ROOT / '1080i' / name)
            fields = [node for node in root.findall('.//include')
                      if node.get('content') == 'AsterQuietFieldBackplate']
            self.assertGreaterEqual(len(fields), minimum, name)
        self.assertFalse(any(control.findtext('texture') ==
                             'special://skin/media/ui-limestone-panel.png' and
                             control.findtext('top') == '502'
                             for control in self.browse.findall('.//control')))

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

    def test_clocks_share_24_hour_charcoal_and_gold_pill(self):
        includes = ET.parse(ROOT / '1080i/Includes.xml')
        clock = includes.find('.//include[@name="AsterClockPill"]/definition')
        self.assertEqual([node.findtext('colordiffuse') for node in
                          clock.findall('control[@type="image"]')],
                         ['75cbb991', 'e029302b'])
        label = clock.find('control[@type="label"]')
        self.assertEqual(label.findtext('label'), '$INFO[System.Time(HH:mm)]')
        self.assertEqual(label.findtext('align'), 'center')
        for name in ('Home.xml', 'IncludesBooks.xml',
                     'custom_1111_digest.xml', 'custom_1112_home.xml',
                     'custom_1122_breaking.xml', 'IncludesMusic.xml'):
            root = ET.parse(ROOT / '1080i' / name)
            references = [node for node in root.findall('.//include')
                          if node.get('content') == 'AsterClockPill']
            self.assertEqual(len(references), 1, name)

    def test_hero_block_is_centred_and_actions_match_rings(self):
        # Leave a gap below the enlarged product mark without hitting the queue.
        greeting = next(control for control in self.home.findall('.//control')
                        if control.findtext('label') == 'Good evening, Jason')
        self.assertGreaterEqual(int(greeting.findtext('top')), 176)
        for identifier in (120, 121):
            button = self.home.find(f'.//control[@id="{identifier}"]')
            self.assertEqual(button.findtext('top'), '411')
            self.assertLessEqual(int(button.findtext('top')) + 56, 492)
        self.assertEqual(self.browse.find('.//control[@id="19"]').findtext('ondown'), '9200')

    def test_genre_rail_peeks_then_lifts_into_view(self):
        includes = [node for node in self.home.findall('.//include')
                    if node.get('content') == 'AsterGenreTile']
        self.assertEqual(len(includes), 6)
        params = [{node.get('name'): node.get('value') for node in include.findall('param')}
                  for include in includes]
        self.assertEqual([row['label'] for row in params],
                         ['Comedy', 'Drama', 'Action', 'Sci-Fi', 'Documentary', 'Horror'])
        self.assertEqual([int(row['left']) for row in params],
                         [125, 405, 685, 965, 1245, 1525])
        recommended = self.home.find('.//control[@id="110"]')
        self.assertEqual(recommended.findtext('ondown'), '140')
        media_group = self.home.find('.//control[@id="22"]')
        slides = [node for node in media_group.findall('animation')
                  if node.get('effect') == 'slide']
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].get('end'), '0,-380')
        for identifier in range(140, 146):
            self.assertIn(f'Control.HasFocus({identifier})', slides[0].get('condition'))
        hero_group = self.home.find('.//control[@id="21"]')
        genre_fade = next(node for node in hero_group.findall('animation')
                          if node.get('condition', '').startswith('Control.HasFocus(140)'))
        self.assertEqual((genre_fade.get('effect'), genre_fade.get('end')),
                         ('fade', '0'))
        template = ET.parse(ROOT / '1080i/Includes.xml').find(
            './/include[@name="AsterGenreTile"]/definition/control')
        self.assertEqual((template.findtext('top'), template.findtext('width'),
                          template.findtext('orientation')), ('1038', '280', 'horizontal'))
        layout = template.find('itemlayout')
        poster = next(control for control in layout.findall('control')
                      if control.find('texture') is not None and
                      control.find('texture').get('diffuse'))
        self.assertEqual((poster.findtext('width'), poster.findtext('height')),
                         ('250', '375'))
        self.assertEqual(int(layout.get('width')) * 6, 1680)
        labels = [node.findtext('label') for node in media_group.findall('control')
                  if node.get('type') == 'label' and node.findtext('top') == '1420']
        self.assertEqual(labels,
                         ['Comedy', 'Drama', 'Action', 'Sci-Fi', 'Documentary', 'Horror'])
        self.assertTrue(all(node.findtext('textcolor') == 'asterInk'
                            for node in media_group.findall('control')
                            if node.get('type') == 'label' and node.findtext('top') == '1420'))
        self.assertFalse(any(control.findtext('top') == '302'
                             for control in template.findall('.//control')))

    def test_genre_rail_uses_native_read_only_playlists(self):
        self.assertIsNone(self.home.find('onload'))
        self.assertNotIn('genre_data.py', (ROOT / '1080i/Home.xml').read_text())
        for folder in ('genre-previews', 'genres'):
            files = list((ROOT / 'playlists' / folder).glob('*.xsp'))
            self.assertEqual(len(files), 6)
            for source in files:
                root = ET.parse(source).getroot()
                self.assertIn(root.get('type'), ('movies', 'tvshows'))
                self.assertEqual(root.find('rule').get('field'), 'genre')
                self.assertEqual(root.find('rule').get('operator'), 'contains')
                self.assertEqual(root.findtext('order'), 'random')
                self.assertEqual(root.findtext('limit'),
                                 '1' if folder == 'genre-previews' else None)


if __name__ == '__main__':
    unittest.main()
