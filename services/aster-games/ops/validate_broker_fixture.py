#!/usr/bin/env python3
"""Validate the sanitized broker catalogue and proposal-only behavior."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


BASE = os.environ.get("ASTER_GAMES_BROKER_URL", "http://127.0.0.1:8099")
TOKEN_FILE = Path(
    os.environ.get("ASTER_GAMES_CLIENT_TOKEN_FILE", "/run/secrets/broker_client_token")
)
ALLOWLIST = {"id", "name", "platform_slug", "cover_url"}


def request(path: str, payload: dict | None = None, headers: dict | None = None) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    call = Request(
        BASE + path,
        data=data,
        method="GET" if data is None else "POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            **(headers or {}),
        },
    )
    with urlopen(call, timeout=10) as response:
        return json.load(response)


def main() -> int:
    capabilities = request("/v1/capabilities")
    catalogue = request("/v1/catalog?limit=10").get("items", [])
    if len(catalogue) != 1 or set(catalogue[0]) != ALLOWLIST:
        fields = sorted(set(catalogue[0])) if catalogue else []
        raise RuntimeError(
            f"broker catalogue mismatch: count={len(catalogue)} fields={fields}"
        )
    game_id = str(catalogue[0].get("id") or "")
    if not game_id:
        raise RuntimeError("sanitized catalogue item has no id")
    proposal = request(
        "/v1/proposals",
        {"action": "request_game", "game_id": game_id},
        {
            "Idempotency-Key": "m4-synthetic-fixture-v1",
            "X-Aster-Device": "m4-synthetic-validator",
        },
    )
    replay = request(
        "/v1/proposals",
        {"action": "request_game", "game_id": game_id},
        {
            "Idempotency-Key": "m4-synthetic-fixture-v1",
            "X-Aster-Device": "m4-synthetic-validator",
        },
    )
    result = {
        "catalogue_items": len(catalogue),
        "catalogue_fields_allowlisted": set(catalogue[0]) == ALLOWLIST,
        "proposal_status": proposal.get("status"),
        "idempotent_replay": replay.get("id") == proposal.get("id"),
        "proposal_execution_enabled": bool(capabilities.get("proposal_execute")),
        "release_gate_open": bool((capabilities.get("release_gate") or {}).get("open")),
    }
    result["ok"] = (
        result["catalogue_items"] == 1
        and result["catalogue_fields_allowlisted"]
        and result["proposal_status"] == "pending"
        and result["idempotent_replay"]
        and not result["proposal_execution_enabled"]
        and not result["release_gate_open"]
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
