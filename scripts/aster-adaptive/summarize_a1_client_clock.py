"""Summarize private A1 headless client clocks without exporting case content.

This is descriptive timing for an admitted candidate Aster path. It cannot
establish useful-answer time, answer quality, native Companion latency or
model promotion. Partial/censored runs remain visible rather than disappearing
from the denominator.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics

from a1_full_path_capture import _clock_row

MAX_ROWS = 20
MAX_BYTES = 40_000


def summarize(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError("invalid A1 client clock size")
    lines = raw.splitlines()
    if not 1 <= len(lines) <= MAX_ROWS:
        raise ValueError("invalid A1 client clock row count")
    seen = set()
    displayed = []
    censored = 0
    for line in lines:
        try:
            row = json.loads(line)
        except (UnicodeError, ValueError):
            raise ValueError("invalid A1 client clock row") from None
        if not isinstance(row, dict) or set(row) != {"case_id", "clock", "error_code"}:
            raise ValueError("unexpected A1 client clock fields")
        case_id = row["case_id"]
        if (not isinstance(case_id, str) or not 1 <= len(case_id) <= 80
                or not case_id.isascii() or case_id in seen):
            raise ValueError("invalid or repeated A1 case identity")
        seen.add(case_id)
        _clock_row(case_id, row["clock"], row["error_code"])
        if row["clock"]["terminal_displayed"]:
            displayed.append(float(row["clock"]["accepted_to_displayed_ms"]))
        else:
            censored += 1
    ordered = sorted(displayed)
    p95 = ordered[math.ceil(0.95 * len(ordered)) - 1] if ordered else None
    return {
        "schema_version": "aster-a1-headless-clock-summary.v1",
        "client_clock_sha256": hashlib.sha256(raw).hexdigest(),
        "planned_cases": MAX_ROWS,
        "observed_attempts": len(lines),
        "not_observed": MAX_ROWS - len(lines),
        "displayed": len(displayed),
        "censored": censored,
        "displayed_median_ms": statistics.median(ordered) if ordered else None,
        "displayed_p95_ms": p95,
        "displayed_max_ms": ordered[-1] if ordered else None,
        "timing_scope": "headless synthetic Aster candidate path; not native Companion",
        "useful_answer_ms": None,
        "qualification": "none; answer review and independent admission evidence required",
    }
