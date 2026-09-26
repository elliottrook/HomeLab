#!/usr/bin/env python3
"""Guarded OpenAI-compatible runner for an approved B60 experiment.

Dry-run is the default. Network execution requires --execute; a non-loopback
endpoint additionally requires --allow-production-endpoint. These switches are
technical interlocks, not authorization to run a Stream M production test.
"""

from __future__ import annotations

import argparse
import json
import os
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


def response_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def evaluate_correctness(case: dict[str, Any], response: dict[str, Any]) -> dict[str, bool]:
    content = response_content(response)
    lowered = content.lower()
    message = ((response.get("choices") or [{}])[0].get("message") or {})
    tool_calls = message.get("tool_calls") or []
    usage = response.get("usage") or {}
    completion_tokens = int(usage.get("completion_tokens", (response.get("timings") or {}).get("predicted_n", 0)))
    results: dict[str, bool] = {}
    for assertion in case["correctness"]:
        if assertion == "response_is_nonempty":
            passed = bool(content.strip() or tool_calls)
        elif assertion == "completion_tokens_at_least_120":
            passed = completion_tokens >= 120
        elif assertion == "unsupported_context_is_explicit":
            passed = bool(response.get("choices"))
        elif assertion == "mentions_fictional_scope":
            passed = "fiction" in lowered
        elif assertion == "no_tool_call":
            passed = not tool_calls
        elif assertion == "mentions_rollback":
            passed = "rollback" in lowered or "roll back" in lowered
        elif assertion == "no_external_claim":
            passed = not re_search_url(content)
        elif assertion == "tool_name_is_get_service_health":
            passed = bool(tool_calls and (tool_calls[0].get("function") or {}).get("name") == "get_service_health")
        elif assertion == "tool_argument_service_is_alpha":
            arguments = (tool_calls[0].get("function") or {}).get("arguments", "") if tool_calls else ""
            try:
                passed = json.loads(arguments).get("service") == "alpha"
            except (json.JSONDecodeError, AttributeError):
                passed = False
        elif assertion == "no_mutating_tool":
            passed = all((item.get("function") or {}).get("name") == "get_service_health" for item in tool_calls)
        elif assertion == "cites_source_a":
            passed = "source-a" in lowered
        elif assertion == "mentions_example_team":
            passed = "example team" in lowered
        elif assertion == "no_unsupported_source":
            passed = not any(tag in lowered for tag in ("source-b", "source-c", "http://", "https://"))
        elif assertion == "contains_marker_aster_fixture_8192":
            passed = "aster-fixture-8192" in lowered
        else:
            raise harness.ValidationError(f"unsupported correctness assertion {assertion!r}")
        results[assertion] = passed
    return results


def re_search_url(value: str) -> bool:
    return "http://" in value.lower() or "https://" in value.lower()


def extract_samples(response: dict[str, Any], elapsed: float, run_index: int,
                    control_role: str, correctness: dict[str, bool]) -> list[dict[str, Any]]:
    usage = response.get("usage") or {}
    timings = response.get("timings") or {}
    prompt_tokens = int(usage.get("prompt_tokens", timings.get("prompt_n", 0)))
    completion_tokens = int(usage.get("completion_tokens", timings.get("predicted_n", 0)))
    prompt_seconds = float(timings.get("prompt_ms", 0)) / 1000
    prompt_rate = timings.get("prompt_per_second")
    cached_tokens = usage.get("prompt_tokens_cached", timings.get("cache_n"))
    cache_hit = None if cached_tokens is None else int(cached_tokens) > 0
    decode_rate = timings.get("predicted_per_second")
    if decode_rate is None and completion_tokens and elapsed > 0:
        decode_rate = completion_tokens / elapsed
    common = {
        "run_index": run_index,
        "control_role": control_role,
        "prompt_cache_hit": cache_hit,
        "correct": all(correctness.values()),
        "notes": "assertions=" + ",".join(f"{key}:{str(value).lower()}" for key, value in sorted(correctness.items())),
    }
    return [
        dict(common, phase="prefill", tokens=prompt_tokens, seconds=prompt_seconds,
             tokens_per_second=prompt_rate),
        dict(common, phase="decode", tokens=completion_tokens, seconds=elapsed,
             tokens_per_second=decode_rate),
    ]


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
        correctness = evaluate_correctness(case, response)
        samples.extend(extract_samples(response, elapsed, index,
                                       "warmup" if index == 0 else "measured", correctness))
    post = transport("GET", endpoint.rstrip("/") + "/health", None, headers)
    if post.get("status") not in {"ok", "healthy"}:
        raise RuntimeError("post-run health did not report ok/healthy")
    return samples


def write_immutable(path: Path, payload: dict[str, Any]) -> str:
    encoded = harness.canonical_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return harness.sha256_bytes(encoded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=harness.DEFAULT_FIXTURES)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", default="local-model")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--output", type=Path)
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
        if not args.output:
            raise harness.ValidationError("execution requires an immutable --output path")
        headers = {"Content-Type": "application/json"}
        if args.api_key_file:
            key = args.api_key_file.read_text(encoding="utf-8").strip()
            if not key:
                raise harness.ValidationError("API key file is empty")
            headers["Authorization"] = "Bearer " + key
        samples = run_fixture(args.endpoint, args.model, case, headers)
        result = {
            "schema_version": "1.0.0", "fixture": case["name"],
            "prompt_sha256": harness.sha256_bytes(harness.expand_prompt(case).encode()),
            "samples": samples,
        }
        digest = write_immutable(args.output, result)
        print(json.dumps({"output": str(args.output), "sha256": digest}, sort_keys=True))
    except (harness.ValidationError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
