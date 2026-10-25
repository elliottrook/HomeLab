"""Validate content-free NLU holdout non-overlap receipts."""

from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-nonoverlap-receipt.v1"
REVIEWER = "stream-a-nlu-holdout-nonoverlap-reviewer-v1"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
REFERENCES = {
    "development": {
        "artifact_sha256": "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785",
        "normalized_text_set_sha256": "53d1e0e098a4785f81e8213e1b3ed700ad8c61c48bc2f9726aa5462442445456",
        "case_count": 24,
    },
    "calibration": {
        "artifact_sha256": "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e",
        "normalized_text_set_sha256": "c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3",
        "case_count": 60,
    },
}
FIELDS = {
    "schema", "reference_class", "subject_source_sha256",
    "subject_normalized_text_set_sha256", "subject_case_count",
    "reference_artifact_sha256", "reference_normalized_text_set_sha256",
    "reference_case_count", "overlap_count", "reviewer", "authority",
    "receipt_sha256",
}


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("receipt_sha256", None)
    raw = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_receipt(value: object, reference_class: str | None = None) -> list[str]:
    if not isinstance(value, dict):
        return ["non-overlap receipt must be an object"]
    errors = []
    if set(value) != FIELDS or value.get("schema") != SCHEMA:
        errors.append("invalid non-overlap receipt schema")
    actual_class = value.get("reference_class")
    if reference_class is not None and actual_class != reference_class:
        errors.append("non-overlap receipt reference class changed")
    expected = REFERENCES.get(actual_class)
    if expected is None:
        errors.append("invalid non-overlap reference class")
    else:
        for field in ("artifact_sha256", "normalized_text_set_sha256", "case_count"):
            if value.get("reference_" + field) != expected[field]:
                errors.append(f"non-overlap reference {field} changed")
    for field in ("subject_source_sha256", "subject_normalized_text_set_sha256"):
        if not isinstance(value.get(field), str) or HEX64.fullmatch(value[field]) is None:
            errors.append(f"invalid {field}")
    if value.get("subject_case_count") != 36:
        errors.append("holdout subject must contain exactly 36 cases")
    if value.get("overlap_count") != 0:
        errors.append("non-overlap receipt must report zero overlap")
    if value.get("reviewer") != REVIEWER:
        errors.append("non-overlap receipt requires the independent reviewer")
    if value.get("authority") != "not-granted":
        errors.append("non-overlap receipt cannot grant authority")
    receipt_sha = value.get("receipt_sha256")
    if not isinstance(receipt_sha, str) or HEX64.fullmatch(receipt_sha) is None:
        errors.append("non-overlap receipt requires receipt_sha256")
    elif receipt_sha != canonical_sha256(value):
        errors.append("non-overlap receipt_sha256 does not match canonical receipt")
    return errors


def load_and_validate(raw: bytes, reference_class: str) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["non-overlap receipt must be unique-key UTF-8 JSON"]
    errors = validate_receipt(value, reference_class)
    return value if isinstance(value, dict) else None, errors
