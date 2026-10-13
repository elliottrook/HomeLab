import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.asr import Transcript, Transcribe
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.tts import Synthesize, SynthesizeVoice

from wyoming_adapter import PCM_CHUNK_BYTES, VOICE_LANGUAGE, VOICE_NAME, WyomingTTSHandler, service_info


class FakeWriter:
    def __init__(self, peer="192.168.20.11"):
        self.peer = peer

    def get_extra_info(self, name):
        return (self.peer, 12345) if name == "peername" else None


class FakeScheduler:
    def __init__(self, units=None):
        self.units = units or []
        self.calls = []
        self.cancelled = []

    async def stream(self, request_id, text, caller):
        self.calls.append((request_id, text, caller))
        for unit in self.units:
            yield unit

    def cancel(self, request_id):
        self.cancelled.append(request_id)


def make_handler(scheduler=None, peer="192.168.20.11", transcriber=None):
    handler = WyomingTTSHandler(None, FakeWriter(peer), scheduler or FakeScheduler(), transcriber or AsyncMock(return_value="hello"), "192.168.20.11")
    handler.write_event = AsyncMock()
    return handler


class WyomingAdapterTests(unittest.IsolatedAsyncioTestCase):
    def test_advertises_only_approved_tts_voice(self):
        info = Info.from_event(service_info().event())
        self.assertEqual(len(info.tts), 1)
        self.assertEqual(len(info.asr), 1)
        self.assertEqual(info.asr[0].models[0].name, "aster-base-en")
        self.assertTrue(info.asr[0].requires_external_vad)
        self.assertEqual(len(info.tts[0].voices), 1)
        self.assertEqual(info.tts[0].voices[0].name, VOICE_NAME)
        self.assertEqual(info.tts[0].voices[0].languages, [VOICE_LANGUAGE])
        self.assertFalse(info.tts[0].supports_synthesize_streaming)

    async def test_denies_non_home_assistant_source(self):
        handler = make_handler(peer="192.168.20.99")
        self.assertFalse(await handler.handle_event(Describe().event()))
        sent = handler.write_event.await_args.args[0]
        self.assertTrue(Error.is_type(sent.type))
        self.assertEqual(Error.from_event(sent).code, "unauthorized")

    async def test_describe_returns_single_voice(self):
        handler = make_handler()
        self.assertTrue(await handler.handle_event(Describe().event()))
        sent = handler.write_event.await_args.args[0]
        self.assertTrue(Info.is_type(sent.type))

    async def test_rejects_wrong_voice_and_language(self):
        for voice in (
            SynthesizeVoice(name="someone-else"),
            SynthesizeVoice(name=VOICE_NAME, language="en-us"),
        ):
            handler = make_handler()
            await handler.handle_event(Synthesize(text="Hello", voice=voice).event())
            sent = handler.write_event.await_args.args[0]
            self.assertTrue(Error.is_type(sent.type))

    async def test_streams_interactive_pcm_in_bounded_chunks(self):
        pcm = b"x" * (PCM_CHUNK_BYTES + 17)
        scheduler = FakeScheduler([SimpleNamespace(sample_rate=24000, pcm=pcm)])
        handler = make_handler(scheduler)
        await handler.handle_event(Synthesize(text="Hello Aster").event())
        events = [call.args[0] for call in handler.write_event.await_args_list]
        self.assertTrue(AudioStart.is_type(events[0].type))
        self.assertTrue(AudioChunk.is_type(events[1].type))
        self.assertTrue(AudioChunk.is_type(events[2].type))
        self.assertTrue(AudioStop.is_type(events[3].type))
        self.assertLessEqual(len(AudioChunk.from_event(events[1]).audio), PCM_CHUNK_BYTES)
        self.assertEqual(scheduler.calls[0][1:], ("Hello Aster", "interactive"))

    async def test_rejects_unknown_event(self):
        handler = make_handler()
        await handler.handle_event(Event(type="not-supported"))
        sent = handler.write_event.await_args.args[0]
        self.assertEqual(Error.from_event(sent).code, "unsupported")

    async def test_transcribes_bounded_pcm_stream(self):
        transcriber = AsyncMock(return_value="Ask Home Assistant")
        handler = make_handler(transcriber=transcriber)
        await handler.handle_event(Transcribe(name="aster-base-en", language="en").event())
        await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
        await handler.handle_event(AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x01" * 32).event())
        await handler.handle_event(AudioStop().event())
        transcriber.assert_awaited_once()
        sent = handler.write_event.await_args.args[0]
        self.assertEqual(Transcript.from_event(sent).text, "Ask Home Assistant")

    async def test_rejects_audio_without_transcribe(self):
        handler = make_handler()
        await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
        self.assertEqual(Error.from_event(handler.write_event.await_args.args[0]).code, "invalid_sequence")

    async def test_rejects_format_change(self):
        handler = make_handler()
        await handler.handle_event(Transcribe().event())
        await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
        await handler.handle_event(AudioChunk(rate=24000, width=2, channels=1, audio=b"xx").event())
        self.assertEqual(Error.from_event(handler.write_event.await_args.args[0]).code, "unsupported_audio")

    async def test_rejects_oversized_audio_before_transcription(self):
        transcriber = AsyncMock()
        handler = make_handler(transcriber=transcriber)
        await handler.handle_event(Transcribe().event())
        await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
        with patch("wyoming_adapter.MAX_STT_AUDIO_BYTES", 2):
            await handler.handle_event(AudioChunk(rate=16000, width=2, channels=1, audio=b"xxxx").event())
        self.assertEqual(Error.from_event(handler.write_event.await_args.args[0]).code, "audio_too_large")
        transcriber.assert_not_awaited()

    async def test_transcription_failure_returns_content_free_error(self):
        handler = make_handler(transcriber=AsyncMock(side_effect=RuntimeError("private detail")))
        await handler.handle_event(Transcribe().event())
        await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
        await handler.handle_event(AudioChunk(rate=16000, width=2, channels=1, audio=b"xx").event())
        await handler.handle_event(AudioStop().event())
        error = Error.from_event(handler.write_event.await_args.args[0])
        self.assertEqual(error.text, "Transcription failed")
        self.assertEqual(error.code, "RuntimeError")


if __name__ == "__main__":
    unittest.main()
