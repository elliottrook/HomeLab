"""Fixed no-effect consumer-health check for the inert SA4 canary adapter."""
from __future__ import annotations

import hashlib

from nlu_threshold_policy import decode_unique_json
import sa4_single_file_repair_contract_v1 as contract


EXPECTED = {"adapter": "sa4-canary",
            "schema": "aster-sa4-canary-adapter.v1", "state": "healthy"}


def check(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if value != EXPECTED or raw != contract.canonical(EXPECTED):
        raise ValueError("SA4 canary consumer contract is not healthy")
    return {"schema": "aster-sa4-canary-consumer-health.v1",
            "state": "pass",
            "measurement_sha256": hashlib.sha256(raw).hexdigest(),
            "consumer": "inert-validator-only", "effects": 0,
            "authority": "none"}
