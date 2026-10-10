"""M2 HTTP streaming contract for the repository-only voice candidate."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from voice_candidate import VoiceScheduler
from voice_protocol import FRAME_MEDIA_TYPE, stream_frames, validated_request_id


class StreamTTSRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    request_id: str | None = None


def build_router(
    scheduler: VoiceScheduler,
    authorize: Callable[..., object],
    caller: Literal["interactive", "batch"] = "interactive",
) -> APIRouter:
    """Build a router with caller class fixed by its authenticated route."""
    router = APIRouter(dependencies=[Depends(authorize)])

    @router.post("/v2/tts/stream")
    async def text_to_speech_stream(request: StreamTTSRequest) -> StreamingResponse:
        try:
            request_id = validated_request_id(request.request_id)
            # Validate synchronously enough to return HTTP errors before the
            # streaming response starts; the scheduler repeats these checks.
            if not request.text.strip():
                raise ValueError("text is required")
            if len(request.text) > 2000:
                raise ValueError("text exceeds the maximum permitted length")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StreamingResponse(
            stream_frames(scheduler, request_id, request.text, caller),
            media_type=FRAME_MEDIA_TYPE,
            headers={"X-Aster-Request-ID": request_id, "Cache-Control": "no-store"},
        )

    @router.delete("/v2/tts/{request_id}", status_code=204)
    async def cancel_text_to_speech(request_id: str) -> Response:
        try:
            request_id = validated_request_id(request_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        scheduler.cancel(request_id)
        return Response(status_code=204)

    return router
