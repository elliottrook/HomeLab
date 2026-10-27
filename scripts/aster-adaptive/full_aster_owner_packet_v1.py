"""Validate an owner-only full-Aster packet and emit a content-free manifest."""
from __future__ import annotations

import hashlib
import json

import full_aster_benchmark_proposal_v1 as proposal


SCHEMA = "aster-full-path-owner-packet.v1"
MANIFEST_SCHEMA = "aster-full-path-owner-packet-manifest.v1"


def _canonical(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def validate(document):
    if (not isinstance(document, dict)
            or set(document) != {"schema", "fictional", "cases"}
            or document["schema"] != SCHEMA
            or document["fictional"] is not True
            or not isinstance(document["cases"], list)
            or len(document["cases"]) != 24):
        raise ValueError("owner packet boundary differs")
    fields = {"id", "family", "request", "context", "expected_outcome",
              "maximum_tool_scope", "rubric"}
    rubric_fields = {"required_facts", "prohibited_claims", "citation_required",
                     "completion_criteria"}
    ids = set()
    counts = {family: 0 for family in proposal.FAMILIES}
    outcomes = set()
    for case in document["cases"]:
        if not isinstance(case, dict) or set(case) != fields:
            raise ValueError("owner case fields differ")
        if (not isinstance(case["id"], str) or not case["id"]
                or case["id"] in ids or case["family"] not in proposal.FAMILIES
                or not isinstance(case["request"], str) or not case["request"].strip()
                or not isinstance(case["context"], list)
                or case["expected_outcome"] not in proposal.OUTCOMES
                or case["maximum_tool_scope"] not in proposal.TOOLS):
            raise ValueError("owner case value differs")
        ids.add(case["id"])
        counts[case["family"]] += 1
        outcomes.add(case["expected_outcome"])
        rubric = case["rubric"]
        if (not isinstance(rubric, dict) or set(rubric) != rubric_fields
                or any(not isinstance(rubric[key], list) for key in
                       ("required_facts", "prohibited_claims", "completion_criteria"))
                or any(not isinstance(item, str) or not item for key in
                       ("required_facts", "prohibited_claims", "completion_criteria")
                       for item in rubric[key])
                or not rubric["completion_criteria"]
                or type(rubric["citation_required"]) is not bool):
            raise ValueError("owner rubric differs")
    if set(counts.values()) != {4}:
        raise ValueError("owner family counts differ")
    if not {"justified_abstention", "clarification", "policy_denial"} <= outcomes:
        raise ValueError("owner negative outcomes differ")
    return document


def content_free_manifest(document):
    validate(document)
    raw = _canonical(document)
    counts = {family: 0 for family in proposal.FAMILIES}
    outcomes = {outcome: 0 for outcome in proposal.OUTCOMES}
    for case in document["cases"]:
        counts[case["family"]] += 1
        outcomes[case["expected_outcome"]] += 1
    return {"schema": MANIFEST_SCHEMA,
            "packet_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_bytes": len(raw), "cases": 24,
            "families": dict(sorted(counts.items())),
            "outcomes": dict(sorted(outcomes.items())),
            "fictional": True, "content_exported": False,
            "authority": "not-granted"}
