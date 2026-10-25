"""Validate private NLU calibration cases and emit a content-free release.

Raw case text and labels remain separate owner-only inputs. The returned
release contains only opaque identifiers and digests and grants no authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

from nlu_calibration_release import canonical_sha256 as release_sha256
from nlu_calibration_release import validate_release
from nlu_threshold_policy import FAMILIES, decode_unique_json, sha256


SOURCE_SCHEMA = "aster-nlu-calibration-cases.v1"
LABEL_SCHEMA = "aster-nlu-calibration-labels.v1"
CANDIDATE_SHA256 = "456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897"
DECISION_SHA256 = "8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da"
CASE_CUSTODIAN = "stream-a-nlu-calibration-case-custodian-v1"
LABEL_REVIEWER = "stream-a-nlu-calibration-label-reviewer-v1"
SCORING_OPERATOR = "stream-a-nlu-calibration-scoring-operator-v1"
CAPABILITIES = {
    "backup.delete",
    "calendar.read",
    "facts.answer",
    "home.control",
    "lab.change",
    "lab.read",
    "local.join",
    "timer.control",
    "web.publish",
    "web.read",
}
LABEL_KEYS = {
    "request_family",
    "sensitivity",
    "capability_needs",
    "ambiguity",
    "disposition",
    "reason",
}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_new_private(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _load(raw: bytes, name: str) -> dict:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def validate_source(source_raw: bytes, development_raw: bytes) -> dict:
    source = _load(source_raw, "calibration source")
    if set(source) != {
        "schema", "data_class", "evidence_class", "candidate_bundle_sha256",
        "accepted_decision_sha256", "cases",
    }:
        raise ValueError("calibration source fields must match the fixed schema")
    if source["schema"] != SOURCE_SCHEMA:
        raise ValueError("invalid calibration source schema")
    if source["data_class"] != "synthetic" or source["evidence_class"] != "disjoint-calibration":
        raise ValueError("calibration source must be synthetic disjoint calibration")
    if source["candidate_bundle_sha256"] != CANDIDATE_SHA256:
        raise ValueError("calibration source candidate changed")
    if source["accepted_decision_sha256"] != DECISION_SHA256:
        raise ValueError("calibration source decision changed")
    cases = source["cases"]
    if not isinstance(cases, list) or len(cases) != 60:
        raise ValueError("calibration source must contain exactly 60 cases")

    development = _load(development_raw, "development fixture")
    development_cases = development.get("cases")
    if not isinstance(development_cases, list):
        raise ValueError("invalid development fixture")
    development_texts = {
        normalized_text(case["text"])
        for case in development_cases
        if isinstance(case, dict) and isinstance(case.get("text"), str)
    }
    ids: set[str] = set()
    texts: set[str] = set()
    counts: Counter[str] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "family", "text"}:
            raise ValueError("calibration case fields must match the fixed schema")
        case_id = case["id"]
        if not isinstance(case_id, str) or IDENTIFIER.fullmatch(case_id) is None or case_id in ids:
            raise ValueError("invalid or duplicate calibration case identifier")
        ids.add(case_id)
        if case["family"] not in FAMILIES:
            raise ValueError("invalid calibration request family")
        counts[case["family"]] += 1
        text = case["text"]
        if not isinstance(text, str) or not text.strip() or len(text.encode()) > 4096:
            raise ValueError("invalid calibration request text")
        normalized = normalized_text(text)
        if normalized in texts:
            raise ValueError("duplicate normalized calibration request")
        if normalized in development_texts:
            raise ValueError("calibration request overlaps development fixture")
        texts.add(normalized)
    if counts != Counter({family: 10 for family in FAMILIES}):
        raise ValueError("calibration source must contain ten cases per family")
    # The set digest is deterministic while revealing neither individual text
    # hashes nor ordering metadata in the content-free receipt.
    text_set_raw = ("\n".join(sorted(texts)) + "\n").encode()
    return {
        "source_sha256": sha256(source_raw),
        "normalized_text_set_sha256": sha256(text_set_raw),
        "case_count": 60,
        "family_counts": {family: counts[family] for family in FAMILIES},
    }


def _validate_label(label: object, family: str) -> None:
    if not isinstance(label, dict) or set(label) != LABEL_KEYS:
        raise ValueError("label fields must match request-interpretation dimensions")
    if label["request_family"] != family:
        raise ValueError("label family does not match case custody family")
    if label["sensitivity"] not in {"public", "internal", "personal"}:
        raise ValueError("invalid label sensitivity")
    capabilities = label["capability_needs"]
    if (
        not isinstance(capabilities, list)
        or len(capabilities) > 8
        or len(capabilities) != len(set(capabilities))
        or any(type(item) is not str or item not in CAPABILITIES for item in capabilities)
    ):
        raise ValueError("invalid label capability needs")
    ambiguity, disposition, reason = label["ambiguity"], label["disposition"], label["reason"]
    allowed = {
        "route": {("clear", "understood")},
        "clarify": {("ambiguous", "ambiguous")},
        "abstain": {("ambiguous", "ambiguous"), ("clear", "unsupported")},
        "deny": {("clear", "policy-denied")},
    }
    if disposition not in allowed or (ambiguity, reason) not in allowed[disposition]:
        raise ValueError("invalid label disposition semantics")
    if (family == "unsupported") != (reason == "unsupported"):
        raise ValueError("unsupported label semantics disagree")


def build_release(source_raw: bytes, label_raw: bytes, development_raw: bytes) -> tuple[dict, dict]:
    summary = validate_source(source_raw, development_raw)
    source = _load(source_raw, "calibration source")
    labels = _load(label_raw, "calibration labels")
    if set(labels) != {"schema", "source_sha256", "reviewer", "labels"}:
        raise ValueError("calibration label fields must match the fixed schema")
    if labels["schema"] != LABEL_SCHEMA or labels["source_sha256"] != sha256(source_raw):
        raise ValueError("calibration labels do not bind the exact source")
    if labels["reviewer"] != LABEL_REVIEWER:
        raise ValueError("calibration labels require the independent reviewer")
    rows = labels["labels"]
    if not isinstance(rows, list) or len(rows) != 60:
        raise ValueError("calibration labels must contain exactly 60 rows")
    by_id = {case["id"]: case for case in source["cases"]}
    seen: set[str] = set()
    release_cases = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "label"}:
            raise ValueError("calibration label row fields must match the fixed schema")
        case_id = row["id"]
        if case_id not in by_id or case_id in seen:
            raise ValueError("unknown or duplicate calibration label identifier")
        seen.add(case_id)
        case = by_id[case_id]
        _validate_label(row["label"], case["family"])
        case_raw = canonical_json(case)
        one_label_raw = canonical_json(row["label"])
        receipt = {
            "schema": "aster-nlu-calibration-label-review.v1",
            "reviewer": LABEL_REVIEWER,
            "case_sha256": sha256(case_raw),
            "label_sha256": sha256(one_label_raw),
            "status": "accepted",
            "authority": "not-granted",
        }
        release_cases.append({
            "id": case_id,
            "family": case["family"],
            "case_sha256": receipt["case_sha256"],
            "label_sha256": receipt["label_sha256"],
            "review_receipt_sha256": sha256(canonical_json(receipt)),
        })
    if seen != set(by_id):
        raise ValueError("calibration labels do not cover the exact source")
    release_cases.sort(key=lambda value: value["id"])
    release = {
        "schema": "aster-nlu-calibration-release.v1",
        "status": "sealed",
        "release_id": "nlu-calibration-v1",
        "target_cases": 60,
        "family_targets": {family: 10 for family in FAMILIES},
        "roles": {
            "case_custodian": CASE_CUSTODIAN,
            "label_reviewer": LABEL_REVIEWER,
            "scoring_operator": SCORING_OPERATOR,
        },
        "candidate_bundle_sha256": CANDIDATE_SHA256,
        "cases": release_cases,
        "release_sha256": "",
        "authority": "not-granted",
    }
    release["release_sha256"] = release_sha256(release)
    errors = validate_release(release)
    if errors:
        raise ValueError("invalid derived calibration release: " + "; ".join(errors))
    return release, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive one content-free NLU calibration release from separate private cases and labels."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        release, summary = build_release(
            args.source.read_bytes(),
            args.labels.read_bytes(),
            args.development.read_bytes(),
        )
        raw = canonical_json(release)
        write_new_private(args.output, raw)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": release["schema"],
        "release_id": release["release_id"],
        "release_sha256": sha256(raw),
        "case_count": summary["case_count"],
        "source_sha256": summary["source_sha256"],
        "normalized_text_set_sha256": summary["normalized_text_set_sha256"],
        "authority": release["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
