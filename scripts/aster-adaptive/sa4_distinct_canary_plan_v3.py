"""Third unique SA4 v2-canary plan identity after the pre-owner v8 stop."""
from __future__ import annotations

import sa4_distinct_canary_plan_v2 as previous
import sa4_distinct_registry_bindings_v2 as bindings
import sa4_single_file_repair_contract_v1 as contract

TARGET_ID = previous.TARGET_ID
BEFORE_SHA256 = previous.BEFORE_SHA256
AFTER_SHA256 = previous.AFTER_SHA256
PLAN_ID = "sa4-canary-v2-third-repair-v1"


def build_plan() -> bytes:
    value = contract.decode_unique_json(previous.build_plan())
    if value.get("plan_id") != previous.PLAN_ID:
        raise ValueError("SA4 v3 plan predecessor changed")
    value["plan_id"] = PLAN_ID
    raw = contract.canonical(value)
    with bindings.accepted_registry(raw): contract.validate_plan(raw)
    return raw


PLAN_SHA256 = contract.sha256(build_plan())
