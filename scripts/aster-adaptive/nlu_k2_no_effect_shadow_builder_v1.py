"""Build content-minimized K2 no-effect shadow evidence from sanitized S0 rows."""
from __future__ import annotations

import hashlib
import math

import nlu_k2_no_effect_shadow_v1 as shadow
import nlu_k2_route_selector_v1 as selector
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


INPUT_KEYS = {"id", "request_text", "expected_label_id", "final_label_id",
              "candidate_accepted", "baseline_status", "latency_seconds"}


def _text(value: object) -> str:
    if (not isinstance(value, str) or not 1 <= len(value) <= 1024
            or value != value.strip()
            or any(ord(character) < 32 and character not in "\t\n"
                   for character in value)):
        raise ValueError("K2 shadow sanitized request changed")
    return value


def build(records: object) -> dict[str, object]:
    if not isinstance(records, list) or len(records) != shadow.CASE_COUNT:
        raise ValueError("K2 shadow input count changed")
    cases = []; seen = set(); families = {family: 0 for family in FAMILIES}
    for record in records:
        if not isinstance(record, dict) or set(record) != INPUT_KEYS:
            raise ValueError("K2 shadow input fields changed")
        case_id = record["id"]
        if (not isinstance(case_id, str) or not 1 <= len(case_id) <= 128
                or case_id in seen or not case_id[0].isalnum()
                or any(not (character.isalnum() or character in "_.:-")
                       for character in case_id)):
            raise ValueError("K2 shadow input identity changed")
        seen.add(case_id)
        request_text = _text(record["request_text"])
        expected_id = record["expected_label_id"]
        final_id = record["final_label_id"]
        if expected_id not in ontology.CATALOGUE or final_id not in ontology.CATALOGUE:
            raise ValueError("K2 shadow input label changed")
        families[ontology.CATALOGUE[expected_id]["request_family"]] += 1
        if type(record["candidate_accepted"]) is not bool:
            raise ValueError("K2 shadow input acceptance changed")
        if record["baseline_status"] not in shadow.ROUTES:
            raise ValueError("K2 shadow baseline changed")
        latency = record["latency_seconds"]
        if (type(latency) not in {int, float} or not math.isfinite(latency)
                or not 0 <= latency <= 45):
            raise ValueError("K2 shadow latency changed")
        _, proposal = selector.select(
            request_id=case_id, principal_ref="shadow-principal",
            interpretation=ontology.CATALOGUE[final_id], now=1,
            ttl_seconds=300)
        if record["candidate_accepted"]:
            status = proposal["status"]
            backend = proposal["backend_id"]
            egress = proposal["egress"]
        else:
            status, backend, egress = "abstain", None, "none"
        cases.append({
            "id": case_id,
            "request_sha256": hashlib.sha256(request_text.encode()).hexdigest(),
            "expected_label_id": expected_id,
            "final_label_id": final_id,
            "candidate_accepted": record["candidate_accepted"],
            "route_status": status, "backend_id": backend, "egress": egress,
            "baseline_status": record["baseline_status"],
            "latency_seconds": float(latency),
            "route_proposal_sha256":
                hashlib.sha256(selector.canonical(proposal)).hexdigest(),
        })
    if any(count != shadow.PER_FAMILY for count in families.values()):
        raise ValueError("K2 shadow input family balance changed")
    value = {
        "schema": shadow.SCHEMA, "status": "sealed",
        "candidate_manifest_sha256": selector.ENGINE_SHA256,
        "selector_policy_sha256": selector.POLICY_SHA256,
        "source_class": "representative-sanitized-S0",
        "case_count": shadow.CASE_COUNT, "cases": cases,
        "model_requests": shadow.CASE_COUNT, "retries": 0,
        "response_errors": 0, "route_execution_attempted": False,
        "provider_egress_attempted": False,
        "external_cost_microunits": 0, "authority": "not-granted",
        "automatic_routing": "off", "release_sha256": "",
    }
    value["release_sha256"] = shadow.release_sha256(value)
    shadow.validate(value)
    return value
