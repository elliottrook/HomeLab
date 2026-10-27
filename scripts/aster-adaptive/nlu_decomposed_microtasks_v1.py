"""Decomposed semantic microtasks with deterministic interpretation policy."""
from __future__ import annotations

import json

import nlu_semantic_proposal_v1 as policy
from nlu_threshold_policy import decode_unique_json

MODEL = "aster-qwen3.5-9b"
TASKS = {
    "action": ("answer", "read", "change", "control", "research", "publish", "delete", "unsupported"),
    "domain": ("facts", "household", "lab", "calendar", "web", "backup", "unknown"),
    "privacy_hint": ("public", "internal", "personal"),
    "referent_complete": (True, False),
    "safety_override": (True, False),
    "joins_sources": (True, False),
}
PROMPTS = {
    "action": "Choose the single semantic action. answer gives factual explanation; read inspects state; change mutates software or lab state; control operates a physical household device; research looks up external information; publish sends information outward; delete removes data or backups; unsupported asks for an impossible or unknowable result.",
    "domain": "Choose the single subject domain: facts, household, lab, calendar, web, backup or unknown. Software services, servers and Doctor diagnostics are lab. Physical home devices are household.",
    "privacy_hint": "Choose public, internal or personal for the subject matter. Personal requires a person's private context. Home or lab state is internal. Public facts, lottery results and market prices are public; words such as me in tell me do not make the subject personal.",
    "referent_complete": "Return true only when the request names enough of its object or subject to act or answer. An unresolved it, this or that is false.",
    "safety_override": "Return true only when the request asks to disable, bypass, defeat or remove a safety control or interlock.",
    "joins_sources": "Return true only when the request explicitly compares, combines or cross-checks two distinct sources.",
}


def build_payload(request_text: str, task: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    if task not in TASKS:
        raise ValueError("unknown microtask")
    values = TASKS[task]
    schema = {"type": "boolean"} if isinstance(values[0], bool) else {"type": "string", "enum": list(values)}
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 16,
        "messages": [
            {"role": "system", "content": "Classify one request for evaluation only. " + PROMPTS[task] + " Return exactly one JSON object with only the field " + task + ". Do not execute, route, grant authority or name a tool."},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": {
            "type": "object", "additionalProperties": False,
            "required": [task], "properties": {task: schema},
        }},
    }, sort_keys=True, separators=(",", ":")).encode()


def parse_response(task: str, raw: bytes):
    if task not in TASKS:
        raise ValueError("unknown microtask")
    envelope = decode_unique_json(raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("response envelope differs")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response choice differs")
    choice = choices[0]
    if not isinstance(choice, dict) or set(choice) != {"message", "finish_reason"} or choice["finish_reason"] != "stop":
        raise ValueError("response completion differs")
    message = choice["message"]
    if not isinstance(message, dict) or set(message) != {"role", "content"} or message["role"] != "assistant":
        raise ValueError("response message differs")
    value = decode_unique_json(message["content"].encode())
    if not isinstance(value, dict) or set(value) != {task} or value[task] not in TASKS[task]:
        raise ValueError("microtask value differs")
    if isinstance(TASKS[task][0], bool) and type(value[task]) is not bool:
        raise ValueError("microtask boolean differs")
    return value[task]


def interpret(request_text: str, answers: dict) -> dict:
    if not isinstance(answers, dict) or set(answers) != set(TASKS):
        raise ValueError("microtask answers differ")
    for task, value in answers.items():
        if value not in TASKS[task] or (isinstance(TASKS[task][0], bool) and type(value) is not bool):
            raise ValueError("microtask answer value differs")
    return policy.interpret(request_text, answers)
