"""Bounded, tool-free M3 development-fixture probe for the existing llama server.

The transport prepends FROZEN_FIXTURE_B64 and runs this source as the local
inference service account. The API key is read inside LXC 110 and never emitted.
"""
import base64
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FIXTURE_SHA256 = "c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec"
MODEL = "aster-qwen3.5-9b"
ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
KEY_PATH = Path("/etc/aster-llama-api-keys")
CAPABILITIES = {
    "timer": "local timer or alarm",
    "home": "Home Assistant household device control",
    "media": "local music or media control",
    "facts": "stable general knowledge",
    "calendar": "private calendar lookup",
    "web": "live public web research",
    "local_join": "combine results locally without exporting private context",
    "lab_read": "read an existing HomeLab status report",
    "private_context": "private personal-context lookup",
}
FORBIDDEN = {"shell", "credentials", "automatic_approval", "cloud_private_export"}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["status", "capabilities"],
    "properties": {
        "status": {"type": "string", "enum": ["plan", "clarify", "abstain"]},
        "capabilities": {"type": "array", "items": {"type": "string", "enum": sorted(CAPABILITIES)},
                         "uniqueItems": True, "maxItems": len(CAPABILITIES)},
    },
}
SYSTEM = (
    "Classify the user's synthetic assistant request. Return only JSON with "
    "status and capabilities. Use 'clarify' if the request cannot be understood "
    "without missing referents; 'abstain' if unsure. Propose required capability "
    "IDs only. If status is clarify or abstain, capabilities MUST be an empty "
    "array. For an unambiguous request with required capabilities, use plan. "
    "You have no tools, credentials, permission to act, or access to "
    "personal data. Never claim execution. Capability IDs: "
    + json.dumps(CAPABILITIES, sort_keys=True)
)


def validate_fixture(raw):
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError("fixture digest mismatch")
    value = json.loads(raw)
    rows = value.get("families")
    if value.get("schema_version") != "routing-families.v1" or not isinstance(rows, list) or len(rows) != 30:
        raise ValueError("unexpected fixture shape")
    ids = set()
    for row in rows:
        if set(row) != {"id", "split", "text", "required", "status"}:
            raise ValueError("unexpected row fields")
        if not isinstance(row["id"], str) or row["id"] in ids or not isinstance(row["text"], str):
            raise ValueError("invalid row identity")
        ids.add(row["id"])
        if row["status"] not in {"plan", "clarify"} or not isinstance(row["required"], list):
            raise ValueError("invalid expected route")
        if len(set(row["required"])) != len(row["required"]) or not set(row["required"]) <= set(CAPABILITIES):
            raise ValueError("unknown expected capability")
    return rows


def parse_response(value):
    content = value["choices"][0]["message"]["content"]
    proposal = json.loads(content)
    if not isinstance(proposal, dict) or set(proposal) != {"status", "capabilities"}:
        raise ValueError("invalid output keys")
    status, capabilities = proposal["status"], proposal["capabilities"]
    if status not in {"plan", "clarify", "abstain"} or not isinstance(capabilities, list):
        raise ValueError("invalid output values")
    if any(type(item) is not str for item in capabilities):
        raise ValueError("invalid capability type")
    if len(set(capabilities)) != len(capabilities) or not set(capabilities) <= set(CAPABILITIES):
        raise ValueError("invalid capability ID")
    if status != "plan" and capabilities:
        raise ValueError("non-plan carries capabilities")
    return status, sorted(capabilities)


def build_request(text, key):
    payload = json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 256,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": text}],
        "response_format": {"type": "json_object", "schema": SCHEMA},
    }).encode()
    return Request(ENDPOINT, data=payload, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
    })


