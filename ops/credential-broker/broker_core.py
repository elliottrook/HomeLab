#!/usr/bin/env python3
"""Deny-by-default state and policy core for the HomeLab AI Access Broker."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
import threading
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


RISK_CLASSES = frozenset({"green", "yellow", "red", "black"})
AUTHORIZATION_POLICY_VERSION = "m1-v1"
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
    policy_hash: str | None = None


def transactional(method):
    """Serialize policy checks and state changes across threads and processes."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._transaction():
            return method(self, *args, **kwargs)
    return wrapped


class BrokerStore:
    def __init__(self, database: str | Path, *, clock=time.time) -> None:
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self.database = str(database)
        self.clock = clock
        self.connection = sqlite3.connect(self.database, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        try:
            self._migrate()
        except BaseException:
            self.connection.close()
            raise

    @contextmanager
    def _transaction(self):
        # One connection may be shared by threads; separate service processes
        # serialize through SQLite's write reservation before reading policy.
        with self._lock:
            outer = self._transaction_depth == 0
            if outer:
                self.connection.execute("BEGIN IMMEDIATE")
            self._transaction_depth += 1
            try:
                yield
            except BaseException:
                if outer:
                    self.connection.rollback()
                raise
            else:
                if outer:
                    try:
                        self.connection.commit()
                    except BaseException:
                        self.connection.rollback()
                        raise
            finally:
                self._transaction_depth -= 1

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            BEGIN IMMEDIATE;
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
        self._ensure_column("requests", "policy_hash", "TEXT")
        self._ensure_column("requests", "approval_actor", "TEXT")
        self._ensure_column("requests", "approval_auth_time", "INTEGER")
        self._ensure_column("requests", "approval_assurance", "TEXT")
        self._ensure_column("requests", "display_json", "TEXT")
        self._ensure_column("services", "credential_type", "TEXT NOT NULL DEFAULT 'none'")
        self._ensure_column("services", "custody_identifier", "TEXT NOT NULL DEFAULT 'none'")
        self._ensure_column("services", "credential_scope", "TEXT NOT NULL DEFAULT 'synthetic-only'")
        self._ensure_column("services", "rotation_due", "TEXT NOT NULL DEFAULT 'not-applicable'")
        self._ensure_column("services", "revocation_method", "TEXT NOT NULL DEFAULT 'disable-service'")
        self._ensure_column("services", "health", "TEXT NOT NULL DEFAULT 'unknown'")
        self.connection.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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

    @transactional
    def register_agent(self, agent_id: str, unix_uid: int) -> None:
        with self._transaction():
            self.connection.execute(
                "INSERT INTO agents(agent_id,unix_uid,state,created_at) VALUES(?,?,'probation',?)",
                (agent_id, unix_uid, self._now()),
            )
            self._audit("agent.register", "operator", "probation")

    @transactional
    def set_agent_state(self, agent_id: str, state: str, *, actor: str = "operator") -> None:
        if state not in AGENT_STATES:
            raise ValueError("invalid agent state")
        with self._transaction():
            previous = self.connection.execute("SELECT state FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
            changed = self.connection.execute("UPDATE agents SET state=? WHERE agent_id=?", (state, agent_id)).rowcount
            if changed != 1:
                raise KeyError(agent_id)
            if previous["state"] != state or state in {"suspended", "retired"}:
                self.connection.execute(
                    "UPDATE requests SET status='revoked',revoked_at=? WHERE agent_id=? AND status IN ('approved','pending')",
                    (self._now(), agent_id),
                )
            self._audit("agent.state", actor, state)

    @transactional
    def register_service(
        self, service_id: str, execution_mode: str = "proxy", *, credential_type: str = "none",
        custody_identifier: str = "none", credential_scope: str = "synthetic-only",
        rotation_due: str = "not-applicable", revocation_method: str = "disable-service",
        health: str = "unknown",
    ) -> None:
        if execution_mode not in {"proxy", "dynamic", "wrapped-static"}:
            raise ValueError("invalid execution mode")
        with self._transaction():
            self.connection.execute(
                """INSERT INTO services(service_id,execution_mode,enabled,created_at,credential_type,
                       custody_identifier,credential_scope,rotation_due,revocation_method,health)
                   VALUES(?,?,1,?,?,?,?,?,?,?)""",
                (service_id, execution_mode, self._now(), credential_type, custody_identifier,
                 credential_scope, rotation_due, revocation_method, health),
            )

    @transactional
    def register_capability(self, capability: str, service_id: str, risk_class: str, *, probation_allowed: bool = False) -> None:
        if risk_class not in RISK_CLASSES:
            raise ValueError("invalid risk class")
        if risk_class == "black" and probation_allowed:
            raise ValueError("black capabilities cannot be probationary")
        with self._transaction():
            self.connection.execute(
                "INSERT INTO capabilities(capability,service_id,risk_class,probation_allowed,enabled) VALUES(?,?,?,?,1)",
                (capability, service_id, risk_class, int(probation_allowed)),
            )

    @transactional
    def grant_capability(self, agent_id: str, capability: str) -> None:
        with self._transaction():
            self.connection.execute(
                "INSERT INTO agent_capabilities(agent_id,capability) VALUES(?,?)",
                (agent_id, capability),
            )

    @transactional
    def agent_for_uid(self, unix_uid: int) -> str:
        row = self.connection.execute("SELECT agent_id FROM agents WHERE unix_uid=?", (unix_uid,)).fetchone()
        if row is None:
            raise BrokerDenied("unregistered peer identity")
        return str(row["agent_id"])

    @transactional
    def global_enabled(self) -> bool:
        return self.connection.execute("SELECT value FROM settings WHERE key='global_enabled'").fetchone()[0] == "1"

    @transactional
    def set_global_enabled(self, enabled: bool, *, actor: str = "operator") -> None:
        with self._transaction():
            self.connection.execute("UPDATE settings SET value=? WHERE key='global_enabled'", ("1" if enabled else "0",))
            if not enabled:
                self.connection.execute(
                    "UPDATE requests SET status='revoked',revoked_at=? WHERE status IN ('approved','pending')",
                    (self._now(),),
                )
            self._audit("global.enable" if enabled else "global.disable", actor, "enabled" if enabled else "disabled")

    @transactional
    def set_service_enabled(self, service_id: str, enabled: bool, *, actor: str = "operator") -> None:
        with self._transaction():
            changed = self.connection.execute(
                "UPDATE services SET enabled=? WHERE service_id=?", (int(enabled), service_id)
            ).rowcount
            if changed != 1:
                raise KeyError(service_id)
            if not enabled:
                self.connection.execute(
                    "UPDATE requests SET status='revoked',revoked_at=? WHERE status IN ('approved','pending') AND capability IN (SELECT capability FROM capabilities WHERE service_id=?)",
                    (self._now(), service_id),
                )
            self._audit("service.enable" if enabled else "service.disable", actor, "enabled" if enabled else "disabled")

    @transactional
    def revoke_request(self, request_id: str, *, actor: str = "operator") -> None:
        record = self.get_request(request_id)
        if record.status not in {"pending", "approved"}:
            raise BrokerDenied("request is not active")
        with self._transaction():
            self.connection.execute(
                "UPDATE requests SET status='revoked',revoked_at=? WHERE request_id=?",
                (self._now(), request_id),
            )
            self._audit("request.revoke", actor, "revoked", record)

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

    def _authorize_capability(self, agent_id: str, capability: str):
        if not self.global_enabled():
            raise BrokerDenied("global emergency disable is active")
        row = self.connection.execute(
            """SELECT a.state,c.risk_class,c.probation_allowed,c.enabled AS capability_enabled,s.enabled AS service_enabled,
                      c.service_id,s.execution_mode,
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

        return row

    def _reauthorize_request(self, record: RequestRecord) -> None:
        current = self._authorize_capability(record.agent_id, record.capability)
        if record.policy_hash is None or self._policy_hash(current) != record.policy_hash:
            raise BrokerDenied("capability policy changed or is unbound; create a new request")

    @staticmethod
    def _policy_hash(policy: sqlite3.Row) -> str:
        return canonical_payload_hash({"version": AUTHORIZATION_POLICY_VERSION, **dict(policy)})

    @transactional
    def create_request(
        self, agent_id: str, capability: str, payload: Mapping[str, Any], *,
        ttl_seconds: int = 300, display: Mapping[str, Any] | None = None,
    ) -> RequestRecord:
        if not self.global_enabled():
            raise BrokerDenied("global emergency disable is active")
        if not 1 <= ttl_seconds <= 900:
            raise BrokerDenied("request TTL is outside policy")
        row = self._authorize_capability(agent_id, capability)

        now = self._now()
        status = "approved" if row["risk_class"] == "green" else "pending"
        record = RequestRecord(
            request_id=str(uuid.uuid4()), agent_id=agent_id, capability=capability,
            risk_class=str(row["risk_class"]), payload_hash=canonical_payload_hash(payload),
            status=status, expires_at=now + ttl_seconds,
            policy_hash=self._policy_hash(row),
        )
        display_json = self._display_json(display)
        with self._transaction():
            self.connection.execute(
                "INSERT INTO requests(request_id,agent_id,capability,risk_class,payload_hash,status,created_at,expires_at,approved_at,display_json,policy_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (record.request_id, agent_id, capability, record.risk_class, record.payload_hash, status, now, record.expires_at, now if status == "approved" else None, display_json, record.policy_hash),
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
        if auth_time is not None and type(auth_time) is not int:
            raise BrokerDenied("authentication time must be an integer")
        with self._transaction():
            record = self.get_request(request_id)
            if record.risk_class not in {"yellow", "red"} or record.status != "pending":
                raise BrokerDenied("request is not approval-eligible")
            if record.payload_hash != expected_payload_hash:
                raise BrokerDenied("approval payload binding mismatch")
            expired = self._now() >= record.expires_at
            if expired:
                self.expire_request(request_id)
            else:
                self._reauthorize_request(record)
                if record.risk_class == "red":
                    if assurance != "passkey" or type(auth_time) is not int:
                        raise BrokerDenied("red approval requires passkey assurance")
                    age = self._now() - auth_time
                    if age < 0 or age > red_freshness_seconds:
                        raise BrokerDenied("red approval requires fresh authentication")
                self.connection.execute(
                    "UPDATE requests SET status='approved',approved_at=?,approval_actor=?,approval_auth_time=?,approval_assurance=? WHERE request_id=?",
                    (self._now(), actor, auth_time, assurance, request_id),
                )
                self._audit("request.approve", actor, "approved", record)
        if expired:
            raise BrokerDenied("request expired")

    @transactional
    def deny_request(self, request_id: str, expected_payload_hash: str, *, actor: str = "human-approval") -> None:
        record = self.get_request(request_id)
        if record.status != "pending":
            raise BrokerDenied("request is not pending")
        if record.payload_hash != expected_payload_hash:
            raise BrokerDenied("denial payload binding mismatch")
        with self._transaction():
            self.connection.execute(
                "UPDATE requests SET status='denied',approval_actor=? WHERE request_id=?",
                (actor, request_id),
            )
            self._audit("request.deny", actor, "denied", record)

    @transactional
    def pending_requests(self) -> list[dict[str, Any]]:
        now = self._now()
        with self._transaction():
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

    def consume_request(self, request_id: str, payload: Mapping[str, Any], *, agent_id: str) -> RequestRecord:
        # Identity comes from authenticated transport, never request JSON or the
        # stored owner as a fallback. No external tool runs inside this lock.
        with self._transaction():
            if not self.global_enabled():
                raise BrokerDenied("global emergency disable is active")
            record = self.get_request(request_id)
            if record.agent_id != agent_id:
                raise BrokerDenied("request belongs to another agent")
            if record.status != "approved":
                raise BrokerDenied("request is not approved")
            expired = self._now() >= record.expires_at
            if expired:
                self.expire_request(request_id)
            else:
                self._reauthorize_request(record)
                if record.payload_hash != canonical_payload_hash(payload):
                    raise BrokerDenied("payload changed after authorization")
                changed = self.connection.execute(
                    "UPDATE requests SET status='consumed',consumed_at=? WHERE request_id=? AND status='approved'",
                    (self._now(), request_id),
                ).rowcount
                if changed != 1:
                    raise BrokerDenied("request is not approved")
                consumed = self.get_request(request_id)
                self._audit("request.consume", agent_id, "consumed", consumed)
        # Commit expiry before reporting the denial; it remains terminal.
        if expired:
            raise BrokerDenied("request expired")
        return consumed

    @transactional
    def expire_request(self, request_id: str) -> None:
        with self._transaction():
            self.connection.execute("UPDATE requests SET status='expired' WHERE request_id=? AND status IN ('pending','approved')", (request_id,))

    @transactional
    def get_request(self, request_id: str) -> RequestRecord:
        row = self.connection.execute(
            "SELECT request_id,agent_id,capability,risk_class,payload_hash,status,expires_at,policy_hash FROM requests WHERE request_id=?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return RequestRecord(**dict(row))

    @transactional
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
        if rows and rows[0]["state"] in {"suspended", "retired"}:
            raise BrokerDenied("agent is not active")
        return [dict(row) for row in rows if row["state"] != "probation" or row["probation_allowed"]]

    @transactional
    def audit_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("SELECT * FROM audit ORDER BY sequence")]

    @transactional
    def management_snapshot(self) -> dict[str, Any]:
        agents = [dict(row) for row in self.connection.execute(
            """SELECT a.agent_id,a.unix_uid,a.state,a.created_at,
                      COUNT(ac.capability) AS capability_count
                 FROM agents a LEFT JOIN agent_capabilities ac ON ac.agent_id=a.agent_id
                GROUP BY a.agent_id ORDER BY a.agent_id"""
        )]
        for agent in agents:
            agent["capabilities"] = [dict(row) for row in self.connection.execute(
                """SELECT c.capability,c.risk_class,c.service_id
                     FROM agent_capabilities ac JOIN capabilities c ON c.capability=ac.capability
                    WHERE ac.agent_id=? ORDER BY c.capability""", (agent["agent_id"],)
            )]
        services = [dict(row) for row in self.connection.execute(
            """SELECT s.service_id,s.execution_mode,s.enabled,s.created_at,s.credential_type,
                      s.custody_identifier,s.credential_scope,s.rotation_due,s.revocation_method,s.health,
                      COUNT(c.capability) AS capability_count
                 FROM services s LEFT JOIN capabilities c ON c.service_id=s.service_id
                GROUP BY s.service_id ORDER BY s.service_id"""
        )]
        active = [dict(row) for row in self.connection.execute(
            """SELECT request_id,agent_id,capability,risk_class,status,created_at,expires_at
                 FROM requests WHERE status IN ('pending','approved') ORDER BY created_at"""
        )]
        return {"global_enabled": self.global_enabled(), "agents": agents,
                "services": services, "active_requests": active}

    @transactional
    def request_history(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 200:
            raise BrokerDenied("history limit is outside policy")
        rows = self.connection.execute(
            """SELECT request_id,agent_id,capability,risk_class,payload_hash,status,
                      created_at,expires_at,approved_at,consumed_at,revoked_at,
                      approval_actor,approval_auth_time,approval_assurance,display_json
                 FROM requests ORDER BY created_at DESC LIMIT ?""", (limit,)
        )
        result = []
        for row in rows:
            item = dict(row)
            item["display"] = json.loads(item.pop("display_json") or "{}")
            result.append(item)
        return result

    @transactional
    def audit_search(self, *, limit: int = 100, event: str | None = None) -> list[dict[str, Any]]:
        if not 1 <= limit <= 200:
            raise BrokerDenied("audit limit is outside policy")
        if event is not None and (not event or len(event) > 64 or not re.fullmatch(r"[a-z.]+", event)):
            raise BrokerDenied("invalid audit event filter")
        if event:
            rows = self.connection.execute(
                "SELECT * FROM audit WHERE event=? ORDER BY sequence DESC LIMIT ?", (event, limit)
            )
        else:
            rows = self.connection.execute("SELECT * FROM audit ORDER BY sequence DESC LIMIT ?", (limit,))
        return [dict(row) for row in rows]
