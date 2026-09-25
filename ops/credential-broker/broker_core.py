#!/usr/bin/env python3
"""Deny-by-default state and policy core for the HomeLab AI Access Broker."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


RISK_CLASSES = frozenset({"green", "yellow", "red", "black"})
AGENT_STATES = frozenset({"probation", "observer", "operator", "specialist", "orchestrator", "suspended", "retired"})
TERMINAL_REQUEST_STATES = frozenset({"consumed", "denied", "expired", "revoked"})
DISPLAY_FIELDS = frozenset({"reason", "target", "effect", "rollback"})
DISPLAY_SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|secret|token|api[_ -]?key|private[_ -]?key|authorization|bearer)"
)


class BrokerDenied(RuntimeError):
    """A request failed closed at the broker policy boundary."""


def canonical_payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RequestRecord:
    request_id: str
    agent_id: str
    capability: str
    risk_class: str
    payload_hash: str
    status: str
    expires_at: int


class BrokerStore:
    def __init__(self, database: str | Path, *, clock=time.time) -> None:
        self.database = str(database)
        self.clock = clock
        self.connection = sqlite3.connect(self.database, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            INSERT OR IGNORE INTO settings(key, value) VALUES ('global_enabled', '1');

            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                unix_uid INTEGER NOT NULL UNIQUE,
                state TEXT NOT NULL CHECK(state IN ('probation','observer','operator','specialist','orchestrator','suspended','retired')),
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS services (
                service_id TEXT PRIMARY KEY,
                execution_mode TEXT NOT NULL,
                enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS capabilities (
                capability TEXT PRIMARY KEY,
                service_id TEXT NOT NULL REFERENCES services(service_id),
                risk_class TEXT NOT NULL CHECK(risk_class IN ('green','yellow','red','black')),
                probation_allowed INTEGER NOT NULL CHECK(probation_allowed IN (0,1)),
                enabled INTEGER NOT NULL CHECK(enabled IN (0,1))
            );
            CREATE TABLE IF NOT EXISTS agent_capabilities (
                agent_id TEXT NOT NULL REFERENCES agents(agent_id),
                capability TEXT NOT NULL REFERENCES capabilities(capability),
                PRIMARY KEY(agent_id, capability)
            );
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL REFERENCES agents(agent_id),
                capability TEXT NOT NULL REFERENCES capabilities(capability),
                risk_class TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                approved_at INTEGER,
                consumed_at INTEGER,
                revoked_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS audit (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at INTEGER NOT NULL,
                event TEXT NOT NULL,
                actor TEXT NOT NULL,
                request_id TEXT,
                capability TEXT,
                risk_class TEXT,
                payload_hash TEXT,
                outcome TEXT NOT NULL
            );
            """
        )
        self.connection.commit()
        self._ensure_column("requests", "approval_actor", "TEXT")
        self._ensure_column("requests", "approval_auth_time", "INTEGER")
        self._ensure_column("requests", "approval_assurance", "TEXT")
        self._ensure_column("requests", "display_json", "TEXT")

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            self.connection.commit()

    def _now(self) -> int:
        return int(self.clock())

    def _audit(self, event: str, actor: str, outcome: str, request: RequestRecord | None = None) -> None:
        self.connection.execute(
            "INSERT INTO audit(occurred_at,event,actor,request_id,capability,risk_class,payload_hash,outcome) VALUES(?,?,?,?,?,?,?,?)",
            (
                self._now(), event, actor,
                request.request_id if request else None,
                request.capability if request else None,
                request.risk_class if request else None,
                request.payload_hash if request else None,
                outcome,
            ),
        )

    def register_agent(self, agent_id: str, unix_uid: int) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO agents(agent_id,unix_uid,state,created_at) VALUES(?,?,'probation',?)",
                (agent_id, unix_uid, self._now()),
            )
            self._audit("agent.register", "operator", "probation")

    def set_agent_state(self, agent_id: str, state: str) -> None:
        if state not in AGENT_STATES:
            raise ValueError("invalid agent state")
        with self.connection:
            changed = self.connection.execute("UPDATE agents SET state=? WHERE agent_id=?", (state, agent_id)).rowcount
            if changed != 1:
                raise KeyError(agent_id)
            if state in {"suspended", "retired"}:
                self.connection.execute(
                    "UPDATE requests SET status='revoked',revoked_at=? WHERE agent_id=? AND status IN ('approved','pending')",
                    (self._now(), agent_id),
                )
            self._audit("agent.state", "operator", state)

    def register_service(self, service_id: str, execution_mode: str = "proxy") -> None:
        if execution_mode not in {"proxy", "dynamic", "wrapped-static"}:
            raise ValueError("invalid execution mode")
        with self.connection:
            self.connection.execute(
                "INSERT INTO services(service_id,execution_mode,enabled,created_at) VALUES(?,?,1,?)",
                (service_id, execution_mode, self._now()),
            )

    def register_capability(self, capability: str, service_id: str, risk_class: str, *, probation_allowed: bool = False) -> None:
        if risk_class not in RISK_CLASSES:
            raise ValueError("invalid risk class")
        if risk_class == "black" and probation_allowed:
            raise ValueError("black capabilities cannot be probationary")
        with self.connection:
            self.connection.execute(
                "INSERT INTO capabilities(capability,service_id,risk_class,probation_allowed,enabled) VALUES(?,?,?,?,1)",
                (capability, service_id, risk_class, int(probation_allowed)),
            )

    def grant_capability(self, agent_id: str, capability: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO agent_capabilities(agent_id,capability) VALUES(?,?)",
                (agent_id, capability),
            )

    def agent_for_uid(self, unix_uid: int) -> str:
        row = self.connection.execute("SELECT agent_id FROM agents WHERE unix_uid=?", (unix_uid,)).fetchone()
        if row is None:
            raise BrokerDenied("unregistered peer identity")
        return str(row["agent_id"])

    def global_enabled(self) -> bool:
        return self.connection.execute("SELECT value FROM settings WHERE key='global_enabled'").fetchone()[0] == "1"

    def set_global_enabled(self, enabled: bool) -> None:
        with self.connection:
            self.connection.execute("UPDATE settings SET value=? WHERE key='global_enabled'", ("1" if enabled else "0",))
            if not enabled:
                self.connection.execute(
                    "UPDATE requests SET status='revoked',revoked_at=? WHERE status IN ('approved','pending')",
                    (self._now(),),
                )
            self._audit("global.enable" if enabled else "global.disable", "operator", "enabled" if enabled else "disabled")

    @staticmethod
    def _display_json(display: Mapping[str, Any] | None) -> str:
        if display is None:
            return "{}"
        if not isinstance(display, Mapping) or set(display) - DISPLAY_FIELDS:
            raise BrokerDenied("approval display contains unsupported fields")
        cleaned: dict[str, str] = {}
        for key, value in display.items():
            if not isinstance(value, str) or not value.strip() or len(value) > 512:
                raise BrokerDenied("approval display values must be non-empty text up to 512 characters")
            if DISPLAY_SECRET_PATTERN.search(key) or DISPLAY_SECRET_PATTERN.search(value):
                raise BrokerDenied("approval display may not contain credential material")
            cleaned[key] = value.strip()
        return json.dumps(cleaned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def create_request(
        self, agent_id: str, capability: str, payload: Mapping[str, Any], *,
        ttl_seconds: int = 300, display: Mapping[str, Any] | None = None,
    ) -> RequestRecord:
        if not self.global_enabled():
            raise BrokerDenied("global emergency disable is active")
        if not 1 <= ttl_seconds <= 900:
            raise BrokerDenied("request TTL is outside policy")
        row = self.connection.execute(
            """SELECT a.state,c.risk_class,c.probation_allowed,c.enabled AS capability_enabled,s.enabled AS service_enabled,
                      EXISTS(SELECT 1 FROM agent_capabilities ac WHERE ac.agent_id=a.agent_id AND ac.capability=c.capability) AS granted
               FROM agents a CROSS JOIN capabilities c JOIN services s ON s.service_id=c.service_id
              WHERE a.agent_id=? AND c.capability=?""",
            (agent_id, capability),
        ).fetchone()
        if row is None or not row["granted"] or not row["capability_enabled"] or not row["service_enabled"]:
            raise BrokerDenied("capability is not granted and enabled")
        if row["state"] in {"suspended", "retired"}:
            raise BrokerDenied("agent is not active")
        if row["state"] == "probation" and not row["probation_allowed"]:
            raise BrokerDenied("capability is prohibited during probation")
        if row["risk_class"] == "black":
            raise BrokerDenied("black capabilities are never delegated")

        now = self._now()
        status = "approved" if row["risk_class"] == "green" else "pending"
        record = RequestRecord(
            request_id=str(uuid.uuid4()), agent_id=agent_id, capability=capability,
            risk_class=str(row["risk_class"]), payload_hash=canonical_payload_hash(payload),
            status=status, expires_at=now + ttl_seconds,
        )
        display_json = self._display_json(display)
        with self.connection:
            self.connection.execute(
                "INSERT INTO requests(request_id,agent_id,capability,risk_class,payload_hash,status,created_at,expires_at,approved_at,display_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (record.request_id, agent_id, capability, record.risk_class, record.payload_hash, status, now, record.expires_at, now if status == "approved" else None, display_json),
            )
            self._audit("request.create", agent_id, status, record)
        return record

    def approve_request(
        self,
        request_id: str,
        expected_payload_hash: str,
        *,
        actor: str = "human-approval",
        auth_time: int | None = None,
        assurance: str = "authenticated",
        red_freshness_seconds: int = 120,
    ) -> None:
        record = self.get_request(request_id)
        if record.risk_class not in {"yellow", "red"} or record.status != "pending":
            raise BrokerDenied("request is not approval-eligible")
        if record.payload_hash != expected_payload_hash:
            raise BrokerDenied("approval payload binding mismatch")
        if self._now() >= record.expires_at:
            self.expire_request(request_id)
            raise BrokerDenied("request expired")
        if record.risk_class == "red":
            if assurance != "passkey" or auth_time is None:
                raise BrokerDenied("red approval requires passkey assurance")
            age = self._now() - int(auth_time)
            if age < 0 or age > red_freshness_seconds:
                raise BrokerDenied("red approval requires fresh authentication")
        with self.connection:
            self.connection.execute(
                "UPDATE requests SET status='approved',approved_at=?,approval_actor=?,approval_auth_time=?,approval_assurance=? WHERE request_id=?",
                (self._now(), actor, auth_time, assurance, request_id),
            )
            self._audit("request.approve", actor, "approved", record)

    def deny_request(self, request_id: str, expected_payload_hash: str, *, actor: str = "human-approval") -> None:
        record = self.get_request(request_id)
        if record.status != "pending":
            raise BrokerDenied("request is not pending")
        if record.payload_hash != expected_payload_hash:
            raise BrokerDenied("denial payload binding mismatch")
        with self.connection:
            self.connection.execute(
                "UPDATE requests SET status='denied',approval_actor=? WHERE request_id=?",
                (actor, request_id),
            )
            self._audit("request.deny", actor, "denied", record)

    def pending_requests(self) -> list[dict[str, Any]]:
        now = self._now()
        with self.connection:
            self.connection.execute(
                "UPDATE requests SET status='expired' WHERE status='pending' AND expires_at<=?",
                (now,),
            )
        result: list[dict[str, Any]] = []
        for row in self.connection.execute(
            "SELECT request_id,agent_id,capability,risk_class,payload_hash,created_at,expires_at,display_json FROM requests WHERE status='pending' ORDER BY created_at"
        ):
            item = dict(row)
            item["display"] = json.loads(item.pop("display_json") or "{}")
            result.append(item)
        return result

    def consume_request(self, request_id: str, payload: Mapping[str, Any]) -> RequestRecord:
        if not self.global_enabled():
            raise BrokerDenied("global emergency disable is active")
        record = self.get_request(request_id)
        if record.status != "approved":
            raise BrokerDenied("request is not approved")
        if self._now() >= record.expires_at:
            self.expire_request(request_id)
            raise BrokerDenied("request expired")
        if record.payload_hash != canonical_payload_hash(payload):
            raise BrokerDenied("payload changed after authorization")
        with self.connection:
            self.connection.execute("UPDATE requests SET status='consumed',consumed_at=? WHERE request_id=?", (self._now(), request_id))
            consumed = self.get_request(request_id)
            self._audit("request.consume", record.agent_id, "consumed", consumed)
        return consumed

    def expire_request(self, request_id: str) -> None:
        with self.connection:
            self.connection.execute("UPDATE requests SET status='expired' WHERE request_id=? AND status IN ('pending','approved')", (request_id,))

    def get_request(self, request_id: str) -> RequestRecord:
        row = self.connection.execute(
            "SELECT request_id,agent_id,capability,risk_class,payload_hash,status,expires_at FROM requests WHERE request_id=?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return RequestRecord(**dict(row))

    def discover_capabilities(self, agent_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """SELECT c.capability,c.risk_class,s.service_id,s.execution_mode,a.state,c.probation_allowed
                 FROM agents a JOIN agent_capabilities ac ON ac.agent_id=a.agent_id
                 JOIN capabilities c ON c.capability=ac.capability
                 JOIN services s ON s.service_id=c.service_id
                WHERE a.agent_id=? AND c.enabled=1 AND s.enabled=1 AND c.risk_class!='black'
                ORDER BY c.capability""",
            (agent_id,),
        ).fetchall()
        return [dict(row) for row in rows if row["state"] != "probation" or row["probation_allowed"]]

    def audit_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("SELECT * FROM audit ORDER BY sequence")]
