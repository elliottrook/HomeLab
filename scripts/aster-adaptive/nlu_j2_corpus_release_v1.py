"""Cross-bind one J2 corpus, complete label review, and custody receipt."""
from __future__ import annotations

import hashlib
import json

import nlu_j2_corpus_v1 as corpus_boundary
import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_label_review_v1 as label_review
from nlu_threshold_policy import decode_unique_json


AUTHORITY = "not-granted"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalized_set_sha256(source_raw: bytes) -> str:
    value = decode_unique_json(source_raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list):
        raise ValueError("J2 release source has no cases")
    texts = {corpus_boundary.normalized_text(case.get("text"))
             for case in cases if isinstance(case, dict)}
    if len(texts) != 960:
        raise ValueError("J2 release source text set differs")
    return sha256(("\n".join(sorted(texts)) + "\n").encode())


def release(source_raw: bytes, review_raw: bytes,
            custody_raw: bytes) -> dict[str, object]:
    review = label_review.validate(source_raw, review_raw)
    receipt = custody.corpus_receipt(custody_raw)
    if receipt["corpus_sha256"] != sha256(source_raw):
        raise ValueError("J2 corpus receipt does not bind the source bytes")
    if receipt["normalized_text_set_sha256"] != _normalized_set_sha256(source_raw):
        raise ValueError("J2 corpus receipt does not bind the normalized text set")
    if receipt["label_review_sha256"] != sha256(review_raw):
        raise ValueError("J2 corpus receipt does not bind the review bytes")
    if (receipt["custodian_id"] != corpus_boundary.CUSTODIAN
            or receipt["reviewer_id"] != label_review.REVIEWER
            or not review["release_eligible"]
            or review["accepted"] != 960 or review["corrected"] != 0):
        raise ValueError("J2 corpus review or custody is not release eligible")
    return {
        "schema": "aster-nlu-j2-corpus-release-summary.v1",
        "manifest_sha256": corpus_boundary.MANIFEST_SHA256,
        "corpus_sha256": sha256(source_raw),
        "normalized_text_set_sha256": receipt["normalized_text_set_sha256"],
        "label_review_sha256": sha256(review_raw),
        "custody_receipt_sha256": sha256(custody_raw),
        "rows": 960,
        "accepted": 960,
        "corrected": 0,
        "reference_count": 8,
        "normalized_overlap": 0,
        "corpus_release_eligible": True,
        "training_authorized": False,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }
