"""Validate a private K2 shadow fixture and emit only a content-free receipt."""
from __future__ import annotations

import hashlib
import json

import nlu_k2_shadow_fixture_preregistration_v1 as prereg
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


CASE_KEYS = {"id", "request_text", "expected_label_id", "data_class"}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _digest_set(values: object, name: str) -> set[str]:
    if (not isinstance(values, (list, tuple, set))
            or any(not isinstance(value, str) or len(value) != 64
                   or any(character not in "0123456789abcdef" for character in value)
                   for value in values)):
        raise ValueError(f"invalid {name} digest set")
    return set(values)


def _identity_set(values: object, name: str) -> set[str]:
    if (not isinstance(values, (list, tuple, set))
            or any(not isinstance(value, str) or not value for value in values)):
        raise ValueError(f"invalid {name} identity set")
    return set(values)


def seal(records: object, *, development_case_ids: object,
         development_request_sha256: object, sealed_case_ids: object,
         sealed_request_sha256: object, custodian_id: str,
         label_reviewer_id: str) -> dict[str, object]:
    summary = prereg.validate(prereg.artifact())
    if (not isinstance(custodian_id, str) or not custodian_id
            or not isinstance(label_reviewer_id, str) or not label_reviewer_id
            or custodian_id == label_reviewer_id):
        raise ValueError("K2 shadow custody roles changed")
    if not isinstance(records, list) or len(records) != 60:
        raise ValueError("K2 shadow fixture count changed")
    forbidden_ids = (_identity_set(development_case_ids, "development case")
                     | _identity_set(sealed_case_ids, "sealed case"))
    forbidden_hashes = (_digest_set(development_request_sha256, "development request")
                        | _digest_set(sealed_request_sha256, "sealed request"))
    seen_ids: set[str] = set(); seen_hashes: set[str] = set()
    families = {family: 0 for family in FAMILIES}; label_rows = []
    for record in records:
        if not isinstance(record, dict) or set(record) != CASE_KEYS:
            raise ValueError("K2 shadow fixture fields changed")
        case_id = record["id"]
        if (not isinstance(case_id, str) or not 1 <= len(case_id) <= 128
                or case_id in seen_ids or case_id in forbidden_ids):
            raise ValueError("K2 shadow fixture identity overlaps or changed")
        text = record["request_text"]
        if (not isinstance(text, str) or text != text.strip()
                or not 1 <= len(text) <= 1024
                or any(ord(character) < 32 and character not in "\t\n"
                       for character in text)):
            raise ValueError("K2 shadow fixture request changed")
        request_sha = hashlib.sha256(text.encode()).hexdigest()
        if request_sha in seen_hashes or request_sha in forbidden_hashes:
            raise ValueError("K2 shadow fixture request overlaps")
        label_id = record["expected_label_id"]
        if label_id not in ontology.CATALOGUE:
            raise ValueError("K2 shadow fixture label changed")
        if record["data_class"] != "synthetic-sanitized-S0":
            raise ValueError("K2 shadow fixture data class changed")
        family = ontology.CATALOGUE[label_id]["request_family"]
        families[family] += 1; seen_ids.add(case_id); seen_hashes.add(request_sha)
        label_rows.append({"id": case_id, "expected_label_id": label_id})
    if any(count != 10 for count in families.values()):
        raise ValueError("K2 shadow fixture family balance changed")
    private_fixture = {
        "schema": "aster-nlu-k2-shadow-private-fixture.v1",
        "source_class": "representative-sanitized-S0", "cases": records,
    }
    return {
        "schema": "aster-nlu-k2-shadow-fixture-custody-receipt.v1",
        "case_count": 60, "request_families": 6, "cases_per_family": 10,
        "fixture_sha256": hashlib.sha256(canonical(private_fixture)).hexdigest(),
        "case_id_set_sha256": hashlib.sha256(
            canonical(sorted(seen_ids))).hexdigest(),
        "request_set_sha256": hashlib.sha256(
            canonical(sorted(seen_hashes))).hexdigest(),
        "label_set_sha256": hashlib.sha256(
            canonical(sorted(label_rows, key=lambda row: row["id"]))).hexdigest(),
        "preregistration_sha256": summary["preregistration_sha256"],
        "zero_development_or_sealed_overlap": True,
        "custodian_and_label_reviewer_distinct": True,
        "private_request_text_exported": False,
        "effect_authorized": False, "authority": "not-granted",
        "automatic_routing": "off",
    }
