"""Validate exact root-only inactive fixed Doctor usefulness staging."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

from fixed_doctor_usefulness import load_unique


SCHEMA = "aster-fixed-doctor-usefulness-stage-manifest.v1"


def validate(
    manifest_raw: bytes, staged_directory: Path, *, expected_uid: int = 0,
    expected_gid: int = 0,
) -> dict:
    manifest = load_unique(manifest_raw)
    if set(manifest) != {
        "schema", "status", "guest_id", "target_directory", "directory_mode",
        "file_mode", "inputs", "declared_byte_total", "outputs", "excluded",
        "authority", "model_route",
    }:
        raise ValueError("staging manifest fields differ")
    if (
        manifest["schema"] != SCHEMA
        or manifest["status"] != "staging-plan-only"
        or manifest["guest_id"] != 104
        or manifest["target_directory"] != "/var/lib/aster/fixed-doctor-usefulness-v1"
        or manifest["directory_mode"] != "0700"
        or manifest["file_mode"] != "0600"
        or manifest["outputs"] != ["attempt-journal.jsonl", "raw-attempts.json"]
        or manifest["excluded"] != [
            "credentials", "tools", "review-labels", "routing-enable"
        ]
        or manifest["authority"] != "not-granted"
        or manifest["model_route"] != "not-enabled"
    ):
        raise ValueError("staging manifest boundary differs")
    metadata = staged_directory.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or staged_directory.is_symlink()
        or metadata.st_uid != expected_uid
        or metadata.st_gid != expected_gid
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise ValueError("staged directory custody differs")
    inputs = manifest["inputs"]
    if not isinstance(inputs, list) or len(inputs) != 8:
        raise ValueError("staging manifest input count differs")
    expected = {}
    for item in inputs:
        if (
            not isinstance(item, dict)
            or set(item) != {"name", "sha256"}
            or not isinstance(item["name"], str)
            or "/" in item["name"]
            or item["name"] in expected
            or not isinstance(item["sha256"], str)
            or len(item["sha256"]) != 64
        ):
            raise ValueError("staging input declaration differs")
        expected[item["name"]] = item["sha256"]
    actual = {entry.name for entry in os.scandir(staged_directory)}
    if actual != set(expected):
        raise ValueError("staged file set differs")
    byte_total = 0
    for name, digest in expected.items():
        path = staged_directory / name
        metadata = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or metadata.st_uid != expected_uid
            or metadata.st_gid != expected_gid
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_nlink != 1
        ):
            raise ValueError(f"{name}: staged file custody differs")
        flags = os.O_RDONLY | os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            raw = bytearray()
            while len(raw) < opened.st_size:
                chunk = os.read(descriptor, min(65536, opened.st_size - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            if len(raw) != opened.st_size or os.read(descriptor, 1):
                raise ValueError(f"{name}: staged file changed during read")
        finally:
            os.close(descriptor)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"{name}: staged file digest differs")
        byte_total += len(raw)
    if byte_total != manifest["declared_byte_total"]:
        raise ValueError("staged byte total differs")
    return {
        "schema": SCHEMA,
        "verified_input_count": len(expected),
        "verified_byte_total": byte_total,
        "authority": "not-granted",
        "model_route": "not-enabled",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--staged-directory", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.manifest.read_bytes(), args.staged_directory)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
