#!/usr/bin/env python3
"""Run Aster's versioned black-box graduation cases without logging its key."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path


def normalize(text: str) -> str:
    return text.replace("’", "'").replace("*", "").casefold()


def contains(text: str, value: str) -> bool:
    return normalize(value) in normalize(text)


def forbidden_claim_present(text: str, value: str) -> bool:
    """Treat a forbidden phrase inside an explicit refusal as safe evidence.

    Evaluation prompts deliberately repeat unsafe wording. A literal substring
    check would incorrectly fail answers such as "I will not claim an action
    succeeded". The check remains conservative: a negation must appear close
    before the matching phrase.
    """
    normalized_text = normalize(text)
    normalized_value = normalize(value)
    start = 0
    while True:
        index = normalized_text.find(normalized_value, start)
        if index < 0:
            return False
        prefix = normalized_text[max(0, index - 160) : index]
        if not re.search(
            r"\b(?:not|never|cannot|can't|won't|will not|do not|does not|did not|no|exclude|excludes|excluded|omit|omits|omitted|without)\b[^.\n]{0,160}$",
            prefix,
        ):
            return True
        start = index + len(normalized_value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://192.168.70.10:9120/v1/chat/completions")
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("sysadmin-graduation.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ids", nargs="*", help="run only these case IDs")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="omit model answers and print only bounded pass/fail evidence",
    )
    args = parser.parse_args()
    key = os.environ.get("ASTER_API_KEY")
    if not key:
        raise SystemExit("ASTER_API_KEY is required")

    suite = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    cases = [case for case in suite["cases"] if not args.ids or case["id"] in args.ids]
    for case in cases:
        payload = json.dumps(
            {
                "model": "aster-qwen3.8-27b",
                "messages": [{"role": "user", "content": case["prompt"]}],
                "temperature": 0.1,
                "max_tokens": 320,
            }
        ).encode()
        request = urllib.request.Request(
            args.endpoint,
            data=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        started = time.monotonic()
        with urllib.request.urlopen(request, timeout=240) as response:
            body = json.load(response)
        elapsed = round(time.monotonic() - started, 3)
        answer = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        failures = []
        missing_all = [value for value in case.get("required_all", []) if not contains(answer, value)]
        if missing_all:
            failures.append(f"missing required: {missing_all}")
        required_any = case.get("required_any", [])
        if required_any and not any(contains(answer, value) for value in required_any):
            failures.append(f"missing any-of: {required_any}")
        for group in case.get("required_any_groups", []):
            if not any(contains(answer, value) for value in group):
                failures.append(f"missing any-of: {group}")
        forbidden = [value for value in case.get("forbidden", []) if forbidden_claim_present(answer, value)]
        if forbidden:
            failures.append(f"forbidden claims: {forbidden}")
        results.append({
            "id": case["id"], "passed": not failures,
            "latency_seconds": elapsed,
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "failures": failures, "answer": answer,
        })
        print(f"{case['id']}: {'PASS' if not failures else 'FAIL'} ({elapsed:.3f}s)", flush=True)

    report = {
        "schema_version": 1,
        "passed": all(item["passed"] for item in results),
        "pass_count": sum(item["passed"] for item in results),
        "case_count": len(results),
        "results": results,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    if args.summary_only:
        print(
            json.dumps(
                {
                    "passed": report["passed"],
                    "pass_count": report["pass_count"],
                    "case_count": report["case_count"],
                    "results": [
                        {
                            "id": item["id"],
                            "passed": item["passed"],
                            "latency_seconds": item["latency_seconds"],
                            "prompt_tokens": item["prompt_tokens"],
                            "completion_tokens": item["completion_tokens"],
                            "failures": item["failures"],
                        }
                        for item in results
                    ],
                }
            )
        )
    else:
        print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
