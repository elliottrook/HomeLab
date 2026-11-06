from __future__ import annotations

import io
import json
import unittest
import wave
from unittest import mock

from lxc import mac_whisper_client, qwen_renderer_client


def wav_bytes(rate: int = 24000) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * 240)
    return output.getvalue()


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json"):
        self.status = 200
        self.body = io.BytesIO(body)
        self.headers = mock.Mock()
        self.headers.get_content_type.return_value = content_type

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, size: int = -1) -> bytes:
        return self.body.read(size)


class ClientTests(unittest.TestCase):
    def test_qwen_requires_loopback(self):
        with self.assertRaisesRegex(RuntimeError, "loopback"):
            qwen_renderer_client.QwenRendererPool("http://192.168.1.206:18140/v1/audio/speech")

    @mock.patch("urllib.request.urlopen")
    def test_qwen_validates_and_returns_pcm(self, open_url):
        open_url.return_value = FakeResponse(wav_bytes(), "audio/wav")
        pcm, rate = qwen_renderer_client.QwenRendererPool()._render("hello")
        self.assertEqual(rate, 24000)
        self.assertEqual(len(pcm), 480)
        body = json.loads(open_url.call_args.args[0].data)
        self.assertEqual(body["voice"], "aster")
        self.assertEqual(body["seed"], 20261104)

    @mock.patch("urllib.request.urlopen")
    def test_whisper_builds_bounded_multipart(self, open_url):
        open_url.return_value = FakeResponse(b'{"text":" hello "}')
        self.assertEqual(mac_whisper_client.transcribe_wav(wav_bytes()), "hello")
        request = open_url.call_args.args[0]
        self.assertTrue(request.full_url.startswith("http://127.0.0.1:"))
        self.assertIn(b'name="file"', request.data)
        self.assertIn(b"RIFF", request.data)


if __name__ == "__main__":
    unittest.main()

