#!/usr/bin/env python3
"""Authenticated Companion bridge to the local AI-PAM approval socket."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field


class ApprovalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ManagementAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(pattern=r"^(agent_state|service_enabled|request_revoke|global_enabled)$")
    target: str | None = Field(default=None, min_length=1, max_length=128)
    state: str | None = Field(default=None, pattern=r"^(probation|observer|operator|specialist|orchestrator|suspended|retired)$")
    enabled: bool | None = None


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

    def identity(claims: dict[str, Any] = Depends(require_claims)) -> tuple[str, int | None]:
        actor = claims.get("owner_hash")
        auth_time = claims.get("auth_time")
        if not isinstance(actor, str):
            raise HTTPException(401, "Sign in with your Companion account")
        return actor, auth_time if isinstance(auth_time, int) else None

    @router.get("")
    def pending(_: tuple[str, int | None] = Depends(identity)) -> Any:
        return client.call({"method": "pending.list"})

    @router.post("/{request_id}/approve")
    def approve(request_id: str, action: ApprovalAction, user: tuple[str, int | None] = Depends(identity)) -> Any:
        actor, auth_time = user
        # The broker independently enforces that Red requests have a recent
        # integer auth_time. Passing None is safe and fails closed there; Yellow
        # approvals do not need to disrupt an otherwise valid OIDC session.
        return client.call({"method": "request.approve", "request_id": request_id,
                            "payload_hash": action.payload_hash, "actor": actor,
                            "auth_time": auth_time, "assurance": "passkey"})

    @router.post("/{request_id}/deny")
    def deny(request_id: str, action: ApprovalAction, user: tuple[str, int | None] = Depends(identity)) -> Any:
        actor, _ = user
        return client.call({"method": "request.deny", "request_id": request_id,
                            "payload_hash": action.payload_hash, "actor": actor})

    @router.get("/management/snapshot")
    def management_snapshot(_: tuple[str, int | None] = Depends(identity)) -> Any:
        return client.call({"method": "management.snapshot"})

    @router.get("/management/history")
    def management_history(limit: int = Query(default=100, ge=1, le=200),
                           _: tuple[str, int | None] = Depends(identity)) -> Any:
        return client.call({"method": "request.history", "limit": limit})

    @router.get("/management/audit")
    def management_audit(limit: int = Query(default=100, ge=1, le=200), event: str | None = None,
                         _: tuple[str, int | None] = Depends(identity)) -> Any:
        request: dict[str, Any] = {"method": "audit.search", "limit": limit}
        if event is not None:
            request["event"] = event
        return client.call(request)

    @router.post("/management/action")
    def management_action(action: ManagementAction,
                          user: tuple[str, int | None] = Depends(identity)) -> Any:
        actor, auth_time = user
        base = {"actor": actor, "auth_time": auth_time, "assurance": "passkey"}
        if action.action == "agent_state":
            if action.target is None or action.state is None:
                raise HTTPException(422, "agent_state requires target and state")
            request = {"method": "management.agent-state", "agent_id": action.target, "state": action.state}
        elif action.action == "service_enabled":
            if action.target is None or action.enabled is None:
                raise HTTPException(422, "service_enabled requires target and enabled")
            request = {"method": "management.service-enabled", "service_id": action.target, "enabled": action.enabled}
        elif action.action == "request_revoke":
            if action.target is None:
                raise HTTPException(422, "request_revoke requires target")
            request = {"method": "management.request-revoke", "request_id": action.target}
        else:
            if action.enabled is None:
                raise HTTPException(422, "global_enabled requires enabled")
            request = {"method": "management.global-enabled", "enabled": action.enabled}
        return client.call(request | base)

    return router
