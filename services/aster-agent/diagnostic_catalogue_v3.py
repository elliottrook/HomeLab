"""Bounded, summary-free contract for named Doctor diagnostic states.

This module is deliberately independent of the live schema-2 fixed Doctor
path.  It defines the source contract needed before a second diagnostic can be
added without treating Doctor's human-readable aggregate lines as authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable


MAX_EVENT_BYTES = 16_384
MAX_CHECKS = 16
STATES = frozenset({"pass", "warn", "fail", "unavailable"})
AGGREGATE_STATES = frozenset({"healthy", "warning", "failed"})
_RUN_ID = re.compile(r"[0-9a-f]{32}")
_DIGEST = re.compile(r"[0-9a-f]{64}")


class CatalogueError(ValueError):
    """The producer evidence cannot safely form a typed catalogue."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogueError("duplicate JSON field")
        result[key] = value
    return result


def _normalise_allowlist(check_ids: Iterable[str]) -> tuple[str, ...]:
    values = tuple(check_ids)
    if not values or len(values) > MAX_CHECKS or any(not isinstance(value, str) for value in values):
        raise CatalogueError("invalid diagnostic allowlist")
    values = tuple(sorted(values))
    if len(values) != len(set(values)):
        raise CatalogueError("invalid diagnostic allowlist")
    for check_id in values:
        if not isinstance(check_id, str) or not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)+", check_id):
            raise CatalogueError("invalid check id")
    return values


def build_catalogue(
    raw_events: bytes,
    *,
    run_id: str,
    generated_at: str,
    aggregate_payload: bytes,
    aggregate_status: str,
    allowed_check_ids: Iterable[str],
) -> dict[str, object]:
    """Build one deterministic catalogue from same-run producer events.

    Every allowlisted check appears exactly once. Missing events become
    ``unavailable``. Unknown, duplicate, malformed or cross-run events reject
    the whole catalogue instead of silently widening or mixing authority.
    """

    allowed = _normalise_allowlist(allowed_check_ids)
    if not isinstance(raw_events, bytes) or len(raw_events) > MAX_EVENT_BYTES:
        raise CatalogueError("invalid event stream size")
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        raise CatalogueError("invalid run id")
    if not isinstance(generated_at, str) or not generated_at:
        raise CatalogueError("invalid generation time")
    if not isinstance(aggregate_payload, bytes) or not aggregate_payload:
        raise CatalogueError("invalid aggregate payload")
    if not isinstance(aggregate_status, str) or aggregate_status not in AGGREGATE_STATES:
        raise CatalogueError("invalid aggregate status")

    observed: dict[str, str] = {}
    if raw_events:
        try:
            lines = raw_events.decode("utf-8").splitlines()
            for line in lines:
                event = json.loads(line, object_pairs_hook=_unique_object)
                if not isinstance(event, dict) or set(event) != {"run_id", "check_id", "state"}:
                    raise CatalogueError("invalid event shape")
                if event["run_id"] != run_id:
                    raise CatalogueError("cross-run event")
                check_id = event["check_id"]
                state = event["state"]
                if check_id not in allowed:
                    raise CatalogueError("unknown check id")
                if not isinstance(state, str) or state not in STATES:
                    raise CatalogueError("invalid check state")
                if check_id in observed:
                    raise CatalogueError("duplicate check event")
                observed[check_id] = state
        except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
            raise CatalogueError("invalid event encoding") from exc

    severity = {"healthy": 0, "warning": 1, "failed": 2}
    check_severity = {"pass": 0, "warn": 1, "fail": 2, "unavailable": 0}
    if any(check_severity[state] > severity[aggregate_status] for state in observed.values()):
        raise CatalogueError("check state contradicts aggregate status")

    checks = [
        {"check_id": check_id, "state": observed.get(check_id, "unavailable")}
        for check_id in allowed
    ]
    return {
        "schema": 3,
        "generated_at": generated_at,
        "run_id": run_id,
        "source_report_digest": hashlib.sha256(aggregate_payload).hexdigest(),
        "checks": checks,
    }


def select_check(
    catalogue: dict[str, object], *, check_id: str, source_report_digest: str
) -> dict[str, str]:
    """Return exactly one fixed check from a validated schema-3 catalogue."""

    if not isinstance(catalogue, dict) or set(catalogue) != {
        "schema", "generated_at", "run_id", "source_report_digest", "checks"
    }:
        raise CatalogueError("invalid catalogue shape")
    if catalogue["schema"] != 3:
        raise CatalogueError("invalid catalogue schema")
    if not isinstance(catalogue["generated_at"], str) or not catalogue["generated_at"]:
        raise CatalogueError("invalid catalogue time")
    if not isinstance(catalogue["run_id"], str) or not _RUN_ID.fullmatch(catalogue["run_id"]):
        raise CatalogueError("invalid catalogue run id")
    digest = catalogue["source_report_digest"]
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest) or digest != source_report_digest:
        raise CatalogueError("aggregate digest mismatch")
    checks = catalogue["checks"]
    if not isinstance(checks, list) or not checks or len(checks) > MAX_CHECKS:
        raise CatalogueError("invalid catalogue checks")

    selected = None
    seen: set[str] = set()
    for item in checks:
        if not isinstance(item, dict) or set(item) != {"check_id", "state"}:
            raise CatalogueError("invalid catalogue check")
        item_id, state = item["check_id"], item["state"]
        if (not isinstance(item_id, str) or
                not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)+", item_id) or
                item_id in seen or
                not isinstance(state, str) or state not in STATES):
            raise CatalogueError("invalid or duplicate catalogue check")
        seen.add(item_id)
        if item_id == check_id:
            selected = {"check_id": item_id, "state": state}
    if selected is None:
        raise CatalogueError("fixed check absent")
    return selected
