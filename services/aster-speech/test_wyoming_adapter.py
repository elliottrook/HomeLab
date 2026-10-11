import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from wyoming.audio import AudioChunk, AudioStart, AudioStop
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


def make_handler(scheduler=None, peer="192.168.20.11"):
    handler = WyomingTTSHandler(None, FakeWriter(peer), scheduler or FakeScheduler(), "192.168.20.11")
    handler.write_event = AsyncMock()
    return handler


class WyomingAdapterTests(unittest.IsolatedAsyncioTestCase):
    def test_advertises_only_approved_tts_voice(self):
        info = Info.from_event(service_info().event())
        self.assertEqual(len(info.tts), 1)
        self.assertEqual(info.asr, [])
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


if __name__ == "__main__":
    unittest.main()
