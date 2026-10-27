"""Durable generation state independent of Calibre."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time
import uuid

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


@dataclass(frozen=True)
class GenerationRecord:
    book_id: int
    source_sha256: str
    compiler_contract: str
    source_size: int
    source_mtime_ns: int
    state: str
    attempt_count: int
    attempt_id: str | None


class QueueStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            # The queue lives on one NFS-mounted dataset. A rollback journal is
            # safe across that boundary; WAL shared-memory coordination is not.
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS generations ("
                "book_id INTEGER NOT NULL, source_sha256 TEXT NOT NULL, "
                "compiler_contract TEXT NOT NULL, source_size INTEGER NOT NULL, "
                "source_mtime_ns INTEGER NOT NULL, state TEXT NOT NULL, "
                "attempt_count INTEGER NOT NULL DEFAULT 0, failure_code TEXT, "
                "attempt_id TEXT, "
                "created_at REAL NOT NULL, updated_at REAL NOT NULL, "
                "PRIMARY KEY (book_id, source_sha256, compiler_contract), "
                "CHECK (state IN ('queued','extracting','narrating','aligning','ready','failed')))"
            )
            columns = {
                str(row[1]) for row in connection.execute("PRAGMA table_info(generations)")
            }
            if "attempt_id" not in columns:
                connection.execute("ALTER TABLE generations ADD COLUMN attempt_id TEXT")

    def reconcile(self, sources: tuple[SourceFingerprint, ...], compiler_contract: str) -> int:
        if not compiler_contract:
            raise ValueError("compiler-contract")
        now = time.time()
        inserted = 0
        with closing(sqlite3.connect(self.path)) as connection, connection:
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
        with closing(sqlite3.connect(self.path)) as connection, connection:
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
        with closing(sqlite3.connect(self.path)) as connection, connection:
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

    def claim_next(self, compiler_contract: str, max_attempts: int = 3) -> GenerationRecord | None:
        """Atomically claim one queued generation for the single worker."""
        if not compiler_contract or max_attempts < 1:
            raise ValueError("claim-contract-attempts")
        attempt_id = uuid.uuid4().hex
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT book_id,source_sha256,compiler_contract,source_size,"
                "source_mtime_ns,state,attempt_count FROM generations "
                "WHERE compiler_contract=? AND state='queued' AND attempt_count<? "
                "ORDER BY created_at,book_id LIMIT 1",
                (compiler_contract, max_attempts),
            ).fetchone()
            if row is None:
                return None
            updated = connection.execute(
                "UPDATE generations SET state='extracting',attempt_count=attempt_count+1,"
                "attempt_id=?,failure_code=NULL,updated_at=? "
                "WHERE book_id=? AND source_sha256=? AND compiler_contract=? AND state='queued'",
                (attempt_id, time.time(), row[0], row[1], row[2]),
            )
            if updated.rowcount != 1:
                raise RuntimeError("generation-claim-race")
            return GenerationRecord(
                book_id=int(row[0]),
                source_sha256=str(row[1]),
                compiler_contract=str(row[2]),
                source_size=int(row[3]),
                source_mtime_ns=int(row[4]),
                state="extracting",
                attempt_count=int(row[6]) + 1,
                attempt_id=attempt_id,
            )

    def recover_interrupted(self, compiler_contract: str, max_attempts: int = 3) -> tuple[str, ...]:
        """Record interrupted work, then requeue only attempts still within policy."""
        recovered: list[str] = []
        now = time.time()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT book_id,source_sha256,attempt_count,attempt_id FROM generations "
                "WHERE compiler_contract=? AND state IN ('extracting','narrating','aligning')",
                (compiler_contract,),
            ).fetchall()
            for book_id, source_sha256, attempts, attempt_id in rows:
                terminal = "queued" if int(attempts) < max_attempts else "failed"
                connection.execute(
                    "UPDATE generations SET state=?,failure_code='interrupted',updated_at=? "
                    "WHERE book_id=? AND source_sha256=? AND compiler_contract=?",
                    (terminal, now, book_id, source_sha256, compiler_contract),
                )
                if isinstance(attempt_id, str) and attempt_id:
                    recovered.append(attempt_id)
        return tuple(recovered)

    def retry_failed(
        self,
        compiler_contract: str,
        failure_code: str,
        max_attempts: int = 3,
    ) -> int:
        """Requeue only a selected bounded failure class below its attempt cap."""
        if not compiler_contract or failure_code not in FAILURE_CODES or max_attempts < 1:
            raise ValueError("retry-policy")
        with closing(sqlite3.connect(self.path)) as connection, connection:
            cursor = connection.execute(
                "UPDATE generations SET state='queued',failure_code=NULL,attempt_id=NULL,updated_at=? "
                "WHERE compiler_contract=? AND state='failed' AND failure_code=? AND attempt_count<?",
                (time.time(), compiler_contract, failure_code, max_attempts),
            )
            return cursor.rowcount

    def counts(self, compiler_contract: str) -> dict[str, int]:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            rows = connection.execute(
                "SELECT state,COUNT(*) FROM generations WHERE compiler_contract=? GROUP BY state",
                (compiler_contract,),
            ).fetchall()
        found = {state: 0 for state in STATES}
        found.update({str(state): int(count) for state, count in rows})
        return found

    def oldest_queued_age(self, compiler_contract: str, now: float | None = None) -> float | None:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            row = connection.execute(
                "SELECT MIN(created_at) FROM generations WHERE compiler_contract=? AND state='queued'",
                (compiler_contract,),
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return max(0.0, (time.time() if now is None else now) - float(row[0]))

