"""Verify the retained pre-effect bytes for a future SA4 canary rollback."""
from __future__ import annotations

import hashlib

from nlu_threshold_policy import decode_unique_json
import sa4_single_file_repair_contract_v1 as contract


EXPECTED = {"adapter": "sa4-canary",
            "schema": "aster-sa4-canary-adapter.v1", "state": "drifted"}
EXPECTED_SHA256 = "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a"


def check(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if (value != EXPECTED or raw != contract.canonical(EXPECTED)
            or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256):
        raise ValueError("SA4 canary rollback checkpoint changed")
    return {"schema": "aster-sa4-canary-rollback-check.v1", "state": "pass",
            "checkpoint_sha256": EXPECTED_SHA256, "rollback_performed": False,
            "effects": 0, "authority": "none"}
