"""No-op proposal validator for Aster's first narrowly scoped ARR repair.

This module deliberately has no HTTP, credential, subprocess, or execution
path.  It is a rehearsal boundary: it can describe one candidate repair but
cannot make it happen.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any


OPERATION = "dismiss_stale_radarr_queue_record"
MAX_REPORT_AGE = timedelta(minutes=15)
REQUEST_FIELDS = {"operation", "service", "candidate_ref", "report_generated_at"}
CANDIDATE_REF = re.compile(r"radarr-q-[a-z2-7]{16}")


class ProposalError(ValueError):
    """A request is outside the sole proposal contract."""


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ProposalError("report_generated_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProposalError("report_generated_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ProposalError("report_generated_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def create_dry_run(request: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Validate and render the only allowed proposal. Never makes a change."""
    if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
        raise ProposalError("request must contain exactly the declared proposal fields")
    if request["operation"] != OPERATION or request["service"] != "radarr":
        raise ProposalError("only the declared Radarr queue-record proposal is allowed")
    candidate_ref = request["candidate_ref"]
    if not isinstance(candidate_ref, str) or not CANDIDATE_REF.fullmatch(candidate_ref):
        raise ProposalError("candidate_ref must be a broker-issued opaque Radarr reference")

    generated_at = _parse_time(request["report_generated_at"])
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if generated_at > current or current - generated_at > MAX_REPORT_AGE:
        raise ProposalError("the sanitized report is stale or from the future")

    return {
        "mode": "dry_run",
        "execution_enabled": False,
        "operation": OPERATION,
        "service": "radarr",
        "candidate_ref": candidate_ref,
        "preconditions": [
            "A fresh validated report produced this broker-issued candidate reference.",
            "The mapped queue record is complete and stale, not downloading or importing.",
            "The mapped record belongs to Radarr and has not been used or superseded.",
            "An operator has independently reviewed this proposal and supplied a task-specific approval at execution time.",
        ],
        "effect_if_later_enabled": "Remove only the mapped Radarr queue record; preserve downloader data and do not blocklist or search.",
        "validation": "Re-read the mapped record through the broker and confirm its absence; report a bounded audit result.",
        "rollback": "Not reversible: the removed queue record is not recreated. Media, downloader data, profiles and monitoring remain unchanged.",
        "next_step": "Operator review and a separately approved broker implementation; this module cannot execute the action.",
    }
