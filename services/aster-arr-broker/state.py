"""Root-owned, opaque broker state for short-lived Radarr candidates."""

from __future__ import annotations

import base64
import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from broker import Candidate
from persistence import atomic_json_write
from proposal import CANDIDATE_REF


def issue_candidate(queue_id: int, *, now: datetime | None = None) -> Candidate:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    token = base64.b32encode(os.urandom(10)).decode("ascii").lower().rstrip("=")
    return Candidate(f"radarr-q-{token}", queue_id, current, current + timedelta(minutes=5))


def load_candidates(path: Path) -> dict[str, Candidate]:
    try:
        status = path.lstat()
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_mode & 0o022
            or status.st_size > 65_536
        ):
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict) or set(payload) != {"candidates"} or not isinstance(payload["candidates"], list):
        return {}
    if len(payload["candidates"]) > 1:
        return {}
    result = {}
    for item in payload["candidates"]:
        if not isinstance(item, dict) or set(item) != {"reference", "queue_id", "issued_at", "expires_at"}:
            continue
        try:
            reference = str(item["reference"])
            queue_id = item["queue_id"]
            if (
                not CANDIDATE_REF.fullmatch(reference)
                or not isinstance(queue_id, int)
                or isinstance(queue_id, bool)
                or queue_id < 1
            ):
                continue
            candidate = Candidate(
                reference,
                queue_id,
                datetime.fromisoformat(str(item["issued_at"]).replace("Z", "+00:00")),
                datetime.fromisoformat(str(item["expires_at"]).replace("Z", "+00:00")),
            )
        except (TypeError, ValueError):
            continue
        if (
            candidate.issued_at.tzinfo is None
            or candidate.expires_at.tzinfo is None
            or candidate.expires_at <= candidate.issued_at
            or candidate.expires_at - candidate.issued_at > timedelta(minutes=5)
        ):
            continue
        if candidate.reference in result:
            return {}
        result[candidate.reference] = candidate
    return result


def store_candidates(
    path: Path,
    candidates: list[Candidate],
    *,
    mode: int = 0o600,
    owner: tuple[int, int] | None = None,
) -> None:
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
    atomic_json_write(path, payload, mode=mode, owner=owner)
