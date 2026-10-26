"""Durable generation state independent of Calibre."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import time

from .catalog import SourceFingerprint


STATES = frozenset({"queued", "extracting", "narrating", "aligning", "ready", "failed"})
FAILURE_CODES = frozenset({
    "source-changed",
    "unsupported-format",
    "epub-invalid",
    "voice-contract",
    "timing-invalid",
    "quota",
    "publish",
    "interrupted",
})
TRANSITIONS = {
    "queued": frozenset({"extracting", "failed"}),
    "extracting": frozenset({"narrating", "failed"}),
    "narrating": frozenset({"aligning", "failed"}),
    "aligning": frozenset({"ready", "failed"}),
    "ready": frozenset(),
    "failed": frozenset({"queued"}),
}


class QueueStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS generations ("
                "book_id INTEGER NOT NULL, source_sha256 TEXT NOT NULL, "
                "compiler_contract TEXT NOT NULL, source_size INTEGER NOT NULL, "
                "source_mtime_ns INTEGER NOT NULL, state TEXT NOT NULL, "
                "attempt_count INTEGER NOT NULL DEFAULT 0, failure_code TEXT, "
                "created_at REAL NOT NULL, updated_at REAL NOT NULL, "
                "PRIMARY KEY (book_id, source_sha256, compiler_contract), "
                "CHECK (state IN ('queued','extracting','narrating','aligning','ready','failed')))"
            )

    def reconcile(self, sources: tuple[SourceFingerprint, ...], compiler_contract: str) -> int:
        if not compiler_contract:
            raise ValueError("compiler-contract")
        now = time.time()
        inserted = 0
        with sqlite3.connect(self.path) as connection:
            for source in sources:
                if (
                    source.calibre_id < 1
                    or len(source.source_sha256) != 64
                    or any(character not in "0123456789abcdef" for character in source.source_sha256)
                    or source.size < 1
                    or source.mtime_ns < 0
                ):
                    raise ValueError("source-fingerprint")
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO generations "
                    "(book_id,source_sha256,compiler_contract,source_size,source_mtime_ns,state,created_at,updated_at) "
                    "VALUES (?,?,?,?,?,'queued',?,?)",
                    (source.calibre_id, source.source_sha256, compiler_contract,
                     source.size, source.mtime_ns, now, now),
                )
                inserted += cursor.rowcount
        return inserted

    def state(self, book_id: int, source_sha256: str, compiler_contract: str) -> str:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT state FROM generations WHERE book_id=? AND source_sha256=? AND compiler_contract=?",
                (book_id, source_sha256, compiler_contract),
            ).fetchone()
        if row is None:
            raise KeyError("generation")
        return str(row[0])

    def transition(
        self,
        book_id: int,
        source_sha256: str,
        compiler_contract: str,
        target: str,
        failure_code: str | None = None,
    ) -> None:
        if target not in STATES:
            raise ValueError("generation-state")
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT state,attempt_count FROM generations "
                "WHERE book_id=? AND source_sha256=? AND compiler_contract=?",
                (book_id, source_sha256, compiler_contract),
            ).fetchone()
            if row is None:
                raise KeyError("generation")
            current, attempts = str(row[0]), int(row[1])
            if target not in TRANSITIONS[current]:
                raise ValueError("generation-transition")
            if target == "failed" and failure_code not in FAILURE_CODES:
                raise ValueError("generation-failure-code")
            if target != "failed" and failure_code is not None:
                raise ValueError("generation-failure-code")
            next_attempts = attempts + 1 if current in ("queued", "failed") and target == "extracting" else attempts
            connection.execute(
                "UPDATE generations SET state=?,attempt_count=?,failure_code=?,updated_at=? "
                "WHERE book_id=? AND source_sha256=? AND compiler_contract=? AND state=?",
                (target, next_attempts, failure_code, time.time(), book_id,
                 source_sha256, compiler_contract, current),
            )

