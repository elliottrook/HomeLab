"""Fixed content-free byte check for the approved SA4 canary target."""
from __future__ import annotations

import hashlib

from nlu_threshold_policy import decode_unique_json
import sa4_single_file_repair_contract_v1 as contract


EXPECTED_SHA256 = "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065"
MAXIMUM_BYTES = 4096


def check(raw: bytes) -> dict[str, object]:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAXIMUM_BYTES:
        raise ValueError("SA4 canary byte measurement is out of bounds")
    value = decode_unique_json(raw)
    if (raw != contract.canonical(value)
            or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256):
        raise ValueError("SA4 canary bytes do not match the fixed artifact")
    return {"schema": "aster-sa4-canary-byte-check.v1", "state": "pass",
            "measurement_sha256": EXPECTED_SHA256, "effects": 0,
            "authority": "none"}
