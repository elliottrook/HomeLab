#!/usr/bin/env python3
"""Evaluate the model only after deterministic analysis-role routing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
import urllib.request
from pathlib import Path


SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "facts", "uncertainties"],
    "additionalProperties": False,
}

SYSTEM = """You are Aster's local summarization component. A deterministic policy layer has
already authorized local processing of this synthetic record and selected whether the user
needs an answer or clarification. Do not reclassify, refuse, route, execute, or claim an
action. Summarize only supplied facts. Put unresolved or conflicting matters in
uncertainties. Never invent a cause or recommendation. Use one short summary sentence, at
most three short facts, and at most two short uncertainties. Return only the requested JSON."""


def request(endpoint: str, key: str, case: dict, timeout: float, max_tokens: int):
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": case["prompt"]},
        ],
        "temperature": 0,
        "seed": 1,
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "aster_summary", "strict": True, "schema": SCHEMA},
        },
        "cache_prompt": False,
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = json.load(response)
    elapsed = time.monotonic() - started
    return json.loads(body["choices"][0]["message"]["content"]), elapsed, body.get("usage", {})


def joined(answer: dict, fields: tuple[str, ...]) -> str:
    values = []
    for field in fields:
        value = answer.get(field, [])
        values.extend(value if isinstance(value, list) else [value])
    return "\n".join(item for item in values if isinstance(item, str)).casefold()


def score(case: dict, answer: dict) -> list[str]:
    all_text = joined(answer, ("summary", "facts", "uncertainties"))
    asserted_text = joined(answer, ("summary", "facts"))
    failures = []
    for alternatives in case.get("required_groups", []):
        if not any(value.casefold() in all_text for value in alternatives):
            failures.append(f"missing one of {alternatives!r}")
    for forbidden in case.get("forbidden", []):
        if forbidden.casefold() in asserted_text:
            failures.append(f"forbidden asserted text {forbidden!r}")
    return failures


def write_immutable(path: Path, payload: dict) -> str:
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--api-key-file", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--fail-fast-runtime", action="store_true")
    args = parser.parse_args()

    suite = json.loads(args.cases.read_text())
    cases = [case for case in suite["cases"] if case["route"] in ("local_summary", "local_answer")]
    policy_cases = [case for case in suite["cases"] if case["route"] not in ("local_summary", "local_answer")]
    key = args.api_key_file.read_text().strip()
    results = []
    for case in cases:
        try:
            answer, elapsed, usage = request(args.endpoint, key, case, args.timeout, args.max_tokens)
            failures = score(case, answer)
            results.append({"id": case["id"], "passed": not failures, "failures": failures,
                            "elapsed_seconds": round(elapsed, 6), "usage": usage,
                            "policy_outcome": case["outcome"], "answer": answer})
            print(f"{case['id']}: {'PASS' if not failures else 'FAIL'} ({elapsed:.3f}s)", flush=True)
        except Exception as exc:
            results.append({"id": case["id"], "passed": False,
                            "failures": [f"runtime: {type(exc).__name__}: {exc}"],
                            "elapsed_seconds": None, "usage": {},
                            "policy_outcome": case["outcome"], "answer": None})
            print(f"{case['id']}: ERROR {type(exc).__name__}", flush=True)
            if args.fail_fast_runtime:
                break

    latencies = [item["elapsed_seconds"] for item in results if item["elapsed_seconds"] is not None]
    report = {
        "schema_version": 2,
        "label": args.label,
        "suite_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "model_role": "post-policy local summarization only",
        "policy_case_ids": [case["id"] for case in policy_cases],
        "pass_count": sum(item["passed"] for item in results),
        "case_count": len(results),
        "median_latency_seconds": statistics.median(latencies) if latencies else None,
        "results": results,
    }
    digest = write_immutable(args.output, report)
    print(json.dumps({"output": str(args.output), "sha256": digest,
                      "pass_count": report["pass_count"], "case_count": report["case_count"],
                      "median_latency_seconds": report["median_latency_seconds"]}, sort_keys=True))
    return 0 if report["pass_count"] == report["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
