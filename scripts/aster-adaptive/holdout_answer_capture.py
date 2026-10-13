"""Label-blind capture for the sealed fictional Aster answer holdout.

This module contains no network or credential access. An admitted adapter
supplies invoke(case); output answers stay in a private local file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Callable


REPO = Path(__file__).resolve().parents[2]
CASE_SHA256 = "8c5293382a457cbcf4f9999a8904820d6b1d126477fbfc6b672b41a87b62cab9"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {"id", "class", "fictional_user_request", "frozen_clock",
          "synthetic_source_records", "private_context_locality_constraint",
          "permitted_capability_set", "maximum_tool_scope"}


def load_cases(raw: bytes) -> list[dict]:
    if hashlib.sha256(raw).hexdigest() != CASE_SHA256:
        raise ValueError("candidate-visible case digest mismatch")
    cases = [json.loads(line) for line in raw.splitlines()]
    if (len(cases) != 20 or any(not isinstance(case, dict) or set(case) != FIELDS
                               or case["maximum_tool_scope"] != "none" for case in cases)):
        raise ValueError("unexpected holdout scope")
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case")
    return cases


def capture(cases_raw: bytes, profile_sha256: str,
            invoke: Callable[[dict], str], clock: Callable[[], float] = time.monotonic,
            max_wall_s: float = 900) -> dict:
    cases = load_cases(cases_raw)
    if (not isinstance(profile_sha256, str) or not HEX64.fullmatch(profile_sha256)
            or max_wall_s <= 0):
        raise ValueError("unfrozen run profile")
    start = clock()
    rows = []
    stopped = False
    for case in cases:
        if stopped or clock() - start >= max_wall_s:
            rows.append({"case_id": case["id"], "status": "not_attempted",
                         "answer": None, "error_code": "prior_stop_or_deadline",
                         "total_ms": None})
            stopped = True
            continue
        begun = clock()
        answer = None
        error_code = None
        try:
            answer = invoke(case)
            if (not isinstance(answer, str) or not answer.strip()
                    or len(answer.encode("utf-8")) > 16_000):
                answer = None
                error_code = "invalid_output"
        except TimeoutError:
            error_code = "timeout"
        except (ConnectionError, OSError):
            error_code = "unavailable"
        except (ValueError, TypeError, KeyError, IndexError):
            error_code = "invalid_output"
        except Exception:
            error_code = "other"
        elapsed = round((clock() - begun) * 1000)
        if elapsed < 0 or elapsed > 600_000:
            raise ValueError("invalid elapsed time")
        if error_code:
            stopped = True
        rows.append({"case_id": case["id"],
                     "status": "failed" if error_code else "completed",
                     "answer": answer, "error_code": error_code,
                     "total_ms": elapsed})
    return {"schema_version": "aster-answer-holdout-capture.v1",
            "cases_sha256": CASE_SHA256, "profile_sha256": profile_sha256,
            "tool_mode": "disabled", "attempts": rows}


def reserve_private(directory: Path) -> None:
    resolved = directory.resolve()
    if (not directory.is_absolute() or resolved == REPO or REPO in resolved.parents
            or any((parent / ".git").exists() for parent in (resolved, *resolved.parents))):
        raise ValueError("raw answers must stay outside Git")
    if not directory.parent.is_dir() or directory.parent.stat().st_mode & 0o077:
        raise ValueError("parent must be owner-only")
    # Prove directory creation and file write *before* any model call. A
    # completed remote batch must never be lost to a predictable local denial.
    directory.mkdir(mode=0o700, exist_ok=False)
    probe = directory / ".write-preflight"
    try:
        fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(b"ok\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        probe.unlink(missing_ok=True)
        directory.rmdir()
        raise
    probe.unlink()


def save_private(directory: Path, result: dict, *, reserved: bool = False) -> dict:
    if not reserved:
        reserve_private(directory)
    elif (not directory.is_dir() or directory.stat().st_mode & 0o077
          or any(directory.iterdir())):
        raise ValueError("reserved output directory is not empty/owner-only")
    raw = (json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    try:
        path = directory / "raw-attempts.json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        for p in directory.iterdir():
            p.unlink()
        directory.rmdir()
        raise
    return {"raw_attempts_sha256": hashlib.sha256(raw).hexdigest(),
            "planned": len(result["attempts"]),
            "completed": sum(row["status"] == "completed" for row in result["attempts"]),
            "failed": sum(row["status"] == "failed" for row in result["attempts"]),
            "not_attempted": sum(row["status"] == "not_attempted" for row in result["attempts"])}
