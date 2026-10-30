#!/usr/bin/env python3
"""Fixed, content-bounded guest workload for the M3 35B public gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import nlu_joint_semantic_35b_v1 as candidate
import nlu_whole_label_public_runner_v1 as runner


FIXTURE = Path(__file__).with_name("nlu-development-v1.json")
KEY_FILE = Path("/etc/aster-llama-api-keys")
REQUESTS = 24


class WorkloadError(RuntimeError):
    def __init__(self, code: str, *, attempted: int = 0, valid: int = 0,
                 first_record_failure: str = "none"):
        super().__init__(code)
        self.code = code
        self.attempted = attempted
        self.valid = valid
        self.first_record_failure = first_record_failure


def execute(*, token: str, fixture_raw: bytes) -> dict[str, object]:
    result = runner.run(
        fixture_raw, token,
        endpoint=candidate.PUBLIC_GATE_ENDPOINT,
        implementation=candidate,
        candidate_name="joint-semantic-35b-v1",
    )
    summary = runner.summarize(fixture_raw, result)
    if (result.get("attempted") != REQUESTS or result.get("valid") != REQUESTS
            or result.get("authority") != "not-granted"
            or result.get("automatic_routing") != "off"):
        failures = [row.get("failure") for row in result.get("records", ())
                    if isinstance(row, dict) and row.get("valid") is False]
        first_failure = failures[0] if failures else "none"
        if first_failure not in {"invalid_response", "engine_error", "http_4xx", "http_5xx", "none"}:
            first_failure = "unknown"
        raise WorkloadError(
            "M3_PUBLIC_RESULT_INCOMPLETE",
            attempted=result.get("attempted") if type(result.get("attempted")) is int else 0,
            valid=result.get("valid") if type(result.get("valid")) is int else 0,
            first_record_failure=first_failure,
        )
    return {"schema": "aster-m3-joint-semantic-35b-guest-result.v1",
            "result": result, "summary": summary,
            "answer_content_retained": False,
            "hidden_reasoning_retained": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.run_authorized:
        print(json.dumps({"state": "disabled", "effects": "not-attempted"}, sort_keys=True))
        return 0
    if os.geteuid() != 0:
        raise SystemExit("root execution is required")
    try:
        token = KEY_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
        value = execute(token=token, fixture_raw=FIXTURE.read_bytes())
    except WorkloadError as exc:
        print(json.dumps({
            "schema": "aster-m3-joint-semantic-35b-guest-failure.v1",
            "state": "failed", "failure_code": exc.code,
            "attempted": exc.attempted, "valid": exc.valid,
            "first_record_failure": exc.first_record_failure,
            "answer_content_retained": False,
            "hidden_reasoning_retained": False,
        }, sort_keys=True, separators=(",", ":")))
        return 1
    except (OSError, ValueError, IndexError):
        print(json.dumps({
            "schema": "aster-m3-joint-semantic-35b-guest-failure.v1",
            "state": "failed", "failure_code": "M3_GUEST_INPUT_OR_IO_FAILED",
            "attempted": 0, "valid": 0, "first_record_failure": "none",
            "answer_content_retained": False,
            "hidden_reasoning_retained": False,
        }, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

