"""Validate a complete independent quality review of one exact J2 corpus."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
import re

import nlu_j2_label_review_v1 as label_review
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-quality-review.v1"
SUMMARY_SCHEMA = "aster-nlu-j2-quality-review-summary.v1"
REVIEWER = "independent-j2-quality-reviewer"
AUTHORITY = "not-granted"
DIMENSIONS = ("grammar", "naturalness", "semantic_label", "split_quality")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def review_sha256(value: dict[str, object]) -> str:
    copied = copy.deepcopy(value)
    copied.pop("review_sha256", None)
    return sha256(canonical(copied))


def template(source_raw: bytes) -> dict[str, object]:
    source = label_review._source(source_raw)
    return {
        "schema": SCHEMA,
        "manifest_sha256": source["manifest_sha256"],
        "source_sha256": sha256(source_raw),
        "custodian_id": source["custodian"],
        "reviewer_id": REVIEWER,
        "authority": AUTHORITY,
        "rows": [{
            "id": case["id"],
            "judgments": {dimension: None for dimension in DIMENSIONS},
            "notes": "",
        } for case in source["cases"]],
        "review_sha256": "",
    }


def validate(source_raw: bytes, review_raw: bytes) -> dict[str, object]:
    source = label_review._source(source_raw)
    try:
        review = decode_unique_json(review_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J2 quality review must be unique-key UTF-8 JSON") from exc
    if not isinstance(review, dict) or set(review) != {
            "schema", "manifest_sha256", "source_sha256", "custodian_id",
            "reviewer_id", "authority", "rows", "review_sha256"}:
        raise ValueError("J2 quality review fields differ")
    if (review["schema"] != SCHEMA
            or review["manifest_sha256"] != source["manifest_sha256"]
            or review["source_sha256"] != sha256(source_raw)
            or review["custodian_id"] != source["custodian"]
            or review["reviewer_id"] != REVIEWER
            or review["reviewer_id"] in {
                source["custodian"], label_review.REVIEWER}
            or review["authority"] != AUTHORITY):
        raise ValueError("J2 quality review metadata differs")
    supplied = review["review_sha256"]
    if (not isinstance(supplied, str) or HEX64.fullmatch(supplied) is None
            or supplied != review_sha256(review)):
        raise ValueError("J2 quality review self-hash differs")

    expected_ids = {case["id"] for case in source["cases"]}
    rows = review["rows"]
    if not isinstance(rows, list) or len(rows) != 960:
        raise ValueError("J2 quality review must contain exactly 960 rows")
    seen: set[str] = set()
    failures: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "judgments", "notes"}:
            raise ValueError("J2 quality review row fields differ")
        case_id = row["id"]
        judgments = row["judgments"]
        notes = row["notes"]
        if (case_id not in expected_ids or case_id in seen
                or not isinstance(judgments, dict)
                or tuple(sorted(judgments)) != tuple(sorted(DIMENSIONS))
                or any(type(judgments[item]) is not bool for item in DIMENSIONS)
                or not isinstance(notes, str) or len(notes.encode()) > 512):
            raise ValueError("invalid J2 quality review row")
        failed = [item for item in DIMENSIONS if not judgments[item]]
        if (failed and not notes.strip()) or (not failed and notes):
            raise ValueError("J2 quality review notes do not match judgments")
        failures.update(failed)
        seen.add(case_id)
    if seen != expected_ids:
        raise ValueError("J2 quality review does not cover the exact source")
    return {
        "schema": SUMMARY_SCHEMA,
        "manifest_sha256": source["manifest_sha256"],
        "source_sha256": sha256(source_raw),
        "review_sha256": supplied,
        "reviewed": 960,
        "grammar_failures": failures["grammar"],
        "naturalness_failures": failures["naturalness"],
        "semantic_label_failures": failures["semantic_label"],
        "split_quality_failures": failures["split_quality"],
        "release_eligible": not failures,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }
