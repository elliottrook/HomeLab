"""Validate the frozen, source-only SA3 expanded-evidence quality packet.

This module does not call a model or read production evidence.  It binds the
synthetic packet and separate answer key, projects only model-visible fields,
and delegates completed-answer grading to the existing fair scorer.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from sa3_fair_scorer import score


SOURCE_IDS = frozenset({
    "doctor_status",
    "forgejo_status",
    "gateway_status",
    "inference_health",
    "netbox_network",
    "gateway_config_identity",
    "backup_protection",
    "gateway_log_aggregate",
})
CASE_FIELDS = frozenset({"id", "prompt", "observations", "capabilities"})
OBSERVATION_FIELDS = frozenset({"source", "state", "summary"})


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _load(path: Path):
    return json.loads(path.read_text(), object_pairs_hook=_unique_object)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def validate_visible_packet(packet: dict) -> dict:
    if not isinstance(packet, dict) or set(packet) != {
        "schema_version", "packet_id", "data_class", "constraints", "cases"
    }:
        raise ValueError("invalid packet envelope")
    if packet["schema_version"] != 1 or packet["data_class"] != "synthetic-sanitized-frozen":
        raise ValueError("invalid packet identity")
    if packet["constraints"] != {"authority": "none", "effect": "none", "tools": "none"}:
        raise ValueError("unsafe packet constraints")
    cases = packet["cases"]
    if not isinstance(cases, list) or len(cases) != 20:
        raise ValueError("exactly twenty cases required")

    ids = []
    source_counts = Counter()
    visible = []
    for case in cases:
        if not isinstance(case, dict) or frozenset(case) != CASE_FIELDS:
            raise ValueError("invalid case shape")
        ident = case["id"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("invalid case identity")
        ids.append(ident)
        if not isinstance(case["prompt"], str) or not 20 <= len(case["prompt"]) <= 600:
            raise ValueError("invalid sanitized prompt")
        observations = case["observations"]
        if not isinstance(observations, list) or len(observations) > len(SOURCE_IDS):
            raise ValueError("invalid observations")
        seen = set()
        for observation in observations:
            if not isinstance(observation, dict) or frozenset(observation) != OBSERVATION_FIELDS:
                raise ValueError("invalid observation shape")
            source = observation["source"]
            if source not in SOURCE_IDS or source in seen:
                raise ValueError("invalid observation source")
            seen.add(source)
            source_counts[source] += 1
            if observation["state"] not in {"ok", "warn", "fail", "unavailable"}:
                raise ValueError("invalid observation state")
            if not isinstance(observation["summary"], str) or not observation["summary"]:
                raise ValueError("invalid observation summary")
        capabilities = case["capabilities"]
        if not isinstance(capabilities, list) or not capabilities:
            raise ValueError("visible capabilities required")
        capability_ids = []
        for capability in capabilities:
            if (not isinstance(capability, dict) or set(capability) != {"id", "description"}
                    or capability["id"] not in SOURCE_IDS
                    or capability["id"] in capability_ids
                    or not isinstance(capability["description"], str)
                    or not capability["description"].strip()):
                raise ValueError("invalid visible capability")
            capability_ids.append(capability["id"])
        visible.append({"id": ident, "capabilities": capabilities})

    if set(source_counts) != SOURCE_IDS or min(source_counts.values()) < 2:
        raise ValueError("packet does not cover every expanded source twice")
    return {
        "packet_id": packet["packet_id"],
        "case_count": len(cases),
        "source_counts": dict(sorted(source_counts.items())),
        "packet_sha256": hashlib.sha256(_canonical(packet)).hexdigest(),
        "visible_cases": visible,
    }


def validate_packet(packet: dict, keys: dict) -> dict:
    visible_result = validate_visible_packet(packet)
    ids = [case["id"] for case in packet["cases"]]
    if not isinstance(keys, dict) or set(keys) != {"schema_version", "packet_id", "case_answer_keys"}:
        raise ValueError("invalid key envelope")
    if keys["schema_version"] != 1 or keys["packet_id"] != packet["packet_id"]:
        raise ValueError("packet/key mismatch")
    answer_keys = keys["case_answer_keys"]
    if not isinstance(answer_keys, list) or {item.get("id") for item in answer_keys} != set(ids):
        raise ValueError("key identity mismatch")
    for item in answer_keys:
        if not isinstance(item, dict) or set(item) != {
            "id", "acceptable_check_sets", "acceptable_outcomes", "must_abstain"
        }:
            raise ValueError("invalid answer key shape")
        options = item["acceptable_check_sets"]
        if (not isinstance(options, list) or not options
                or any(not isinstance(option, list)
                       or len(option) != len(set(option))
                       or not set(option) <= SOURCE_IDS
                       for option in options)):
            raise ValueError("invalid answer key checks")
        outcomes = item["acceptable_outcomes"]
        if (not isinstance(outcomes, list) or not outcomes
                or len(outcomes) != len(set(outcomes))
                or not set(outcomes) <= {"plan", "clarify"}):
            raise ValueError("invalid answer key outcomes")
        if type(item["must_abstain"]) is not bool:
            raise ValueError("invalid abstention key")
        if item["must_abstain"] and (outcomes != ["clarify"] or options != [[]]):
            raise ValueError("contradictory abstention key")
    if sum(item.get("must_abstain") is True for item in answer_keys) < 4:
        raise ValueError("at least four abstention cases required")

    return {
        "schema": "aster-sa3-expanded-quality-freeze.v1",
        "packet_id": visible_result["packet_id"],
        "case_count": visible_result["case_count"],
        "source_counts": visible_result["source_counts"],
        "abstention_cases": sum(item.get("must_abstain") is True for item in answer_keys),
        "packet_sha256": visible_result["packet_sha256"],
        "keys_sha256": hashlib.sha256(_canonical(keys)).hexdigest(),
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
        "routing_authorized": False,
        "repair_authorized": False,
        "visible_cases": visible_result["visible_cases"],
    }


def grade(packet: dict, keys: dict, predictions: list, reviews: list) -> dict:
    freeze = validate_packet(packet, keys)
    result = score(freeze["visible_cases"], keys["case_answer_keys"], predictions, reviews)
    result["packet_id"] = freeze["packet_id"]
    result["packet_sha256"] = freeze["packet_sha256"]
    result["keys_sha256"] = freeze["keys_sha256"]
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("keys", type=Path)
    args = parser.parse_args(argv)
    result = validate_packet(_load(args.packet), _load(args.keys))
    result.pop("visible_cases")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
