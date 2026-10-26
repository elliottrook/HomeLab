"""Durable one-attempt journal for fixed Doctor usefulness capture.

Importing this module has no network effect. An interrupted invocation is
uncertain and its owner-only directory must never be reused.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
from pathlib import Path
from typing import Callable

import fixed_doctor_usefulness_capture as capture


class EvidenceWriteFailure(BaseException):
    """Stop inference if evidence cannot be sealed."""


def _write_event(stream, event: dict) -> None:
    try:
        raw = (json.dumps(
            event, sort_keys=True, ensure_ascii=False, allow_nan=False
        ) + "\n").encode()
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as error:
        raise EvidenceWriteFailure(
            "private attempt journal failed; stop without retry"
        ) from error


def _create_private(path: Path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.fdopen(os.open(path, flags, 0o600), "wb")


def capture_journaled(
    fixture_raw: bytes,
    profile_sha256: str,
    invoke: Callable[..., str],
    directory: Path,
    *,
    clock=None,
    max_wall_s: float = 600,
    min_call_s: float = 60,
    after_attempt_returned: Callable[[str], None] | None = None,
) -> dict:
    if not callable(invoke):
        raise ValueError("candidate adapter must be callable")
    capture.load_fixture(fixture_raw)
    if not isinstance(profile_sha256, str) or not capture.HEX64.fullmatch(profile_sha256):
        raise ValueError("unfrozen run profile")
    if (
        isinstance(max_wall_s, bool)
        or not isinstance(max_wall_s, (int, float))
        or not math.isfinite(max_wall_s)
        or not 0 < max_wall_s <= 600
        or isinstance(min_call_s, bool)
        or not isinstance(min_call_s, (int, float))
        or not math.isfinite(min_call_s)
        or not 0 < min_call_s <= 60
    ):
        raise ValueError("invalid bounded run deadline")
    monotonic = clock or __import__("time").monotonic
    started = monotonic()
    parameters = inspect.signature(invoke).parameters
    accepts_timeout = (
        "timeout_s" in parameters
        or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )
    )
    capture.reserve_private(directory)
    journal = directory / "attempt-journal.jsonl"
    with _create_private(journal) as stream:
        _write_event(stream, {
            "event": "run_started",
            "schema": "aster-fixed-doctor-usefulness-attempt-journal.v1",
            "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
            "profile_sha256": profile_sha256,
            "tool_mode": "disabled",
            "authority": "not-granted",
        })

        def witnessed(case: dict) -> str:
            case_id = case["id"]
            _write_event(stream, {"event": "attempt_started", "case_id": case_id})
            try:
                # Recompute after the durable start row. A delayed fsync cannot
                # leave a stale timeout that opens transport after the deadline.
                remaining = max_wall_s - (monotonic() - started)
                if remaining < min_call_s:
                    raise TimeoutError("insufficient time for another bounded call")
                answer = (
                    invoke(case, timeout_s=min(60.0, remaining))
                    if accepts_timeout else invoke(case)
                )
            except Exception as error:
                if isinstance(error, TimeoutError):
                    code = "timeout"
                elif isinstance(error, (ConnectionError, OSError)):
                    code = "unavailable"
                elif isinstance(error, (ValueError, TypeError, KeyError, IndexError)):
                    code = "invalid_output"
                else:
                    code = "other"
                _write_event(stream, {
                    "event": "attempt_error", "case_id": case_id, "error_code": code
                })
                raise
            if isinstance(answer, str) and len(answer.encode("utf-8")) <= 16_000:
                _write_event(stream, {
                    "event": "attempt_returned", "case_id": case_id, "answer": answer
                })
                if after_attempt_returned is not None:
                    after_attempt_returned(case_id)
            else:
                _write_event(stream, {
                    "event": "attempt_invalid_output", "case_id": case_id
                })
            return answer

        def can_start_case() -> bool:
            return max_wall_s - (monotonic() - started) >= min_call_s

        options = {"max_wall_s": max_wall_s, "before_case": can_start_case}
        if clock is not None:
            options["clock"] = clock
        result = capture.capture(
            fixture_raw, profile_sha256, witnessed, **options
        )
        _write_event(stream, {
            "event": "capture_completed", "planned": len(result["attempts"])
        })

    raw = (json.dumps(
        result, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n").encode()
    pending = directory / "raw-attempts.json.tmp"
    try:
        with _create_private(pending) as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, directory / "raw-attempts.json")
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as error:
        pending.unlink(missing_ok=True)
        raise EvidenceWriteFailure(
            "final capture write failed; journal retained; no retry"
        ) from error
    return {
        "planned": len(result["attempts"]),
        "completed": sum(row["status"] == "completed" for row in result["attempts"]),
        "failed": sum(row["status"] == "failed" for row in result["attempts"]),
        "not_attempted": sum(
            row["status"] == "not_attempted" for row in result["attempts"]
        ),
        "raw_attempts_sha256": hashlib.sha256(raw).hexdigest(),
        "attempt_journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest(),
        "profile_sha256": profile_sha256,
    }
