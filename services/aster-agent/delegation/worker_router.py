"""Unregistered worker protocol routes. No inference or user-token fallback.

The embedding gateway must provide a dedicated verified workload-identity
dependency. Do not substitute companion_owner or trust worker IDs in JSON.
"""
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: str = Field(min_length=1, max_length=256)
    event: Literal["accepted", "running", "unknown", "completed", "failed", "interrupted"]
    result_sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")


def worker_router(gateway, worker_dependency, *, enabled=False):
    router = APIRouter(prefix="/v1/delegation/worker/jobs")

    def check_enabled():
        if not enabled:
            raise HTTPException(503, "Worker integration is not enabled")

    @router.post("/{job_id}/offer")
    async def offer(job_id: str, response: Response, worker=Depends(worker_dependency)):
        check_enabled()
        response.headers["Cache-Control"] = "no-store"
        try:
            return {"offer": gateway.offer(worker, job_id)}
        except KeyError:
            raise HTTPException(404, "Job not found") from None

    @router.post("/{job_id}/receipt")
    async def receipt(job_id: str, receipt: Receipt, response: Response,
                      worker=Depends(worker_dependency)):
        check_enabled()
        response.headers["Cache-Control"] = "no-store"
        try:
            return {"state": gateway.receipt(worker, job_id, **receipt.model_dump())}
        except KeyError:
            raise HTTPException(404, "Job not found") from None
        except ValueError:
            raise HTTPException(409, "Receipt conflicts with the job contract") from None

    return router
