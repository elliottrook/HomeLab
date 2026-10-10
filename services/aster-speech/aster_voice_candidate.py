"""Side-by-side M2 application; never imported by the production unit."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response

import aster_speech as legacy_speech
from aster_speech import TTSRequest, require_api_key, speech_to_text
from kokoro_candidate import KokoroRendererPool
from voice_candidate import VoiceScheduler
from voice_candidate_http import build_router
from voice_protocol import pcm_to_wav


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


app = FastAPI(title="Aster Voice Candidate", version="2.0.0-candidate")
_proxy = SchedulerProxy()
_pool: KokoroRendererPool | None = None

app.include_router(build_router(_proxy, require_api_key))  # type: ignore[arg-type]
app.add_api_route(
    "/v1/stt",
    speech_to_text,
    methods=["POST"],
    dependencies=[Depends(require_api_key)],
)


@app.on_event("startup")
async def startup() -> None:
    global _pool
    # This is a separate FastAPI application, so the legacy app's startup hook
    # does not run automatically. Initialize the shared STT implementation here.
    await legacy_speech._startup()
    _pool = KokoroRendererPool()
    scheduler = VoiceScheduler(_pool.renderers)
    await scheduler.start()
    _proxy.target = scheduler


@app.on_event("shutdown")
async def shutdown() -> None:
    global _pool
    scheduler, _proxy.target = _proxy.target, None
    if scheduler is not None:
        await scheduler.close()
    if _pool is not None:
        _pool.close()
        _pool = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok" if _proxy.target is not None else "starting",
        "service": "aster-voice-candidate",
        "voice": "aster-bm-daniel",
    }


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
