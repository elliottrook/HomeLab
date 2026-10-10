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
            CREATE TABLE IF NOT EXISTS editions (
              edition_id INTEGER PRIMARY KEY AUTOINCREMENT,
              site TEXT NOT NULL,
              label TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('draft', 'published', 'cancelled')),
              created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_draft_edition_per_site
              ON editions(site) WHERE status = 'draft';
            CREATE TABLE IF NOT EXISTS edition_slots (
              edition_id INTEGER NOT NULL,
              content_id TEXT NOT NULL,
              baseline_hash TEXT NOT NULL,
              candidate_version INTEGER,
              action TEXT NOT NULL DEFAULT 'replace' CHECK(action IN ('replace', 'remove')),
              PRIMARY KEY (edition_id, content_id),
              FOREIGN KEY (edition_id) REFERENCES editions(edition_id)
            );
            CREATE TABLE IF NOT EXISTS publications (
              edition_id INTEGER PRIMARY KEY,
              site TEXT NOT NULL,
              release_id TEXT NOT NULL UNIQUE,
              manifest_sha256 TEXT NOT NULL,
              published_at TEXT NOT NULL,
              FOREIGN KEY (edition_id) REFERENCES editions(edition_id)
            );
            CREATE TABLE IF NOT EXISTS publication_rollbacks (
              rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,
              site TEXT NOT NULL,
              from_release_id TEXT NOT NULL,
              to_release_id TEXT NOT NULL,
              manifest_sha256 TEXT NOT NULL,
              rolled_back_at TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.database.close()

    def _insert(self, record: ContentRecord) -> int:
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
            edition = self.database.execute(
                "SELECT edition_id FROM editions WHERE site = ? AND status = 'draft'",
                (record.site,),
            ).fetchone()
            if edition is not None:
                self.database.execute(
                    "UPDATE edition_slots SET candidate_version = ? "
                    "WHERE edition_id = ? AND content_id = ? AND baseline_hash != ?",
                    (version, int(edition["edition_id"]), record.id, record.public_hash()),
                )
            self.database.commit()
            return version

    def save(self, record: ContentRecord) -> int:
        with self.lock:
            try:
                current, _ = self.latest(record.site, record.id)
            except KeyError:
                current = None
            if current is not None and current.sample and not record.sample:
                raise ContentError("sample flag can only be removed by explicit promotion")
            return self._insert(record)

    def promote(self, site: str, content_id: str, confirmation: str) -> int:
        with self.lock:
            if confirmation != "PROMOTE REAL CONTENT":
                raise ContentError("promotion confirmation did not match")
            current, _ = self.latest(site, content_id)
            if not current.sample:
                raise ContentError("record is already real content")
            if not current.asset_path.startswith("imports/"):
                raise ContentError("replace the placeholder with an imported photograph")
            if current.title.upper().startswith("PLACEHOLDER"):
                raise ContentError("replace the placeholder title")
            if current.story.upper().startswith("PLACEHOLDER"):
                raise ContentError("replace the placeholder story")
            promoted = ContentRecord.from_dict({**asdict(current), "sample": False})
            blockers = promoted.approval_blockers()
            if blockers:
                raise ContentError("; ".join(blockers))
            return self._insert(promoted)

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

    def version(self, site: str, content_id: str, version: int) -> ContentRecord:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            row = self.database.execute(
                "SELECT record_json FROM content_versions WHERE site = ? AND content_id = ? AND version = ?",
                (site, content_id, version),
            ).fetchone()
            if row is None:
                raise KeyError((site, content_id, version))
            return ContentRecord.from_dict(json.loads(row["record_json"]))

    def list_latest(self, site: str) -> list[tuple[ContentRecord, int]]:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            rows = self.database.execute(
                "SELECT versions.version, versions.record_json FROM content_versions AS versions "
                "JOIN (SELECT content_id, MAX(version) AS version FROM content_versions "
                "WHERE site = ? GROUP BY content_id) AS latest "
                "ON latest.content_id = versions.content_id AND latest.version = versions.version "
                "WHERE versions.site = ? ORDER BY versions.content_id",
                (site, site),
            ).fetchall()
            return [(ContentRecord.from_dict(json.loads(row["record_json"])), int(row["version"]))
                    for row in rows]

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

    def start_refresh(self, site: str, label: str) -> dict:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            if not label.strip() or len(label.strip()) > 80:
                raise ContentError("edition label must be 1 to 80 characters")
            records = self.list_latest(site)
            if not records:
                raise ContentError("site has no slots to replace")
            try:
                cursor = self.database.execute(
                    "INSERT INTO editions(site, label, status, created_at) VALUES (?, ?, 'draft', ?)",
                    (site, label.strip(), _now()),
                )
            except sqlite3.IntegrityError as error:
                raise ContentError("a fortnightly refresh is already in progress") from error
            edition_id = int(cursor.lastrowid)
            self.database.executemany(
                "INSERT INTO edition_slots(edition_id, content_id, baseline_hash) VALUES (?, ?, ?)",
                [(edition_id, record.id, record.public_hash()) for record, _ in records],
            )
            self.database.commit()
            return self.edition_status(site)

    def edition_status(self, site: str) -> dict:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            edition = self.database.execute(
                "SELECT edition_id, label, created_at FROM editions "
                "WHERE site = ? AND status = 'draft'",
                (site,),
            ).fetchone()
            if edition is None:
                return {"site": site, "active": False, "total": 0,
                        "replaced": 0, "approved": 0, "ready": False}
            slots = self.database.execute(
                "SELECT content_id, candidate_version, action FROM edition_slots WHERE edition_id = ?",
                (int(edition["edition_id"]),),
            ).fetchall()
            replaced = sum(row["candidate_version"] is not None or row["action"] == "remove"
                           for row in slots)
            approved = 0
            removed = []
            for row in slots:
                if row["action"] == "remove":
                    removed.append(row["content_id"])
                    approved += 1
                    continue
                if row["candidate_version"] is None:
                    continue
                record, current_version = self.latest(site, row["content_id"])
                if (current_version == int(row["candidate_version"]) and not record.sample
                        and self.current_approval(site, row["content_id"]) is not None):
                    approved += 1
            total = len(slots)
            return {"site": site, "active": True,
                    "edition_id": int(edition["edition_id"]), "label": edition["label"],
                    "created_at": edition["created_at"], "total": total,
                    "replaced": replaced, "approved": approved,
                    "removed": removed,
                    "ready": total > 0 and approved == total}

    def set_slot_removal(self, site: str, content_id: str, remove: bool,
                         confirmation: str = "") -> dict:
        with self.lock:
            if remove and confirmation != "REMOVE SLOT":
                raise ContentError("slot removal confirmation did not match")
            edition = self.database.execute(
                "SELECT edition_id FROM editions WHERE site = ? AND status = 'draft'",
                (site,),
            ).fetchone()
            if edition is None:
                raise ContentError("no fortnightly refresh is in progress")
            cursor = self.database.execute(
                "UPDATE edition_slots SET action = ?, candidate_version = CASE WHEN ? THEN NULL ELSE candidate_version END "
                "WHERE edition_id = ? AND content_id = ?",
                ("remove" if remove else "replace", 1 if remove else 0,
                 int(edition["edition_id"]), content_id),
            )
            if cursor.rowcount != 1:
                raise ContentError("slot is not part of this edition")
            self.database.commit()
            return self.edition_status(site)

    def edition_manifest(self, site: str) -> dict:
        with self.lock:
            status = self.edition_status(site)
            if not status["active"]:
                raise ContentError("no fortnightly refresh is in progress")
            rows = self.database.execute(
                "SELECT content_id, candidate_version, action FROM edition_slots "
                "WHERE edition_id = ? ORDER BY content_id",
                (status["edition_id"],),
            ).fetchall()
            slots = []
            for row in rows:
                if row["action"] == "remove":
                    slots.append({"id": row["content_id"], "action": "remove",
                                  "state": "complete", "version": None})
                    continue
                if row["candidate_version"] is None:
                    current, _ = self.latest(site, row["content_id"])
                    slots.append({"id": row["content_id"], "action": "replace",
                                  "state": "awaiting replacement", "version": None,
                                  "title": current.title, "collection": current.collection})
                    continue
                candidate_version = int(row["candidate_version"])
                candidate = self.version(site, row["content_id"], candidate_version)
                approval = self.current_approval(site, row["content_id"])
                approved = approval is not None and approval.version == candidate_version
                slots.append({"id": row["content_id"], "action": "replace",
                              "state": "approved" if approved else "awaiting approval",
                              "version": candidate_version, "title": candidate.title,
                              "collection": candidate.collection,
                              "annotation_text": candidate.annotation_text,
                              "approved_hash": approval.approved_hash if approved else None})
            return {**status, "slots": slots}

    def record_publication(self, site: str, edition_id: int, release_id: str,
                           manifest_sha256: str) -> dict:
        """Close only the still-ready draft edition after origin activation."""
        with self.lock:
            manifest = self.edition_manifest(site)
            if not manifest["ready"] or manifest["edition_id"] != edition_id:
                raise ContentError("edition is no longer ready for publication")
            if not release_id.startswith(f"{site}-e{edition_id}-"):
                raise ContentError("release does not match edition")
            if len(manifest_sha256) != 64 or any(
                    character not in "0123456789abcdef" for character in manifest_sha256):
                raise ContentError("publication manifest digest is invalid")
            published_at = _now()
            self.database.execute(
                "INSERT INTO publications VALUES (?, ?, ?, ?, ?)",
                (edition_id, site, release_id, manifest_sha256, published_at),
            )
            cursor = self.database.execute(
                "UPDATE editions SET status = 'published' "
                "WHERE edition_id = ? AND site = ? AND status = 'draft'",
                (edition_id, site),
            )
            if cursor.rowcount != 1:
                self.database.rollback()
                raise ContentError("edition publication state changed")
            self.database.commit()
            return {"site": site, "edition_id": edition_id, "release_id": release_id,
                    "manifest_sha256": manifest_sha256, "published_at": published_at}

    def latest_publication(self, site: str) -> Optional[dict]:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            row = self.database.execute(
                "SELECT * FROM publications WHERE site = ? ORDER BY published_at DESC LIMIT 1",
                (site,),
            ).fetchone()
            return dict(row) if row is not None else None

    def record_rollback(self, site: str, from_release_id: str, to_release_id: str,
                        manifest_sha256: str) -> dict:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            if (from_release_id == to_release_id
                    or not from_release_id.startswith(site + "-e")
                    or not to_release_id.startswith(site + "-e")):
                raise ContentError("rollback release identity is invalid")
            if len(manifest_sha256) != 64 or any(
                    character not in "0123456789abcdef" for character in manifest_sha256):
                raise ContentError("rollback manifest digest is invalid")
            rolled_back_at = _now()
            cursor = self.database.execute(
                "INSERT INTO publication_rollbacks "
                "(site, from_release_id, to_release_id, manifest_sha256, rolled_back_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (site, from_release_id, to_release_id, manifest_sha256, rolled_back_at),
            )
            self.database.commit()
            return {"rollback_id": int(cursor.lastrowid), "site": site,
                    "from_release_id": from_release_id, "to_release_id": to_release_id,
                    "manifest_sha256": manifest_sha256,
                    "rolled_back_at": rolled_back_at}

    def latest_rollback(self, site: str) -> Optional[dict]:
        with self.lock:
            if site not in SITES:
                raise ContentError("unknown site")
            row = self.database.execute(
                "SELECT * FROM publication_rollbacks WHERE site = ? "
                "ORDER BY rollback_id DESC LIMIT 1",
                (site,),
            ).fetchone()
            return dict(row) if row is not None else None

    def copy_to_site(self, source_site: str, content_id: str, target_site: str) -> int:
        with self.lock:
            if source_site == target_site or target_site not in SITES:
                raise ContentError("copy requires two different known sites")
            record, _ = self.latest(source_site, content_id)
            copied = ContentRecord.from_dict({**asdict(record), "site": target_site})
            return self.save(copied)
