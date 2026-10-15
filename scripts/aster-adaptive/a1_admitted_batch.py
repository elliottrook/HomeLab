"""Compose a frozen A1 batch after an external live authority admits it.

This is a Mini-side client, not a lease issuer or receipt verifier. The
platform-owned ``assert_admitted`` callback must authenticate current host
state and raise unless the exact A1 application lease, sidecar endpoint and
watchdog are valid. It receives the profile SHA-256 and exact endpoint, and is
called again immediately before each possible model call.
Importing this module opens no socket and reads no private evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Callable

from a1_full_path_capture import capture_full_path
from a1_headless_client import invoke
from holdout_answer_capture import load_cases
import a1_full_path_capture as capture_module
import a1_headless_client as client_module

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_CASE_BYTES = 100_000
MAX_PROFILE_BYTES = 16_000
A1_TEST_ENDPOINT = "http://192.168.70.10:19104/v1/chat/completions"
ADMISSION_FIELDS = {"schema", "lease_id", "generation", "receipt_sha256",
                    "profile_sha256", "endpoint"}
ADMISSION_SCHEMA = "aster-a1-admission.v1"


def _owner_file(path: Path, *, maximum: int) -> bytes:
    if not isinstance(path, Path) or not path.is_absolute() or path.is_symlink():
        raise ValueError("invalid private input path")
    info = path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077 or info.st_size > maximum):
        raise ValueError("private input custody failed")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (opened.st_ino != info.st_ino or opened.st_dev != info.st_dev
                or opened.st_size > maximum):
            raise ValueError("private input changed")
        raw = os.read(fd, maximum + 1)
    finally:
        os.close(fd)
    if len(raw) > maximum:
        raise ValueError("private input too large")
    return raw


def _validate_admission(value: object, profile_sha256: str) -> dict[str, object]:
    if (type(value) is not dict or set(value) != ADMISSION_FIELDS
            or value.get("schema") != ADMISSION_SCHEMA
            or not isinstance(value.get("lease_id"), str)
            or not 1 <= len(value["lease_id"]) <= 128
            or type(value.get("generation")) is not int
            or value["generation"] < 1
            or not isinstance(value.get("receipt_sha256"), str)
            or not HEX64.fullmatch(value["receipt_sha256"])
            or value.get("profile_sha256") != profile_sha256
            or value.get("endpoint") != A1_TEST_ENDPOINT):
        raise RuntimeError("A1 authenticated admission receipt unavailable")
    return value


def _write_final_manifest(directory: Path, *, profile_sha256: str,
                          admission: dict[str, object], receipt_digests: set[str],
                          checks: int, summary: dict) -> None:
    if (not directory.is_dir() or directory.stat().st_uid != os.getuid()
            or directory.stat().st_mode & 0o077):
        raise RuntimeError("A1 final manifest custody failed")
    manifest = {
        "schema": "aster-a1-final-manifest.v1",
        "profile_sha256": profile_sha256,
        "endpoint": A1_TEST_ENDPOINT,
        "lease_id": admission["lease_id"],
        "generation": admission["generation"],
        "receipt_digests": sorted(receipt_digests),
        "admission_checks": checks,
        "completed": summary.get("completed"),
        "failed": summary.get("failed"),
        "not_attempted": summary.get("not_attempted"),
    }
    raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                    allow_nan=False) + "\n").encode()
    path = directory / "final-manifest.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise RuntimeError("A1 final manifest write failed") from exc


def run_admitted_batch(*, cases_path: Path, profile_path: Path,
                       expected_profile_sha256: str, ingress_token_path: Path,
                       endpoint: str, output_dir: Path,
                       assert_admitted: Callable[[str, str], dict],
                       transport=invoke, capture=capture_full_path) -> dict:
    """Run at most one sealed 20-case batch and return content-free counts.

    ``assert_admitted`` is an external *authenticated* live check, never a
    boolean from a model or a caller-supplied preview receipt. It must return
    The callback must return a content-free authenticated receipt containing
    the lease ID, generation, host receipt digest, profile hash and exact
    endpoint. A failed check before the batch creates no output; a later
    failure is journaled as an uncertain stopped attempt. The caller must
    preserve that partial output.
    """
    if not callable(assert_admitted) or not callable(transport) or not callable(capture):
        raise ValueError("missing A1 authority or client")
    if not isinstance(expected_profile_sha256, str) or not HEX64.fullmatch(expected_profile_sha256):
        raise ValueError("invalid pinned A1 profile")
    if endpoint != A1_TEST_ENDPOINT:
        raise ValueError("A1 endpoint is not the pinned isolated sidecar")
    with profile_path.open("rb") as profile_stream:
        profile_raw = profile_stream.read(MAX_PROFILE_BYTES + 1)
    if (len(profile_raw) > MAX_PROFILE_BYTES
            or hashlib.sha256(profile_raw).hexdigest() != expected_profile_sha256):
        raise ValueError("A1 profile drift")
    profile = json.loads(profile_raw)
    if (not isinstance(profile, dict)
            or profile.get("schema") != "aster-full-path-development-profile.v1"
            or profile.get("result_class") != "stream-a-candidate-path-baseline"
            or profile.get("tool_mode") != "disabled"
            or profile.get("max_calls") != 20
            or profile.get("batch_max_wall_seconds") != 1200
            or profile.get("per_request_timeout_seconds") != 60):
        raise ValueError("unexpected A1 profile")
    for field, module in (("headless_client_sha256", client_module),
                          ("client_capture_sha256", capture_module)):
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != profile.get(field):
            raise ValueError("A1 client source drift")
    cases_raw = _owner_file(cases_path, maximum=MAX_CASE_BYTES)
    load_cases(cases_raw)
    if hashlib.sha256(cases_raw).hexdigest() != profile.get("case_fixture_sha256"):
        raise ValueError("A1 cases do not match profile")
    token = _owner_file(ingress_token_path, maximum=256)
    if (not 16 <= len(token) <= 256 or any(not 33 <= byte <= 126 for byte in token)):
        raise ValueError("invalid A1 ingress credential")

    admission: dict[str, object] | None = None
    receipt_digests: set[str] = set()
    admission_checks = 0

    def require_live_admission() -> None:
        nonlocal admission, admission_checks
        current = _validate_admission(
            assert_admitted(expected_profile_sha256, A1_TEST_ENDPOINT),
            expected_profile_sha256)
        if admission is not None and (current["lease_id"], current["generation"]) != (admission["lease_id"], admission["generation"]):
            raise RuntimeError("A1 lease identity changed during batch")
        admission = current
        receipt_digests.add(current["receipt_sha256"])
        admission_checks += 1

    require_live_admission()

    def admitted_invoke(case: dict, *, timeout_s: float):
        require_live_admission()
        return transport(case, endpoint=endpoint, ingress_token=token,
                         timeout_s=timeout_s)

    summary = capture(cases_raw, expected_profile_sha256, output_dir,
                      admitted_invoke, max_wall_s=1200)
    _write_final_manifest(output_dir, profile_sha256=expected_profile_sha256,
                          admission=admission, receipt_digests=receipt_digests,
                          checks=admission_checks, summary=summary)
    return summary
