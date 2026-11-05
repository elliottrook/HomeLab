"""Content-free custody receipts required before any J2 corpus or training."""
from __future__ import annotations

import hashlib
import json
import re

from nlu_threshold_policy import decode_unique_json


MANIFEST_SHA256 = "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
AUTHORITY = "not-granted"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _decode(raw: bytes, schema: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError("J2 custody receipt schema changed")
    supplied = value.get("receipt_sha256")
    copied = dict(value); copied.pop("receipt_sha256", None)
    if not isinstance(supplied, str) or supplied != _digest(copied):
        raise ValueError("J2 custody receipt self-hash changed")
    if value.get("manifest_sha256") != MANIFEST_SHA256:
        raise ValueError("J2 preregistration binding changed")
    if value.get("authority") != AUTHORITY:
        raise ValueError("J2 custody receipt grants authority")
    return value


def _identity(value: object) -> str:
    if (not isinstance(value, str) or not IDENTITY.fullmatch(value)
            or value != value.strip() or value != value.casefold()):
        raise ValueError("J2 custody identity is not canonical")
    return value


def corpus_receipt(raw: bytes) -> dict[str, object]:
    value = _decode(raw, "aster-nlu-j2-corpus-custody.v1")
    if set(value) != {"schema", "manifest_sha256", "custodian_id", "reviewer_id",
                      "corpus_sha256", "normalized_text_set_sha256",
                      "label_review_sha256", "quality_review_sha256",
                      "train_rows", "validation_rows",
                      "labels", "overlap_reference_count", "normalized_overlap",
                      "content_in_receipt", "authority", "receipt_sha256"}:
        raise ValueError("J2 corpus receipt fields changed")
    identities = (_identity(value["custodian_id"]),
                  _identity(value["reviewer_id"]))
    if identities[0] == identities[1]:
        raise ValueError("J2 corpus custody roles are not distinct")
    for field in ("corpus_sha256", "normalized_text_set_sha256",
                  "label_review_sha256", "quality_review_sha256"):
        if not isinstance(value[field], str) or not HEX64.fullmatch(value[field]):
            raise ValueError("J2 corpus digest changed")
    if (value["train_rows"] != 768 or value["validation_rows"] != 192
            or value["labels"] != 16 or value["overlap_reference_count"] != 8
            or value["normalized_overlap"] != 0 or value["content_in_receipt"] is not False):
        raise ValueError("J2 corpus custody facts changed")
    return value


def evaluation_receipt(raw: bytes) -> dict[str, object]:
    value = _decode(raw, "aster-nlu-j2-evaluation-seal.v1")
    if set(value) != {"schema", "manifest_sha256", "custodian_id",
                      "evaluation_sha256", "normalized_text_set_sha256", "cases",
                      "labels", "cases_per_label", "sealed_before_training",
                      "trainer_access", "content_in_receipt", "authority",
                      "receipt_sha256"}:
        raise ValueError("J2 evaluation receipt fields changed")
    _identity(value["custodian_id"])
    for field in ("evaluation_sha256", "normalized_text_set_sha256"):
        if not isinstance(value[field], str) or not HEX64.fullmatch(value[field]):
            raise ValueError("J2 evaluation digest changed")
    if (value["cases"] != 32 or value["labels"] != 16
            or value["cases_per_label"] != 2 or value["sealed_before_training"] is not True
            or value["trainer_access"] != "forbidden"
            or value["content_in_receipt"] is not False):
        raise ValueError("J2 evaluation seal changed")
    return value


def admit(corpus_raw: bytes, evaluation_raw: bytes) -> dict[str, object]:
    corpus = corpus_receipt(corpus_raw)
    evaluation = evaluation_receipt(evaluation_raw)
    identities = {corpus["custodian_id"], corpus["reviewer_id"],
                  evaluation["custodian_id"]}
    if len(identities) != 3:
        raise ValueError("J2 corpus, label and evaluation custody are not distinct")
    if corpus["normalized_text_set_sha256"] == evaluation["normalized_text_set_sha256"]:
        raise ValueError("J2 corpus and evaluation text sets are not distinct")
    return {"schema": "aster-nlu-j2-training-admission.v1",
            "manifest_sha256": MANIFEST_SHA256,
            "corpus_receipt_sha256": hashlib.sha256(corpus_raw).hexdigest(),
            "evaluation_receipt_sha256": hashlib.sha256(evaluation_raw).hexdigest(),
            "roles_distinct": True, "content_in_receipts": False,
            "training_authorized": False, "authority": AUTHORITY,
            "automatic_routing": "off"}
