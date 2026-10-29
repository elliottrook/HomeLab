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
    pass


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
        raise WorkloadError("M3 public result is incomplete")
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
    token = KEY_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
    try:
        value = execute(token=token, fixture_raw=FIXTURE.read_bytes())
    except (OSError, ValueError, WorkloadError):
        print(json.dumps({"state": "failed", "effects": "not-attempted"}, sort_keys=True))
        return 1
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

