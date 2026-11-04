"""Validate a disjoint synthetic corpus for the preregistered J2 candidate."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import unicodedata

import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-training-corpus.v1"
DATA_CLASS = "synthetic"
EVIDENCE_CLASS = "preregistered-training"
AUTHORITY = "not-granted"
CUSTODIAN = "independent-j2-corpus-custodian"
MANIFEST_SHA256 = "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
TRAIN_PER_LABEL = 48
VALIDATION_PER_LABEL = 12
REFERENCE_COUNT = 8
CASE_ID = re.compile(r"j2-(train|validation)-[a-z0-9-]{6,80}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 4096:
        raise ValueError("invalid J2 request text")
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def ontology_sha256() -> str:
    return sha256(ontology._catalogue_text().encode())


def _reference(name: str, raw: bytes) -> tuple[set[str], dict[str, object]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from exc
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{name} must contain a nonempty cases list")
    texts = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("text"), str):
            raise ValueError(f"{name} contains an invalid case")
        normalized = normalized_text(case["text"])
        if normalized in texts:
            raise ValueError(f"{name} contains duplicate normalized text")
        texts.add(normalized)
    text_set = ("\n".join(sorted(texts)) + "\n").encode()
    return texts, {"artifact_sha256": sha256(raw),
                   "normalized_text_set_sha256": sha256(text_set),
                   "case_count": len(texts)}


def validate_corpus(raw: bytes, references: dict[str, bytes]) -> dict[str, object]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("J2 corpus must be unique-key UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != {
            "schema", "manifest_sha256", "data_class", "evidence_class",
            "ontology_sha256", "custodian", "authority", "cases"}:
        raise ValueError("J2 corpus fields differ from the preregistration")
    if (value["schema"] != SCHEMA or value["manifest_sha256"] != MANIFEST_SHA256
            or value["data_class"] != DATA_CLASS
            or value["evidence_class"] != EVIDENCE_CLASS
            or value["ontology_sha256"] != ontology_sha256()
            or value["custodian"] != CUSTODIAN
            or value["authority"] != AUTHORITY):
        raise ValueError("J2 corpus metadata differs")
    if not isinstance(references, dict) or len(references) != REFERENCE_COUNT:
        raise ValueError("J2 corpus requires exactly eight explicit reference corpora")

    reference_texts: set[str] = set()
    reference_summary = {}
    for name in sorted(references):
        if not isinstance(name, str) or not name:
            raise ValueError("invalid J2 reference name")
        texts, summary = _reference(name, references[name])
        reference_texts.update(texts)
        reference_summary[name] = summary

    labels = set(ontology.CATALOGUE)
    expected_count = len(labels) * (TRAIN_PER_LABEL + VALIDATION_PER_LABEL)
    cases = value["cases"]
    if not isinstance(cases, list) or len(cases) != expected_count:
        raise ValueError(f"J2 corpus must contain exactly {expected_count} cases")
    identifiers, texts = set(), set()
    counts: Counter[tuple[str, str]] = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "split", "text", "label_id"}:
            raise ValueError("J2 case fields differ from the preregistration")
        case_id, split, label_id = case["id"], case["split"], case["label_id"]
        if (not isinstance(case_id, str) or CASE_ID.fullmatch(case_id) is None
                or case_id in identifiers or split not in {"train", "validation"}
                or not case_id.startswith(f"j2-{split}-") or label_id not in labels):
            raise ValueError("invalid or duplicate J2 case identity")
        identifiers.add(case_id)
        normalized = normalized_text(case["text"])
        if normalized in texts:
            raise ValueError("duplicate normalized J2 request")
        if normalized in reference_texts:
            raise ValueError("J2 request overlaps an exposed reference corpus")
        texts.add(normalized)
        counts[(split, label_id)] += 1

    for label_id in labels:
        if counts[("train", label_id)] != TRAIN_PER_LABEL:
            raise ValueError("J2 train split is not balanced by label")
        if counts[("validation", label_id)] != VALIDATION_PER_LABEL:
            raise ValueError("J2 validation split is not balanced by label")
    text_set = ("\n".join(sorted(texts)) + "\n").encode()
    return {"schema": "aster-nlu-j2-training-corpus-summary.v1",
            "manifest_sha256": MANIFEST_SHA256,
            "source_sha256": sha256(raw),
            "normalized_text_set_sha256": sha256(text_set),
            "ontology_sha256": ontology_sha256(),
            "case_count": len(cases), "train_count": 768,
            "validation_count": 192, "label_count": 16,
            "references": reference_summary, "overlap_count": 0,
            "authority": AUTHORITY, "automatic_routing": "off"}
