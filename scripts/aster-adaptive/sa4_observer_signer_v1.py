"""Fixed Proxmox observer signer for canonical SA4 receipt proofs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Callable


KEY_PATH = "/var/lib/aster/sa4-observer/independent-observer-v1.pem"
OPENSSL = "/usr/bin/openssl"
OBSERVER_ID = "aster-observer"
KEY_SHA256 = "a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b"
FIELDS = {"schema", "receipt_sha256", "observer_id",
          "observer_key_sha256", "signature_algorithm", "authority"}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate_statement(raw: bytes) -> bytes:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 4096:
        raise ValueError("observer proof size changed")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("observer proof is not JSON") from exc
    digest = value.get("receipt_sha256") if isinstance(value, dict) else None
    if (not isinstance(value, dict) or set(value) != FIELDS
            or value["schema"] != "aster-sa4-independent-receipt-proof.v1"
            or not isinstance(digest, str) or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or value["observer_id"] != OBSERVER_ID
            or value["observer_key_sha256"] != KEY_SHA256
            or value["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or value["authority"] != "observer-proof-only-no-effect"
            or canonical(value) != raw):
        raise ValueError("observer proof statement changed")
    return raw


def read_statement(path: str) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("observer proof is not a regular file")
        raw = os.read(descriptor, 4097)
    finally:
        os.close(descriptor)
    return validate_statement(raw)


def sign(raw: bytes, *, runner: Callable[..., subprocess.CompletedProcess]
         = subprocess.run) -> str:
    message = validate_statement(raw)
    result = runner([OPENSSL, "dgst", "-sha256", "-sign", KEY_PATH],
                    input=message, capture_output=True, check=False, timeout=15)
    if result.returncode != 0:
        raise RuntimeError("fixed observer signer failed")
    if not isinstance(result.stdout, bytes) or len(result.stdout) != 256:
        raise RuntimeError("observer signature shape changed")
    return result.stdout.hex()


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        raise ValueError("usage: sa4-observer-signer <canonical-proof-path>")
    print(sign(read_statement(arguments[1])))
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main(sys.argv))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr); raise SystemExit(1)

