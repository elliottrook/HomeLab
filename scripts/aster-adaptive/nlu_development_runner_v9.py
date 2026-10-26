"""Bounded local-model runner for the exposed NLU development fixture."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import nlu_local_model_adapter_v9 as adapter
from nlu_threshold_policy import decode_unique_json, sha256


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
FIXTURE_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
ENGINE_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
PER_CASE_TIMEOUT = 90
WALL_DEADLINE = 600


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def run(fixture_raw: bytes, token: str) -> dict:
    if sha256(fixture_raw) != FIXTURE_SHA256:
        raise ValueError("development fixture changed")
    fixture = decode_unique_json(fixture_raw)
    cases = fixture["cases"]
    if len(cases) != 24:
        raise ValueError("development fixture must contain 24 cases")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    records = []
    for case in cases:
        remaining = WALL_DEADLINE - (time.monotonic() - started)
        if remaining <= 0:
            break
        request = urllib.request.Request(
            ENDPOINT, data=adapter.build_payload(case["text"]), method="POST",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        one_started = time.monotonic()
        try:
            with opener.open(request, timeout=min(PER_CASE_TIMEOUT, remaining)) as response:
                raw = response.read(65_537)
            if response.status != 200 or len(raw) > 65_536:
                raise RuntimeError("engine response failed boundary")
            records.append(adapter.result_record(
                case_id=case["id"], principal_ref="nlu-development-v2",
                engine_sha256=ENGINE_SHA256,
                policy_sha256=sha256(adapter.SYSTEM_POLICY.encode()),
                latency_seconds=round(time.monotonic() - one_started, 3),
                response_raw=json.dumps({
                    "choices": [{
                        "message": json.loads(raw)["choices"][0]["message"],
                        "finish_reason": json.loads(raw)["choices"][0]["finish_reason"],
                    }]
                }, sort_keys=True, separators=(",", ":")).encode(),
            ))
        except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            records.append({"id": case["id"], "valid": False,
                            "latency_seconds": round(time.monotonic() - one_started, 3),
                            "failure": "invalid_response", "error_type": "response_invalid"})
        except (urllib.error.URLError, OSError, RuntimeError, TimeoutError):
            records.append({"id": case["id"], "valid": False,
                            "latency_seconds": round(time.monotonic() - one_started, 3),
                            "failure": "engine_error", "error_type": "engine_unavailable"})
            break
    return {
        "schema": "aster-nlu-run.v1", "engine": "aster-qwen3.5-9b-v9",
        "fixture_sha256": FIXTURE_SHA256, "attempted": len(records),
        "valid": sum(row["valid"] for row in records), "records": records,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = args.key_file.read_text().splitlines()[0].strip()
    if not 16 <= len(token) <= 256:
        parser.error("invalid local service credential")
    result = run(args.fixture.read_bytes(), token)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"attempted": result["attempted"], "valid": result["valid"],
                      "complete": result["attempted"] == 24,
                      "output_sha256": sha256(args.output.read_bytes())}, sort_keys=True))
    return 0 if result["attempted"] == 24 else 2


if __name__ == "__main__":
    raise SystemExit(main())
