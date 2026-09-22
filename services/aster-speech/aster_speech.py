"""Aster's speech service: STT (faster-whisper) and TTS (Piper), M6.

Deliberately bounded blast radius (docs/projects/Aster-Companion-App.md,
M1 decision): this service knows nothing about ARR, Home Assistant,
personas, or the knowledge corpus. It takes audio in and gives text out,
or takes text in and gives audio out - nothing else. It is authenticated
with its own dedicated bearer key, separate from aster-agent's, so a leak
of one key does not expose the other surface.
"""

from __future__ import annotations

import hmac
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request

ASTER_SPEECH_API_KEY = os.environ.get("ASTER_SPEECH_API_KEY", "")
WHISPER_MODEL_SIZE = os.environ.get("ASTER_SPEECH_STT_MODEL", "base.en")
PIPER_BINARY = Path(os.environ.get("ASTER_SPEECH_PIPER_BIN", "/opt/piper/piper/piper"))
PIPER_VOICE = Path(
    os.environ.get("ASTER_SPEECH_PIPER_VOICE", "/opt/piper/voices/en_US-lessac-medium.onnx")
)
# Matches the pacing Jason asked for in the audio-digest project
# (docs/projects/completed projects/News-Aggregator-Audio-Digest.md) -
# same voice, same preference, applied consistently rather than
# re-deciding it here.
PIPER_LENGTH_SCALE = os.environ.get("ASTER_SPEECH_PIPER_LENGTH_SCALE", "1.15")
MAX_AUDIO_BYTES = 15 * 1024 * 1024
MAX_TEXT_CHARS = 2000

app = FastAPI(title="Aster Speech", version="1.0.0")

_whisper_model: Any = None
_transcribe_lock: Any = None


def _load_whisper_model() -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


@app.on_event("startup")
async def _startup() -> None:
    import asyncio

    global _whisper_model, _transcribe_lock
    _whisper_model = _load_whisper_model()
    _transcribe_lock = asyncio.Lock()


def require_api_key(request: Request) -> None:
    if not ASTER_SPEECH_API_KEY:
        raise HTTPException(status_code=503, detail="Speech service is not configured")
    authorization = request.headers.get("authorization", "")
    if not hmac.compare_digest(authorization, f"Bearer {ASTER_SPEECH_API_KEY}"):
        raise HTTPException(status_code=401, detail="Invalid or missing credentials")


class TTSRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "aster-speech"}


@app.post("/v1/stt", dependencies=[Depends(require_api_key)])
async def speech_to_text(audio: UploadFile) -> dict[str, str]:
    data = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio exceeds the maximum permitted size")
    if not data:
        raise HTTPException(status_code=400, detail="No audio data received")

    with tempfile.NamedTemporaryFile(suffix=".audio", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        async with _transcribe_lock:
            segments, _info = _whisper_model.transcribe(tmp.name, beam_size=5)
            text = "".join(segment.text for segment in segments).strip()

    return {"text": text}


@app.post("/v1/tts", dependencies=[Depends(require_api_key)])
async def text_to_speech(request: TTSRequest) -> Response:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text supplied")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail="Text exceeds the maximum permitted length")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        try:
            result = subprocess.run(
                [
                    str(PIPER_BINARY),
                    "--model", str(PIPER_VOICE),
                    "--length_scale", PIPER_LENGTH_SCALE,
                    "--output_file", tmp.name,
                ],
                input=text,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            raise HTTPException(status_code=502, detail="Speech synthesis failed") from exc
        del result
        audio_bytes = Path(tmp.name).read_bytes()

    return Response(content=audio_bytes, media_type="audio/wav")
