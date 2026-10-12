"""No-tool accepted-9B request adapter for fictional Aster answer cases.

Importing this module makes no network call. An admitted run supplies the
source-local key and calls invoke. Never put a key or raw answer in Git.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen

from a1_9b_synthetic_answer_probe import ENDPOINT, MODEL, SYSTEM


def request_for(case: dict, key: str) -> Request:
    if not isinstance(key, str) or not key or "\n" in key or "\r" in key:
        raise ValueError("invalid source-local key")
    if case.get("maximum_tool_scope") != "none":
        raise ValueError("connected tools forbidden")
    user = {"request": case["fictional_user_request"],
            "clock": case["frozen_clock"],
            "private_context_locality_constraint": case["private_context_locality_constraint"],
            "context": case["synthetic_source_records"]}
    payload = json.dumps({"model": MODEL, "temperature": 0,
                          "stream": False, "max_tokens": 256,
                          "messages": [{"role": "system", "content": SYSTEM},
                                       {"role": "user", "content": json.dumps(user, sort_keys=True)}]},
                         sort_keys=True).encode()
    return Request(ENDPOINT, data=payload,
                   headers={"Authorization": "Bearer " + key,
                            "Content-Type": "application/json"})


def invoke(case: dict, key: str, request_fn=urlopen) -> str:
    with request_fn(request_for(case, key), timeout=60) as response:
        body = json.load(response)
    choice = body["choices"][0]
    answer = choice["message"]["content"]
    if choice.get("finish_reason") != "stop" or not isinstance(answer, str):
        raise ValueError("invalid terminal model response")
    return answer
