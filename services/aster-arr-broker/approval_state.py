"""Persistent, server-side approvals for one narrowly bound ARR action."""

from __future__ import annotations

import base64
import json
import os
import re
import stat
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from persistence import atomic_json_write
from proposal import CANDIDATE_REF, OPERATION


APPROVAL_TTL = timedelta(minutes=2)
APPROVAL_REF = re.compile(r"approval-[a-z2-7]{16}")


class ApprovalStateError(ValueError):
    """Approval state is malformed or cannot safely satisfy a request."""


@dataclass(frozen=True)
class ApprovalRecord:
    reference: str
    candidate_ref: str
    operation: str
    issued_at: datetime
    expires_at: datetime
    nonreversible_accepted: bool
    consumed_at: datetime | None = None


def _time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ApprovalStateError("invalid approval timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApprovalStateError("invalid approval timestamp") from exc
    if parsed.tzinfo is None:
        raise ApprovalStateError("invalid approval timestamp")
    return parsed.astimezone(timezone.utc)


def _render_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_approvals(path: Path) -> dict[str, ApprovalRecord]:
    if not path.exists():
        return {}
    try:
        status = path.lstat()
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_mode & 0o077
            or status.st_size > 65_536
        ):
            raise ApprovalStateError("approval state has unsafe file metadata")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ApprovalStateError("approval state is unavailable") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "approvals"}:
        raise ApprovalStateError("approval state has an invalid schema")
    if payload["schema_version"] != 1 or not isinstance(payload["approvals"], list):
        raise ApprovalStateError("approval state has an invalid schema")

    result: dict[str, ApprovalRecord] = {}
    fields = {
        "reference", "candidate_ref", "operation", "issued_at", "expires_at",
        "nonreversible_accepted", "consumed_at",
    }
    for item in payload["approvals"]:
        if not isinstance(item, dict) or set(item) != fields:
            raise ApprovalStateError("approval state has an invalid record")
        reference = item["reference"]
        candidate_ref = item["candidate_ref"]
        if (
            not isinstance(reference, str)
            or not APPROVAL_REF.fullmatch(reference)
            or not isinstance(candidate_ref, str)
            or not CANDIDATE_REF.fullmatch(candidate_ref)
            or item["operation"] != OPERATION
            or item["nonreversible_accepted"] is not True
        ):
            raise ApprovalStateError("approval state has an invalid record")
        consumed_at = None if item["consumed_at"] is None else _time(item["consumed_at"])
        record = ApprovalRecord(
            reference=reference,
            candidate_ref=candidate_ref,
            operation=OPERATION,
            issued_at=_time(item["issued_at"]),
            expires_at=_time(item["expires_at"]),
            nonreversible_accepted=True,
            consumed_at=consumed_at,
        )
        if record.expires_at <= record.issued_at or record.expires_at - record.issued_at > APPROVAL_TTL:
            raise ApprovalStateError("approval state has an invalid lifetime")
        if consumed_at is not None and consumed_at < record.issued_at:
            raise ApprovalStateError("approval state has an invalid consumption time")
        if reference in result:
            raise ApprovalStateError("approval state contains a duplicate")
        result[reference] = record
    return result


def store_approvals(path: Path, approvals: dict[str, ApprovalRecord]) -> None:
    payload = {
        "schema_version": 1,
        "approvals": [
            {
                "reference": item.reference,
                "candidate_ref": item.candidate_ref,
                "operation": item.operation,
                "issued_at": _render_time(item.issued_at),
                "expires_at": _render_time(item.expires_at),
                "nonreversible_accepted": item.nonreversible_accepted,
                "consumed_at": None if item.consumed_at is None else _render_time(item.consumed_at),
            }
            for item in sorted(approvals.values(), key=lambda value: value.issued_at)
        ],
    }
    atomic_json_write(path, payload)


def new_approval(candidate_ref: str, *, now: datetime | None = None) -> ApprovalRecord:
    if not isinstance(candidate_ref, str) or not CANDIDATE_REF.fullmatch(candidate_ref):
        raise ApprovalStateError("candidate reference is invalid")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    token = base64.b32encode(os.urandom(10)).decode("ascii").lower().rstrip("=")
    return ApprovalRecord(
        reference=f"approval-{token}",
        candidate_ref=candidate_ref,
        operation=OPERATION,
        issued_at=current,
        expires_at=current + APPROVAL_TTL,
        nonreversible_accepted=True,
    )


def pending_approval(
    approvals: dict[str, ApprovalRecord], candidate_ref: str, *, now: datetime
) -> ApprovalRecord:
    matches = [
        item
        for item in approvals.values()
        if item.candidate_ref == candidate_ref
        and item.operation == OPERATION
        and item.nonreversible_accepted
        and item.consumed_at is None
        and item.issued_at <= now
        and item.expires_at > now
    ]
    if len(matches) != 1:
        raise ApprovalStateError("exactly one fresh task-specific approval is required")
    return matches[0]


def consume_approval(record: ApprovalRecord, *, now: datetime) -> ApprovalRecord:
    if record.consumed_at is not None or record.expires_at <= now:
        raise ApprovalStateError("approval is expired or already consumed")
    return replace(record, consumed_at=now)
