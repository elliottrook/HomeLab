"""Source-restricted Wyoming TTS/STT adapter for Home Assistant."""

from __future__ import annotations

import contextlib
import uuid
from typing import Any, Awaitable, Callable

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.asr import Transcript, Transcribe
from wyoming.info import AsrModel, AsrProgram, Attribution, Describe, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.tts import Synthesize, SynthesizeTextFormat

VOICE_NAME = "aster-bm-daniel"
VOICE_LANGUAGE = "en-gb"
PCM_CHUNK_BYTES = 4096
MAX_STT_AUDIO_BYTES = 15 * 1024 * 1024
ASR_NAME = "aster-base-en"
ASR_LANGUAGE = "en"


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
    return Info(asr=[AsrProgram(
        name="aster-stt",
        attribution=attribution,
        installed=True,
        description="Aster local household speech recognition",
        version="1",
        models=[AsrModel(
            name=ASR_NAME,
            attribution=attribution,
            installed=True,
            description="Aster tuned faster-whisper base English",
            version="1",
            languages=[ASR_LANGUAGE],
        )],
        supports_transcript_streaming=False,
        requires_external_vad=True,
    )], tts=[TtsProgram(
        name="aster-voice",
        attribution=attribution,
        installed=True,
        description="Aster canonical text-to-speech",
        version="1",
        voices=[voice],
        supports_synthesize_streaming=False,
    )])


class WyomingTTSHandler(AsyncEventHandler):
    def __init__(self, reader, writer, scheduler: Any, transcriber: Callable[..., Awaitable[str]], allowed_peer: str):
        super().__init__(reader, writer)
        self.scheduler = scheduler
        self.transcriber = transcriber
        self._stt_format: tuple[int, int, int] | None = None
        self._stt_audio = bytearray()
        self._awaiting_audio = False
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
        if Transcribe.is_type(event.type):
            request = Transcribe.from_event(event)
            if request.name not in (None, ASR_NAME) or request.language not in (None, ASR_LANGUAGE, "en-gb"):
                await self._error("Unknown STT model or language", "unsupported")
                return True
            self._stt_format = None
            self._stt_audio.clear()
            self._awaiting_audio = True
            return True
        if AudioStart.is_type(event.type):
            if not self._awaiting_audio:
                await self._error("Audio without transcription request", "invalid_sequence")
                return True
            audio = AudioStart.from_event(event)
            if audio.width != 2 or audio.channels != 1 or not 8000 <= audio.rate <= 48000:
                self._awaiting_audio = False
                await self._error("Unsupported audio format", "unsupported_audio")
                return True
            self._stt_format = (audio.rate, audio.width, audio.channels)
            return True
        if AudioChunk.is_type(event.type):
            if not self._awaiting_audio or self._stt_format is None:
                await self._error("Audio chunk out of sequence", "invalid_sequence")
                return True
            audio = AudioChunk.from_event(event)
            if (audio.rate, audio.width, audio.channels) != self._stt_format:
                self._awaiting_audio = False
                await self._error("Audio format changed", "unsupported_audio")
                return True
            if len(self._stt_audio) + len(audio.audio) > MAX_STT_AUDIO_BYTES:
                self._awaiting_audio = False
                self._stt_audio.clear()
                await self._error("Audio exceeds maximum size", "audio_too_large")
                return True
            self._stt_audio.extend(audio.audio)
            return True
        if AudioStop.is_type(event.type):
            if not self._awaiting_audio or self._stt_format is None or not self._stt_audio:
                await self._error("Incomplete audio stream", "invalid_sequence")
                return True
            rate, width, channels = self._stt_format
            audio = bytes(self._stt_audio)
            self._awaiting_audio = False
            self._stt_format = None
            self._stt_audio.clear()
            try:
                text = await self.transcriber(audio, rate, width, channels)
                await self.write_event(Transcript(text=text, language=ASR_LANGUAGE).event())
            except Exception as exc:
                await self._error("Transcription failed", type(exc).__name__)
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


async def start_wyoming_server(scheduler: Any, transcriber: Callable[..., Awaitable[str]], uri: str, allowed_peer: str) -> AsyncServer:
    server = AsyncServer.from_uri(uri)
    factory: Callable[..., WyomingTTSHandler] = lambda reader, writer: WyomingTTSHandler(
        reader, writer, scheduler, transcriber, allowed_peer
    )
    await server.start(factory)
    return server
