"""Validate content-free J1 non-overlap receipts for every exposed corpus."""

from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j1-nonoverlap-receipt.v1"
REVIEWER = "stream-a-nlu-j1-nonoverlap-reviewer-v1"
SUBJECT_CASE_COUNT = 400
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
REFERENCES = {
    "development-v1": {
        "artifact_sha256": "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785",
        "normalized_text_set_sha256": "53d1e0e098a4785f81e8213e1b3ed700ad8c61c48bc2f9726aa5462442445456",
        "case_count": 24,
    },
    "calibration-v1": {
        "artifact_sha256": "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e",
        "normalized_text_set_sha256": "c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3",
        "case_count": 60,
    },
    "calibration-v2": {
        "artifact_sha256": "c865bb045fa157592429bf1c4bd20a5aadd7a3f8b40ed0aaa536150a300334df",
        "normalized_text_set_sha256": "71d5154563adb5ba360fa79aca468e87319f8e8b29f4c2ed0bbf2d2305257fdb",
        "case_count": 60,
    },
    "calibration-v3": {
        "artifact_sha256": "b55098df5b7e475b4360007669d3c3b788fc89a1ab6eacaf023df0948bee4455",
        "normalized_text_set_sha256": "33fc068f2c259213ab53bf135770709802bc317f2661067380a2ad9e4e8c524c",
        "case_count": 60,
    },
    "calibration-v4": {
        "artifact_sha256": "09f82238506e01b8e8e2b443dfaee566263344a020032862cfb1570e958079c3",
        "normalized_text_set_sha256": "1a78b883cc5a39c88f96b5def07574c2ebe1821dfc17c15465ca80e87cbb906f",
        "case_count": 60,
    },
    "calibration-v5": {
        "artifact_sha256": "50b6a36b64e8942eb83dd8769f52c52b6fa4a0e7a1d42adeebd7be2c5157c676",
        "normalized_text_set_sha256": "be93e28afa6de2a5a6c525c1659563292196c05a84bcff1412b38795d39d2423",
        "case_count": 60,
    },
    "calibration-v6": {
        "artifact_sha256": "a0a85ba1e46e88c0a7557dcd8744530d336bef74f5cd1854d25ba31877a5da4d",
        "normalized_text_set_sha256": "76a9d7164f63878babf6ef7fe4d836eb7270cbca8bc6a776cc60e93e3f438b6e",
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


def validate_receipt(value: object, reference_class: str) -> list[str]:
    if not isinstance(value, dict):
        return ["J1 non-overlap receipt must be an object"]
    errors = []
    if set(value) != FIELDS or value.get("schema") != SCHEMA:
        errors.append("invalid J1 non-overlap receipt schema")
    if reference_class not in REFERENCES or value.get("reference_class") != reference_class:
        errors.append("J1 non-overlap reference class changed")
    expected = REFERENCES.get(reference_class)
    if expected is not None:
        for field in ("artifact_sha256", "normalized_text_set_sha256", "case_count"):
            if value.get("reference_" + field) != expected[field]:
                errors.append(f"J1 non-overlap reference {field} changed")
    for field in ("subject_source_sha256", "subject_normalized_text_set_sha256"):
        if not isinstance(value.get(field), str) or HEX64.fullmatch(value[field]) is None:
            errors.append(f"invalid {field}")
    if value.get("subject_case_count") != SUBJECT_CASE_COUNT:
        errors.append("J1 subject must contain exactly 400 cases")
    if value.get("overlap_count") != 0:
        errors.append("J1 non-overlap receipt must report zero overlap")
    if value.get("reviewer") != REVIEWER:
        errors.append("J1 non-overlap receipt requires the independent reviewer")
    if value.get("authority") != "not-granted":
        errors.append("J1 non-overlap receipt cannot grant authority")
    receipt_sha = value.get("receipt_sha256")
    if not isinstance(receipt_sha, str) or HEX64.fullmatch(receipt_sha) is None:
        errors.append("J1 non-overlap receipt requires receipt_sha256")
    elif receipt_sha != canonical_sha256(value):
        errors.append("J1 non-overlap receipt_sha256 does not match")
    return errors


def validate_set(raw_by_reference: dict[str, bytes]) -> tuple[dict[str, dict], list[str]]:
    """Require one exact receipt for every exposed, non-holdout corpus."""
    if not isinstance(raw_by_reference, dict) or set(raw_by_reference) != set(REFERENCES):
        return {}, ["J1 non-overlap receipt set must cover every exposed corpus exactly"]
    values = {}
    errors = []
    subject_identity = None
    for reference_class in sorted(REFERENCES):
        try:
            value = decode_unique_json(raw_by_reference[reference_class])
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            errors.append(f"{reference_class}: receipt must be unique-key UTF-8 JSON")
            continue
        one_errors = validate_receipt(value, reference_class)
        errors.extend(f"{reference_class}: {error}" for error in one_errors)
        if isinstance(value, dict):
            values[reference_class] = value
            identity = (
                value.get("subject_source_sha256"),
                value.get("subject_normalized_text_set_sha256"),
                value.get("subject_case_count"),
            )
            if subject_identity is None:
                subject_identity = identity
            elif identity != subject_identity:
                errors.append("J1 non-overlap receipts do not bind one subject")
    return values, errors
