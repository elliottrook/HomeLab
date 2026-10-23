from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from refresh_books import collect_audio, encode_feed, refresh

BOOK = 'ada9a4a3-ce8e-46ad-85f5-b45dd3286eb3'
LIBRARY = 'd314ea90-ce9a-4a50-8186-9159bbf4a755'


class RefreshTests(unittest.TestCase):
    def test_retains_ebook_provenance_and_replaces_audio(self):
        previous = {'generated_at': '2026-10-01T00:00:00+00:00', 'items': [
            {'authority': 'calibre', 'media_type': 'ebook', 'authority_id': '1', 'title': 'Book'},
            {'authority': 'audiobookshelf', 'media_type': 'audiobook',
             'authority_id': BOOK, 'title': 'Old title'}]}
        audio = [dict(previous['items'][1], title='Updated title')]
        result, raw = encode_feed(previous, audio, datetime.now(timezone.utc).isoformat())
        self.assertEqual(result['ebook_snapshot_at'], previous['generated_at'])
        self.assertEqual(result['items'][0], previous['items'][0])
        self.assertEqual(json.loads(raw)['items'][1]['title'], 'Updated title')
        with self.assertRaises(ValueError):
            encode_feed(previous, [], datetime.now(timezone.utc).isoformat())

    def test_projects_only_sanitized_fields(self):
        def api(path):
            if path == '/api/libraries':
                return {'libraries': [{'id': LIBRARY, 'mediaType': 'book'}]}
            return {'total': 1, 'results': [{'id': BOOK, 'path': '/private/source',
                    'media': {'metadata': {'title': 'Title', 'description': '<p>Synopsis</p>'}}}]}
        rows = collect_audio(api)
        self.assertEqual(rows[0]['description'], 'Synopsis')
        self.assertNotIn('path', rows[0])

    def test_incomplete_page_is_rejected(self):
        def api(path):
            if path == '/api/libraries':
                return {'libraries': [{'id': LIBRARY, 'mediaType': 'podcast'}]}
            return {'total': 2, 'results': []}
        with self.assertRaises(ValueError):
            collect_audio(api)

    def test_network_failure_does_not_replace_feed(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder)
            root = profile/'addon_data/skin.asterhome/feeds'
            root.mkdir(parents=True)
            original = b'{"items":[],"generated_at":"2026-10-01T00:00:00+00:00"}'
            (root/'books.json').write_bytes(original)
            config = profile/'addon_data/plugin.audio.asterbooks'
            config.mkdir()
            key = config/'client.json'
            key.write_text(json.dumps({'server_url': 'https://example.invalid',
                                       'api_key': 'test-credential-000000'}))
            key.chmod(0o600)
            with patch('refresh_books.urllib.request.build_opener') as opener:
                opener.return_value.open.side_effect = OSError('outage')
                with self.assertRaises(OSError):
                    refresh(profile)
            self.assertEqual((root/'books.json').read_bytes(), original)
