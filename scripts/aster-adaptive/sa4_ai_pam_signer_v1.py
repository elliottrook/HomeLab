"""Fixed AI-PAM signer for one canonical SA4 grant proof statement.

The private key path, signer identity and proof scope are compiled constants.
The module exposes no key-export or arbitrary-message operation.  Importing it
has no effect; the fixed key is opened only by the target-local OpenSSL child
after the complete canonical statement has passed validation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Callable


KEY_PATH = "/var/lib/homelab-broker/sa4-signing/ai-pam-grant-v1.pem"
OPENSSL = "/usr/bin/openssl"
SIGNER_ID = "aster-ai-pam"
KEY_SHA256 = "f9ff0e192840dc0794e4adb65dad91a608e32e5d1d389bccbeac3612f54e9cb0"
FIELDS = {
    "schema", "proof_scope", "signer_id", "signer_key_sha256",
    "payload_sha256", "signature_algorithm", "authority",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate_statement(raw: bytes) -> bytes:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 4096:
        raise ValueError("AI-PAM proof size changed")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AI-PAM proof is not JSON") from exc
    if (not isinstance(value, dict) or set(value) != FIELDS
            or value["schema"] != "aster-sa4-detached-proof.v1"
            or value["proof_scope"] != "ai-pam-grant"
            or value["signer_id"] != SIGNER_ID
            or value["signer_key_sha256"] != KEY_SHA256
            or not isinstance(value["payload_sha256"], str)
            or len(value["payload_sha256"]) != 64
            or any(character not in "0123456789abcdef"
                   for character in value["payload_sha256"])
            or value["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or value["authority"] != "signature-only-no-effect"
            or canonical(value) != raw):
        raise ValueError("AI-PAM proof statement changed")
    return raw


def read_statement(path: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("AI-PAM proof is not a regular file")
        raw = os.read(descriptor, 4097)
        if os.read(descriptor, 1):
            raise ValueError("AI-PAM proof exceeds bounded read")
    finally:
        os.close(descriptor)
    return validate_statement(raw)


def sign(raw: bytes, *, runner: Callable[..., subprocess.CompletedProcess]
         = subprocess.run) -> str:
    message = validate_statement(raw)
    result = runner(
        [OPENSSL, "dgst", "-sha256", "-sign", KEY_PATH],
        input=message, capture_output=True, check=False, timeout=15)
    if result.returncode != 0:
        raise RuntimeError("AI-PAM fixed signer failed")
    signature = result.stdout
    if not isinstance(signature, bytes) or len(signature) != 256:
        raise RuntimeError("AI-PAM signature shape changed")
    return signature.hex()


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        raise ValueError("usage: sa4-ai-pam-signer <canonical-proof-path>")
    print(sign(read_statement(arguments[1])))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)

