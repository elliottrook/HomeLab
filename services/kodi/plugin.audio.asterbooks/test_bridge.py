"""Synthetic, credential-free tests for the Aster audio bridge."""

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resources.lib.bridge import Bridge, BridgeError, control_request, load_config, secure_kodi_log


class Reply(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}


class FakeOpener:
    def __init__(self):
        self.calls = []
        self.metadata_reply = None

    def open(self, request, timeout):
        self.calls.append((request.full_url, request.get_header('Authorization'),
                           request.get_header('Range'), request.get_method()))
        if request.full_url.endswith('?expanded=1'):
            if self.metadata_reply is not None:
                return Reply(json.dumps(self.metadata_reply).encode())
            kind = 'podcast' if '/li_pod?' in request.full_url else 'book'
            media = ({'episodes': [{'title': 'Episode One', 'audioFile': {'ino': 52}}]}
                     if kind == 'podcast' else
                     {'audioFiles': [{'ino': 31, 'metadata': {'filename': 'Part One.m4b'}}]})
            return Reply(json.dumps({'id': 'li_pod' if kind == 'podcast' else 'li_book',
                                     'mediaType': kind, 'media': media}).encode())
        if request.get_header('Range') == 'bytes=2-4':
            return Reply(b'cde', 206, {'Content-Type': 'audio/mp4',
                                       'Content-Range': 'bytes 2-4/6', 'Content-Length': '3',
                                       'Accept-Ranges': 'bytes'})
        return Reply(b'abcdef', 200, {'Content-Type': 'audio/mp4', 'Content-Length': '6',
                                      'Accept-Ranges': 'bytes'})


class BridgeTests(unittest.TestCase):
    def test_kodi_log_is_private_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'kodi.log'
            path.write_text('test')
            os.chmod(path, 0o644)
            secure_kodi_log(path)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            link = Path(temp) / 'link.log'
            link.symlink_to(path)
            with self.assertRaises(OSError):
                secure_kodi_log(link)

    def test_private_https_config(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'client.json'
            path.write_text(json.dumps({'server_url': 'https://audio.example.test',
                                        'api_key': 'a' * 32}))
            os.chmod(path, 0o600)
            self.assertEqual(load_config(path), ('https://audio.example.test', 'a' * 32))
            os.chmod(path, 0o644)
            with self.assertRaises(BridgeError):
                load_config(path)
            os.chmod(path, 0o600)
            path.write_text(json.dumps({'server_url': 'http://audio.example.test',
                                        'api_key': 'a' * 32}))
            with self.assertRaises(BridgeError):
                load_config(path)

    def test_failed_socket_bind_does_not_hang_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            bridge = Bridge('https://audio.example.test', 's' * 32)
            with self.assertRaises(OSError):
                bridge.start(Path(temp) / ('a' * 240))
            bridge.stop()

    def test_book_and_podcast_use_private_header_and_local_capabilities(self):
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as temp:
            bridge = Bridge('https://audio.example.test', 's' * 32, opener=opener)
            bridge.start(Path(temp) / 'bridge.sock')
            try:
                book = control_request(Path(temp) / 'bridge.sock', 'audiobook', 'li_book')
                podcast = control_request(Path(temp) / 'bridge.sock', 'podcast', 'li_pod')
                self.assertEqual(book[0]['title'], 'Part One.m4b')
                self.assertEqual(podcast[0]['title'], 'Episode One')
                self.assertTrue(book[0]['url'].startswith('http://127.0.0.1:'))
                self.assertNotIn('s' * 32, book[0]['url'])
                self.assertNotIn('li_book', book[0]['url'])
                request = urllib.request.Request(book[0]['url'], headers={'Range': 'bytes=2-4'})
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b'cde')
                    self.assertEqual(response.headers['Content-Range'], 'bytes 2-4/6')
                with urllib.request.urlopen(urllib.request.Request(book[0]['url'], method='HEAD')) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers['Content-Length'], '6')
                self.assertTrue(all(call[1] == 'Bearer ' + 's' * 32 for call in opener.calls))
                self.assertTrue(all('s' * 32 not in call[0] for call in opener.calls))
                self.assertEqual(opener.calls[-2][2], 'bytes=2-4')
            finally:
                bridge.stop()

    def test_invalid_and_expired_capabilities_fail_closed(self):
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as temp:
            bridge = Bridge('https://audio.example.test', 's' * 32, opener=opener,
                            clock=lambda: 100)
            bridge.start(Path(temp) / 'bridge.sock')
            try:
                with self.assertRaises(BridgeError):
                    control_request(Path(temp) / 'bridge.sock', 'podcast', '../bad')
                url = control_request(Path(temp) / 'bridge.sock', 'audiobook', 'li_book')[0]['url']
                with self.assertRaises(urllib.error.HTTPError) as context:
                    urllib.request.urlopen(url + '/other')
                self.assertEqual(context.exception.code, 404)
                bridge.clock = lambda: 100 + 12 * 3600 + 1
                with self.assertRaises(urllib.error.HTTPError) as context:
                    urllib.request.urlopen(url)
                self.assertEqual(context.exception.code, 404)
            finally:
                bridge.stop()

    def test_malformed_metadata_fails_closed_without_killing_control_socket(self):
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as temp:
            bridge = Bridge('https://audio.example.test', 's' * 32, opener=opener)
            bridge.start(Path(temp) / 'bridge.sock')
            try:
                opener.metadata_reply = {'id': 'li_book', 'mediaType': 'book',
                                         'media': {'audioFiles': 'not-a-list'}}
                with self.assertRaises(BridgeError):
                    control_request(Path(temp) / 'bridge.sock', 'audiobook', 'li_book')
                opener.metadata_reply = {'id': 'li_book', 'mediaType': 'book',
                                         'media': {'audioFiles': [{'metadata': 'bad', 'ino': 31}]}}
                self.assertEqual(control_request(Path(temp) / 'bridge.sock', 'audiobook', 'li_book'), [])
                opener.metadata_reply = None
                self.assertEqual(len(control_request(Path(temp) / 'bridge.sock', 'audiobook', 'li_book')), 1)
            finally:
                bridge.stop()


if __name__ == '__main__':
    unittest.main()
