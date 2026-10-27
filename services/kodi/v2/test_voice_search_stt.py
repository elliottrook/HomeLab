import json
import unittest
import wave
from io import BytesIO

from voice_search_stt import STTUnavailable, request, response, wav


PCM = b'\x00\x00' * 8000
TOKEN = 'a' * 48


class VoiceSearchSTTTests(unittest.TestCase):
    def test_pcm_becomes_bounded_mono_wav(self):
        raw = wav(PCM)
        with wave.open(BytesIO(raw), 'rb') as stream:
            self.assertEqual((stream.getnchannels(), stream.getsampwidth(),
                              stream.getframerate(), stream.getnframes()),
                             (1, 2, 16000, 8000))

    def test_request_is_exact_multipart_and_contains_no_url(self):
        first = request(PCM, TOKEN)
        second = request(PCM, TOKEN)
        self.assertEqual(first, second)
        self.assertEqual(first.path, '/v1/stt')
        self.assertEqual(first.timeout, 20)
        self.assertEqual(first.headers['Authorization'], 'Bearer '+TOKEN)
        self.assertEqual(int(first.headers['Content-Length']), len(first.body))
        self.assertIn(b'name="audio"; filename="voice.wav"', first.body)
        self.assertNotIn(b'http://', first.body)
        self.assertNotIn(b'https://', first.body)

    def test_response_is_strict_and_normalized_for_grouped_search(self):
        raw = json.dumps({'text': '  the   morning show '}).encode()
        self.assertEqual(response(200, 'application/json; charset=utf-8', raw),
                         'the morning show')
        self.assertEqual(response(200, 'application/json',
                                  json.dumps({'text': ' Search for Dune '}).encode()),
                         'Dune')
        self.assertEqual(response(200, 'application/json',
                                  json.dumps({'text': 'Search Party'}).encode()),
                         'Search Party')
        for status, kind, body in ((401, 'application/json', raw),
                                   (200, 'text/plain', raw),
                                   (200, 'application/json', b'{}'),
                                   (200, 'application/json', b'{"text":""}'),
                                   (200, 'application/json', b'{"text":"ok","extra":1}')):
            with self.assertRaises(STTUnavailable):
                response(status, kind, body)

    def test_audio_and_credentials_fail_closed(self):
        for pcm in (b'', b'\x00', b'\x00\x00' * 100,
                    b'\x00\x00' * 200000):
            with self.assertRaises(STTUnavailable):
                wav(pcm)
        for token in ('', 'short', 'contains space', 'a' * 513):
            with self.assertRaises(STTUnavailable):
                request(PCM, token)


if __name__ == '__main__':
    unittest.main()
