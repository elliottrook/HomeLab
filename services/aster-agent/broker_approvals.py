#!/usr/bin/env python3
"""Authenticated Companion bridge to the local AI-PAM approval socket."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class ApprovalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class BrokerApprovalClient:
    def __init__(self, socket_path: str | Path, timeout: float = 3.0) -> None:
        self.socket_path = str(socket_path)
        self.timeout = timeout

    def call(self, request: dict[str, Any]) -> Any:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(self.timeout)
                connection.connect(self.socket_path)
                connection.sendall(encoded)
                response = b""
                while not response.endswith(b"\n"):
                    chunk = connection.recv(65_536)
                    if not chunk:
                        break
                    response += chunk
                    if len(response) > 65_536:
                        raise ValueError("oversized broker response")
            decoded = json.loads(response)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise HTTPException(503, "Approval service is unavailable") from error
        if not isinstance(decoded, dict) or not decoded.get("ok"):
            detail = decoded.get("error", "Approval was rejected") if isinstance(decoded, dict) else "Approval was rejected"
            raise HTTPException(409, str(detail))
        return decoded.get("result")


def approval_router(client: BrokerApprovalClient, require_claims: Callable[..., dict[str, Any]]) -> APIRouter:
    router = APIRouter(prefix="/v1/companion/approvals", tags=["approvals"])

    def identity(claims: dict[str, Any] = Depends(require_claims)) -> tuple[str, int]:
        actor = claims.get("owner_hash")
        auth_time = claims.get("auth_time")
        if not isinstance(actor, str) or not isinstance(auth_time, int):
            raise HTTPException(401, "A fresh Companion sign-in is required")
        return actor, auth_time

    @router.get("")
    def pending(_: tuple[str, int] = Depends(identity)) -> Any:
        return client.call({"method": "pending.list"})

    @router.post("/{request_id}/approve")
    def approve(request_id: str, action: ApprovalAction, user: tuple[str, int] = Depends(identity)) -> Any:
        actor, auth_time = user
        return client.call({"method": "request.approve", "request_id": request_id,
                            "payload_hash": action.payload_hash, "actor": actor,
                            "auth_time": auth_time, "assurance": "passkey"})

    @router.post("/{request_id}/deny")
    def deny(request_id: str, action: ApprovalAction, user: tuple[str, int] = Depends(identity)) -> Any:
        actor, _ = user
        return client.call({"method": "request.deny", "request_id": request_id,
                            "payload_hash": action.payload_hash, "actor": actor})

    return router
