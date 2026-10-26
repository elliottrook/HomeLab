"""Label-blind capture boundary for the fixed Doctor usefulness fixture.

This module performs no network or credential access. A separately admitted
adapter supplies ``invoke(case)`` and raw synthetic answers remain private.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Callable

from fixed_doctor_usefulness import load_unique, validate


REPO = Path(__file__).resolve().parents[2]
FIXTURE_SHA256 = "8478b516e10b64eb3ed2ac9c8bf90ef151023fe8f9b8241fc37cecb9be0df43f"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def load_fixture(raw: bytes) -> dict:
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError("fixed Doctor fixture digest mismatch")
    fixture = load_unique(raw)
    validate(fixture)
    return fixture


def capture(
    fixture_raw: bytes,
    profile_sha256: str,
    invoke: Callable[[dict], str],
    *,
    clock: Callable[[], float] = time.monotonic,
    max_wall_s: float = 600,
    before_case: Callable[[], bool] | None = None,
) -> dict:
    fixture = load_fixture(fixture_raw)
    if (
        not isinstance(profile_sha256, str)
        or not HEX64.fullmatch(profile_sha256)
        or type(max_wall_s) not in {int, float}
        or max_wall_s <= 0
    ):
        raise ValueError("unfrozen usefulness run profile")
    started = clock()
    rows = []
    stopped = False
    for case in fixture["cases"]:
        if (
            stopped
            or clock() - started >= max_wall_s
            or (before_case is not None and not before_case())
        ):
            rows.append({
                "case_id": case["id"],
                "status": "not_attempted",
                "answer": None,
                "error_code": "prior_stop_or_deadline",
                "total_ms": None,
            })
            stopped = True
            continue
        begun = clock()
        answer = None
        error_code = None
        try:
            answer = invoke(case)
            if (
                not isinstance(answer, str)
                or not answer.strip()
                or len(answer.encode("utf-8")) > 16_000
            ):
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
        rows.append({
            "case_id": case["id"],
            "status": "failed" if error_code else "completed",
            "answer": answer,
            "error_code": error_code,
            "total_ms": elapsed,
        })
    return {
        "schema": "aster-fixed-doctor-usefulness-capture.v1",
        "fixture_sha256": FIXTURE_SHA256,
        "profile_sha256": profile_sha256,
        "tool_mode": "disabled",
        "authority": "not-granted",
        "attempts": rows,
    }


def reserve_private(directory: Path) -> None:
    resolved = directory.resolve()
    if (
        not directory.is_absolute()
        or resolved == REPO
        or REPO in resolved.parents
        or any((parent / ".git").exists() for parent in (resolved, *resolved.parents))
    ):
        raise ValueError("raw answers must stay outside Git")
    if not directory.parent.is_dir() or directory.parent.stat().st_mode & 0o077:
        raise ValueError("parent must be owner-only")
    directory.mkdir(mode=0o700, exist_ok=False)


def save_private(directory: Path, result: dict) -> dict:
    reserve_private(directory)
    raw = (json.dumps(
        result, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n").encode()
    path = directory / "raw-attempts.json"
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(path, flags, 0o600), "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return {
        "raw_attempts_sha256": hashlib.sha256(raw).hexdigest(),
        "planned": len(result["attempts"]),
        "completed": sum(row["status"] == "completed" for row in result["attempts"]),
        "failed": sum(row["status"] == "failed" for row in result["attempts"]),
        "not_attempted": sum(
            row["status"] == "not_attempted" for row in result["attempts"]
        ),
    }
