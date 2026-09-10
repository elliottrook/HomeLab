"""Durable, resumable pipeline journal."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


class State:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
          status TEXT NOT NULL CHECK(status IN ('running','accepted','failed','interrupted'))
        );
        CREATE TABLE IF NOT EXISTS items (
          run_id TEXT NOT NULL REFERENCES runs(id), source_id TEXT NOT NULL,
          input_sha256 TEXT, stage TEXT NOT NULL, status TEXT NOT NULL,
          reason TEXT, updated_at TEXT NOT NULL,
          PRIMARY KEY(run_id, source_id)
        );
        CREATE INDEX IF NOT EXISTS item_hash_stage ON items(source_id,input_sha256,stage,status);
        CREATE TABLE IF NOT EXISTS http_validators (
          source_id TEXT PRIMARY KEY, etag TEXT, last_modified TEXT,
          checked_at TEXT NOT NULL
        );
        """)
        current = self.db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if current and int(current[0]) != SCHEMA_VERSION:
            raise RuntimeError("unsupported state schema")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version',?)", (str(SCHEMA_VERSION),))
        self.db.commit()

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def start(self, run_id: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO runs VALUES (?,?,NULL,'running')", (run_id, self.now()))
        self.db.commit()

    def checkpoint(self, run_id: str, source_id: str, stage: str, status: str,
                   input_sha256: str | None = None, reason: str | None = None) -> None:
        self.db.execute("""
          INSERT INTO items VALUES (?,?,?,?,?,?,?)
          ON CONFLICT(run_id,source_id) DO UPDATE SET input_sha256=excluded.input_sha256,
            stage=excluded.stage,status=excluded.status,reason=excluded.reason,updated_at=excluded.updated_at
        """, (run_id, source_id, input_sha256, stage, status, reason, self.now()))
        self.db.commit()

    def completed(self, source_id: str, digest: str, stage: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM items WHERE source_id=? AND input_sha256=? AND stage=? AND status='ok' LIMIT 1",
            (source_id, digest, stage),
        ).fetchone() is not None

    def validators(self, source_id: str) -> tuple[str | None, str | None]:
        row = self.db.execute(
            "SELECT etag,last_modified FROM http_validators WHERE source_id=?", (source_id,)
        ).fetchone()
        return (row[0], row[1]) if row else (None, None)

    def save_validators(self, source_id: str, etag: str | None,
                        last_modified: str | None) -> None:
        self.db.execute("""
          INSERT INTO http_validators VALUES (?,?,?,?)
          ON CONFLICT(source_id) DO UPDATE SET etag=excluded.etag,
            last_modified=excluded.last_modified,checked_at=excluded.checked_at
        """, (source_id, etag, last_modified, self.now()))
        self.db.commit()

    def finish(self, run_id: str, status: str) -> None:
        self.db.execute("UPDATE runs SET status=?,finished_at=? WHERE id=?", (status, self.now(), run_id))
        self.db.commit()

    def summary(self, run_id: str) -> dict[str, int | str]:
        counts = {row[0]: row[1] for row in self.db.execute(
            "SELECT status,count(*) FROM items WHERE run_id=? GROUP BY status", (run_id,))}
        return {"run_id": run_id, "ok": counts.get("ok", 0),
                "unchanged": counts.get("unchanged", 0),
                "quarantined": counts.get("quarantined", 0), "failed": counts.get("failed", 0)}

    def latest(self) -> dict[str, str | None] | None:
        row = self.db.execute(
            "SELECT id,started_at,finished_at,status FROM runs ORDER BY started_at DESC,id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def stale_running(self) -> list[str]:
        return [row[0] for row in self.db.execute("SELECT id FROM runs WHERE status='running'")]

    def close(self) -> None:
        self.db.close()
