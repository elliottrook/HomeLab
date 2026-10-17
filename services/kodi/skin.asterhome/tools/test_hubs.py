"""Synthetic hub contracts; no live feed, library or playback mutations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from hub_data import cached_digest_audio, digest_view, show_digest_story, story_at_elapsed, story_for_playback, WINDOWS
from digest_data import DigestCards, merge_chapters, public_image
from hub_feeds import books_view, home_view, read_feed
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

    def test_selected_story_survives_pre_seek_window_refresh(self):
        stories = [{'start': value} for value in (4, 62, 131)]
        self.assertEqual(story_for_playback(stories, None, 62), 1)
        self.assertEqual(story_for_playback(stories, 1, 62), 1)
        self.assertEqual(story_for_playback(stories, 63, 62), 1)
        self.assertEqual(story_for_playback(stories, 132, 62), 2)
        self.assertEqual(story_for_playback(stories, 1, None), 0)

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

    def test_all_runtime_assets_exist(self):
        for path in (ROOT / '1080i').glob('*.xml'):
            for node in ET.parse(path).iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)


if __name__ == '__main__':
    unittest.main()
