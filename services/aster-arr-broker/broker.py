"""A one-operation ARR repair broker core.

The core accepts opaque broker references only.  It deliberately has no HTTP
client, no API key handling and no generic request capability; a later reviewed
adapter is the only component that may contact Radarr.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from proposal import MAX_REPORT_AGE, OPERATION, ProposalError, create_dry_run

RADARR_DELETE_PARAMETERS = {
    "removeFromClient": "false",
    "blocklist": "false",
    "skipRedownload": "true",
    "changeCategory": "false",
}


@dataclass(frozen=True)
class Candidate:
    reference: str
    queue_id: int
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class Approval:
    reference: str
    candidate_ref: str
    operation: str
    expires_at: datetime


@dataclass(frozen=True)
class QueueState:
    queue_id: int
    completed: bool
    downloading: bool
    importing: bool


class RadarrQueueAdapter(Protocol):
    """Minimal future adapter; it never receives an arbitrary URL or method."""

    def inspect(self, queue_id: int) -> QueueState | None: ...

    def dismiss_preserving_downloader_data(self, queue_id: int) -> None:
        """Use only RADARR_DELETE_PARAMETERS with the fixed queue route."""


class Broker:
    """Bind one candidate and one task-specific approval to one repair only."""

    def __init__(self, candidates: dict[str, Candidate], approvals: dict[str, Approval]) -> None:
        self._candidates = candidates
        self._approvals = approvals
        self._used_approvals: set[str] = set()

    @staticmethod
    def _now(now: datetime | None) -> datetime:
        return (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    def dry_run(self, request: dict[str, object], *, now: datetime | None = None) -> dict[str, object]:
        result = create_dry_run(request, now=self._now(now))
        candidate = self._candidate(str(request["candidate_ref"]), self._now(now))
        return {**result, "candidate_expires_at": candidate.expires_at.isoformat()}

    def execute(
        self,
        request: dict[str, object],
        *,
        approval_ref: str,
        adapter: RadarrQueueAdapter,
        now: datetime | None = None,
    ) -> dict[str, str]:
        current = self._now(now)
        self.dry_run(request, now=current)
        candidate_ref = str(request["candidate_ref"])
        candidate = self._candidate(candidate_ref, current)
        approval = self._approval(approval_ref, candidate_ref, current)

        try:
            state = adapter.inspect(candidate.queue_id)
        except Exception:
            return self._audit(candidate_ref, "inspection_failed", current)
        if state is None:
            self._used_approvals.add(approval.reference)
            return self._audit(candidate_ref, "already_absent", current)
        if state.queue_id != candidate.queue_id or not state.completed or state.downloading or state.importing:
            raise ProposalError("candidate no longer meets the narrow repair preconditions")

        self._used_approvals.add(approval.reference)
        try:
            adapter.dismiss_preserving_downloader_data(candidate.queue_id)
        except Exception:
            # A timeout can occur after Radarr receives the request.  Consume
            # the approval so retrying cannot widen an uncertain outcome.
            return self._audit(candidate_ref, "outcome_unknown", current)
        return self._audit(candidate_ref, "dismissed", current)

    def _candidate(self, reference: str, now: datetime) -> Candidate:
        candidate = self._candidates.get(reference)
        if candidate is None or candidate.expires_at <= now:
            raise ProposalError("candidate reference is unknown, expired or already superseded")
        return candidate

    def _approval(self, reference: str, candidate_ref: str, now: datetime) -> Approval:
        approval = self._approvals.get(reference)
        if (
            approval is None
            or approval.reference in self._used_approvals
            or approval.expires_at <= now
            or approval.candidate_ref != candidate_ref
            or approval.operation != OPERATION
        ):
            raise ProposalError("approval is missing, expired, replayed or outside this candidate")
        return approval

    @staticmethod
    def _audit(candidate_ref: str, result: str, now: datetime) -> dict[str, str]:
        return {
            "operation": OPERATION,
            "candidate_ref": candidate_ref,
            "result": result,
            "at": now.isoformat(),
        }
