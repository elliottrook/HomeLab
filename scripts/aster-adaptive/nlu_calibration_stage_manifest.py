"""Validate the no-effect LXC110 NLU calibration staging manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

from nlu_threshold_policy import decode_unique_json, sha256


SCHEMA = "aster-nlu-calibration-stage-manifest.v1"
INPUTS = [
    ("cases.json", "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e", "private-synthetic"),
    ("release.json", "f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1", "content-free"),
    ("nlu-development-v1.json", "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785", "public-synthetic"),
    ("nlu_calibration_runner.py", "88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0", "source"),
    ("nlu_calibration_corpus.py", "3b383dcc181cc5c6a41d3aa9a30bc72ee30896ff0375bbc270de9bd82ba4f983", "source"),
    ("nlu_calibration_release.py", "bdc93c7892eda067c0675c04259c996d6f43935ee84ba4ae6bbea6d1892488d9", "source"),
    ("nlu_calibration_score.py", "7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd", "source"),
    ("nlu_calibration_journal.py", "966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb", "source"),
    ("nlu_local_model_adapter.py", "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0", "source"),
    ("nlu_candidate_bundle.py", "5a797b2f0166d6ead276c0487887074ea1f78396d2ddfcd4ea7d6915df36e156", "source"),
    ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d", "source"),
]


def expected_manifest() -> dict:
    return {
        "schema": SCHEMA,
        "status": "staging-plan-only",
        "run_id": "nlu-calibration-v1",
        "guest_id": 110,
        "base_directory": "/var/lib/aster-nlu-calibration",
        "directory_mode": "0700",
        "file_mode": "0600",
        "endpoint": "http://192.168.70.12:11435/v1/chat/completions",
        "key_path": "/etc/aster-llama-api-keys",
        "inputs": [
            {"name": name, "sha256": digest, "data_class": data_class}
            for name, digest, data_class in INPUTS
        ],
        "outputs": ["run.json", "attempt-journal.jsonl"],
        "excluded": [
            "labels.json", "nlu-policy-registration-v1.json",
            "nlu_threshold_selection.py", "cloud-credentials", "tools",
        ],
        "cleanup": "only-after-verified-mac-custody-and-production-postcheck",
        "uncertain_outcome": "retain-owner-only-and-do-not-retry",
        "authority": "not-granted",
    }


def load_and_validate(raw: bytes) -> dict:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("stage manifest must be unique-key UTF-8 JSON") from error
    if value != expected_manifest():
        raise ValueError("stage manifest does not match the frozen no-effect packet")
    return value


def validate_packet_files(manifest: dict, paths: dict[str, Path]) -> dict:
    if manifest != expected_manifest():
        raise ValueError("cannot validate files against an unfrozen stage manifest")
    expected = {row["name"]: row["sha256"] for row in manifest["inputs"]}
    if set(paths) != set(expected):
        raise ValueError("packet paths must name the exact frozen inputs")
    total = 0
    for name, digest in expected.items():
        path = paths[name]
        descriptor = None
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            metadata = os.fstat(descriptor)
        except OSError as error:
            raise ValueError(f"cannot open regular non-symlink packet input: {name}") from error
        if not stat.S_ISREG(metadata.st_mode):
            os.close(descriptor)
            raise ValueError(f"packet input must be a regular non-symlink file: {name}")
        hasher = hashlib.sha256()
        try:
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = None
                for chunk in iter(lambda: stream.read(65_536), b""):
                    hasher.update(chunk)
        except OSError as error:
            raise ValueError(f"cannot read packet input: {name}") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
        if hasher.hexdigest() != digest:
            raise ValueError(f"packet input digest changed: {name}")
        total += metadata.st_size
    return {"input_count": len(expected), "byte_total": total}


def validate_staged_directory(manifest: dict, directory: Path, *,
                              expected_uid: int = 0, expected_gid: int = 0) -> dict:
    """Validate the exact inactive LXC packet and its root-only custody."""
    if manifest != expected_manifest():
        raise ValueError("cannot validate custody against an unfrozen stage manifest")
    try:
        metadata = directory.lstat()
    except OSError as error:
        raise ValueError("staged directory is unavailable") from error
    if (not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != expected_uid or metadata.st_gid != expected_gid
            or stat.S_IMODE(metadata.st_mode) != 0o700):
        raise ValueError("staged directory custody is invalid")
    expected = {row["name"] for row in manifest["inputs"]}
    try:
        names = {entry.name for entry in directory.iterdir()}
    except OSError as error:
        raise ValueError("cannot enumerate staged directory") from error
    if names != expected:
        raise ValueError("staged directory must contain exactly the frozen inputs")
    paths: dict[str, Path] = {}
    for name in sorted(expected):
        path = directory / name
        try:
            item = path.lstat()
        except OSError as error:
            raise ValueError(f"cannot inspect staged input: {name}") from error
        if (not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode)
                or item.st_uid != expected_uid or item.st_gid != expected_gid
                or stat.S_IMODE(item.st_mode) != 0o600):
            raise ValueError(f"staged input custody is invalid: {name}")
        paths[name] = path
    return validate_packet_files(manifest, paths) | {"custody_verified": True}


def _assignments(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path or name in result:
            raise ValueError("each --input must be one unique NAME=PATH assignment")
        result[name] = Path(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the frozen NLU staging packet.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--staged-directory", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.manifest.read_bytes()
        value = load_and_validate(raw)
        if args.input and args.staged_directory is not None:
            raise ValueError("use either --input or --staged-directory")
        if args.staged_directory is not None:
            verified = validate_staged_directory(value, args.staged_directory)
        elif args.input:
            verified = validate_packet_files(value, _assignments(args.input))
        else:
            verified = {"input_count": 0, "byte_total": 0,
                        "custody_verified": False}
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": value["schema"],
        "declared_input_count": len(value["inputs"]),
        "verified_input_count": verified["input_count"],
        "verified_byte_total": verified["byte_total"],
        "custody_verified": verified.get("custody_verified", False),
        "manifest_sha256": sha256(raw),
        "authority": value["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
