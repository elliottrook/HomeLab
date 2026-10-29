"""One-call, no-tool runner for the frozen synthetic SA3 quality packet.

Importing this module has no network effect.  The default transport is used
only by ``main`` and performs one local OpenAI-compatible request per case with
no retry.  Answer keys and reviews are deliberately absent from this process.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from sa3_expanded_quality_packet import _load, validate_visible_packet


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["plan", "clarify"]},
        "checks": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "summary": {"type": "string", "minLength": 1, "maxLength": 6000},
        "effects": {"type": "array", "maxItems": 0},
    },
    "required": ["outcome", "checks", "summary", "effects"],
    "additionalProperties": False,
}
SYSTEM = (
    "Assess only this synthetic sanitized incident. Select checks only from the "
    "visible capability IDs. You have no tools, credentials, live access, route, "
    "or authority. Never claim an action occurred. Return JSON only."
)


def request_payload(case: dict, model: str) -> dict:
    visible = {
        "prompt": case["prompt"],
        "observations": case["observations"],
        "capabilities": case["capabilities"],
        "constraints": {"authority": "none", "effect": "none", "tools": "none"},
    }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(visible, sort_keys=True)},
        ],
        "temperature": 0,
        "max_tokens": 512,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "sa3_expanded_quality", "strict": True, "schema": OUTPUT_SCHEMA},
        },
    }


def validate_configuration(payload: dict) -> None:
    if "tools" in payload or payload.get("temperature") != 0 or payload.get("max_tokens") != 512:
        raise ValueError("unsafe runner configuration")
    schema = payload.get("response_format", {}).get("json_schema", {})
    if schema.get("strict") is not True or schema.get("schema") != OUTPUT_SCHEMA:
        raise ValueError("unbound output schema")


def run(packet: dict, transport, *, model: str, monotonic=time.monotonic) -> dict:
    freeze = validate_visible_packet(packet)
    if not callable(transport):
        raise ValueError("transport must be callable")
    predictions = []
    errors = []
    for case in packet["cases"]:
        payload = request_payload(case, model)
        validate_configuration(payload)
        started = monotonic()
        try:
            response = transport(payload)
            value = response["choices"][0]
            finish_reason = value["finish_reason"]
            content = json.loads(value["message"]["content"])
            if not isinstance(content, dict) or set(content) != {"outcome", "checks", "summary", "effects"}:
                raise ValueError("invalid response fields")
            prediction = {
                "id": case["id"],
                **content,
                "finish_reason": finish_reason,
                "latency_seconds": round(monotonic() - started, 3),
            }
        except Exception as error:
            prediction = {
                "id": case["id"], "outcome": "invalid", "checks": [], "summary": "invalid",
                "effects": [], "finish_reason": "error",
                "latency_seconds": round(monotonic() - started, 3),
            }
            errors.append({"id": case["id"], "error_class": type(error).__name__})
        predictions.append(prediction)
    return {
        "schema_version": 1,
        "packet_id": freeze["packet_id"],
        "packet_sha256": freeze["packet_sha256"],
        "model": model,
        "request_count": len(predictions),
        "retry_count": 0,
        "predictions": predictions,
        "errors": errors,
    }


def _transport(endpoint: str, key: str, timeout: int = 240):
    def call(payload):
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    return call


def main() -> int:
    packet_path = Path(os.environ.get(
        "ASTER_SA3_QUALITY_PACKET", Path(__file__).with_name("sa3-expanded-source-quality-v1.json")
    ))
    endpoint = os.environ.get("ASTER_LLAMA_BASE_URL", "http://192.168.70.12:11435/v1").rstrip("/") + "/chat/completions"
    key = os.environ.get("ASTER_LLAMA_API_KEY", "")
    model = os.environ.get("ASTER_LLAMA_MODEL", "accepted-local-model")
    if not key:
        print(json.dumps({"status": "no_go", "reason": "existing_authentication_missing"}))
        return 1
    result = run(_load(packet_path), _transport(endpoint, key), model=model)
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
