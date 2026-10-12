"""Create a private backend-blind review packet after a holdout run is sealed.

This never sends data to a model and emits only digests/counts to its caller.
The answer key is read only in the reviewer/custodian step, never by the runner.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from holdout_answer_capture import CASE_SHA256, REPO, load_cases


KEY_SHA256 = "27b6049546abcda89a0c725fffad3452fc6a58ce2595e87a73560545a0933744"


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _encode(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def prepare(cases_raw: bytes, key_raw: bytes, attempts_raw: bytes) -> tuple[bytes, bytes]:
    cases = load_cases(cases_raw)
    if _digest(key_raw) != KEY_SHA256:
        raise ValueError("hidden key digest mismatch")
    keys = [json.loads(line) for line in key_raw.splitlines()]
    if len(keys) != len(cases) or [k["id"] for k in keys] != [c["id"] for c in cases]:
        raise ValueError("case/key alignment mismatch")
    attempts = json.loads(attempts_raw)
    if (attempts.get("schema_version") != "aster-answer-holdout-capture.v1"
            or attempts.get("cases_sha256") != CASE_SHA256
            or attempts.get("tool_mode") != "disabled"
            or not isinstance(attempts.get("attempts"), list)
            or len(attempts["attempts"]) != len(cases)):
        raise ValueError("capture scope mismatch")
    if [a["case_id"] for a in attempts["attempts"]] != [c["id"] for c in cases]:
        raise ValueError("attempt order mismatch")
    packet_rows = []
    blank_rows = []
    for case, key, attempt in zip(cases, keys, attempts["attempts"]):
        if attempt["status"] not in ("completed", "failed", "not_attempted"):
            raise ValueError("invalid attempt status")
        if attempt["status"] == "completed":
            if not isinstance(attempt["answer"], str) or not attempt["answer"].strip():
                raise ValueError("missing completed answer")
        elif attempt["answer"] is not None:
            raise ValueError("answer on incomplete attempt")
        packet_rows.append({
            "case_id": case["id"], "class": case["class"],
            "request": case["fictional_user_request"],
            "frozen_clock": case["frozen_clock"],
            "permitted_sources": case["synthetic_source_records"],
            "private_context_locality_constraint": case["private_context_locality_constraint"],
            "expected_outcome_category": key["correct_outcome_category"],
            "expected_observable_behavior": key["expected_observable_behavior"],
            "rubric_checks": key["rubric_checks"],
            "prohibited_claims": key["prohibited_claims"],
            "answer": attempt["answer"], "status": attempt["status"],
            "error_code": attempt["error_code"],
        })
        blank_rows.append({"case_id": case["id"],
                           "rubric_checks": [None] * len(key["rubric_checks"]),
                           "prohibited_claims_present": [None] * len(key["prohibited_claims"]),
                           "privacy_violation": None,
                           "reviewer_outcome": None})
    binding = _digest(attempts_raw)
    packet = {"schema_version": "aster-answer-holdout-review-packet.v1",
              "attempts_sha256": binding, "cases": packet_rows,
              "qualification": "none; reviewer judgment and independent validation pending"}
    packet_raw = _encode(packet)
    template = {"schema_version": "aster-answer-holdout-review.v1",
                "attempts_sha256": binding, "packet_sha256": _digest(packet_raw),
                "reviewer_id": None,
                "reviews": blank_rows}
    return packet_raw, _encode(template)


def save_private(output_dir: Path, packet: bytes, template: bytes) -> dict:
    resolved = output_dir.resolve()
    if (not output_dir.is_absolute() or resolved == REPO or REPO in resolved.parents
            or any((parent / ".git").exists() for parent in (resolved, *resolved.parents))):
        raise ValueError("review packet must stay outside Git")
    if not output_dir.parent.is_dir() or output_dir.parent.stat().st_mode & 0o077:
        raise ValueError("parent must be owner-only")
    output_dir.mkdir(mode=0o700, exist_ok=False)
    try:
        for name, raw in (("review-packet.json", packet), ("blank-review.json", template)):
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(output_dir / name, flags, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
    except Exception:
        for child in output_dir.iterdir():
            child.unlink()
        output_dir.rmdir()
        raise
    return {"packet_sha256": _digest(packet), "blank_review_sha256": _digest(template),
            "case_count": len(json.loads(packet)["cases"])}
