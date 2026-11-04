"""Validate an independent semantic label review of one exact J2 corpus."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
import re

import nlu_j2_corpus_v1 as corpus_boundary
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-label-review.v1"
SUMMARY_SCHEMA = "aster-nlu-j2-label-review-summary.v1"
REVIEWER = "independent-j2-label-reviewer"
AUTHORITY = "not-granted"
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


def _source(raw: bytes) -> dict[str, object]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J2 review source must be unique-key UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != {
            "schema", "manifest_sha256", "data_class", "evidence_class",
            "ontology_sha256", "custodian", "authority", "cases"}:
        raise ValueError("J2 review source schema differs")
    if (value["schema"] != corpus_boundary.SCHEMA
            or value["manifest_sha256"] != corpus_boundary.MANIFEST_SHA256
            or value["custodian"] != corpus_boundary.CUSTODIAN
            or value["authority"] != AUTHORITY):
        raise ValueError("J2 review source metadata differs")
    cases = value["cases"]
    expected = len(ontology.CATALOGUE) * (
        corpus_boundary.TRAIN_PER_LABEL + corpus_boundary.VALIDATION_PER_LABEL)
    if not isinstance(cases, list) or len(cases) != expected:
        raise ValueError("J2 review source must contain exactly 960 cases")
    identifiers: set[str] = set()
    counts: Counter[tuple[str, str]] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
                "id", "split", "text", "label_id"}:
            raise ValueError("J2 review source case fields differ")
        case_id = case["id"]
        split = case["split"]
        label_id = case["label_id"]
        if (not isinstance(case_id, str)
                or corpus_boundary.CASE_ID.fullmatch(case_id) is None
                or case_id in identifiers
                or split not in {"train", "validation"}
                or not case_id.startswith(f"j2-{split}-")
                or label_id not in ontology.CATALOGUE):
            raise ValueError("J2 review source case identity differs")
        corpus_boundary.normalized_text(case["text"])
        identifiers.add(case_id)
        counts[(split, label_id)] += 1
    for label_id in ontology.CATALOGUE:
        if (counts[("train", label_id)] != corpus_boundary.TRAIN_PER_LABEL
                or counts[("validation", label_id)]
                != corpus_boundary.VALIDATION_PER_LABEL):
            raise ValueError("J2 review source is not balanced by label")
    return value


def template(source_raw: bytes) -> dict[str, object]:
    source = _source(source_raw)
    return {
        "schema": SCHEMA,
        "manifest_sha256": corpus_boundary.MANIFEST_SHA256,
        "source_sha256": sha256(source_raw),
        "custodian_id": corpus_boundary.CUSTODIAN,
        "reviewer_id": REVIEWER,
        "authority": AUTHORITY,
        "rows": [
            {"id": case["id"], "status": "pending", "reviewed_label_id": ""}
            for case in source["cases"]
        ],
        "review_sha256": "",
    }


def validate(source_raw: bytes, review_raw: bytes) -> dict[str, object]:
    source = _source(source_raw)
    try:
        review = decode_unique_json(review_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J2 label review must be unique-key UTF-8 JSON") from exc
    if not isinstance(review, dict) or set(review) != {
            "schema", "manifest_sha256", "source_sha256", "custodian_id",
            "reviewer_id", "authority", "rows", "review_sha256"}:
        raise ValueError("J2 label review fields differ")
    if (review["schema"] != SCHEMA
            or review["manifest_sha256"] != corpus_boundary.MANIFEST_SHA256
            or review["source_sha256"] != sha256(source_raw)
            or review["custodian_id"] != corpus_boundary.CUSTODIAN
            or review["reviewer_id"] != REVIEWER
            or review["custodian_id"] == review["reviewer_id"]
            or review["authority"] != AUTHORITY):
        raise ValueError("J2 label review metadata differs")
    supplied = review["review_sha256"]
    if (not isinstance(supplied, str) or HEX64.fullmatch(supplied) is None
            or supplied != review_sha256(review)):
        raise ValueError("J2 label review self-hash differs")

    by_id = {case["id"]: case for case in source["cases"]}
    if len(by_id) != 960:
        raise ValueError("J2 review source identifiers are not unique")
    rows = review["rows"]
    if not isinstance(rows, list) or len(rows) != 960:
        raise ValueError("J2 label review must contain exactly 960 rows")
    seen: set[str] = set()
    accepted = 0
    corrected = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                "id", "status", "reviewed_label_id"}:
            raise ValueError("J2 label review row fields differ")
        case_id = row["id"]
        if case_id not in by_id or case_id in seen:
            raise ValueError("unknown or duplicate J2 review identifier")
        seen.add(case_id)
        label_id = row["reviewed_label_id"]
        if label_id not in ontology.CATALOGUE:
            raise ValueError("J2 label review contains an unknown label")
        if row["status"] == "accepted":
            if label_id != by_id[case_id]["label_id"]:
                raise ValueError("accepted J2 review row changed its label")
            accepted += 1
        elif row["status"] == "corrected":
            if label_id == by_id[case_id]["label_id"]:
                raise ValueError("corrected J2 review row retained its label")
            corrected += 1
        else:
            raise ValueError("J2 label review row is not explicit")
    if seen != set(by_id):
        raise ValueError("J2 label review does not cover the exact source")
    return {
        "schema": SUMMARY_SCHEMA,
        "manifest_sha256": corpus_boundary.MANIFEST_SHA256,
        "source_sha256": sha256(source_raw),
        "review_sha256": supplied,
        "reviewed": 960,
        "accepted": accepted,
        "corrected": corrected,
        "release_eligible": accepted == 960 and corrected == 0,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }
