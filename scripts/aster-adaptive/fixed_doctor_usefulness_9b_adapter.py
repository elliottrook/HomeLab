"""Tool-free accepted-9B adapter for fixed Doctor usefulness cases.

Importing this module performs no network or credential access. A separately
admitted runner supplies a credential descriptor and invokes one case.
"""

from __future__ import annotations

import json
import urllib.request


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
MODEL = "aster-qwen3.5-9b"
SYSTEM = (
    "Answer one question about a fixed, read-only Aster inference observation. "
    "Use only the supplied structured observation. State the observed status, "
    "its age or timestamp, and that the evidence covers only the named Aster "
    "inference check. If the observation is unavailable, say it cannot determine "
    "health. Do not infer a cause, recommend or claim a repair, claim tool "
    "authority, or generalize to broader system health. Keep the answer concise."
)
MAX_RESPONSE_BYTES = 32_768


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def request_for(case: dict, key: str) -> urllib.request.Request:
    if not isinstance(key, str) or not key or "\n" in key or "\r" in key:
        raise ValueError("invalid source-local key")
    if set(case) != {"id", "question", "observation", "expected"}:
        raise ValueError("fixed Doctor case fields differ")
    user = {
        "question": case["question"],
        "observation": case["observation"],
    }
    payload = json.dumps({
        "model": MODEL,
        "temperature": 0,
        "stream": False,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(
                user, sort_keys=True, separators=(",", ":")
            )},
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


def _answer(raw: bytes) -> str:
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("model response is oversized")
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("model response is not JSON") from error
    if not isinstance(value, dict) or not isinstance(value.get("choices"), list):
        raise ValueError("model response envelope differs")
    if len(value["choices"]) != 1 or not isinstance(value["choices"][0], dict):
        raise ValueError("model response choice differs")
    choice = value["choices"][0]
    message = choice.get("message")
    if (
        choice.get("finish_reason") != "stop"
        or not isinstance(message, dict)
        or message.get("role", "assistant") != "assistant"
        or not isinstance(message.get("content"), str)
        or not message["content"].strip()
    ):
        raise ValueError("model response did not complete with text")
    answer = message["content"]
    if len(answer.encode("utf-8")) > 16_000:
        raise ValueError("model answer is oversized")
    return answer


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
