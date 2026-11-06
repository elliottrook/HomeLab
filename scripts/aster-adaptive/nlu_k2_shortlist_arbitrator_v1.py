"""Strict accepted-9B arbitrator for one fixed four-label K2 shortlist.

This module performs no transport and grants no authority. It builds one
tool-free request, validates one response, and applies the tightening-only
deterministic guard. Request text is never retained in its output record.
"""
from __future__ import annotations

import copy
import json

import nlu_deterministic_guard_v1 as guard
import nlu_local_model_adapter as contract
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


MODEL = "aster-qwen3.5-9b"
SHORTLIST_SIZE = 4
MAX_TOKENS = 32
LABEL_FIELDS = ontology.LABEL_FIELDS
CATALOGUE = ontology.CATALOGUE


def _validate_shortlist(shortlist_ids: list[str]) -> tuple[str, ...]:
    if (
        not isinstance(shortlist_ids, list)
        or len(shortlist_ids) != SHORTLIST_SIZE
        or any(type(item) is not str or item not in CATALOGUE
               for item in shortlist_ids)
        or len(set(shortlist_ids)) != SHORTLIST_SIZE
    ):
        raise ValueError("shortlist must contain four unique known label IDs")
    return tuple(shortlist_ids)


def _offered_catalogue(shortlist: tuple[str, ...]) -> str:
    rows = [{"label_id": label_id, **CATALOGUE[label_id]}
            for label_id in shortlist]
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))


def response_schema(shortlist_ids: list[str]) -> dict[str, object]:
    shortlist = _validate_shortlist(shortlist_ids)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["label_id"],
        "properties": {
            "label_id": {"type": "string", "enum": list(shortlist)},
        },
    }


def build_payload(request_text: str, shortlist_ids: list[str]) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    shortlist = _validate_shortlist(shortlist_ids)
    policy = (
        "Classify one assistant request for evaluation only. Choose exactly "
        "one label_id from the four offered coherent labels and return only "
        "a JSON object containing that label_id. Do not return reasoning, "
        "confidence, free text, a provider, a route, a tool, permission or a "
        "result. Offered labels: " + _offered_catalogue(shortlist)
    )
    value = {
        "model": MODEL,
        "temperature": 0,
        "seed": 20261106,
        "stream": False,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": policy},
            {"role": "user", "content": request_text},
        ],
        "response_format": {
            "type": "json_object",
            "schema": response_schema(list(shortlist)),
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def parse_selection(response_raw: bytes, shortlist_ids: list[str]) -> str:
    shortlist = _validate_shortlist(shortlist_ids)
    envelope = decode_unique_json(response_raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("response envelope differs")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response choice differs")
    choice = choices[0]
    if (
        not isinstance(choice, dict)
        or set(choice) != {"message", "finish_reason"}
        or choice["finish_reason"] != "stop"
    ):
        raise ValueError("response completion differs")
    message = choice["message"]
    if (
        not isinstance(message, dict)
        or set(message) != {"role", "content"}
        or message["role"] != "assistant"
        or not isinstance(message["content"], str)
    ):
        raise ValueError("response message differs")
    selection = decode_unique_json(message["content"].encode())
    if not isinstance(selection, dict) or set(selection) != {"label_id"}:
        raise ValueError("selection fields differ")
    label_id = selection["label_id"]
    if type(label_id) is not str or label_id not in shortlist:
        raise ValueError("selection was not offered")
    return label_id


def interpret(request_text: str, response_raw: bytes,
              shortlist_ids: list[str]) -> dict[str, object]:
    label_id = parse_selection(response_raw, shortlist_ids)
    selected = copy.deepcopy(CATALOGUE[label_id])
    guarded = guard.apply(request_text, selected)
    restrictiveness = {"route": 0, "clarify": 0, "abstain": 1, "deny": 2}
    reviewed = guarded if (
        restrictiveness[guarded["disposition"]]
        > restrictiveness[selected["disposition"]]
    ) else selected
    contract._validate_semantics(reviewed)
    return {
        "selected_label_id": label_id,
        "guard_changed": reviewed != selected,
        "interpretation": reviewed,
        "authority": "not-granted",
    }


def result_record(*, case_id: str, shortlist_ids: list[str],
                  response_raw: bytes, request_text: str,
                  latency_seconds: float) -> dict[str, object]:
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case ID is required")
    if type(latency_seconds) not in {int, float} or latency_seconds < 0:
        raise ValueError("latency must be nonnegative")
    result = interpret(request_text, response_raw, shortlist_ids)
    return {
        "case_id": case_id,
        "shortlist_ids": list(_validate_shortlist(shortlist_ids)),
        "selected_label_id": result["selected_label_id"],
        "guard_changed": result["guard_changed"],
        "interpretation": result["interpretation"],
        "latency_seconds": float(latency_seconds),
        "authority": "not-granted",
    }
