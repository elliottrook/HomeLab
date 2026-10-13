"""Offline A1-v2-to-Aster request serializer; no transport or credentials.

This constructs the exact no-tool request for a future isolated test gateway.
It neither establishes a test-only server boundary nor invokes Aster.
"""
from __future__ import annotations

import json
import hashlib

from holdout_answer_capture import FIELDS, load_cases


def payload_for(case: dict) -> dict:
    if (not isinstance(case, dict) or set(case) != FIELDS
            or case.get("maximum_tool_scope") != "none"
            or not isinstance(case.get("fictional_user_request"), str)
            or not case["fictional_user_request"].strip()):
        raise ValueError("invalid frozen no-tool case")
    user = {
        "request": case["fictional_user_request"],
        "clock": case["frozen_clock"],
        "private_context_locality_constraint": case["private_context_locality_constraint"],
        "context": case["synthetic_source_records"],
    }
    return {
        "model": "aster-qwen3.5-9b",
        "messages": [{"role": "user", "content": json.dumps(user, sort_keys=True)}],
        "temperature": 0,
        "max_tokens": 256,
        "stream": False,
        "progress": False,
        "persona": "sysadmin",
        "enabled_tools": [],
    }


def wire_bytes_for(case: dict) -> bytes:
    """Pin the JSON bytes used by both the private client and test gateway."""
    return json.dumps(payload_for(case), ensure_ascii=False).encode("utf-8")


def frozen_request_hashes(cases_raw: bytes) -> frozenset[str]:
    """Return only request digests after validating the sealed 20-case input."""
    bodies = [wire_bytes_for(case) for case in load_cases(cases_raw)]
    digests = frozenset(hashlib.sha256(body).hexdigest() for body in bodies)
    if len(digests) != 20:
        raise ValueError("duplicate serialized request")
    return digests
