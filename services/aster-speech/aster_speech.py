"""Aster's speech service: STT (faster-whisper) and TTS (Piper), M6.

Deliberately bounded blast radius (docs/projects/Aster-Companion-App.md,
M1 decision): this service knows nothing about ARR, Home Assistant,
personas, or the knowledge corpus. It takes audio in and gives text out,
or takes text in and gives audio out - nothing else. It accepts either its
own dedicated bearer key or an Authentik-issued token for the same
"aster-companion" application aster-agent already uses - the Companion
apps' existing login session works here too, with no separate voice-only
login flow, matching aster_agent.py's own dual-credential-type pattern
(services/aster-agent/aster_agent.py's require_api_key/_authentik_claims).
"""

from __future__ import annotations

import asyncio
import hmac
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict

ASTER_SPEECH_API_KEY = os.environ.get("ASTER_SPEECH_API_KEY", "")
WHISPER_MODEL_SIZE = os.environ.get("ASTER_SPEECH_STT_MODEL", "base.en")
PIPER_BINARY = Path(os.environ.get("ASTER_SPEECH_PIPER_BIN", "/opt/piper/piper/piper"))
PIPER_VOICE = Path(
    os.environ.get("ASTER_SPEECH_PIPER_VOICE", "/opt/piper/voices/en_US-lessac-medium.onnx")
)
AUTHENTIK_ISSUER = os.environ.get(
    "ASTER_AUTHENTIK_ISSUER", "https://auth.elliottrook.com/application/o/aster-companion/"
)
AUTHENTIK_JWKS_URL = os.environ.get(
    "ASTER_AUTHENTIK_JWKS_URL", "https://auth.elliottrook.com/application/o/aster-companion/jwks/"
)
AUTHENTIK_AUDIENCE = os.environ.get("ASTER_AUTHENTIK_AUDIENCE", "aster-companion")
_authentik_jwks_client = jwt.PyJWKClient(AUTHENTIK_JWKS_URL, cache_keys=True, lifespan=3600, timeout=5)
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
    global _whisper_model, _transcribe_lock
    _whisper_model = _load_whisper_model()
    _transcribe_lock = asyncio.Lock()


def _authentik_claims(authorization: str | None) -> dict[str, Any] | None:
    """Validate an Authentik-issued bearer token; return its claims, or None.

    Never raises: any JWKS/network/decode/validation failure is treated as
    "not a valid Authentik token" so a JWKS hiccup fails closed to 401
    rather than surfacing as a server error, and so this can be tried
    unconditionally without disturbing the existing bearer-key path.
    Identical in shape to aster_agent.py's own helper - kept as a separate
    copy rather than a shared import, since these are independent services
    with their own deploy/rollback lifecycle.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    try:
        signing_key = _authentik_jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=AUTHENTIK_ISSUER,
            audience=AUTHENTIK_AUDIENCE,
        )
    except Exception as exc:
        # Log only the failure category; JWT claims and submitted content are private.
        print(f"aster-speech: Authentik token rejected: {type(exc).__name__}", file=sys.stderr)
        return None


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if ASTER_SPEECH_API_KEY and authorization and hmac.compare_digest(
        authorization, f"Bearer {ASTER_SPEECH_API_KEY}"
    ):
        return
    if _authentik_claims(authorization) is not None:
        return
    if not ASTER_SPEECH_API_KEY:
        raise HTTPException(status_code=503, detail="Speech service is not configured")
    raise HTTPException(status_code=401, detail="Invalid or missing credentials")


class TTSRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "aster-speech"}


def _run_transcription(path: str) -> str:
    """Materialize Whisper's lazy result on a worker, keeping the event loop free."""
    segments, _info = _whisper_model.transcribe(path, beam_size=1)
    return "".join(segment.text for segment in segments).strip()


@app.post("/v1/stt", dependencies=[Depends(require_api_key)])
async def speech_to_text(audio: UploadFile) -> dict[str, str]:
    data = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio exceeds the maximum permitted size")
    if not data:
        raise HTTPException(status_code=400, detail="No audio data received")

    start = time.monotonic()
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        async with _transcribe_lock:
            text = await asyncio.to_thread(_run_transcription, tmp.name)
    print(
        f"aster-speech: /v1/stt completed in {time.monotonic() - start:.2f}s, bytes={len(data)}",
        file=sys.stderr,
    )

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
            result = await asyncio.to_thread(
                subprocess.run,
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
