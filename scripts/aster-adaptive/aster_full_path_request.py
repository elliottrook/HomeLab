"""Offline A1-v2-to-Aster request serializer; no transport or credentials.

This constructs the exact no-tool request for a future isolated test gateway.
It neither establishes a test-only server boundary nor invokes Aster.
"""
from __future__ import annotations

import json

from holdout_answer_capture import FIELDS


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
