"""Persistent, one-attempt execution coordinator for the first ARR repair."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from approval_state import (
    ApprovalRecord,
    ApprovalStateError,
    consume_approval,
    load_approvals,
    new_approval,
    pending_approval,
    store_approvals,
)
from broker import Approval, Broker, RadarrQueueAdapter
from persistence import append_json_line, state_lock
from proposal import OPERATION, ProposalError, parse_report_time
from state import load_candidates


AUDIT_RESULTS = {
    "attempt_started",
    "already_absent",
    "dismissed",
    "inspection_failed",
    "outcome_unknown",
    "postcondition_failed",
    "precondition_refused",
}


class ExecutionConflict(ProposalError):
    """The approved target changed before the one permitted attempt."""


def _now(value: datetime | None = None) -> datetime:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc)


def _audit(request: dict[str, object], result: str, now: datetime) -> dict[str, object]:
    if result not in AUDIT_RESULTS:
        raise ValueError("unsupported audit result")
    candidate_ref = request.get("candidate_ref")
    if not isinstance(candidate_ref, str):
        raise ValueError("invalid audit candidate")
    report_age = int((now - parse_report_time(request.get("report_generated_at"))).total_seconds())
    return {
        "operation": OPERATION,
        "candidate_ref": candidate_ref,
        "decision": "approved_execute",
        "report_age_seconds": report_age,
        "result": result,
        "at": now.isoformat(),
    }


def append_audit(path: Path, record: dict[str, object]) -> None:
    required = {
        "operation", "candidate_ref", "decision", "report_age_seconds", "result", "at"
    }
    if set(record) != required or record["operation"] != OPERATION:
        raise ValueError("invalid audit schema")
    if record["decision"] != "approved_execute" or record["result"] not in AUDIT_RESULTS:
        raise ValueError("invalid audit decision")
    if (
        not isinstance(record["report_age_seconds"], int)
        or isinstance(record["report_age_seconds"], bool)
        or not 0 <= record["report_age_seconds"] <= 900
    ):
        raise ValueError("invalid audit report age")
    append_json_line(path, record)


def grant_approval(
    candidate_ref: str,
    *,
    candidates_path: Path,
    approvals_path: Path,
    lock_path: Path,
    now: datetime | None = None,
) -> ApprovalRecord:
    """Record one explicit non-reversible approval without exposing a token."""
    current = _now(now)
    with state_lock(lock_path):
        candidate = load_candidates(candidates_path).get(candidate_ref)
        if (
            candidate is None
            or candidate.issued_at > current
            or candidate.expires_at <= current
        ):
            raise ApprovalStateError("candidate is unknown or expired")
        approvals = load_approvals(approvals_path)
        existing = [
            item
            for item in approvals.values()
            if item.candidate_ref == candidate_ref
            and item.consumed_at is None
            and item.issued_at <= current
            and item.expires_at > current
        ]
        if len(existing) > 1:
            raise ApprovalStateError("candidate has ambiguous pending approvals")
        if existing:
            return existing[0]
        record = new_approval(candidate_ref, now=current)
        # Retain only a bounded recent history; audit records are the durable
        # outcome history and contain no approval references.
        retained = sorted(approvals.values(), key=lambda item: item.issued_at)[-31:]
        approvals = {item.reference: item for item in retained}
        approvals[record.reference] = record
        store_approvals(approvals_path, approvals)
        return record


class ExecutionCoordinator:
    """Reserve one approval persistently, then make one bounded adapter attempt."""

    def __init__(
        self,
        *,
        candidates_path: Path,
        approvals_path: Path,
        audit_path: Path,
        lock_path: Path,
        adapter: RadarrQueueAdapter,
    ) -> None:
        self.candidates_path = candidates_path
        self.approvals_path = approvals_path
        self.audit_path = audit_path
        self.lock_path = lock_path
        self.adapter = adapter

    def execute(
        self, request: dict[str, object], *, now: datetime | None = None
    ) -> dict[str, object]:
        current = _now(now)
        with state_lock(self.lock_path):
            candidates = load_candidates(self.candidates_path)
            broker = Broker(candidates, {})
            broker.dry_run(request, now=current)
            candidate_ref = str(request["candidate_ref"])
            approvals = load_approvals(self.approvals_path)
            record = pending_approval(approvals, candidate_ref, now=current)
            approvals[record.reference] = consume_approval(record, now=current)
            store_approvals(self.approvals_path, approvals)
            append_audit(self.audit_path, _audit(request, "attempt_started", current))

            # Keep the mapping stable through the sole adapter attempt. The
            # issuer uses the same lock, so it cannot supersede the opaque
            # reference after validation but before use.
            broker = Broker(
                candidates,
                {
                    record.reference: Approval(
                        record.reference,
                        record.candidate_ref,
                        record.operation,
                        record.expires_at,
                    )
                },
            )
            try:
                result = broker.execute(
                    request,
                    approval_ref=record.reference,
                    adapter=self.adapter,
                    now=current,
                )
            except ProposalError as exc:
                result = _audit(request, "precondition_refused", current)
                append_audit(self.audit_path, result)
                raise ExecutionConflict(
                    "candidate preconditions changed; approval was consumed"
                ) from exc

            append_audit(self.audit_path, result)
        return result
