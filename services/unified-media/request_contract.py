"""Pure M2 request planning primitives.

This module deliberately performs no HTTP calls. Authority adapters can use
the plan/idempotency checks before their explicit mutation step.
"""

from dataclasses import dataclass
import hashlib
from typing import Any


@dataclass(frozen=True)
class Candidate:
    media_type: str
    authority: str
    authority_id: str
    title: str
    evidence: tuple[str, ...] = ()
    match_count: int = 1
    owned: bool = False
    archived: bool = False


def idempotency_key(candidate: Candidate) -> str:
    raw = "|".join((candidate.media_type, candidate.authority, candidate.authority_id))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def plan_action(candidate: Candidate, *, approve: bool = False) -> dict[str, Any]:
    reasons: list[str] = []
    if candidate.match_count != 1:
        reasons.append("ambiguous_match")
    if candidate.owned:
        reasons.append("already_owned")
    if candidate.archived:
        reasons.append("archived_item")
    if not candidate.evidence:
        reasons.append("missing_evidence")
    if not approve:
        reasons.append("explicit_approval_required")
    return {
        "action": "request",
        "approved": approve and not reasons,
        "candidate": candidate.title,
        "authority": candidate.authority,
        "authority_id": candidate.authority_id,
        "idempotency_key": idempotency_key(candidate),
        "reasons": reasons,
    }
