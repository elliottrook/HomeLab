"""Tool-free accepted-9B adapter for limitation-calibrated Doctor answers.

This source-only successor keeps the v1 transport and evidence boundary while
requiring an explicit statement that the fixed observation cannot establish a
cause or repair.  Importing it performs no network or credential access.
"""

from __future__ import annotations

from fixed_doctor_usefulness_9b_adapter import (
    ENDPOINT,
    MAX_RESPONSE_BYTES,
    MODEL,
    _NoRedirect,
    _answer,
)
import json
import urllib.request


SYSTEM = (
    "Answer one question about a fixed, read-only Aster inference observation. "
    "Use only the supplied structured observation. State the observed status, "
    "its age or timestamp, and that the evidence covers only the named Aster "
    "inference check. Explicitly state that this observation alone cannot "
    "establish a cause or a repair. If the observation is unavailable, say it "
    "cannot determine health, cause, or repair. Do not recommend or claim a "
    "repair, claim tool authority, or generalize to broader system health. Keep "
    "the answer concise."
)


def request_for(case: dict, key: str) -> urllib.request.Request:
    if not isinstance(key, str) or not key or "\n" in key or "\r" in key:
        raise ValueError("invalid source-local key")
    if set(case) != {"id", "question", "observation", "expected"}:
        raise ValueError("fixed Doctor case fields differ")
    payload = json.dumps({
        "model": MODEL,
        "temperature": 0,
        "stream": False,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "question": case["question"],
                "observation": case["observation"],
            }, sort_keys=True, separators=(",", ":"))},
        ],
    }, sort_keys=True, separators=(",", ":")).encode()
    return urllib.request.Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
    )


def invoke(case: dict, key: str, *, timeout: float = 60, opener=None) -> str:
    if type(timeout) not in {int, float} or not 0 < timeout <= 60:
        raise ValueError("invalid bounded timeout")
    transport = opener if opener is not None else urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect()
    )
    with transport.open(request_for(case, key), timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        status = response.status
    if status != 200:
        raise ConnectionError("local model endpoint unavailable")
    return _answer(raw)
