"""Explicit, descriptor-only entrypoint for fixed Doctor usefulness capture.

This source is inert unless invoked with ``--execute``. It grants no tools or
routing authority and never reads a credential path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import fixed_doctor_usefulness_9b_adapter as adapter
import fixed_doctor_usefulness_profile as profile
import journaled_fixed_doctor_usefulness_capture as journaled


PROFILE_SHA256 = "5f3183e5a805f2f1a3ab9f1c9f8d5fa30d9006aaba0550cabb33aa6f51f0c003"
MAX_KEY_BYTES = 4096


def read_key_fd(descriptor: int) -> bytearray:
    if type(descriptor) is not int or descriptor < 3:
        raise ValueError("inherited credential descriptor required")
    raw = bytearray()
    while len(raw) <= MAX_KEY_BYTES:
        chunk = os.read(descriptor, min(512, MAX_KEY_BYTES + 1 - len(raw)))
        if not chunk:
            break
        raw.extend(chunk)
    if (
        not raw
        or len(raw) > MAX_KEY_BYTES
        or any(byte <= 32 or byte >= 127 for byte in raw)
    ):
        raw[:] = b"\0" * len(raw)
        raise ValueError("credential descriptor contains an invalid key")
    return raw


def run(
    fixture_path: Path,
    profile_path: Path,
    output_directory: Path,
    key_fd: int,
) -> dict:
    fixture_raw = fixture_path.read_bytes()
    profile_raw = profile_path.read_bytes()
    if hashlib.sha256(profile_raw).hexdigest() != PROFILE_SHA256:
        raise ValueError("run profile digest mismatch")
    run_profile = profile.validate(profile_raw)
    secret = read_key_fd(key_fd)
    try:
        key = secret.decode("ascii")

        def invoke(case: dict, *, timeout_s: float) -> str:
            return adapter.invoke(case, key, timeout=timeout_s)

        return journaled.capture_journaled(
            fixture_raw,
            PROFILE_SHA256,
            invoke,
            output_directory,
            max_wall_s=run_profile["wall_deadline_seconds"],
            min_call_s=run_profile["per_case_timeout_seconds"],
        )
    finally:
        secret[:] = b"\0" * len(secret)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--key-fd", required=True, type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("explicit --execute gate required")
    try:
        result = run(
            args.fixture, args.profile, args.output_directory, args.key_fd
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["completed"] == 8 else 2


if __name__ == "__main__":
    raise SystemExit(main())
