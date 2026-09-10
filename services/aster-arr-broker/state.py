"""Root-owned, opaque broker state for short-lived Radarr candidates."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from broker import Candidate


def issue_candidate(queue_id: int, *, now: datetime | None = None) -> Candidate:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    token = base64.b32encode(os.urandom(10)).decode("ascii").lower().rstrip("=")
    return Candidate(f"radarr-q-{token}", queue_id, current, current + timedelta(minutes=5))


def load_candidates(path: Path) -> dict[str, Candidate]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict) or set(payload) != {"candidates"} or not isinstance(payload["candidates"], list):
        return {}
    result = {}
    for item in payload["candidates"]:
        if not isinstance(item, dict) or set(item) != {"reference", "queue_id", "issued_at", "expires_at"}:
            continue
        try:
            candidate = Candidate(
                str(item["reference"]),
                int(item["queue_id"]),
                datetime.fromisoformat(str(item["issued_at"]).replace("Z", "+00:00")),
                datetime.fromisoformat(str(item["expires_at"]).replace("Z", "+00:00")),
            )
        except (TypeError, ValueError):
            continue
        result[candidate.reference] = candidate
    return result


def store_candidates(path: Path, candidates: list[Candidate]) -> None:
    payload = {
        "candidates": [
            {
                "reference": candidate.reference,
                "queue_id": candidate.queue_id,
                "issued_at": candidate.issued_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "expires_at": candidate.expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            for candidate in candidates
        ]
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)
