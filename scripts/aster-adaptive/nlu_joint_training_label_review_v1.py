"""Validate an independent semantic review of the exact M3 J1 corpus draft."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j1-label-review.v1"
SOURCE_SHA256 = "b736f0a94125e3b05238d9a54d2d6bdf107005f047c4b120cc43cbf1bf8fcefa"
REVIEWER = "stream-a-nlu-j1-label-reviewer-v1"
AUTHORITY = "not-granted"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("review_sha256", None)
    return sha256(json.dumps(copied, sort_keys=True, separators=(",", ":")).encode())


def template(source_raw: bytes) -> dict:
    if sha256(source_raw) != SOURCE_SHA256:
        raise ValueError("J1 review source SHA-256 changed")
    source = decode_unique_json(source_raw)
    cases = source.get("cases") if isinstance(source, dict) else None
    if not isinstance(cases, list) or len(cases) != 400:
        raise ValueError("J1 review source must contain exactly 400 cases")
    return {
        "schema": SCHEMA,
        "source_sha256": SOURCE_SHA256,
        "reviewer": REVIEWER,
        "authority": AUTHORITY,
        "rows": [
            {"id": case["id"], "status": "pending", "reviewed_label_id": ""}
            for case in cases
        ],
        "review_sha256": "",
    }


def validate(source_raw: bytes, review_raw: bytes) -> dict[str, object]:
    if sha256(source_raw) != SOURCE_SHA256:
        raise ValueError("J1 review source SHA-256 changed")
    try:
        source = decode_unique_json(source_raw)
        review = decode_unique_json(review_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J1 source and review must be unique-key UTF-8 JSON") from exc
    cases = source.get("cases") if isinstance(source, dict) else None
    if not isinstance(cases, list) or len(cases) != 400:
        raise ValueError("J1 review source must contain exactly 400 cases")
    if not isinstance(review, dict) or set(review) != {
        "schema", "source_sha256", "reviewer", "authority", "rows", "review_sha256",
    }:
        raise ValueError("J1 label review fields must match the fixed schema")
    if (review["schema"] != SCHEMA or review["source_sha256"] != SOURCE_SHA256
            or review["reviewer"] != REVIEWER or review["authority"] != AUTHORITY):
        raise ValueError("J1 label review metadata differs")
    if (not isinstance(review["review_sha256"], str)
            or HEX64.fullmatch(review["review_sha256"]) is None
            or review["review_sha256"] != canonical_sha256(review)):
        raise ValueError("J1 label review self-hash differs")
    rows = review["rows"]
    if not isinstance(rows, list) or len(rows) != 400:
        raise ValueError("J1 label review must contain exactly 400 rows")
    by_id = {case["id"]: case for case in cases}
    if len(by_id) != 400:
        raise ValueError("J1 review source contains duplicate identifiers")
    seen = set()
    accepted = 0
    corrected = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "id", "status", "reviewed_label_id",
        }:
            raise ValueError("J1 label review row fields differ")
        case_id = row["id"]
        if case_id not in by_id or case_id in seen:
            raise ValueError("unknown or duplicate J1 label review identifier")
        seen.add(case_id)
        if row["status"] not in {"accepted", "corrected"}:
            raise ValueError("J1 label review rows must be explicit")
        if row["reviewed_label_id"] not in ontology.CATALOGUE:
            raise ValueError("J1 label review contains an unknown label")
        if row["status"] == "accepted":
            if row["reviewed_label_id"] != by_id[case_id]["label_id"]:
                raise ValueError("accepted J1 review row changed its label")
            accepted += 1
        else:
            if row["reviewed_label_id"] == by_id[case_id]["label_id"]:
                raise ValueError("corrected J1 review row did not change its label")
            corrected += 1
    if seen != set(by_id):
        raise ValueError("J1 label review does not cover the exact source")
    return {
        "schema": "aster-nlu-j1-label-review-summary.v1",
        "source_sha256": SOURCE_SHA256,
        "review_sha256": review["review_sha256"],
        "reviewed": len(rows),
        "accepted": accepted,
        "corrected": corrected,
        "release_eligible": corrected == 0 and accepted == 400,
        "authority": AUTHORITY,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-template", type=Path, required=True)
    args = parser.parse_args(argv)
    value = template(args.source.read_bytes())
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(
        args.output_template,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({
        "schema": SCHEMA,
        "source_sha256": SOURCE_SHA256,
        "rows": 400,
        "status": "unscored-template",
        "authority": AUTHORITY,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