def run(rows, key, request_fn=urlopen, now=time.monotonic):
    records = []
    started = now()
    for row in rows:
        if now() - started >= 1200:
            break
        req = build_request(row["text"], key)
        one_start = now()
        record = {"id": row["id"]}
        try:
            with request_fn(req, timeout=90) as response:
                value = json.load(response)
            status, capabilities = parse_response(value)
            record.update({"valid": True, "status": status, "capabilities": capabilities,
                           "exact_match": status == row["status"] and capabilities == sorted(row["required"]),
                           "extra": sorted(set(capabilities) - set(row["required"])),
                           "missing": sorted(set(row["required"]) - set(capabilities))})
        except HTTPError as exc:
            record.update({"valid": False, "failure": "http_error", "http_status": exc.code})
        except (URLError, TimeoutError, OSError):
            record.update({"valid": False, "failure": "transport_error"})
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            record.update({"valid": False, "failure": "invalid_response"})
        record["latency_seconds"] = round(now() - one_start, 3)
        records.append(record)
        if not record["valid"]:
            break  # One attempt per case; first unexpected failure stops the run.
    times = [r["latency_seconds"] for r in records]
    result = {"schema": "m3-9b-sycl-compat.v4", "model": MODEL,
              "fixture_sha256": FIXTURE_SHA256, "attempted": len(records),
              "valid": sum(r["valid"] for r in records),
              "exact_match": sum(r.get("exact_match", False) for r in records),
              "records": records, "elapsed_seconds": round(now() - started, 3),
              "limits": ["synthetic development fixtures, not independent holdout",
                         "no confidence calibration, authority or production routing"]}
    if len(records) == 30 and all(r["valid"] for r in records):
        result["p50_seconds"] = round(statistics.median(times), 3)
        result["p95_seconds"] = round(sorted(times)[int(.95 * (len(times)-1))], 3)
    return result


def diagnose_one(row, key, request_fn=urlopen, now=time.monotonic):
    """One new synthetic case; no raw content, prompt or secret in the result."""
    start = now()
    result = {"schema": "m3-9b-sycl-compat-diagnostic.v2", "id": row["id"],
              "model": MODEL, "valid": False}
    try:
        with request_fn(build_request(row["text"], key), timeout=90) as response:
            value = json.load(response)
        choices = value.get("choices") if isinstance(value, dict) else None
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            result["stage"] = "response_envelope"
        else:
            choice = choices[0]
            finish = choice.get("finish_reason")
            result["finish_reason"] = finish if finish in {"stop", "length"} else "other"
            message = choice.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            result["content_type"] = "string" if isinstance(content, str) else (
                "null" if content is None else "other")
            if not isinstance(content, str):
                result["stage"] = "content_type"
            else:
                result["content_bytes"] = len(content.encode())
                result["content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    result["stage"] = "json_syntax"
                else:
                    result["json_type"] = "object" if isinstance(parsed, dict) else "other"
                    if isinstance(parsed, dict):
                        result["expected_keys"] = sorted(set(parsed) & {"status", "capabilities"})
                        result["extra_key_count"] = len(set(parsed) - {"status", "capabilities"})
                        status_value = parsed.get("status")
                        caps_value = parsed.get("capabilities")
                        result["status_type"] = type(status_value).__name__
                        result["status_allowed"] = type(status_value) is str and status_value in {
                            "plan", "clarify", "abstain"}
                        result["capabilities_type"] = type(caps_value).__name__
                        if isinstance(caps_value, list):
                            result["capability_count"] = len(caps_value)
                            result["non_string_capability_count"] = sum(type(c) is not str for c in caps_value)
                            strings = [c for c in caps_value if type(c) is str]
                            result["unknown_capability_count"] = sum(c not in CAPABILITIES for c in strings)
                            result["duplicate_capability_count"] = len(strings) - len(set(strings))
                            result["nonplan_has_capabilities"] = status_value != "plan" and bool(caps_value)
                    try:
                        parse_response(value)
                    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
                        result["stage"] = "schema_or_capability"
                    else:
                        result["stage"] = "valid"
                        result["valid"] = True
    except HTTPError as exc:
        result.update({"stage": "http_error", "http_status": exc.code})
    except (URLError, TimeoutError, OSError, ValueError, TypeError, KeyError):
        result["stage"] = "transport_or_envelope"
    result["latency_seconds"] = round(now() - start, 3)
    return result


def main():
    fixture_b64 = globals().get("FROZEN_FIXTURE_B64")
    if not isinstance(fixture_b64, str):
        raise SystemExit("transport fixture missing")
    rows = validate_fixture(base64.b64decode(fixture_b64, validate=True))
    # The service-account file is never included in output, exceptions or arguments.
    key = KEY_PATH.read_text().splitlines()[0].strip()
    if not key:
        raise SystemExit("local service credential unavailable")
    if len(sys.argv) == 2 and sys.argv[1] == "diagnostic-v2":
        print(json.dumps(diagnose_one(rows[1], key), sort_keys=True))
    elif len(sys.argv) == 2 and sys.argv[1] == "diagnostic-v3":
        print(json.dumps(diagnose_one(rows[2], key), sort_keys=True))
    elif len(sys.argv) == 1:
        print(json.dumps(run(rows, key), sort_keys=True))
    else:
        raise SystemExit("unsupported mode")


if __name__ == "__main__":
    main()
