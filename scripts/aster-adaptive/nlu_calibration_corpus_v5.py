"""Derive the exact Candidate-v9 calibration-v5 content-free release.

This versioned tool pins the reviewed source, blind labels, custody manifest,
public development fixture, normalized text set, candidate, and decision. Raw
request text and labels never enter the release artifact.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import nlu_calibration_corpus as base
from nlu_calibration_release import canonical_sha256 as release_sha256
from nlu_calibration_release import validate_release
from nlu_threshold_policy import FAMILIES, sha256


SOURCE_SCHEMA = "aster-nlu-calibration-cases.v1"
LABEL_SCHEMA = "aster-nlu-calibration-labels.v1"
MANIFEST_SCHEMA = "aster-nlu-calibration-custody-manifest.v1"
RELEASE_ID = "nlu-calibration-v5"
CANDIDATE_SHA256 = "1941b4754c5195e11b623479f63cb368cacfea64a7adc3223bf22794e3b825f5"
DECISION_SHA256 = "8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da"
EXPECTED_SOURCE_SHA256 = "50b6a36b64e8942eb83dd8769f52c52b6fa4a0e7a1d42adeebd7be2c5157c676"
EXPECTED_LABEL_SHA256 = "5cf947586cac331efe08f375a4a22aceca0ea0f9b1bea92ae466a0fec2a811ae"
EXPECTED_MANIFEST_SHA256 = "87e1a39de0fe7f6ef6585f51727f131251df6ad665108b843c4d9ab2db544e8b"
EXPECTED_DEVELOPMENT_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
EXPECTED_NORMALIZED_TEXT_SET_SHA256 = (
    "be93e28afa6de2a5a6c525c1659563292196c05a84bcff1412b38795d39d2423"
)
CASE_CUSTODIAN = "stream-a-nlu-calibration-v5-case-custodian"
LABEL_REVIEWER = "stream-a-nlu-calibration-v5-label-reviewer"
SCORING_OPERATOR = "stream-a-nlu-calibration-v5-scoring-operator"

canonical_json = base.canonical_json
write_new_private = base.write_new_private
LABEL_KEYS = base.LABEL_KEYS
_validate_label = base._validate_label


def validate_manifest(manifest_raw: bytes, source_raw: bytes) -> None:
    if sha256(manifest_raw) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("calibration-v5 custody manifest SHA-256 changed")
    manifest = base._load(manifest_raw, "calibration-v5 custody manifest")
    if set(manifest) != {
        "schema", "release_id", "custodian_role", "case_count", "files", "authority",
    }:
        raise ValueError("calibration-v5 custody manifest fields must match the fixed schema")
    if manifest["schema"] != MANIFEST_SCHEMA:
        raise ValueError("invalid calibration-v5 custody manifest schema")
    if manifest["release_id"] != RELEASE_ID:
        raise ValueError("calibration-v5 custody manifest release changed")
    if manifest["custodian_role"] != CASE_CUSTODIAN:
        raise ValueError("calibration-v5 custody manifest role changed")
    if manifest["case_count"] != 60:
        raise ValueError("calibration-v5 custody manifest must bind exactly 60 cases")
    if manifest["authority"] != "not-granted":
        raise ValueError("calibration-v5 custody manifest must not grant authority")
    files = manifest["files"]
    if not isinstance(files, dict) or set(files) != {"cases.json", "custodian-design.json"}:
        raise ValueError("calibration-v5 custody manifest file set changed")
    case_file = files["cases.json"]
    if (
        not isinstance(case_file, dict)
        or set(case_file) != {"bytes", "sha256"}
        or case_file["bytes"] != len(source_raw)
        or case_file["sha256"] != sha256(source_raw)
    ):
        raise ValueError("calibration-v5 custody manifest does not bind the exact source")
    design_file = files["custodian-design.json"]
    if (
        not isinstance(design_file, dict)
        or set(design_file) != {"bytes", "sha256"}
        or type(design_file["bytes"]) is not int
        or design_file["bytes"] <= 0
        or not isinstance(design_file["sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", design_file["sha256"]) is None
    ):
        raise ValueError("invalid calibration-v5 custody design binding")


def validate_source(source_raw: bytes, development_raw: bytes) -> dict:
    if sha256(source_raw) != EXPECTED_SOURCE_SHA256:
        raise ValueError("calibration-v5 source SHA-256 changed")
    if sha256(development_raw) != EXPECTED_DEVELOPMENT_SHA256:
        raise ValueError("public development fixture SHA-256 changed")
    source = base._load(source_raw, "calibration-v5 source")
    if set(source) != {
        "schema", "data_class", "evidence_class", "candidate_bundle_sha256",
        "accepted_decision_sha256", "cases",
    }:
        raise ValueError("calibration-v5 source fields must match the fixed schema")
    if source["schema"] != SOURCE_SCHEMA:
        raise ValueError("invalid calibration-v5 source schema")
    if source["data_class"] != "synthetic" or source["evidence_class"] != "disjoint-calibration":
        raise ValueError("calibration-v5 source must be synthetic disjoint calibration")
    if source["candidate_bundle_sha256"] != CANDIDATE_SHA256:
        raise ValueError("calibration-v5 source candidate changed")
    if source["accepted_decision_sha256"] != DECISION_SHA256:
        raise ValueError("calibration-v5 source decision changed")
    cases = source["cases"]
    if not isinstance(cases, list) or len(cases) != 60:
        raise ValueError("calibration-v5 source must contain exactly 60 cases")

    development = base._load(development_raw, "development fixture")
    development_cases = development.get("cases")
    if not isinstance(development_cases, list):
        raise ValueError("invalid development fixture")
    development_texts = {
        base.normalized_text(case["text"])
        for case in development_cases
        if isinstance(case, dict) and isinstance(case.get("text"), str)
    }
    identifiers: set[str] = set()
    texts: set[str] = set()
    counts: Counter[str] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "family", "text"}:
            raise ValueError("calibration-v5 case fields must match the fixed schema")
        case_id = case["id"]
        if (
            not isinstance(case_id, str)
            or base.IDENTIFIER.fullmatch(case_id) is None
            or case_id in identifiers
        ):
            raise ValueError("invalid or duplicate calibration-v5 case identifier")
        identifiers.add(case_id)
        if case["family"] not in FAMILIES:
            raise ValueError("invalid calibration-v5 request family")
        counts[case["family"]] += 1
        text = case["text"]
        if not isinstance(text, str) or not text.strip() or len(text.encode()) > 4096:
            raise ValueError("invalid calibration-v5 request text")
        normalized = base.normalized_text(text)
        if normalized in texts:
            raise ValueError("duplicate normalized calibration-v5 request")
        if normalized in development_texts:
            raise ValueError("calibration-v5 request overlaps development fixture")
        texts.add(normalized)
    if counts != Counter({family: 10 for family in FAMILIES}):
        raise ValueError("calibration-v5 source must contain ten cases per family")
    text_set_raw = ("\n".join(sorted(texts)) + "\n").encode()
    text_set_sha256 = sha256(text_set_raw)
    if text_set_sha256 != EXPECTED_NORMALIZED_TEXT_SET_SHA256:
        raise ValueError("calibration-v5 normalized text-set SHA-256 changed")
    return {
        "source_sha256": sha256(source_raw),
        "normalized_text_set_sha256": text_set_sha256,
        "case_count": 60,
        "family_counts": {family: counts[family] for family in FAMILIES},
    }


def build_release(
    source_raw: bytes,
    label_raw: bytes,
    manifest_raw: bytes,
    development_raw: bytes,
) -> tuple[dict, dict]:
    validate_manifest(manifest_raw, source_raw)
    summary = validate_source(source_raw, development_raw)
    if sha256(label_raw) != EXPECTED_LABEL_SHA256:
        raise ValueError("calibration-v5 labels SHA-256 changed")
    source = base._load(source_raw, "calibration-v5 source")
    labels = base._load(label_raw, "calibration-v5 labels")
    if set(labels) != {"schema", "source_sha256", "reviewer", "labels"}:
        raise ValueError("calibration-v5 label fields must match the fixed schema")
    if labels["schema"] != LABEL_SCHEMA or labels["source_sha256"] != sha256(source_raw):
        raise ValueError("calibration-v5 labels do not bind the exact source")
    if labels["reviewer"] != LABEL_REVIEWER:
        raise ValueError("calibration-v5 labels require the independent reviewer")
    rows = labels["labels"]
    if not isinstance(rows, list) or len(rows) != 60:
        raise ValueError("calibration-v5 labels must contain exactly 60 rows")

    by_id = {case["id"]: case for case in source["cases"]}
    seen: set[str] = set()
    release_cases = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "label"}:
            raise ValueError("calibration-v5 label row fields must match the fixed schema")
        case_id = row["id"]
        if case_id not in by_id or case_id in seen:
            raise ValueError("unknown or duplicate calibration-v5 label identifier")
        seen.add(case_id)
        case = by_id[case_id]
        base._validate_label(row["label"], case["family"])
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
        raise ValueError("calibration-v5 labels do not cover the exact source")
    release_cases.sort(key=lambda value: value["id"])

    release = {
        "schema": "aster-nlu-calibration-release.v1",
        "status": "sealed",
        "release_id": RELEASE_ID,
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
        raise ValueError("invalid derived calibration-v5 release: " + "; ".join(errors))
    return release, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive the exact Candidate-v9 calibration-v5 content-free release."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        release, summary = build_release(
            args.source.read_bytes(),
            args.labels.read_bytes(),
            args.manifest.read_bytes(),
            args.development.read_bytes(),
        )
        raw = canonical_json(release)
        write_new_private(args.output, raw)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": release["schema"],
        "release_id": release["release_id"],
        "artifact_sha256": sha256(raw),
        "canonical_self_sha256": release["release_sha256"],
        "case_count": summary["case_count"],
        "source_sha256": summary["source_sha256"],
        "normalized_text_set_sha256": summary["normalized_text_set_sha256"],
        "authority": release["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
