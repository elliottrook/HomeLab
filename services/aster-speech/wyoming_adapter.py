"""Source-restricted Wyoming TTS adapter for Home Assistant."""

from __future__ import annotations

import contextlib
import uuid
from typing import Any, Callable

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Attribution, Describe, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.tts import Synthesize, SynthesizeTextFormat

VOICE_NAME = "aster-bm-daniel"
VOICE_LANGUAGE = "en-gb"
PCM_CHUNK_BYTES = 4096


def service_info() -> Info:
    attribution = Attribution(name="Aster", url="https://git.elliottrook.com/jason/homelab")
    voice = TtsVoice(
        name=VOICE_NAME,
        attribution=attribution,
        installed=True,
        description="Aster approved household voice",
        version="1",
        languages=[VOICE_LANGUAGE],
    )
    return Info(tts=[TtsProgram(
        name="aster-voice",
        attribution=attribution,
        installed=True,
        description="Aster canonical text-to-speech",
        version="1",
        voices=[voice],
        supports_synthesize_streaming=False,
    )])


class WyomingTTSHandler(AsyncEventHandler):
    def __init__(self, reader, writer, scheduler: Any, allowed_peer: str):
        super().__init__(reader, writer)
        self.scheduler = scheduler
        peer = writer.get_extra_info("peername")
        self.authorized = bool(peer and peer[0] == allowed_peer)

    async def _error(self, text: str, code: str) -> None:
        with contextlib.suppress(Exception):
            await self.write_event(Error(text=text, code=code).event())

    async def handle_event(self, event: Event) -> bool:
        if not self.authorized:
            await self._error("Unauthorized", "unauthorized")
            return False
        if Describe.is_type(event.type):
            await self.write_event(service_info().event())
            return True
        if not Synthesize.is_type(event.type):
            await self._error("Unsupported request", "unsupported")
            return True

        try:
            request = Synthesize.from_event(event)
        except Exception:
            await self._error("Invalid synthesis request", "invalid_request")
            return True
        if request.text_format not in (None, SynthesizeTextFormat.TEXT, "text"):
            await self._error("SSML is not supported", "unsupported")
            return True
        if request.voice:
            if request.voice.name not in (None, VOICE_NAME):
                await self._error("Unknown voice", "unknown_voice")
                return True
            if request.voice.language not in (None, VOICE_LANGUAGE):
                await self._error("Unknown language", "unknown_language")
                return True

        request_id = f"ha-{uuid.uuid4().hex}"
        started = False
        try:
            async for unit in self.scheduler.stream(request_id, request.text, "interactive"):
                if not started:
                    await self.write_event(
                        AudioStart(rate=unit.sample_rate, width=2, channels=1).event()
                    )
                    started = True
                for offset in range(0, len(unit.pcm), PCM_CHUNK_BYTES):
                    await self.write_event(AudioChunk(
                        rate=unit.sample_rate,
                        width=2,
                        channels=1,
                        audio=unit.pcm[offset:offset + PCM_CHUNK_BYTES],
                    ).event())
            if not started:
                raise RuntimeError("renderer returned no audio")
            await self.write_event(AudioStop().event())
        except Exception as exc:
            self.scheduler.cancel(request_id)
            await self._error("Synthesis failed", type(exc).__name__)
        return True


async def start_wyoming_server(scheduler: Any, uri: str, allowed_peer: str) -> AsyncServer:
    server = AsyncServer.from_uri(uri)
    factory: Callable[..., WyomingTTSHandler] = lambda reader, writer: WyomingTTSHandler(
        reader, writer, scheduler, allowed_peer
    )
    await server.start(factory)
    return server
