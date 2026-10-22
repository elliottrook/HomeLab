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

    def test_v1_companion_and_youtube_plugins_are_required_dependencies(self):
        addon = ET.parse(ROOT / 'addon.xml')
        imports = {node.get('addon'): node.get('version')
                   for node in addon.findall('.//requires/import')}
        self.assertEqual(imports.get('plugin.video.asterhome'), '1.0.1')
        self.assertEqual(imports.get('plugin.audio.asterbooks'), '1.0.1')
        self.assertEqual(imports.get('plugin.video.youtube'), '7.4.4')

    def test_youtube_is_a_first_class_navigation_destination(self):
        rail = ET.parse(ROOT / '1080i/IncludesHub.xml')
        youtube = rail.find('.//control[@id="9008"]')
        self.assertIsNotNone(youtube)
        self.assertEqual(youtube.findtext('label'), 'YouTube')
        self.assertEqual(
            youtube.findtext('onclick'),
            'ActivateWindow(Videos,"plugin://plugin.video.youtube/",return)')
        self.assertEqual(youtube.findtext('onup'), '9007')
        self.assertEqual(youtube.findtext('ondown'), '9005')
        self.assertEqual(rail.find('.//control[@id="9007"]').findtext('ondown'),
                         '9008')
        self.assertEqual(rail.find('.//control[@id="9005"]').findtext('onup'),
                         '9008')
        youtube_icons = [node.text for node in rail.findall('.//texture')
                         if node.text and 'plugin.video.youtube' in node.text]
        self.assertEqual(len(youtube_icons), 2)
        self.assertTrue(all(icon.endswith('/resources/media/icon.png')
                            for icon in youtube_icons))

        includes = ET.parse(ROOT / '1080i/Includes.xml')
        icon = includes.find('.//variable[@name="AsterBrowseIcon"]/value[1]')
        self.assertIn('plugin.video.youtube', icon.get('condition'))
        self.assertEqual(icon.text,
                         'special://home/addons/plugin.video.youtube/resources/media/icon.png')
        heading = includes.find('.//variable[@name="AsterBrowseHeading"]/value[1]')
        self.assertIn('plugin.video.youtube', heading.get('condition'))
        self.assertEqual(heading.text, 'YouTube')

    def test_settings_exposes_only_installed_support_tools(self):
        settings = ET.parse(ROOT / '1080i/Settings.xml')
        items = settings.findall('.//control[@id="9000"]/content/item')
        actions = {item.findtext('label'): item.findtext('onclick') for item in items}
        self.assertEqual(actions['Remote controls'], 'RunAddon(script.keymap)')
        self.assertEqual(actions['Backup & restore'], 'RunAddon(script.xbmcbackup)')
        self.assertEqual(actions['Diagnostics'], 'RunAddon(script.logviewer)')
        self.assertEqual(actions['Lyrics'], 'Addon.OpenSettings(script.cu.lrclyrics)')
        for label, addon_id in (('Remote controls', 'script.keymap'),
                                ('Backup & restore', 'script.xbmcbackup'),
                                ('Diagnostics', 'script.logviewer'),
                                ('Lyrics', 'script.cu.lrclyrics')):
            item = next(item for item in items if item.findtext('label') == label)
            self.assertEqual(item.findtext('visible'), f'System.HasAddon({addon_id})')

    def test_support_addon_dialog_contracts_are_present(self):
        select = ET.parse(ROOT / '1080i/DialogSelect.xml')
        self.assertEqual(select.getroot().get('id'), '2000')
        self.assertEqual(select.findtext('./defaultcontrol'), '3')
        self.assertEqual(select.find('.//control[@id="3"]').get('type'), 'list')
        self.assertEqual(select.find('.//control[@id="1"]').get('type'), 'label')
        confirm = ET.parse(ROOT / '1080i/DialogConfirm.xml')
        self.assertEqual(confirm.findtext('./defaultcontrol'), '10')
        for identifier in ('1', '9', '10', '11', '12'):
            self.assertIsNotNone(confirm.find(f'.//control[@id="{identifier}"]'))

        context = ET.parse(ROOT / '1080i/DialogContextMenu.xml')
        self.assertEqual(context.findtext('./defaultcontrol'), '996')
        self.assertEqual(context.find('.//control[@id="996"]').get('type'), 'grouplist')
        self.assertEqual(context.find('.//control[@id="1000"]').get('type'), 'button')

        addon_settings = ET.parse(ROOT / '1080i/DialogAddonSettings.xml')
        expected_controls = (
            ('grouplist', '3'), ('grouplist', '5'), ('button', '7'),
            ('radiobutton', '8'), ('spincontrolex', '9'), ('edit', '12'),
            ('sliderex', '13'), ('label', '14'), ('colorbutton', '15'),
            ('scrollbar', '60'),
        )
        for control_type, identifier in expected_controls:
            control = addon_settings.find(
                f'.//control[@type="{control_type}"][@id="{identifier}"]')
            self.assertIsNotNone(control, f'{control_type} {identifier}')
        for identifier in ('28', '29', '30'):
            control = addon_settings.find(
                f'.//control[@type="button"][@id="{identifier}"]')
            self.assertIsNotNone(control, f'button {identifier}')

    def test_video_player_osd_contract_is_present(self):
        osd = ET.parse(ROOT / '1080i/VideoOSD.xml')
        self.assertEqual(osd.findtext('./defaultcontrol'), '602')
        by_id = {control.get('id'): control for control in osd.findall('.//control')
                 if control.get('id')}
        for identifier in ('600', '601', '602', '603', '605', '606', '607',
                           '70043', '7100', '7101', '7102', '9000'):
            self.assertIn(identifier, by_id)
        actions = [node.text for node in osd.findall('.//onclick')]
        for action in ('PlayerControl(Previous)', 'Seek(-10)',
                       'PlayerControl(Play)', 'Seek(30)',
                       'PlayerControl(Next)', 'PlayerControl(Stop)'):
            self.assertIn(action, actions)
        self.assertIsNotNone(osd.find('.//info[.="Player.Progress"]'))
        labels = [node.text or '' for node in osd.findall('.//label')]
        self.assertTrue(any('Player.Time' in label for label in labels))
        self.assertTrue(any('Player.Duration' in label for label in labels))
        self.assertEqual(by_id['7100'].findtext('onclick'),
                         'ActivateWindow(osdaudiosettings)')
        self.assertEqual(by_id['7101'].findtext('onclick'),
                         'ActivateWindow(osdsubtitlesettings)')
        quality_actions = [node.text for node in by_id['7102'].findall('onclick')]
        self.assertEqual(quality_actions,
                         ['PlayerResolutionSelect',
                          'ActivateWindow(osdvideosettings)'])
        self.assertEqual([node.text for node in by_id['70043'].findall('onclick')],
                         ['Dialog.Close(VideoOSD)',
                          'ActivateWindow(fullscreeninfo)'])
        home_info = self.home.find('.//control[@id="121"]')
        self.assertIsNotNone(home_info)
        self.assertEqual([node.text for node in home_info.findall('onclick')],
                         ['SetFocus(100)', 'Action(Info)'])
        ET.parse(ROOT / '1080i/VideoFullScreen.xml')

        settings = ET.parse(ROOT / '1080i/DialogSettings.xml')
        for control_type, identifier in (('grouplist', '5'), ('button', '7'),
                                         ('radiobutton', '8'),
                                         ('spincontrolex', '9'),
                                         ('sliderex', '13'),
                                         ('scrollbar', '60')):
            self.assertIsNotNone(settings.find(
                f'.//control[@type="{control_type}"][@id="{identifier}"]'))

        full_info = ET.parse(ROOT / '1080i/DialogFullScreenInfo.xml')
        self.assertEqual(full_info.findtext('./defaultcontrol'), '999')
        self.assertEqual(full_info.find('.//control[@id="999"]/onclick').text,
                         'OSD')
        self.assertTrue(any('VideoPlayer.Plot' in (node.text or '')
                            for node in full_info.findall('.//label')))

        seek = ET.parse(ROOT / '1080i/DialogSeekBar.xml')
        self.assertIsNotNone(seek.find('.//info[.="Player.Progress"]'))
        self.assertTrue(any('VideoPlayer.Title' in (node.text or '')
                            for node in seek.findall('.//label')))

    def test_media_cards_expose_watch_state_and_episode_counts(self):
        includes = ET.parse(ROOT / '1080i/Includes.xml')
        badges = includes.find('.//include[@name="AsterWatchBadges"]')
        self.assertIsNotNone(badges)
        labels = [node.text or '' for node in badges.findall('.//label')]
        self.assertIn('✓', labels)
        self.assertIn('●', labels)
        self.assertTrue(any('UnWatchedEpisodes' in label for label in labels))
        conditions = [node.text or '' for node in badges.findall('.//visible')]
        self.assertTrue(any('ListItem.PlayCount' in condition
                            for condition in conditions))
        self.assertTrue(any('ListItem.IsResumable' in condition
                            for condition in conditions))
        textures = [node.text or '' for node in badges.findall('.//texture')]
        self.assertIn('special://skin/media/ui-timer-dot.png', textures)

        for page in ('Home.xml', 'MyVideoNav.xml'):
            tree = ET.parse(ROOT / '1080i' / page)
            uses = tree.findall('.//include[@content="AsterWatchBadges"]')
            self.assertGreaterEqual(len(uses), 2, page)

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
        fanart = self.home.find('.//control[@id="12"]')
        genre_fade = next(node for node in fanart.findall('animation')
                          if 'Control.HasFocus(140)' in node.get('condition', ''))
        self.assertEqual((genre_fade.get('effect'), genre_fade.get('start'),
                          genre_fade.get('end'), genre_fade.get('time'),
                          genre_fade.get('reversible')),
                         ('fade', '100', '0', '220', 'true'))
        self.assertIn('Control.HasFocus(146)', genre_fade.get('condition'))
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
        self.assertEqual(len(includes), 7)
        params = [{node.get('name'): node.get('value') for node in include.findall('param')}
                  for include in includes]
        self.assertEqual([int(row['left']) for row in params],
                         [125, 365, 605, 845, 1085, 1325, 1565])
        recommended = self.home.find('.//control[@id="110"]')
        self.assertEqual(recommended.findtext('ondown'), '140')
        media_group = self.home.find('.//control[@id="22"]')
        slides = [node for node in media_group.findall('animation')
                  if node.get('effect') == 'slide']
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].get('end'), '0,-380')
        for identifier in range(140, 147):
            self.assertIn(f'Control.HasFocus({identifier})', slides[0].get('condition'))
        hero_group = self.home.find('.//control[@id="21"]')
        genre_fade = next(node for node in hero_group.findall('animation')
                          if node.get('condition', '').startswith('Control.HasFocus(140)'))
        self.assertEqual((genre_fade.get('effect'), genre_fade.get('end')),
                         ('fade', '0'))
        template = ET.parse(ROOT / '1080i/Includes.xml').find(
            './/include[@name="AsterGenreTile"]/definition/control')
        self.assertEqual((template.findtext('top'), template.findtext('width'),
                          template.findtext('orientation')), ('1100', '240', 'horizontal'))
        layout = template.find('itemlayout')
        poster = next(control for control in layout.findall('control')
                      if control.find('texture') is not None and
                      control.find('texture').get('diffuse'))
        self.assertEqual((poster.findtext('width'), poster.findtext('height')),
                         ('210', '315'))
        self.assertEqual(int(layout.get('width')) * 7, 1680)
        self.assertEqual([row['label'] for row in params],
                         ['Comedy', 'Drama', 'Action', 'Sci-Fi', 'Documentary', 'Horror', 'Family'])
        for layout_name in ('itemlayout', 'focusedlayout'):
            caption = next(control for control in template.find(layout_name).findall('control')
                           if control.get('type') == 'label')
            self.assertEqual(caption.findtext('label'), '$PARAM[label]')
            self.assertEqual(caption.findtext('textcolor'), 'asterInk')
        self.assertFalse(any(control.findtext('top') == '302'
                             for control in template.findall('.//control')))

    def test_rail_headings_remain_black(self):
        media_group = self.home.find('.//control[@id="22"]')
        for label in ('Continue Watching', 'Recommended for You', 'Genre'):
            headings = [control for control in media_group.findall('control')
                        if control.get('type') == 'label' and
                        control.findtext('label') == label]
            self.assertEqual(len(headings), 1, label)
            self.assertEqual(headings[0].findtext('textcolor'), 'asterInk')
            self.assertIsNone(headings[0].find('visible'))

    def test_genre_rail_uses_read_only_previews_and_combined_browser(self):
        self.assertIsNone(self.home.find('onload'))
        self.assertNotIn('genre_data.py', (ROOT / '1080i/Home.xml').read_text())
        files = list((ROOT / 'playlists' / 'genre-previews').glob('*.xsp'))
        self.assertEqual(len(files), 7)
        for source in files:
            root = ET.parse(source).getroot()
            self.assertIn(root.get('type'), ('movies', 'tvshows'))
            self.assertEqual(root.find('rule').get('field'), 'genre')
            self.assertEqual(root.find('rule').get('operator'), 'contains')
            self.assertEqual(root.findtext('order'), 'random')
            self.assertEqual(root.findtext('limit'), '1')
        includes = [node for node in self.home.findall('.//include')
                    if node.get('content') == 'AsterGenreTile']
        browse = [{param.get('name'): param.get('value')
                   for param in include.findall('param')} for include in includes]
        for row in browse:
            self.assertEqual(row['browse'],
                             f"plugin://plugin.video.asterhome/?genre={row['label']}")
        self.assertFalse(list((ROOT / 'playlists' / 'genres').glob('*.xsp')))
        includes_root = ET.parse(ROOT / '1080i/Includes.xml')
        heading = includes_root.find('.//variable[@name="AsterBrowseHeading"]')
        plugin_value = next(value for value in heading.findall('value')
                            if 'plugin.video.asterhome' in
                            value.get('condition', ''))
        self.assertEqual(plugin_value.text, '$INFO[Container.PluginCategory]')

    def test_settings_landing_uses_aster_cards_and_identity(self):
        root = ET.parse(ROOT / '1080i/Settings.xml')
        self.assertEqual(root.getroot().get('id'), '4')
        self.assertEqual(root.findtext('./backgroundcolor'), 'asterStone')
        panel = root.find('.//control[@type="panel"][@id="9000"]')
        self.assertIsNotNone(panel)
        self.assertEqual((panel.findtext('left'), panel.findtext('width')),
                         ('462', '1390'))
        self.assertEqual(len(panel.findall('./content/item')), 8)
        self.assertTrue(all(item.find('property[@name="Description"]') is not None
                            for item in panel.findall('./content/item')))
        self.assertIsNotNone(root.find(
            './/texture[.="special://skin/media/aster-home-horizontal-512.png"]'))
        focus = panel.find('./focusedlayout/control[@type="image"]/texture')
        self.assertEqual(focus.get('colordiffuse'), 'asterSage')

    def test_settings_category_preserves_kodi_contract_with_aster_styling(self):
        root = ET.parse(ROOT / '1080i/SettingsCategory.xml')
        self.assertEqual(root.getroot().get('id'), '12')
        controls = root.findall('.//control')
        by_id = {control.get('id'): control for control in controls if control.get('id')}
        for identifier in ('2', '3', '5', '6', '7', '8', '9', '10', '11',
                           '13', '14', '15', '20', '60'):
            self.assertIn(identifier, by_id)
        self.assertEqual(by_id['3'].get('type'), 'grouplist')
        self.assertEqual(by_id['5'].get('type'), 'grouplist')
        for identifier in ('7', '8', '9', '13', '15'):
            self.assertEqual(by_id[identifier].find('texturefocus').get('colordiffuse'),
                             'asterSage')
        self.assertEqual(by_id['2'].findtext('textcolor'), 'asterInk')
        self.assertIsNotNone(root.find(
            './/texture[.="special://skin/media/rail-background.png"]'))


if __name__ == '__main__':
    unittest.main()
