"""Side-by-side M2 application; never imported by the production unit."""

from __future__ import annotations

import asyncio
import hmac
import os
import uuid
from pathlib import Path
from typing import Any, Protocol

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response

import aster_speech as legacy_speech
from aster_speech import TTSRequest, require_api_key, speech_to_text
from kokoro_candidate import KokoroRendererPool
from vulkan_renderer_client import VulkanRendererPool
from voice_candidate import VoiceScheduler
from voice_candidate_http import build_router
from voice_protocol import pcm_to_wav
from wyoming_adapter import start_wyoming_server


class SchedulerProxy:
    """Stable router dependency populated only after verified startup."""

    target: VoiceScheduler | None = None

    async def stream(self, *args: Any, **kwargs: Any):
        if self.target is None:
            raise RuntimeError("voice candidate is not ready")
        async for unit in self.target.stream(*args, **kwargs):
            yield unit

    def cancel(self, request_id: str) -> None:
        if self.target is not None:
            self.target.cancel(request_id)

    def is_cancelled(self, request_id: str) -> bool:
        return self.target is not None and self.target.is_cancelled(request_id)


app = FastAPI(title="Aster Voice Candidate", version="2.0.0-candidate")
_proxy = SchedulerProxy()
VOICE_ID = "aster-bm-daniel"
VOICE_MODEL = "kokoro-v1.0"
VOICE_POLICY_VERSION = "1"
STT_MODEL = "aster-base-en"

class RendererPool(Protocol):
    @property
    def renderers(self): ...

    def close(self) -> None: ...

    def healthy(self) -> bool: ...


_pool: RendererPool | None = None
_batch_pool: RendererPool | None = None
_wyoming_server = None


def require_batch_api_key(authorization: str | None = Header(default=None)) -> None:
    """Authorize only the dedicated News identity; never accept Companion JWTs."""
    key = os.environ.get("ASTER_BATCH_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Batch speech is not configured")
    if authorization and hmac.compare_digest(authorization, f"Bearer {key}"):
        return
    raise HTTPException(status_code=401, detail="Invalid or missing credentials")

app.include_router(build_router(_proxy, require_api_key))  # type: ignore[arg-type]
app.include_router(  # type: ignore[arg-type]
    build_router(_proxy, require_batch_api_key, caller="batch")
)
app.add_api_route(
    "/v1/stt",
    speech_to_text,
    methods=["POST"],
    dependencies=[Depends(require_api_key)],
)


@app.on_event("startup")
async def startup() -> None:
    global _pool, _batch_pool, _wyoming_server
    # This is a separate FastAPI application, so the legacy app's startup hook
    # does not run automatically. Initialize the shared STT implementation here.
    await legacy_speech._startup()
    renderer = os.environ.get("ASTER_VOICE_RENDERER", "onnx")
    if renderer == "onnx":
        _pool = KokoroRendererPool()
    elif renderer == "vulkan":
        _pool = VulkanRendererPool()
    else:
        raise RuntimeError("unsupported Aster voice renderer")
    batch_renderer = None
    batch_url = os.environ.get("ASTER_BATCH_RENDERER_URL", "").strip()
    if batch_url:
        _batch_pool = VulkanRendererPool(
            endpoint=batch_url,
            key_file=Path(os.environ.get(
                "ASTER_BATCH_RENDERER_KEY_FILE",
                "/etc/aster-speech/batch-renderer.key",
            )),
            timeout=float(os.environ.get("ASTER_BATCH_RENDERER_TIMEOUT", "120")),
        )
        batch_renderer = _batch_pool.renderers[0]
    scheduler = VoiceScheduler(_pool.renderers, batch_renderer=batch_renderer)
    await scheduler.start()
    _proxy.target = scheduler
    wyoming_uri = os.environ.get("ASTER_WYOMING_URI", "").strip()
    if wyoming_uri:
        _wyoming_server = await start_wyoming_server(
            _proxy,
            legacy_speech.transcribe_pcm,
            wyoming_uri,
            os.environ.get("ASTER_WYOMING_ALLOWED_PEER", "192.168.20.11"),
        )


@app.on_event("shutdown")
async def shutdown() -> None:
    global _pool, _batch_pool, _wyoming_server
    if _wyoming_server is not None:
        await _wyoming_server.stop()
        _wyoming_server = None
    scheduler, _proxy.target = _proxy.target, None
    if scheduler is not None:
        await scheduler.close()
    if _pool is not None:
        _pool.close()
        _pool = None
    if _batch_pool is not None:
        _batch_pool.close()
        _batch_pool = None


@app.get("/health")
async def health() -> JSONResponse:
    ready = _proxy.target is not None and _pool is not None
    if ready:
        ready = await asyncio.to_thread(_pool.healthy)
    if ready and _batch_pool is not None:
        ready = await asyncio.to_thread(_batch_pool.healthy)
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ok" if ready else "unavailable",
            "service": "aster-voice-candidate",
            "voice": VOICE_ID,
            "voice_model": VOICE_MODEL,
            "voice_policy_version": VOICE_POLICY_VERSION,
            "stt_model": STT_MODEL,
        },
    )


@app.post("/v1/tts", dependencies=[Depends(require_api_key)])
async def compatibility_text_to_speech(request: TTSRequest) -> Response:
    if _proxy.target is None:
        raise HTTPException(status_code=503, detail="Voice candidate is not ready")
    request_id = uuid.uuid4().hex
    chunks = []
    sample_rate = 0
    try:
        async for unit in _proxy.target.stream(request_id, request.text, "interactive"):
            if sample_rate and unit.sample_rate != sample_rate:
                raise RuntimeError("renderer sample rate changed within request")
            sample_rate = unit.sample_rate
            chunks.append(unit.pcm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Speech synthesis failed") from exc
    return Response(content=pcm_to_wav(b"".join(chunks), sample_rate), media_type="audio/wav")
