#!/usr/bin/env python3
"""Guarded OpenAI-compatible runner for an approved B60 experiment.

Dry-run is the default. Network execution requires --execute; a non-loopback
endpoint additionally requires --allow-production-endpoint. These switches are
technical interlocks, not authorization to run a Stream M production test.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

import harness


Transport = Callable[[str, str, Optional[dict[str, Any]], dict[str, str]], dict[str, Any]]


def is_loopback(endpoint: str) -> bool:
    host = (urllib.parse.urlparse(endpoint).hostname or "").lower()
    return host in {"127.0.0.1", "::1", "localhost"}


def urllib_transport(method: str, url: str, payload: Optional[dict[str, Any]],
                     headers: dict[str, str]) -> dict[str, Any]:
    data = harness.canonical_bytes(payload) if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}") from exc


def selected_fixture(path: Path, name: str) -> dict[str, Any]:
    cases = harness.validate_fixtures(harness.read_json(path))
    matches = [case for case in cases if case["name"] == name]
    if len(matches) != 1:
        raise harness.ValidationError(f"fixture {name!r} not found exactly once")
    return matches[0]


def extract_sample(response: dict[str, Any], elapsed: float, run_index: int,
                   control_role: str) -> dict[str, Any]:
    usage = response.get("usage") or {}
    timings = response.get("timings") or {}
    prompt_tokens = int(usage.get("prompt_tokens", timings.get("prompt_n", 0)))
    completion_tokens = int(usage.get("completion_tokens", timings.get("predicted_n", 0)))
    decode_rate = timings.get("predicted_per_second")
    if decode_rate is None and completion_tokens and elapsed > 0:
        decode_rate = completion_tokens / elapsed
    return {
        "run_index": run_index,
        "control_role": control_role,
        "phase": "decode",
        "tokens": completion_tokens,
        "seconds": elapsed,
        "tokens_per_second": decode_rate,
        "prompt_cache_hit": None,
        "correct": bool(response.get("choices")),
        "notes": f"reported_prompt_tokens={prompt_tokens}; telemetry_pending",
    }


def run_fixture(endpoint: str, model: str, case: dict[str, Any], headers: dict[str, str],
                transport: Transport = urllib_transport) -> list[dict[str, Any]]:
    health = transport("GET", endpoint.rstrip("/") + "/health", None, headers)
    if health.get("status") not in {"ok", "healthy"}:
        raise RuntimeError("pre-run health did not report ok/healthy")
    prompt = harness.expand_prompt(case)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": case.get("max_output_tokens", 128),
        "temperature": 0,
        "seed": 1,
        "stream": False,
        "cache_prompt": case["cache_state"] != "cold",
    }
    samples = []
    total = case["repetitions"] + 1
    for index in range(total):
        started = time.monotonic()
        response = transport("POST", endpoint.rstrip("/") + "/v1/chat/completions", payload, headers)
        elapsed = time.monotonic() - started
        samples.append(extract_sample(response, elapsed, index, "warmup" if index == 0 else "measured"))
    post = transport("GET", endpoint.rstrip("/") + "/health", None, headers)
    if post.get("status") not in {"ok", "healthy"}:
        raise RuntimeError("post-run health did not report ok/healthy")
    return samples


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=harness.DEFAULT_FIXTURES)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", default="local-model")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-production-endpoint", action="store_true")
    args = parser.parse_args(argv)
    try:
        case = selected_fixture(args.fixtures, args.fixture)
        if not args.execute:
            print(json.dumps({"execution_authorized": False, "fixture": case["name"],
                              "endpoint_loopback": is_loopback(args.endpoint)}, sort_keys=True))
            return 0
        if not is_loopback(args.endpoint) and not args.allow_production_endpoint:
            raise harness.ValidationError("non-loopback execution requires --allow-production-endpoint")
        headers = {"Content-Type": "application/json"}
        if args.api_key_file:
            key = args.api_key_file.read_text(encoding="utf-8").strip()
            if not key:
                raise harness.ValidationError("API key file is empty")
            headers["Authorization"] = "Bearer " + key
        samples = run_fixture(args.endpoint, args.model, case, headers)
        print(json.dumps({"fixture": case["name"], "samples": samples}, indent=2, sort_keys=True))
    except (harness.ValidationError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
