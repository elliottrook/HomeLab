"""Owner-only attempt journal for a future fictional A1 candidate run.

Importing this module has no network effect. The caller must separately prove
the candidate profile, endpoint, lease, backup chain and output custody before
supplying invoke(case). An interrupted invocation is never retried here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Callable

import holdout_answer_capture as holdout


class EvidenceWriteFailure(BaseException):
    """Stop inference if evidence cannot be sealed, bypassing capture's OSError handler."""


def _write_event(stream, event: dict) -> None:
    try:
        raw = (json.dumps(event, sort_keys=True, ensure_ascii=False,
                          allow_nan=False) + "\n").encode("utf-8")
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise EvidenceWriteFailure("private attempt journal failed; stop without retry") from exc


def _create_private(path: Path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.fdopen(os.open(path, flags, 0o600), "wb")


def capture_journaled(cases_raw: bytes, profile_sha256: str,
                      invoke: Callable[[dict], str], directory: Path,
                      *, clock=None, max_wall_s: float = 900) -> dict:
    """Capture once, durably journaling starts and returned text before proceeding.

    A started event without a later returned/error event is an uncertain call.
    The directory may not be reused, even if no final envelope was produced.
    """
    if not callable(invoke):
        raise ValueError("candidate adapter must be callable")
    holdout.load_cases(cases_raw)
    if not isinstance(profile_sha256, str) or not holdout.HEX64.fullmatch(profile_sha256):
        raise ValueError("unfrozen candidate profile")
    if (isinstance(max_wall_s, bool) or not isinstance(max_wall_s, (int, float))
            or not math.isfinite(max_wall_s) or not 0 < max_wall_s <= 900):
        raise ValueError("invalid bounded batch deadline")
    holdout.reserve_private(directory)
    journal = directory / "attempt-journal.jsonl"
    with _create_private(journal) as stream:
        _write_event(stream, {"event": "run_started", "schema_version": "aster-answer-attempt-journal.v0",
                              "cases_sha256": hashlib.sha256(cases_raw).hexdigest(),
                              "profile_sha256": profile_sha256, "tool_mode": "disabled"})

        def witnessed(case: dict) -> str:
            case_id = case["id"]
            _write_event(stream, {"event": "attempt_started", "case_id": case_id})
            try:
                answer = invoke(case)
            except Exception as exc:
                # Record an allowlisted class only; exception text may contain
                # a URL, prompt or credential and must never enter the journal.
                if isinstance(exc, TimeoutError):
                    code = "timeout"
                elif isinstance(exc, (ConnectionError, OSError)):
                    code = "unavailable"
                elif isinstance(exc, (ValueError, TypeError, KeyError, IndexError)):
                    code = "invalid_output"
                else:
                    code = "other"
                _write_event(stream, {"event": "attempt_error", "case_id": case_id,
                                      "error_code": code})
                raise
            if isinstance(answer, str) and len(answer.encode("utf-8")) <= 16_000:
                _write_event(stream, {"event": "attempt_returned", "case_id": case_id,
                                      "answer": answer})
            else:
                _write_event(stream, {"event": "attempt_invalid_output", "case_id": case_id})
            return answer

        options = {"max_wall_s": max_wall_s}
        if clock is not None:
            options["clock"] = clock
        result = holdout.capture(cases_raw, profile_sha256, witnessed, **options)
        _write_event(stream, {"event": "capture_completed", "planned": len(result["attempts"])})

    raw = (json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    pending = directory / "raw-attempts.json.tmp"
    try:
        with _create_private(pending) as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, directory / "raw-attempts.json")
        dirfd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    except OSError as exc:
        pending.unlink(missing_ok=True)
        raise EvidenceWriteFailure("final capture write failed; journal retained; no retry") from exc
    return {"planned": len(result["attempts"]),
            "completed": sum(row["status"] == "completed" for row in result["attempts"]),
            "failed": sum(row["status"] == "failed" for row in result["attempts"]),
            "not_attempted": sum(row["status"] == "not_attempted" for row in result["attempts"]),
            "raw_attempts_sha256": hashlib.sha256(raw).hexdigest(),
            "attempt_journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest(),
            "profile_sha256": profile_sha256}
