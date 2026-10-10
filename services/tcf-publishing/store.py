"""Durable, site-scoped content versions and immutable approvals."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Optional

from content import Approval, ContentError, ContentRecord, SITES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ContentStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.database = sqlite3.connect(path, check_same_thread=False)
        os.chmod(path, 0o600)
        self.database.row_factory = sqlite3.Row
        self.database.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS content_versions (
              site TEXT NOT NULL,
              content_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              record_json TEXT NOT NULL,
              public_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY (site, content_id, version)
            );
            CREATE TABLE IF NOT EXISTS approvals (
              site TEXT NOT NULL,
              content_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              public_hash TEXT NOT NULL,
              approved_by TEXT NOT NULL,
              approved_at TEXT NOT NULL,
              PRIMARY KEY (site, content_id, version),
              FOREIGN KEY (site, content_id, version)
                REFERENCES content_versions(site, content_id, version)
            );
            """
        )

    def close(self) -> None:
        self.database.close()

    def save(self, record: ContentRecord) -> int:
        with self.lock:
            record.validate()
            row = self.database.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM content_versions "
                "WHERE site = ? AND content_id = ?",
                (record.site, record.id),
            ).fetchone()
            version = int(row["version"]) + 1
            self.database.execute(
                "INSERT INTO content_versions VALUES (?, ?, ?, ?, ?, ?)",
                (record.site, record.id, version,
                 json.dumps(asdict(record), ensure_ascii=False, sort_keys=True),
                 record.public_hash(), _now()),
            )
            self.database.commit()
            return version

    def latest(self, site: str, content_id: str) -> tuple[ContentRecord, int]:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            row = self.database.execute(
                "SELECT version, record_json FROM content_versions "
                "WHERE site = ? AND content_id = ? ORDER BY version DESC LIMIT 1",
                (site, content_id),
            ).fetchone()
            if row is None:
                raise KeyError((site, content_id))
            return ContentRecord.from_dict(json.loads(row["record_json"])), int(row["version"])

    def approve(self, site: str, content_id: str, approved_by: str) -> Approval:
        with self.lock:
            record, version = self.latest(site, content_id)
            blockers = record.approval_blockers()
            if blockers:
                raise ContentError("; ".join(blockers))
            approval = Approval(content_id, version, record.public_hash(), approved_by, _now())
            self.database.execute(
                "INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?)",
                (site, approval.content_id, approval.version, approval.approved_hash,
                 approval.approved_by, approval.approved_at),
            )
            self.database.commit()
            return approval

    def current_approval(self, site: str, content_id: str) -> Optional[Approval]:
        with self.lock:
            record, version = self.latest(site, content_id)
            row = self.database.execute(
                "SELECT * FROM approvals WHERE site = ? AND content_id = ? "
                "AND version = ? AND public_hash = ?",
                (site, content_id, version, record.public_hash()),
            ).fetchone()
            if row is None:
                return None
            return Approval(row["content_id"], int(row["version"]), row["public_hash"],
                            row["approved_by"], row["approved_at"])

    def copy_to_site(self, source_site: str, content_id: str, target_site: str) -> int:
        with self.lock:
            if source_site == target_site or target_site not in SITES:
                raise ContentError("copy requires two different known sites")
            record, _ = self.latest(source_site, content_id)
            copied = ContentRecord.from_dict({**asdict(record), "site": target_site})
            return self.save(copied)
