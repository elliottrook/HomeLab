"""Validate the non-admitted fixed Doctor F6 workload proposal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fixed_doctor_usefulness import load_unique


EXPECTED = {
    "schema": "aster-stream-a-f6-workload-proposal.v1",
    "status": "not-admitted",
    "workload": "fixed-doctor-usefulness-v1",
    "guest_id": 104,
    "packet_directory": "/var/lib/aster/fixed-doctor-usefulness-v1",
    "entrypoint": "run_fixed_doctor_usefulness.py",
    "entrypoint_sha256": "a014d0b52ed410b7edffa931c8ad7c90212ef4a382ececd621e49431a0bed981",
    "fixture_sha256": "8478b516e10b64eb3ed2ac9c8bf90ef151023fe8f9b8241fc37cecb9be0df43f",
    "profile_sha256": "5f3183e5a805f2f1a3ab9f1c9f8d5fa30d9006aaba0550cabb33aa6f51f0c003",
    "execution_identity": "fixed-nonlogin-identity-required",
    "credential_delivery": "inherited-read-only-descriptor",
    "fresh_prerequisites": ["F2", "F3", "F4", "F5"],
    "lease_scope": "whole-host-ai-lab",
    "maximum_model_requests": 8,
    "per_case_timeout_seconds": 60,
    "wall_deadline_seconds": 600,
    "recovery_reserve_seconds": 900,
    "attempt_policy": "one-shot-no-retry",
    "expected_outputs": ["attempt-journal.jsonl", "raw-attempts.json"],
    "tools": "disabled",
    "authority": "not-granted",
    "routing": "not-enabled",
    "sequence_binding": "separate-reviewed-plan-required",
    "recovery": "exact-accepted-qwen3.5-9b-q4_k_m-sycl-and-schedules",
}


def validate(raw: bytes) -> dict:
    value = load_unique(raw)
    if value != EXPECTED:
        raise ValueError("fixed Doctor F6 workload proposal differs")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal", type=Path)
    args = parser.parse_args(argv)
    try:
        value = validate(args.proposal.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": value["schema"],
        "status": value["status"],
        "workload": value["workload"],
        "authority": value["authority"],
        "routing": value["routing"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
