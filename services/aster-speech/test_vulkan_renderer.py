from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
import wave
from email.message import Message
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

import vulkan_renderer_bridge
import vulkan_renderer_client


def wav_bytes(pcm: bytes = b"\x01\x00\x02\x00") -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(24000)
        target.writeframes(pcm)
    return output.getvalue()


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "audio/wav", status: int = 200):
        self.body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, maximum: int = -1) -> bytes:
        return self.body if maximum < 0 else self.body[:maximum]


class VulkanRendererClientTests(unittest.TestCase):
    def test_pool_authenticates_pins_request_and_caches_acknowledgement(self):
        calls = []

        def fake_open(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(wav_bytes())

        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "key"
            key_file.write_text("k" * 32, encoding="utf-8")
            with patch.object(vulkan_renderer_client.urllib.request, "urlopen", fake_open):
                pool = vulkan_renderer_client.VulkanRendererPool(
                    "http://192.168.70.12:9132/render", key_file, 3.0
                )
                before = len(calls)
                self.assertEqual(pool.renderers[1](vulkan_renderer_client.ACKNOWLEDGEMENT), (b"\x01\x00\x02\x00", 24000))
                self.assertEqual(pool.renderers[0]("Hello"), (b"\x01\x00\x02\x00", 24000))
                self.assertTrue(pool.healthy())
        self.assertEqual(before, 1)
        self.assertEqual(len(calls), 3)
        request, timeout = calls[-2]
        self.assertEqual(request.full_url, "http://192.168.70.12:9132/render")
        self.assertEqual(request.data, b"Hello")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {'k' * 32}")
        self.assertEqual(timeout, 3.0)

    def test_invalid_key_and_audio_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "key"
            key_file.write_text("short", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                vulkan_renderer_client.VulkanRendererPool(key_file=key_file)
        with self.assertRaises(RuntimeError):
            vulkan_renderer_client._wav_to_pcm(b"not a wav")


class VulkanRendererBridgeTests(unittest.TestCase):
    def setUp(self):
        self.requests = []

        def fake_open(request, timeout):
            self.requests.append((request, timeout))
            return FakeResponse(wav_bytes(b"\x03\x00"))

        self.urlopen_patch = patch.object(
            vulkan_renderer_bridge.urllib.request, "urlopen", fake_open
        )
        self.urlopen_patch.start()
        self.server = vulkan_renderer_bridge.RendererServer(
            ("127.0.0.1", 0), vulkan_renderer_bridge.Handler, "b" * 32
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.urlopen_patch.stop()

    def request(self, text: str, key: str | None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        headers = {"Content-Type": "text/plain"}
        if key is not None:
            headers["Authorization"] = f"Bearer {key}"
        connection.request("POST", "/render", body=text.encode(), headers=headers)
        response = connection.getresponse()
        result = response.status, response.getheader("Content-Type"), response.read()
        connection.close()
        return result

    def test_refuses_unauthenticated_request_without_forwarding(self):
        status, content_type, _body = self.request("Hello", None)
        self.assertEqual((status, content_type), (401, "application/json"))
        self.assertEqual(self.requests, [])

    def test_forwards_only_fixed_voice_speed_and_wav(self):
        status, content_type, body = self.request("Hello", "b" * 32)
        self.assertEqual((status, content_type, body), (200, "audio/wav", wav_bytes(b"\x03\x00")))
        self.assertEqual(len(self.requests), 1)
        request, timeout = self.requests[0]
        submitted = json.loads(request.data)
        self.assertEqual(submitted, {
            "text": "Hello", "voice": "bm_daniel", "speed": 0.95, "format": "wav"
        })
        self.assertEqual(timeout, vulkan_renderer_bridge.UPSTREAM_TIMEOUT)

    def test_rejects_oversized_text_without_forwarding(self):
        status, _content_type, _body = self.request("x" * 241, "b" * 32)
        self.assertEqual(status, 400)
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
