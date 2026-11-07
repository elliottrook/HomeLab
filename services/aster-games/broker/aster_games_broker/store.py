from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = frozenset({"request_game", "install_game"})


class ValidationError(ValueError):
    pass


class ProposalStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    action TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    device_id TEXT,
                    requester TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status = 'pending'),
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _clean(value: Any, field: str, *, required: bool = True) -> str | None:
        if value is None and not required:
            return None
        if not isinstance(value, str):
            raise ValidationError(f"{field} must be a string")
        value = value.strip()
        if required and not value:
            raise ValidationError(f"{field} is required")
        if len(value) > 128:
            raise ValidationError(f"{field} is too long")
        if any(ord(character) < 32 for character in value):
            raise ValidationError(f"{field} contains control characters")
        return value

    def create(
        self,
        payload: dict[str, Any],
        *,
        idempotency_key: str,
        requester: str,
    ) -> tuple[dict[str, Any], bool]:
        if not isinstance(payload, dict):
            raise ValidationError("request body must be an object")
        unknown = set(payload) - {"action", "game_id", "device_id"}
        if unknown:
            raise ValidationError(f"unknown fields: {', '.join(sorted(unknown))}")

        action = self._clean(payload.get("action"), "action")
        if action not in ALLOWED_ACTIONS:
            raise ValidationError("action is not allowed")
        game_id = self._clean(payload.get("game_id"), "game_id")
        device_id = self._clean(payload.get("device_id"), "device_id", required=False)
        if action == "install_game" and not device_id:
            raise ValidationError("device_id is required for install_game")
        key = self._clean(idempotency_key, "Idempotency-Key")
        actor = self._clean(requester, "requester")

        proposal_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        stored_payload = {
            "action": action,
            "game_id": game_id,
            "device_id": device_id,
        }

        with self._lock, self._connect() as db:
            existing = db.execute(
                "SELECT * FROM proposals WHERE idempotency_key = ?", (key,)
            ).fetchone()
            if existing:
                existing_payload = json.loads(existing["payload_json"])
                if existing_payload != stored_payload or existing["requester"] != actor:
                    raise ValidationError("Idempotency-Key was reused with different input")
                return self._row(existing), False
            db.execute(
                """
                INSERT INTO proposals
                    (id, idempotency_key, action, game_id, device_id, requester,
                     status, created_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    proposal_id,
                    key,
                    action,
                    game_id,
                    device_id,
                    actor,
                    created_at,
                    json.dumps(stored_payload, sort_keys=True),
                ),
            )
            row = db.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        return self._row(row), True

    def get(self, proposal_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        return self._row(row) if row else None

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "action": row["action"],
            "game_id": row["game_id"],
            "device_id": row["device_id"],
            "requester": row["requester"],
            "status": row["status"],
            "created_at": row["created_at"],
        }

