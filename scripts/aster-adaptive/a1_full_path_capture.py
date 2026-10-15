"""Private, one-attempt A1 answer capture with a separate content-free clock.

This module neither authenticates an admission receipt nor opens a transport.
The platform controller must validate the live lease and sidecar immediately
before the caller supplies an admitted ``invoke_case`` function.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Callable

from a1_headless_client import A1TransportError, ClientDisplayClock
from journaled_holdout_capture import EvidenceWriteFailure, capture_journaled

CLOCK_FIELDS = {"schema_version", "observation_id", "http_status",
                "accepted_to_displayed_ms", "terminal_displayed"}
OBSERVATION_ID = re.compile(r"[0-9a-f]{32}\Z")
ERROR_CODES = {None, "unavailable_or_uncertain", "invalid_or_uncertain_response",
               "client_exception"}


def _clock_row(case_id: str, timing: dict, error_code: str | None) -> dict:
    if (not isinstance(timing, dict) or set(timing) != CLOCK_FIELDS
            or timing.get("schema_version") != "aster-client-clock.v0"
            or type(timing.get("terminal_displayed")) is not bool
            or error_code not in ERROR_CODES
            or ((timing["observation_id"] is not None) and (
                not isinstance(timing["observation_id"], str)
                or not OBSERVATION_ID.fullmatch(timing["observation_id"])))
            or ((timing["http_status"] is not None) and (
                type(timing["http_status"]) is not int
                or not 100 <= timing["http_status"] <= 599))
            or (timing["terminal_displayed"] and (
                not isinstance(timing.get("observation_id"), str)
                or not isinstance(timing.get("accepted_to_displayed_ms"), (int, float))
                or isinstance(timing.get("accepted_to_displayed_ms"), bool)
                or not math.isfinite(timing["accepted_to_displayed_ms"])
                or not 0 <= timing["accepted_to_displayed_ms"] <= 600_000
                or timing["http_status"] != 200 or error_code is not None))
            or (not timing["terminal_displayed"]
                and (timing.get("accepted_to_displayed_ms") is not None
                     or error_code is None))):
        raise ValueError("invalid A1 client clock")
    return {"case_id": case_id, "clock": timing, "error_code": error_code}


def capture_full_path(cases_raw: bytes, profile_sha256: str, directory: Path,
                      invoke_case: Callable[..., tuple[str, object]],
                      *, clock=None, max_wall_s: float = 1200) -> dict:
    """Capture one frozen batch; retain failures and never retry an attempt.

    ``invoke_case`` normally wraps ``a1_headless_client.invoke`` with a
    validated local endpoint and test-only ingress key. This function records
    answers only in the owner-only journal/output created by
    ``capture_journaled``. Its clock file contains no prompt or answer.
    """
    if not callable(invoke_case):
        raise ValueError("admitted A1 client is required")
    clock_file = directory / "client-clock.jsonl"
    stream = None
    row_count = 0
    pending: dict[str, object] = {}

    def append(case_id: str, timing: dict, error_code: str | None) -> None:
        nonlocal stream, row_count
        row = _clock_row(case_id, timing, error_code)
        if stream is None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                stream = os.fdopen(os.open(clock_file, flags, 0o600), "wb")
                directory_fd = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                raise EvidenceWriteFailure("A1 client clock unavailable; stop without retry") from None
        try:
            raw = (json.dumps(row, sort_keys=True, separators=(",", ":"),
                              allow_nan=False) + "\n").encode("utf-8")
            if stream.write(raw) != len(raw):
                raise OSError("short clock write")
            stream.flush()
            os.fsync(stream.fileno())
            row_count += 1
        except (OSError, TypeError, ValueError):
            raise EvidenceWriteFailure("A1 client clock failed; stop without retry") from None

    def invoke_for_journal(case: dict, *, timeout_s: float) -> str:
        try:
            answer, timing = invoke_case(case, timeout_s=timeout_s)
        except A1TransportError as exc:
            append(case["id"], exc.timing, exc.args[0])
            if exc.args[0] == "unavailable_or_uncertain":
                raise ConnectionError("A1 transport uncertain") from None
            raise ValueError("A1 response uncertain") from None
        except Exception:
            append(case["id"], {"schema_version": "aster-client-clock.v0",
                                "observation_id": None, "http_status": None,
                                "accepted_to_displayed_ms": None,
                                "terminal_displayed": False}, "client_exception")
            raise
        pending[case["id"]] = timing
        return answer

    def after_attempt_returned(case_id: str) -> None:
        timing = pending.pop(case_id)
        if isinstance(timing, ClientDisplayClock):
            timing = timing.finish(terminal_displayed=True)
        append(case_id, timing, None)

    options = {"max_wall_s": max_wall_s}
    if clock is not None:
        options["clock"] = clock
    try:
        summary = capture_journaled(cases_raw, profile_sha256, invoke_for_journal,
                                    directory, after_attempt_returned=after_attempt_returned,
                                    allow_full_path_20m=True, min_call_s=60, **options)
    finally:
        if stream is not None:
            stream.close()
    if row_count:
        summary["client_clock_sha256"] = hashlib.sha256(clock_file.read_bytes()).hexdigest()
    else:
        summary["client_clock_sha256"] = None
    summary["client_clock_rows"] = row_count
    return summary
