"""Synthetic hub contracts; no live feed, library or playback mutations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import wave
import xml.etree.ElementTree as ET
from hub_data import (CAMERA_PILOT_SECONDS, CAMERA_PILOT_URL, TIMER_PRESETS, WINDOWS,
                      cached_digest_audio, digest_view, show_digest_story,
                      story_at_elapsed, story_for_playback, sync_digest_window,
                      timer_display)
from digest_data import BreakingCards, DigestCards, merge_chapters, public_image
from hub_feeds import books_view, home_dashboard, home_view, read_feed
import json
import io
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class HubTests(unittest.TestCase):
    def feed(self, **extra):
        return {'generated_at': datetime.now(timezone.utc).isoformat(),
                'chapters': [{'title': '[B]Synthetic headline[/B]', 'start': 61.2}], **extra}

    def test_chapter_times_and_markup_are_safe(self):
        rows, _ = digest_view(self.feed())
        self.assertEqual(rows[0][1], '1:01')
        self.assertNotIn('[', rows[0][0])

    def test_stale_and_future_feeds_fail_closed(self):
        for delta in (-48, 2):
            with self.assertRaises(ValueError):
                digest_view(self.feed(generated_at=(datetime.now(timezone.utc) + timedelta(hours=delta)).isoformat()))

    def test_empty_and_invalid_offsets_rejected(self):
        with self.assertRaises(ValueError):
            digest_view(self.feed(chapters=[]))
        for start in (-1, float('nan'), float('inf'), 14401):
            with self.assertRaises(ValueError):
                digest_view(self.feed(chapters=[{'title': 'Synthetic', 'start': start}]))
        with self.assertRaises(ValueError):
            digest_view(self.feed(chapters=[{'title': 'Later', 'start': 62},
                                            {'title': 'Earlier', 'start': 61}]))

    def test_bounded_rows(self):
        rows, _ = digest_view(self.feed(chapters=[{'title': 'Synthetic', 'start': n} for n in range(100)]))
        self.assertEqual(len(rows), 40)

    def test_published_cards_join_audio_chapters_without_inventing_art(self):
        parser = DigestCards()
        parser.feed('''<section><article class="digest-card"><img class="digest-hero"
            src="https://news.example.org/photo.jpg"><div class="digest-source">BBC &middot; CBC</div>
            <div class="digest-body"><div class="digest-headline">A &amp; B</div>
            <p class="digest-summary">A real published summary.</p></div></article></section>''')
        stories = merge_chapters([('A & B', '1:01', 61.2), ('Unmatched', '2:03', 123.0)],
                                 parser.cards)
        self.assertEqual(stories[0]['summary'], 'A real published summary.')
        self.assertEqual(stories[0]['source'], 'BBC · CBC')
        self.assertEqual(stories[0]['image'], 'https://news.example.org/photo.jpg')
        self.assertEqual(stories[1]['image'], '')
        self.assertEqual(stories[1]['summary'], '')

    def test_breaking_page_parser_keeps_only_reading_fields(self):
        parser = BreakingCards()
        parser.feed('''<section><article class="cluster" data-search="discard">
            <div class="cluster-head"><div><div class="eyebrow">Story cluster</div>
            <h2>A &amp; B</h2></div><span class="header-stat"><strong>2</strong> sources</span></div>
            <p class="cluster-summary">A published summary.</p>
            <div class="outlets"><a href="https://example.org/a">CBC</a>
            <span class="rating">Centre</span> · <a href="https://example.org/b">BBC</a></div>
            </article></section>''')
        self.assertEqual(parser.cards, [{
            'title': 'A & B', 'summary': 'A published summary.',
            'source': 'CBC Centre · BBC'}])

    def test_feed_images_cannot_target_lan_or_non_https(self):
        for value in ('http://example.org/x.jpg', 'https://192.168.1.1/x',
                      'https://news.internal/x', 'https://localhost/x',
                      'https://example.org:8080/x', 'https://example.org:bad/x',
                      'https://user:pass@example.org/x'):
            self.assertEqual(public_image(value), '')

    def test_story_selection_follows_chapter_boundaries(self):
        stories = [{'start': value} for value in (4, 62, 131)]
        self.assertEqual([story_at_elapsed(stories, value) for value in (0, 4, 61, 62, 200)],
                         [0, 0, 0, 1, 2])

    def test_timer_display_uses_sixty_pips_at_minute_boundary(self):
        self.assertEqual(timer_display(60), ('01:00', '60'))
        self.assertEqual(timer_display(59), ('00:59', '59'))
        self.assertEqual(timer_display(1), ('00:01', '1'))
        self.assertEqual(timer_display(0), ('00:00', '0'))
        self.assertEqual(timer_display(90000), ('1440:00', '60'))
        for invalid in (True, 1.5, '60'):
            with self.assertRaises(ValueError):
                timer_display(invalid)

    def test_timer_presets_are_named_and_bounded(self):
        self.assertEqual(TIMER_PRESETS, {
            'timer_1': (60, 'One minute timer'),
            'timer_5': (300, 'Five minute timer'),
            'timer_30': (1800, 'Thirty minute timer'),
        })

    def test_timer_completion_chime_is_five_seconds(self):
        with wave.open(str(ROOT / 'media/timer-complete.wav'), 'rb') as chime:
            self.assertEqual(chime.getnchannels(), 1)
            self.assertEqual(chime.getsampwidth(), 2)
            self.assertAlmostEqual(chime.getnframes() / chime.getframerate(), 5.0,
                                   places=3)

    def test_selected_story_survives_pre_seek_window_refresh(self):
        stories = [{'start': value} for value in (4, 62, 131)]
        self.assertEqual(story_for_playback(stories, None, 62), 1)
        self.assertEqual(story_for_playback(stories, 1, 62), 1)
        self.assertEqual(story_for_playback(stories, 63, 62), 1)
        self.assertEqual(story_for_playback(stories, 132, 62), 2)
        self.assertEqual(story_for_playback(stories, 1, None), 0)

    def test_bounded_digest_sync_advances_panel_without_a_worker(self):
        class Window:
            def __init__(self):
                self.properties = {'AsterHub.AudioPath': '/tmp/digest.mp3',
                                   'AsterHub.RowsReady': 'true',
                                   'AsterHub.ActiveIndex': '0',
                                   'AsterHub.Stories': json.dumps([
                                       {'start': 0, 'title': 'First',
                                        'summary': 'First summary', 'source': 'Test source',
                                        'image': ''},
                                       {'start': 10, 'title': 'Second',
                                        'summary': 'Second summary', 'source': 'Test source',
                                        'image': ''},
                                       {'start': 20, 'title': 'Third',
                                        'summary': 'Third summary', 'source': 'Test source',
                                        'image': ''}])}
            def getProperty(self, key):
                return self.properties.get(key, '')
            def setProperty(self, key, value):
                self.properties[key] = value
        class Player:
            def isPlayingAudio(self): return True
            def getPlayingFile(self): return '/tmp/digest.mp3'
            def getTime(self): return 12
        class Xbmc:
            def __init__(self): self.builtins = []
            def Player(self): return Player()
            def executebuiltin(self, command): self.builtins.append(command)
        window = Window()
        xbmc = Xbmc()
        sync_digest_window(xbmc, window)
        self.assertEqual(window.properties['AsterHub.ActiveTitle'], 'Second')
        self.assertEqual(window.properties['AsterHub.ActiveIndex'], '1')
        self.assertEqual(window.properties['AsterHub.DigestPlaying'], 'true')
        self.assertEqual(xbmc.builtins, ['Control.SetFocus(500,1,absolute)'])
        self.assertFalse(hasattr(window, 'getControl'))

    def test_digest_audio_cache_is_bounded_and_reused(self):
        class Vfs:
            def __init__(self, path):
                self.path = path
            def translatePath(self, name):
                self.assert_name = name
                return self.path
        class Source(io.BytesIO):
            headers = {'Content-Length': '7',
                       'Last-Modified': 'Fri, 16 Oct 2026 00:00:00 GMT'}
        with tempfile.TemporaryDirectory() as directory:
            vfs = Vfs(directory)
            with patch('hub_data.urlopen', return_value=Source(b'example')) as fetch:
                path = cached_digest_audio(vfs, '2026-10-16T00:00:00+00:00')
                self.assertEqual(Path(path).read_bytes(), b'example')
                self.assertEqual(cached_digest_audio(vfs, '2026-10-16T00:00:00+00:00'), path)
                fetch.assert_called_once()
            with patch('hub_data.urlopen', return_value=Source(b'different')):
                other = cached_digest_audio(vfs, '2026-10-16T00:00:01+00:00')
                self.assertNotEqual(other, path)
            with patch('hub_data.urlopen', return_value=Source(b'')):
                with self.assertRaises(ValueError):
                    cached_digest_audio(vfs, '2026-10-16T00:00:02+00:00')
            with patch('hub_data.urlopen', return_value=Source(b'changed')):
                with self.assertRaisesRegex(ValueError, 'changed'):
                    cached_digest_audio(vfs, '2026-10-17T00:00:00+00:00')
            self.assertFalse(list(Path(directory).glob('*.part')))

    def test_story_panel_bounds_summary_and_keeps_art(self):
        class Window:
            properties = {}
            def setProperty(self, key, value):
                self.properties[key] = value
        class Item:
            def getProperty(self, key):
                return {'AsterHub.StoryTitle': 'Example',
                        'AsterHub.StorySummary': 'word ' * 100,
                        'AsterHub.StorySource': 'Example News',
                        'AsterHub.StoryImage': 'https://news.example.org/photo.jpg'}[key]
        window = Window()
        show_digest_story(window, Item())
        self.assertLessEqual(len(window.properties['AsterHub.ActiveSummary']), 160)
        self.assertEqual(window.properties['AsterHub.ActiveImage'], 'https://news.example.org/photo.jpg')
        self.assertNotIn('watch_digest', (ROOT / 'tools/hub_data.py').read_text())

    def test_books_feed_selects_only_approved_library_fields(self):
        payload = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
                   'items': [
                       {'authority': 'audiobookshelf', 'media_type': 'audiobook',
                        'authority_id': 'a1', 'title': 'A [Book]', 'secret': 'discard'},
                       {'authority': 'radarr', 'media_type': 'movie',
                        'authority_id': 'm1', 'title': 'Not a book'},
                       {'authority': 'audiobookshelf', 'media_type': 'audiobook',
                        'authority_id': 'a1', 'title': 'Duplicate'},
                       {'authority': 'calibre', 'media_type': 'ebook',
                        'authority_id': 'e1', 'title': 'An Ebook'}]}
        rows = books_view(payload)
        self.assertEqual(rows, [('A (Book)', 'Audiobook · Audiobookshelf', None),
                                ('An Ebook', 'Ebook · Calibre', None)])
        payload['generated_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        with self.assertRaises(ValueError):
            books_view(payload)

    def test_home_feed_is_presence_only_and_bounded(self):
        payload = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
                   'snapshot': {'schema_version': 1, 'rooms': ['Living Room'],
                                'entities': ['Laundry lights'], 'timers': [],
                                'media_providers': []}}
        self.assertEqual(home_view(payload), [('Living Room', 'Room', None),
                                              ('Laundry lights', 'Available light or switch', None)])
        payload['snapshot']['entities'] = ['Secret\nvalue']
        with self.assertRaises(ValueError):
            home_view(payload)

    def test_home_v2_accepts_only_bounded_light_and_temperature_values(self):
        payload = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
                   'snapshot': {'schema_version': 2, 'rooms': [], 'entities': ['laundry lights'],
                                'timers': [], 'media_providers': [],
                                'lights': [{'alias': 'laundry lights', 'state': 'on'}],
                                'temperatures': [{'alias': 'hall temperature', 'value': 20.6,
                                                  'unit': '°C'}],
                                'cameras': [{'alias': 'Front of house', 'status': 'online'}]}}
        self.assertEqual(home_view(payload), [('laundry lights', 'Light · On', None),
                                              ('hall temperature', 'Temperature · 20.6°C', None),
                                              ('Front of house', 'Camera · Online · Live view in Frigate app', None)])
        self.assertEqual(home_dashboard(payload), {
            'LightLabel': 'Laundry Lights', 'LightValue': 'On',
            'TemperatureLabel': 'Hall Temperature', 'TemperatureValue': '20.6°C',
            'CameraLabel': 'Front Of House', 'CameraStatus': 'Online',
            'WeatherLabel': 'Weather', 'WeatherValue': 'Unavailable',
            'WeatherDetail': 'No reviewed weather',
            'TimerName': 'No active timer', 'TimerLabel': 'Not connected',
            'TimerDigital': '--:--',
            'TimerSecond': '0', 'TimerActive': 'false'})
        payload['snapshot']['temperatures'][0]['value'] = float('nan')
        with self.assertRaises(ValueError):
            home_view(payload)
        payload['snapshot']['temperatures'] = []
        payload['snapshot']['cameras'][0]['status'] = 'stream-url'
        with self.assertRaises(ValueError):
            home_view(payload)
        payload['snapshot']['cameras'][0]['status'] = 'online'
        payload['generated_at'] = (datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat()
        with self.assertRaises(ValueError):
            home_view(payload)

    def test_home_v3_projects_bounded_current_weather(self):
        payload = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
                   'snapshot': {'schema_version': 3, 'rooms': [], 'entities': [],
                                'timers': [], 'media_providers': [], 'lights': [],
                                'temperatures': [], 'cameras': [],
                                'weather': [{'alias': 'home weather',
                                             'condition': 'partlycloudy',
                                             'temperature': 16.4, 'unit': '°C',
                                             'humidity': 55.0}]}}
        self.assertEqual(home_view(payload), [
            ('home weather', 'Partly Cloudy · 16.4°C · 55% humidity', None)])
        dashboard = home_dashboard(payload)
        self.assertEqual(dashboard['WeatherLabel'], 'Home Weather')
        self.assertEqual(dashboard['WeatherValue'], 'Partly Cloudy')
        self.assertEqual(dashboard['WeatherDetail'], '16.4°C · 55% humidity')
        payload['snapshot']['weather'][0]['condition'] = 'secret-state'
        with self.assertRaises(ValueError):
            home_view(payload)
        payload['snapshot']['weather'][0]['condition'] = 'sunny'
        payload['snapshot']['weather'][0]['humidity'] = 101
        with self.assertRaises(ValueError):
            home_view(payload)

    def test_local_feed_rejects_symlinks_and_oversized_content(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'books.json'
            file.write_text(json.dumps({'schema_version': 1}), encoding='utf-8')
            self.assertEqual(read_feed(file), {'schema_version': 1})
            alias = Path(directory) / 'alias.json'
            alias.symlink_to(file)
            with self.assertRaises(ValueError):
                read_feed(alias)
            file.write_bytes(b'x' * 262145)
            with self.assertRaises(ValueError):
                read_feed(file)

    def test_hub_windows_and_shared_rail(self):
        rail = ET.parse(ROOT / '1080i/IncludesHub.xml')
        routes = [node.text for node in rail.findall('.//onclick')]
        self.assertIn('ActivateWindow(Home)', routes)
        for page, identifier in WINDOWS.items():
            short = identifier - 10000
            if page == 'breaking':
                self.assertIn(f'ActivateWindow({short})',
                              [node.text for node in ET.parse(
                                  ROOT / '1080i/custom_1111_digest.xml').findall('.//onclick')])
            else:
                self.assertIn(f'ActivateWindow({short})', routes)
            window = ET.parse(ROOT / f'1080i/custom_{short}_{page}.xml')
            self.assertEqual(window.getroot().get('id'), str(short))
            if page in ('music', 'books'):
                name = 'AsterMusicPage' if page == 'music' else 'AsterBooksPage'
                self.assertIsNotNone(window.find(f'.//include[@content="{name}"]'))
                shared = ET.parse(ROOT / f'1080i/Includes{page.title()}.xml')
                self.assertIsNotNone(shared.find('.//control[@id="500"]'))
                self.assertIsNotNone(shared.find('.//include[@content="AsterNavigationRail"]'))
            else:
                self.assertIsNotNone(window.find('.//control[@id="500"]'))
                self.assertIsNotNone(window.find('.//include[@content="AsterNavigationRail"]'))
        digest = (ROOT / '1080i/custom_1111_digest.xml').read_text()
        self.assertIn('AsterHub.ActiveImage', digest)
        self.assertIn('AsterHub.ActiveSummary', digest)
        self.assertIn('AsterHub.DigestPlaying', digest)
        self.assertIn('AlarmClock(AsterDigestFollow', digest)
        self.assertIn('CancelAlarm(AsterDigestFollow,silent)', digest)

    def test_home_window_is_dashboard_with_camera_and_black_timer_panel(self):
        home = ET.parse(ROOT / '1080i/custom_1112_home.xml')
        labels = [node.text or '' for node in home.findall('.//label')]
        self.assertIn('Cameras', labels)
        self.assertIn('Timer', labels)
        self.assertIn('Home Assistant', labels)
        self.assertTrue(any('AsterHub.HomeCameraLabel' in label for label in labels))
        self.assertTrue(any('AsterHub.HomeTimerDigital' in label for label in labels))
        self.assertEqual(CAMERA_PILOT_URL,
                         'http://127.0.0.1:15102/api/front_of_house/latest.jpg')
        self.assertEqual(CAMERA_PILOT_SECONDS, 300)
        camera_images = [node for node in home.findall('.//control[@type="image"]')
                         if node.findtext('texture') ==
                         '$INFO[Window.Property(AsterHub.CameraImage)]']
        self.assertEqual(len(camera_images), 1)
        camera_actions = [node.text for node in home.findall('.//onclick')]
        self.assertIn('RunScript(special://skin/tools/hub_data.py,home,camera)',
                      camera_actions)
        for preset in ('timer_1', 'timer_5', 'timer_30'):
            self.assertIn(f'RunScript(special://skin/tools/hub_data.py,home,{preset})',
                          camera_actions)
        preset_labels = {node.get('id'): node.findtext('label')
                         for node in home.findall('.//control[@type="button"]')
                         if node.get('id') in {'303', '304', '305'}}
        self.assertEqual(preset_labels, {
            '303': 'One minute', '304': 'Five minutes', '305': 'Thirty minutes'})
        live_view = home.find('.//control[@id="302"]')
        self.assertEqual(live_view.findtext('top'), '922')
        self.assertEqual(live_view.findtext('height'), '58')
        self.assertEqual({home.find(f'.//control[@id="{identifier}"]').findtext('top')
                          for identifier in ('302', '303', '304', '305')}, {'922'})
        self.assertEqual(home.getroot().findtext('onunload'),
                         'RunScript(special://skin/tools/hub_data.py,home,home_stop)')
        timer_cards = [node for node in home.findall('.//control[@type="image"]')
                       if node.findtext('left') == '1005' and node.findtext('top') == '478']
        self.assertEqual(len(timer_cards), 1)
        self.assertEqual(timer_cards[0].findtext('width'), '400')
        self.assertEqual(timer_cards[0].findtext('height'), '526')
        self.assertEqual(timer_cards[0].findtext('colordiffuse'), 'ff10110f')
        timer_face = [node for node in home.findall('.//control[@type="image"]')
                      if node.findtext('texture') == 'special://skin/media/ui-timer-base.png']
        self.assertEqual(timer_face, [])
        digital = next(node for node in home.findall('.//control[@type="label"]')
                       if 'AsterHub.HomeTimerDigital' in (node.findtext('label') or ''))
        self.assertEqual(digital.findtext('font'), 'font80')
        self.assertEqual(int(digital.findtext('left')) + int(digital.findtext('width')) // 2,
                         1210)
        self.assertEqual(int(digital.findtext('top')) + int(digital.findtext('height')) // 2,
                         665)
        timer_name = next(node for node in home.findall('.//control[@type="label"]')
                          if 'AsterHub.HomeTimerName' in (node.findtext('label') or ''))
        self.assertEqual(int(timer_name.findtext('top')) +
                         int(timer_name.findtext('height')) // 2, 734)
        self.assertEqual(timer_name.findtext('font'), 'font24')
        ring = ET.parse(ROOT / '1080i/IncludesTimer.xml')
        dot_definition = ring.find('.//include[@name="AsterTimerDot"]/definition/control')
        self.assertEqual(dot_definition.findtext('width'), '16')
        self.assertEqual(dot_definition.findtext('height'), '16')
        self.assertIsNone(dot_definition.find('texture').get('border'))
        self.assertEqual(dot_definition.findtext('texture'),
                         'special://skin/media/ui-timer-dot.png')
        self.assertEqual(dot_definition.findtext('aspectratio'), 'keep')
        fonts = ET.parse(ROOT / '1080i/Font.xml')
        font_sizes = {node.findtext('name'): node.findtext('size')
                      for node in fonts.findall('.//font')}
        self.assertEqual(font_sizes.get('font64'), '64')
        self.assertEqual(font_sizes.get('font80'), '80')
        ring_group = next(node for node in home.findall('.//control[@type="group"]')
                          if node.find("include[@content='AsterTimerRing']") is not None)
        self.assertEqual(ring_group.findtext('left'), '-6')
        self.assertEqual(ring_group.findtext('top'), '24')
        completion = next(node for node in home.findall('.//control[@type="label"]')
                          if node.findtext('label') == 'Timer complete')
        self.assertGreaterEqual(int(completion.findtext('top')), 484)
        self.assertLessEqual(int(completion.findtext('top')) +
                             int(completion.findtext('height')), 865)
        dots = ring.findall('.//include[@content="AsterTimerDot"]')
        self.assertEqual(len(dots), 60)
        self.assertEqual([int(node.find("param[@name='threshold']").get('value'))
                          for node in dots], list(range(60)))
        self.assertTrue(all(node.find("param[@name='angle']") is None for node in dots))
        self.assertIsNotNone(home.find('.//control[@id="500"]'))

    def test_all_runtime_assets_exist(self):
        for path in (ROOT / '1080i').glob('*.xml'):
            for node in ET.parse(path).iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)


if __name__ == '__main__':
    unittest.main()
