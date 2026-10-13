#!/usr/bin/env python3
"""Network-free one-shot validator for a human-carried bundle directory."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from bundle_verifier import Denied, verify_bundle, verify_openssh_signature

BUNDLE_ID = re.compile(r"^[A-Za-z0-9_-]{22,128}$")

def _value(path: Path, label: str) -> str:
    try:
        value = path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise Denied(f"{label} policy is unavailable") from exc
    if "\n" in value or "\r" in value:
        raise Denied(f"{label} policy is invalid")
    return value

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--base-file", type=Path, required=True)
    parser.add_argument("--policy-file", type=Path, required=True)
    parser.add_argument("--allowed-signers", type=Path, required=True)
    parser.add_argument("--principal", default="cloud-producer")
    args = parser.parse_args()
    if not BUNDLE_ID.fullmatch(args.bundle_id):
        raise SystemExit("DENIED bundle identifier is invalid")
    try:
        inbox = args.inbox.resolve(strict=True)
        bundle = (inbox / args.bundle_id).resolve(strict=True)
        if bundle.parent != inbox:
            raise Denied("bundle directory escapes inbox")
        verified = verify_bundle(
            bundle,
            current_base_revision=_value(args.base_file, "base revision"),
            policy_digest=_value(args.policy_file, "policy digest"),
            verify_signature=lambda body, signature, principal: (
                principal == args.principal and verify_openssh_signature(
                    body, signature, allowed_signers=args.allowed_signers,
                    principal=principal,
                )
            ),
        )
    except (Denied, OSError) as exc:
        raise SystemExit(f"DENIED {exc}") from None
    print(json.dumps({
        "status": "validated", "request_digest": verified.request_digest,
        "signer": verified.signer, "repository": verified.repository,
        "base_revision": verified.base_revision, "target_branch": verified.target_branch,
        "content_digest": verified.content_digest, "expires_at": verified.expires_at,
    }, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
