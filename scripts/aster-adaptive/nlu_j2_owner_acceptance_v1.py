"""Fail-closed owner acceptance for the exact J2 corpus-v4 release candidate."""
from __future__ import annotations

import hashlib
import json

from nlu_threshold_policy import decode_unique_json


CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
NORMALIZED_SET_SHA256 = "a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0"
LABEL_REVIEW_SHA256 = "896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028"
QUALITY_REVIEW_SHA256 = "f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f"
SCHEMA = "aster-nlu-j2-owner-acceptance.v1"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def receipt_sha256(value: dict[str, object]) -> str:
    copied = dict(value)
    copied.pop("receipt_sha256", None)
    return hashlib.sha256(canonical(copied)).hexdigest()


def accepted_record(owner_id: str) -> dict[str, object]:
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ValueError("J2 owner identity is required")
    value: dict[str, object] = {
        "schema": SCHEMA,
        "owner_id": owner_id.strip(),
        "decision": "accept",
        "scope": "corpus-release-only",
        "corpus_sha256": CORPUS_SHA256,
        "normalized_text_set_sha256": NORMALIZED_SET_SHA256,
        "label_review_sha256": LABEL_REVIEW_SHA256,
        "quality_review_sha256": QUALITY_REVIEW_SHA256,
        "training_authorized": False,
        "sealed_evaluation_access": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }
    value["receipt_sha256"] = receipt_sha256(value)
    return value


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {
        "schema", "owner_id", "decision", "scope", "corpus_sha256",
        "normalized_text_set_sha256", "label_review_sha256",
        "quality_review_sha256", "training_authorized",
        "sealed_evaluation_access", "authority", "automatic_routing",
        "receipt_sha256",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("J2 owner acceptance shape changed")
    if (value["schema"] != SCHEMA
            or not isinstance(value["owner_id"], str)
            or not value["owner_id"].strip()
            or value["decision"] != "accept"
            or value["scope"] != "corpus-release-only"
            or value["corpus_sha256"] != CORPUS_SHA256
            or value["normalized_text_set_sha256"] != NORMALIZED_SET_SHA256
            or value["label_review_sha256"] != LABEL_REVIEW_SHA256
            or value["quality_review_sha256"] != QUALITY_REVIEW_SHA256
            or value["training_authorized"] is not False
            or value["sealed_evaluation_access"] is not False
            or value["authority"] != "not-granted"
            or value["automatic_routing"] != "off"
            or value["receipt_sha256"] != receipt_sha256(value)):
        raise ValueError("J2 owner acceptance is ineligible")
    return value

