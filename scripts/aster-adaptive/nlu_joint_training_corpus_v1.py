"""Validate a preregistered synthetic corpus for the M3 J1 joint classifier.

This module defines custody and non-overlap only.  It does not generate cases,
train a model, select a threshold, call an endpoint, or grant routing authority.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import unicodedata

import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j1-training-corpus.v1"
DATA_CLASS = "synthetic"
EVIDENCE_CLASS = "preregistered-training"
AUTHORITY = "not-granted"
CUSTODIAN = "stream-a-nlu-j1-corpus-custodian-v1"
TRAIN_PER_LABEL = 20
VALIDATION_PER_LABEL = 5
CASE_ID = re.compile(r"j1-(train|validation)-[a-z0-9-]{6,80}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 4096:
        raise ValueError("invalid J1 request text")
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def ontology_sha256() -> str:
    return sha256(ontology._catalogue_text().encode())


def _reference_texts(name: str, raw: bytes) -> tuple[set[str], dict[str, object]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from exc
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{name} must contain a nonempty cases list")
    texts: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("text"), str):
            raise ValueError(f"{name} contains an invalid case")
        text = normalized_text(case["text"])
        if text in texts:
            raise ValueError(f"{name} contains duplicate normalized text")
        texts.add(text)
    text_set_raw = ("\n".join(sorted(texts)) + "\n").encode()
    return texts, {
        "artifact_sha256": sha256(raw),
        "normalized_text_set_sha256": sha256(text_set_raw),
        "case_count": len(texts),
    }


def validate_corpus(raw: bytes, references: dict[str, bytes]) -> dict[str, object]:
    """Return a content-free summary for one exact, disjoint J1 corpus."""
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J1 corpus must be unique-key UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema", "data_class", "evidence_class", "ontology_sha256",
        "custodian", "authority", "cases",
    }:
        raise ValueError("J1 corpus fields must match the fixed schema")
    if (value["schema"] != SCHEMA or value["data_class"] != DATA_CLASS
            or value["evidence_class"] != EVIDENCE_CLASS
            or value["ontology_sha256"] != ontology_sha256()
            or value["custodian"] != CUSTODIAN
            or value["authority"] != AUTHORITY):
        raise ValueError("J1 corpus metadata differs")
    if not isinstance(references, dict) or not references:
        raise ValueError("J1 corpus requires explicit reference corpora")

    reference_texts: set[str] = set()
    reference_summary: dict[str, object] = {}
    for name in sorted(references):
        if not isinstance(name, str) or not name:
            raise ValueError("invalid J1 reference name")
        texts, summary = _reference_texts(name, references[name])
        reference_texts.update(texts)
        reference_summary[name] = summary

    labels = set(ontology.CATALOGUE)
    expected_count = len(labels) * (TRAIN_PER_LABEL + VALIDATION_PER_LABEL)
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != expected_count:
        raise ValueError(f"J1 corpus must contain exactly {expected_count} cases")
    identifiers: set[str] = set()
    texts: set[str] = set()
    counts: Counter[tuple[str, str]] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "split", "text", "label_id",
        }:
            raise ValueError("J1 case fields must match the fixed schema")
        case_id = case["id"]
        split = case["split"]
        label_id = case["label_id"]
        if (not isinstance(case_id, str) or CASE_ID.fullmatch(case_id) is None
                or case_id in identifiers or split not in {"train", "validation"}
                or not case_id.startswith(f"j1-{split}-")
                or label_id not in labels):
            raise ValueError("invalid or duplicate J1 case identity")
        identifiers.add(case_id)
        text = normalized_text(case["text"])
        if text in texts:
            raise ValueError("duplicate normalized J1 request")
        if text in reference_texts:
            raise ValueError("J1 request overlaps an evaluation corpus")
        texts.add(text)
        counts[(split, label_id)] += 1

    for label_id in labels:
        if counts[("train", label_id)] != TRAIN_PER_LABEL:
            raise ValueError("J1 train split is not balanced by label")
        if counts[("validation", label_id)] != VALIDATION_PER_LABEL:
            raise ValueError("J1 validation split is not balanced by label")
    text_set_raw = ("\n".join(sorted(texts)) + "\n").encode()
    return {
        "schema": "aster-nlu-j1-training-corpus-summary.v1",
        "source_sha256": sha256(raw),
        "normalized_text_set_sha256": sha256(text_set_raw),
        "ontology_sha256": ontology_sha256(),
        "case_count": len(cases),
        "train_count": len(labels) * TRAIN_PER_LABEL,
        "validation_count": len(labels) * VALIDATION_PER_LABEL,
        "label_count": len(labels),
        "references": reference_summary,
        "overlap_count": 0,
        "authority": AUTHORITY,
    }
