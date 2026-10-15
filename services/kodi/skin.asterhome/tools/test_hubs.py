"""Synthetic hub contracts; no live feed, library or playback mutations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from hub_data import digest_view, WINDOWS
from hub_feeds import books_view, home_view, read_feed
import json
import tempfile

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

    def test_bounded_rows(self):
        rows, _ = digest_view(self.feed(chapters=[{'title': 'Synthetic', 'start': n} for n in range(100)]))
        self.assertEqual(len(rows), 40)

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
                                                  'unit': '°C'}]}}
        self.assertEqual(home_view(payload), [('laundry lights', 'Light · On', None),
                                              ('hall temperature', 'Temperature · 20.6°C', None)])
        payload['snapshot']['temperatures'][0]['value'] = float('nan')
        with self.assertRaises(ValueError):
            home_view(payload)
        payload['snapshot']['temperatures'] = []
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
            self.assertIsNotNone(window.find('.//control[@id="500"]'))
            self.assertIsNotNone(window.find('.//include[@content="AsterNavigationRail"]'))

    def test_all_runtime_assets_exist(self):
        for path in (ROOT / '1080i').glob('*.xml'):
            for node in ET.parse(path).iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)


if __name__ == '__main__':
    unittest.main()
