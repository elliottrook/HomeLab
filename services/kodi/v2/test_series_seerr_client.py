import io
import json
from pathlib import Path
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:
    Image = None

from series_catalogue import parse_catalogue, season_proposal
from series_seerr_client import (CatalogueClient, CatalogueUnavailable,
                                 GrayscaleCache, SeasonRequestWriter)


CATALOGUE = {'schema': 1, 'candidate_id': 'seerr:tv:456', 'title': 'Series',
             'seasons': [{'number': 2, 'name': 'Season 2', 'episode_count': 1,
                          'state': 'unknown', 'request_id': None,
                          'request_state': 'none', 'requestable': True}]}


class Response:
    def __init__(self, value, url='http://192.168.20.40:8788/value'):
        self.raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.status = 200; self.url = url
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self, amount): return self.raw[:amount]
    def geturl(self): return self.url


class SeriesSeerrClientTests(unittest.TestCase):
    def token(self, root):
        path = Path(root) / 'token'; path.write_text('a' * 48); return path

    def test_resolve_and_season_use_only_restricted_routes(self):
        calls = []
        def open_request(request, timeout):
            calls.append((request.full_url, request.method))
            if '/resolve?' in request.full_url: return Response(CATALOGUE)
            return Response({'schema': 1, 'candidate_id': 'seerr:tv:456',
                'title': 'Series', 'season': CATALOGUE['seasons'][0],
                'episodes': [{'number': 1, 'title': 'Episode', 'overview': '',
                              'air_date': '2026-01-01', 'still': ''}]})
        with tempfile.TemporaryDirectory() as root:
            client = CatalogueClient('http://192.168.20.40:8788', self.token(root), open_request)
            catalogue = client.resolve(250487, 'Series title')
            detail = client.season(catalogue, 2)
        self.assertEqual(detail.episodes[0].number, 1)
        self.assertIn('tvdb=250487&title=Series%20title', calls[0][0])
        self.assertTrue(calls[1][0].endswith('/v1/tv/456/season/2'))

    def test_request_writer_commits_once_and_replays_only_result(self):
        catalogue = parse_catalogue(CATALOGUE)
        payload = season_proposal(catalogue, 2, True); calls = []
        def send(value):
            calls.append(value)
            return {'schema': 1, 'candidate_id': 'seerr:tv:456', 'season': 2,
                    'request_id': 7, 'state': 'pending', 'duplicate': False}
        with tempfile.TemporaryDirectory() as root:
            writer = SeasonRequestWriter(root, send)
            self.assertEqual(writer.submit(payload, catalogue)['request_id'], 7)
            self.assertEqual(writer.submit(payload, catalogue)['request_id'], 7)
            self.assertEqual(len(calls), 1)

    def test_uncertain_write_is_never_retried(self):
        catalogue = parse_catalogue(CATALOGUE)
        payload = season_proposal(catalogue, 2, True)
        with tempfile.TemporaryDirectory() as root:
            writer = SeasonRequestWriter(root, lambda value: (_ for _ in ()).throw(OSError()))
            with self.assertRaisesRegex(CatalogueUnavailable, 'outcome-uncertain'):
                writer.submit(payload, catalogue)
            with self.assertRaisesRegex(CatalogueUnavailable, 'recovery-required'):
                writer.submit(payload, catalogue)

    @unittest.skipUnless(Image is not None, 'Pillow is supplied by the Kodi appliance')
    def test_cache_outputs_real_grayscale_and_refuses_redirect(self):
        image = Image.new('RGB', (8, 8), (200, 30, 10)); raw = io.BytesIO()
        image.save(raw, format='PNG')
        url = 'https://image.tmdb.org/t/p/w500/still.png'
        with tempfile.TemporaryDirectory() as root:
            cache = GrayscaleCache(root, lambda request, timeout: Response(raw.getvalue(), url))
            path = cache.fetch(url)
            with Image.open(path) as rendered:
                self.assertEqual(rendered.getpixel((0, 0))[0], rendered.getpixel((0, 0))[1])
            bad = GrayscaleCache(root + '/bad', lambda request, timeout: Response(raw.getvalue(), 'https://evil.invalid/x'))
            with self.assertRaisesRegex(CatalogueUnavailable, 'response-invalid'):
                bad.fetch(url)


if __name__ == '__main__':
    unittest.main()
