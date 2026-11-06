"""Validate the independently authored, sealed J2 evaluation boundary."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re

import nlu_j2_corpus_v1 as corpus_boundary
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-sealed-evaluation.v1"
SUMMARY_SCHEMA = "aster-nlu-j2-sealed-evaluation-summary.v1"
MANIFEST_SHA256 = corpus_boundary.MANIFEST_SHA256
CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
CORPUS_SET_SHA256 = "a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0"
CUSTODIAN = "independent-j2-evaluation-custodian"
AUTHORITY = "not-granted"
CASE_ID = re.compile(r"j2-evaluation-[a-z0-9-]{6,80}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def normalized_set(value: object, expected: int) -> set[str]:
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != expected:
        raise ValueError("J2 evaluation source case count changed")
    texts: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("text"), str):
            raise ValueError("J2 evaluation source contains an invalid case")
        text = corpus_boundary.normalized_text(case["text"])
        if text in texts:
            raise ValueError("J2 evaluation contains duplicate normalized text")
        texts.add(text)
    return texts


def set_sha256(texts: set[str]) -> str:
    return sha256(("\n".join(sorted(texts)) + "\n").encode())


def validate(evaluation_raw: bytes, corpus_raw: bytes) -> dict[str, object]:
    if sha256(corpus_raw) != CORPUS_SHA256:
        raise ValueError("J2 evaluation comparison corpus changed")
    try:
        corpus = decode_unique_json(corpus_raw)
        evaluation = decode_unique_json(evaluation_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J2 evaluation inputs must be unique-key UTF-8 JSON") from exc
    corpus_texts = normalized_set(corpus, 960)
    if set_sha256(corpus_texts) != CORPUS_SET_SHA256:
        raise ValueError("J2 evaluation comparison text set changed")
    if not isinstance(evaluation, dict) or set(evaluation) != {
            "schema", "manifest_sha256", "data_class", "evidence_class",
            "ontology_sha256", "custodian", "sealed_before_training",
            "trainer_access", "authority", "cases"}:
        raise ValueError("J2 evaluation fields differ from preregistration")
    if (evaluation["schema"] != SCHEMA
            or evaluation["manifest_sha256"] != MANIFEST_SHA256
            or evaluation["data_class"] != "synthetic"
            or evaluation["evidence_class"] != "preregistered-sealed-evaluation"
            or evaluation["ontology_sha256"] != corpus_boundary.ontology_sha256()
            or evaluation["custodian"] != CUSTODIAN
            or evaluation["sealed_before_training"] is not True
            or evaluation["trainer_access"] != "forbidden"
            or evaluation["authority"] != AUTHORITY):
        raise ValueError("J2 evaluation metadata differs from preregistration")

    cases = evaluation["cases"]
    labels = set(ontology.CATALOGUE)
    identifiers: set[str] = set()
    counts: Counter[str] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "text", "label_id"}:
            raise ValueError("J2 evaluation case fields changed")
        case_id = case["id"]
        label_id = case["label_id"]
        if (not isinstance(case_id, str) or CASE_ID.fullmatch(case_id) is None
                or case_id in identifiers or label_id not in labels):
            raise ValueError("J2 evaluation case identity or label changed")
        identifiers.add(case_id)
        counts[label_id] += 1
    if any(counts[label] != 2 for label in labels):
        raise ValueError("J2 evaluation is not balanced at two cases per label")
    evaluation_texts = normalized_set(evaluation, 32)
    intersection = corpus_texts.intersection(evaluation_texts)
    if intersection:
        raise ValueError("J2 evaluation overlaps the released corpus")
    return {
        "schema": SUMMARY_SCHEMA,
        "manifest_sha256": MANIFEST_SHA256,
        "evaluation_sha256": sha256(evaluation_raw),
        "normalized_text_set_sha256": set_sha256(evaluation_texts),
        "cases": 32,
        "labels": 16,
        "cases_per_label": 2,
        "intersection_count": 0,
        "sealed_before_training": True,
        "trainer_access": "forbidden",
        "content_in_summary": False,
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }
