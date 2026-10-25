#!/usr/bin/env python3
"""Read-only pre/post verifier for the bounded M1 Red ceremony.

The checker opens an existing broker SQLite database in read-only mode.  It
never creates, migrates, checkpoints, or modifies the database.  Its JSON
output contains policy identifiers and counts only; it does not emit request
display text or payloads.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


AGENT = "agent-hermes"
CAPABILITY = "broker.synthetic.network-change"
SERVICE = "synthetic"
TERMINAL = {"consumed", "denied", "expired", "revoked"}
HASH = re.compile(r"^[a-f0-9]{64}$")


class CheckError(RuntimeError):
    pass


def connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise CheckError("database is not a regular file")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def one(connection: sqlite3.Connection, query: str, values: tuple[Any, ...] = ()) -> sqlite3.Row:
    rows = connection.execute(query, values).fetchall()
    if len(rows) != 1:
        raise CheckError(f"expected exactly one row, got {len(rows)}")
    return rows[0]


def snapshot(path: Path) -> dict[str, Any]:
    connection = connect_read_only(path)
    try:
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise CheckError("database integrity check failed")
        agent = one(connection, "SELECT agent_id,unix_uid,state FROM agents WHERE agent_id=?", (AGENT,))
        service = one(
            connection,
            "SELECT service_id,execution_mode,enabled,credential_type,custody_identifier,"
            "credential_scope,rotation_due,revocation_method,health FROM services WHERE service_id=?",
            (SERVICE,),
        )
        capability = one(
            connection,
            "SELECT capability,service_id,risk_class,probation_allowed,enabled FROM capabilities WHERE capability=?",
            (CAPABILITY,),
        )
        grant = one(
            connection,
            "SELECT COUNT(*) AS count FROM agent_capabilities WHERE agent_id=? AND capability=?",
            (AGENT, CAPABILITY),
        )
        global_enabled = one(connection, "SELECT value FROM settings WHERE key='global_enabled'")["value"]
        counts = {
            table: int(one(connection, f"SELECT COUNT(*) AS count FROM {table}")["count"])
            for table in ("agents", "services", "capabilities", "agent_capabilities", "requests", "audit")
        }
        active = int(one(
            connection,
            "SELECT COUNT(*) AS count FROM requests WHERE status IN ('pending','approved')",
        )["count"])
        max_audit = int(one(connection, "SELECT COALESCE(MAX(sequence),0) AS value FROM audit")["value"])
        max_request_created = int(one(
            connection,
            "SELECT COALESCE(MAX(created_at),0) AS value FROM requests",
        )["value"])
        return {
            "schema": 1,
            "integrity": "ok",
            "agent": dict(agent),
            "service": dict(service),
            "capability": dict(capability),
            "grant_count": int(grant["count"]),
            "global_enabled": global_enabled,
            "counts": counts,
            "active_request_count": active,
            "max_audit_sequence": max_audit,
            "max_request_created_at": max_request_created,
        }
    finally:
        connection.close()


def validate_pre(value: dict[str, Any]) -> None:
    failures = []
    if value.get("integrity") != "ok": failures.append("integrity")
    if value.get("active_request_count") != 0: failures.append("active-requests")
    if value.get("global_enabled") != "1": failures.append("global-disabled")
    if value.get("agent", {}).get("state") != "operator": failures.append("agent-state")
    if value.get("service", {}).get("enabled") != 1: failures.append("service-disabled")
    capability = value.get("capability", {})
    if capability.get("service_id") != SERVICE: failures.append("capability-service")
    if capability.get("risk_class") != "red": failures.append("capability-risk")
    if capability.get("enabled") != 1: failures.append("capability-disabled")
    if value.get("grant_count") != 1: failures.append("capability-grant")
    if failures:
        raise CheckError("precheck failed: " + ",".join(failures))


def load_baseline(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise CheckError("baseline schema is invalid")
    validate_pre(value)
    return value


def validate_post(path: Path, baseline: dict[str, Any], request_id: str, payload_hash: str) -> dict[str, Any]:
    if not request_id or not HASH.fullmatch(payload_hash):
        raise CheckError("request id or payload hash is invalid")
    after = snapshot(path)
    validate_pre(after)
    stable_keys = ("agent", "service", "capability", "grant_count", "global_enabled")
    failures = [f"changed-{key}" for key in stable_keys if after[key] != baseline[key]]
    expected_counts = dict(baseline["counts"])
    expected_counts["requests"] += 1
    expected_counts["audit"] += 4
    if after["counts"] != expected_counts: failures.append("unexpected-table-delta")
    if after["active_request_count"] != 0: failures.append("active-request-remains")
    if after["max_audit_sequence"] != baseline["max_audit_sequence"] + 4:
        failures.append("unexpected-audit-sequence")

    connection = connect_read_only(path)
    try:
        request = one(
            connection,
            "SELECT request_id,agent_id,capability,risk_class,payload_hash,status,created_at,expires_at,"
            "approved_at,consumed_at,revoked_at,approval_actor,approval_auth_time,approval_assurance "
            "FROM requests WHERE request_id=?",
            (request_id,),
        )
        if request["agent_id"] != AGENT: failures.append("request-agent")
        if request["capability"] != CAPABILITY: failures.append("request-capability")
        if request["risk_class"] != "red": failures.append("request-risk")
        if request["payload_hash"] != payload_hash: failures.append("request-payload-hash")
        if request["status"] != "consumed": failures.append("request-status")
        if request["revoked_at"] is not None: failures.append("request-revoked")
        if request["approved_at"] is None or request["consumed_at"] is None:
            failures.append("request-timestamps")
        else:
            if request["approval_assurance"] != "passkey": failures.append("request-assurance")
            if type(request["approval_auth_time"]) is not int: failures.append("request-auth-time")
            elif request["approved_at"] - request["approval_auth_time"] not in range(0, 121):
                failures.append("request-auth-freshness")
            if not (request["created_at"] <= request["approved_at"] <= request["consumed_at"] < request["expires_at"]):
                failures.append("request-order")

        rows = [dict(row) for row in connection.execute(
            "SELECT sequence,event,actor,request_id,capability,risk_class,payload_hash,outcome "
            "FROM audit WHERE sequence>? ORDER BY sequence",
            (baseline["max_audit_sequence"],),
        )]
        events = [row["event"] for row in rows]
        if events != ["request.create", "request.approve", "request.consume", "agent.state"]:
            failures.append("audit-events")
        if len(rows) == 4:
            for row in rows[:3]:
                if row["request_id"] != request_id or row["capability"] != CAPABILITY or row["risk_class"] != "red" or row["payload_hash"] != payload_hash:
                    failures.append("audit-request-binding")
                    break
            if rows[0]["actor"] != AGENT or rows[2]["actor"] != AGENT:
                failures.append("audit-agent-actors")
            if rows[1]["actor"] != request["approval_actor"] or not HASH.fullmatch(rows[1]["actor"] or ""):
                failures.append("audit-approval-actor")
            if rows[3]["actor"] != request["approval_actor"] or rows[3]["outcome"] != "operator":
                failures.append("audit-management-binding")
            if any(rows[index]["outcome"] != outcome for index, outcome in enumerate(("pending", "approved", "consumed", "operator"))):
                failures.append("audit-outcomes")
    finally:
        connection.close()

    if failures:
        raise CheckError("postcheck failed: " + ",".join(dict.fromkeys(failures)))
    return {
        "schema": 1,
        "decision": "pass",
        "request_id": request_id,
        "payload_hash": payload_hash,
        "request_status": "consumed",
        "audit_sequence_start": baseline["max_audit_sequence"] + 1,
        "audit_sequence_end": after["max_audit_sequence"],
        "audit_events": ["request.create", "request.approve", "request.consume", "agent.state"],
        "active_request_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    sub = parser.add_subparsers(dest="phase", required=True)
    pre = sub.add_parser("pre")
    pre.add_argument("--output", required=True, type=Path)
    post = sub.add_parser("post")
    post.add_argument("--baseline", required=True, type=Path)
    post.add_argument("--request-id", required=True)
    post.add_argument("--payload-hash", required=True)
    args = parser.parse_args()
    try:
        if args.phase == "pre":
            result = snapshot(args.database)
            validate_pre(result)
            args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
            args.output.chmod(0o600)
        else:
            result = validate_post(args.database, load_baseline(args.baseline), args.request_id, args.payload_hash)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (CheckError, json.JSONDecodeError, OSError, sqlite3.Error) as error:
        print(json.dumps({"schema": 1, "decision": "no_go", "error": str(error)}, sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
