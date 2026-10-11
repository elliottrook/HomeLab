import json
import struct
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import aster_batch_tts


def frame(metadata, payload=b""):
    header = json.dumps(metadata).encode()
    return b"AVS1" + struct.pack(">II", len(header), len(payload)) + header + payload


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = aster_batch_tts.FRAME_MEDIA_TYPE

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, maximum=-1):
        return self.body if maximum < 0 else self.body[:maximum]


class AsterBatchTTSTests(unittest.TestCase):
    def test_decodes_ordered_audio_and_end(self):
        body = frame({"type": "audio", "index": 0, "channels": 1,
                      "sample_format": "pcm_s16le", "sample_rate": 24000}, b"\x01\x00")
        body += frame({"type": "audio", "index": 1, "channels": 1,
                       "sample_format": "pcm_s16le", "sample_rate": 24000}, b"\x02\x00")
        body += frame({"type": "end"})
        self.assertEqual(aster_batch_tts.decode_audio_frames(body), (b"\x01\x00\x02\x00", 24000))

    def test_rejects_error_truncated_and_out_of_order_responses(self):
        with self.assertRaises(RuntimeError):
            aster_batch_tts.decode_audio_frames(frame({"type": "error"}))
        with self.assertRaises(RuntimeError):
            aster_batch_tts.decode_audio_frames(b"AVS1")
        bad = frame({"type": "audio", "index": 1, "channels": 1,
                     "sample_format": "pcm_s16le", "sample_rate": 24000}, b"\x00\x00")
        with self.assertRaises(RuntimeError):
            aster_batch_tts.decode_audio_frames(bad + frame({"type": "end"}))

    def test_client_uses_file_credential_and_fixed_request(self):
        body = frame({"type": "audio", "index": 0, "channels": 1,
                      "sample_format": "pcm_s16le", "sample_rate": 24000}, b"\x01\x00")
        body += frame({"type": "end"})
        calls = []

        def fake_open(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(body)

        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "key"
            key_file.write_text("k" * 32, encoding="utf-8")
            with patch.object(aster_batch_tts.urllib.request, "urlopen", fake_open):
                client = aster_batch_tts.AsterBatchTTS(
                    "http://192.168.70.14:9131/v2/batch/tts/stream", key_file, 90
                )
                self.assertEqual(client.synthesize("Home Assistant."), (b"\x01\x00", 24000))
        request, timeout = calls[0]
        self.assertEqual(json.loads(request.data), {"text": "Home Assistant."})
        self.assertEqual(request.get_header("Authorization"), f"Bearer {'k' * 32}")
        self.assertEqual(timeout, 90)


if __name__ == "__main__":
    unittest.main()
