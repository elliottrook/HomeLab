import unittest
import io
import asyncio
import threading
import wave

from voice_candidate import VoiceScheduler
from voice_protocol import (
    FRAME_MAGIC,
    decode_frames,
    encode_frame,
    pcm_to_wav,
    stream_frames,
    validated_request_id,
)


class FrameTests(unittest.TestCase):
    def test_round_trip_multiple_frames(self):
        wire = encode_frame({"type": "audio", "index": 0}, b"pcm")
        wire += encode_frame({"type": "end"})
        self.assertEqual(
            decode_frames(wire),
            [({"index": 0, "type": "audio"}, b"pcm"), ({"type": "end"}, b"")],
        )

    def test_decoder_rejects_truncated_and_invalid_frames(self):
        with self.assertRaises(ValueError):
            decode_frames(FRAME_MAGIC)
        with self.assertRaises(ValueError):
            decode_frames(b"NOPE" + b"\0" * 8)
        with self.assertRaises(ValueError):
            decode_frames(encode_frame({"type": "end"})[:-1])

    def test_request_id_validation(self):
        self.assertEqual(validated_request_id("phone.request-7"), "phone.request-7")
        self.assertEqual(len(validated_request_id(None)), 32)
        for invalid in ("", "has space", "/path", "x" * 65, "é"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validated_request_id(invalid)

    def test_pcm_to_compatibility_wav(self):
        pcm = b"\x00\x00\xff\x7f"
        encoded = pcm_to_wav(pcm, 24000)
        with wave.open(io.BytesIO(encoded), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertEqual(wav.getframerate(), 24000)
            self.assertEqual(wav.readframes(2), pcm)
        with self.assertRaises(ValueError):
            pcm_to_wav(b"odd", 24000)


class StreamFrameTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.scheduler = VoiceScheduler(lambda text: (text.encode(), 24000))
        await self.scheduler.start()

    async def asyncTearDown(self):
        await self.scheduler.close()

    async def test_audio_units_are_followed_by_end_frame(self):
        wire = b"".join([
            frame async for frame in stream_frames(
                self.scheduler, "request-1", "First sentence. Second sentence.", "interactive"
            )
        ])
        frames = decode_frames(wire)
        self.assertEqual([frame[0]["type"] for frame in frames], ["audio", "audio", "end"])
        self.assertEqual([frame[0].get("index") for frame in frames], [0, 1, None])
        self.assertEqual([frame[1] for frame in frames[:2]], [b"First sentence.", b"Second sentence."])

    async def test_renderer_failure_returns_content_free_error(self):
        await self.scheduler.close()

        def broken_renderer(_text):
            raise RuntimeError("private submitted text must not escape")

        self.scheduler = VoiceScheduler(broken_renderer)
        await self.scheduler.start()
        wire = b"".join([
            frame async for frame in stream_frames(
                self.scheduler, "request-2", "Secret words.", "interactive"
            )
        ])
        metadata, payload = decode_frames(wire)[0]
        self.assertEqual(metadata["type"], "error")
        self.assertEqual(metadata["error"], "RuntimeError")
        self.assertNotIn(b"private", wire)
        self.assertNotIn(b"Secret", wire)
        self.assertEqual(payload, b"")

    async def test_explicit_cancel_finishes_with_cancelled_frame(self):
        await self.scheduler.close()
        entered = threading.Event()
        release = threading.Event()

        def slow_renderer(text):
            entered.set()
            release.wait(timeout=2)
            return text.encode(), 24000

        self.scheduler = VoiceScheduler(slow_renderer)
        await self.scheduler.start()

        async def collect():
            return b"".join([
                frame async for frame in stream_frames(
                    self.scheduler, "request-cancel", "A longer uncached response.", "interactive"
                )
            ])

        task = asyncio.create_task(collect())
        await asyncio.wait_for(asyncio.to_thread(entered.wait), timeout=1)
        self.scheduler.cancel("request-cancel")
        release.set()
        frames = decode_frames(await task)
        self.assertEqual(frames, [
            ({"request_id": "request-cancel", "type": "cancelled"}, b"")
        ])


if __name__ == "__main__":
    unittest.main()
