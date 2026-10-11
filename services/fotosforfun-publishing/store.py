"""SQLite catalogue with immutable versions, approvals and publication audit."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading

from model import Approval, ContentError, Photo, clean_text


SCHEMA_VERSION = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CatalogueStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        self.path = path
        self.lock = threading.RLock()
        self.database = sqlite3.connect(path, check_same_thread=False)
        os.chmod(path, 0o600)
        self.database.row_factory = sqlite3.Row
        self.database.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS schema_metadata (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS photo_versions (
              photo_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              record_json TEXT NOT NULL,
              approval_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              created_by TEXT NOT NULL,
              PRIMARY KEY (photo_id, version)
            );
            CREATE TABLE IF NOT EXISTS approvals (
              photo_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              approval_hash TEXT NOT NULL,
              approved_by TEXT NOT NULL,
              approved_at TEXT NOT NULL,
              PRIMARY KEY (photo_id, version),
              FOREIGN KEY (photo_id, version)
                REFERENCES photo_versions(photo_id, version)
            );
            CREATE TABLE IF NOT EXISTS publications (
              publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
              release_id TEXT NOT NULL UNIQUE,
              manifest_sha256 TEXT NOT NULL,
              catalogue_sha256 TEXT NOT NULL,
              published_by TEXT NOT NULL,
              published_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publication_rollbacks (
              rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,
              from_release_id TEXT NOT NULL,
              to_release_id TEXT NOT NULL,
              manifest_sha256 TEXT NOT NULL,
              rolled_back_by TEXT NOT NULL,
              rolled_back_at TEXT NOT NULL
            );
            """
        )
        existing = self.database.execute(
            "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if existing is None:
            self.database.execute(
                "INSERT INTO schema_metadata VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
        elif int(existing["value"]) != SCHEMA_VERSION:
            raise ContentError("catalogue schema version is not supported")
        self.database.commit()

    def close(self) -> None:
        self.database.close()

    def save(self, photo: Photo, actor: str) -> int:
        with self.lock:
            photo.validate()
            actor = clean_text(actor, "actor", 160)
            current = self.database.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM photo_versions WHERE photo_id = ?",
                (photo.id,),
            ).fetchone()
            version = int(current["version"]) + 1
            self.database.execute(
                "INSERT INTO photo_versions VALUES (?, ?, ?, ?, ?, ?)",
                (photo.id, version,
                 json.dumps(asdict(photo), ensure_ascii=False, sort_keys=True),
                 photo.approval_hash(), now(), actor),
            )
            self.database.commit()
            return version

    def latest(self, photo_id: str) -> tuple[Photo, int]:
        with self.lock:
            row = self.database.execute(
                "SELECT version, record_json FROM photo_versions WHERE photo_id = ? "
                "ORDER BY version DESC LIMIT 1", (photo_id,),
            ).fetchone()
            if row is None:
                raise KeyError(photo_id)
            return Photo.from_dict(json.loads(row["record_json"])), int(row["version"])

    def list_latest(self, *, include_retired: bool = True) -> list[tuple[Photo, int]]:
        with self.lock:
            rows = self.database.execute(
                "SELECT versions.version, versions.record_json FROM photo_versions AS versions "
                "JOIN (SELECT photo_id, MAX(version) AS version FROM photo_versions GROUP BY photo_id) AS latest "
                "ON latest.photo_id = versions.photo_id AND latest.version = versions.version "
                "ORDER BY versions.photo_id"
            ).fetchall()
            records = [(Photo.from_dict(json.loads(row["record_json"])), int(row["version"]))
                       for row in rows]
            if not include_retired:
                records = [(photo, version) for photo, version in records if not photo.retired]
            return records

    def set_retired(self, photo_id: str, retired: bool, actor: str,
                    confirmation: str = "") -> int:
        if retired and confirmation != "RETIRE PHOTO":
            raise ContentError("retirement confirmation did not match")
        photo, _ = self.latest(photo_id)
        if photo.retired == retired:
            raise ContentError("photo already has the requested retirement state")
        return self.save(replace(photo, retired=retired), actor)

    def approve(self, photo_id: str, actor: str) -> Approval:
        with self.lock:
            photo, version = self.latest(photo_id)
            if photo.retired:
                raise ContentError("retired photos cannot be approved")
            if photo.sample:
                raise ContentError("sample photos cannot be approved for publication")
            actor = clean_text(actor, "actor", 160)
            approval = Approval(photo_id, version, photo.approval_hash(), actor, now())
            self.database.execute(
                "INSERT INTO approvals VALUES (?, ?, ?, ?, ?)",
                (approval.photo_id, approval.version, approval.approved_hash,
                 approval.approved_by, approval.approved_at),
            )
            self.database.commit()
            return approval

    def current_approval(self, photo_id: str) -> Approval | None:
        with self.lock:
            photo, version = self.latest(photo_id)
            row = self.database.execute(
                "SELECT * FROM approvals WHERE photo_id = ? AND version = ? AND approval_hash = ?",
                (photo_id, version, photo.approval_hash()),
            ).fetchone()
            if row is None:
                return None
            return Approval(row["photo_id"], int(row["version"]), row["approval_hash"],
                            row["approved_by"], row["approved_at"])

    def publishable(self) -> list[tuple[Photo, int, Approval]]:
        records: list[tuple[Photo, int, Approval]] = []
        for photo, version in self.list_latest(include_retired=False):
            approval = self.current_approval(photo.id)
            if approval is None or photo.sample:
                continue
            records.append((photo, version, approval))
        return sorted(records, key=lambda item: (item[0].sort_order, item[0].id))

    def publication_snapshot(self) -> list[tuple[Photo, int, Approval]]:
        """Freeze a complete active catalogue or fail rather than drop an item."""
        active = self.list_latest(include_retired=False)
        if not active:
            raise ContentError("gallery has no active photographs")
        snapshot: list[tuple[Photo, int, Approval]] = []
        blockers: list[str] = []
        for photo, version in active:
            approval = self.current_approval(photo.id)
            if photo.sample:
                blockers.append(f"{photo.id}: sample")
            elif approval is None:
                blockers.append(f"{photo.id}: awaiting approval")
            else:
                snapshot.append((photo, version, approval))
        if blockers:
            raise ContentError("publication blocked — " + "; ".join(blockers))
        return sorted(snapshot, key=lambda item: (item[0].sort_order, item[0].id))

    def record_publication(self, release_id: str, manifest_sha256: str,
                           catalogue_sha256: str, actor: str) -> None:
        values = [release_id, manifest_sha256, catalogue_sha256]
        if not release_id.startswith("fotosforfun-") or any(not value for value in values):
            raise ContentError("publication identity is invalid")
        if any(len(value) != 64 for value in values[1:]):
            raise ContentError("publication digest is invalid")
        self.database.execute(
            "INSERT INTO publications(release_id, manifest_sha256, catalogue_sha256, published_by, published_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (release_id, manifest_sha256, catalogue_sha256,
             clean_text(actor, "actor", 160), now()),
        )
        self.database.commit()

    def record_rollback(self, from_release: str, to_release: str,
                        manifest_sha256: str, actor: str) -> None:
        if from_release == to_release or not all(
                value.startswith("fotosforfun-") for value in (from_release, to_release)):
            raise ContentError("rollback identity is invalid")
        if len(manifest_sha256) != 64:
            raise ContentError("rollback digest is invalid")
        self.database.execute(
            "INSERT INTO publication_rollbacks(from_release_id, to_release_id, manifest_sha256, "
            "rolled_back_by, rolled_back_at) VALUES (?, ?, ?, ?, ?)",
            (from_release, to_release, manifest_sha256,
             clean_text(actor, "actor", 160), now()),
        )
        self.database.commit()
