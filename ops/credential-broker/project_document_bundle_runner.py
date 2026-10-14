#!/usr/bin/env python3
"""Stage and approve bounded project-document bundles without inline payloads."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from bundle_runner import BrokerDenied, broker_call
from bundle_verifier import ReplayLedger, verify_openssh_signature
from project_document_bundle_verifier import (
    Denied,
    VerifiedDocumentBundle,
    reverify_document_bundle,
    verify_document_bundle,
)


def _copy_bounded(source: Path, target: Path, *, mode: int = 0o640) -> None:
    data = source.read_bytes()
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), mode)
    try:
        written = 0
        while written < len(data):
            written += os.write(descriptor, data[written:])
        os.fchmod(descriptor, mode)
    finally:
        os.close(descriptor)


def stage_bundle(source: Path, handoff_root: Path, verified: VerifiedDocumentBundle) -> Path:
    """Copy a verified package into an exclusive, digest-named handoff."""
    root = handoff_root.resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise Denied("handoff root is not a directory")
    final = root / verified.request_digest
    if final.exists() or final.is_symlink():
        raise Denied("handoff digest is already staged")
    temporary = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
    try:
        os.chmod(temporary, 0o750)
        (temporary / "files").mkdir(mode=0o750)
        _copy_bounded(source.resolve(strict=True) / "manifest.json", temporary / "manifest.json")
        _copy_bounded(source.resolve(strict=True) / "manifest.sig", temporary / "manifest.sig")
        for document in verified.documents:
            relative = PurePosixPath("files") / document.path
            target = temporary / relative
            target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
            _copy_bounded(source.resolve(strict=True) / relative, target)
        reverify_document_bundle(
            verified, bundle_dir=temporary,
            current_base_revision=verified.base_revision,
            policy_digest=verified.policy_digest,
            now=int(time.time()),
        )
        os.replace(temporary, final)
        os.chmod(final, 0o750)
        return final
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def promotion_payload(verified: VerifiedDocumentBundle) -> dict[str, object]:
    return {
        "owner": "jason", "repo": "homelab", "bundle_id": verified.request_digest,
        "base_revision": verified.base_revision, "policy_digest": verified.policy_digest,
        "branch_name": "main", "new_branch_name": verified.target_branch,
        "message": verified.commit_message,
        "files": [
            {"filePath": document.path, "content_sha256": document.content_sha256,
             "content_size": document.content_size}
            for document in verified.documents
        ],
    }


@dataclass(frozen=True)
class PendingDocumentBundle:
    verified: VerifiedDocumentBundle
    broker_request_id: str
    handoff_dir: Path


class ProjectDocumentBundleRunner:
    def __init__(
        self,
        ledger: ReplayLedger,
        broker: Callable[[Mapping[str, object]], Mapping[str, object]],
        handoff_root: Path,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.ledger = ledger
        self.broker = broker
        self.handoff_root = handoff_root
        self.clock = clock

    def submit(
        self,
        bundle_dir: Path,
        *,
        current_base_revision: str,
        policy_digest: str,
        verify_signature,
    ) -> PendingDocumentBundle:
        now = int(self.clock())
        verified = verify_document_bundle(
            bundle_dir, current_base_revision=current_base_revision,
            policy_digest=policy_digest, verify_signature=verify_signature, now=now,
        )
        handoff = stage_bundle(bundle_dir, self.handoff_root, verified)
        try:
            self.ledger.reserve(verified, now)  # type: ignore[arg-type]
            result = self.broker({
                "method": "request.create",
                "capability": "forgejo.write.project-documents",
                "payload": promotion_payload(verified),
                "ttl_seconds": min(900, verified.expires_at - now),
                "display": {
                    "reason": "Approved cloud project-document package",
                    "target": f"{len(verified.documents)} project/hand-over documents",
                    "effect": f"Create a new Forgejo branch {verified.target_branch}",
                    "rollback": "Do not merge; revoke or retain the non-main branch",
                },
            })
            request_id = result.get("request_id")
            if result.get("status") != "pending" or not isinstance(request_id, str):
                self.ledger.revoke(verified.nonce, verified.request_digest, now)
                raise BrokerDenied("broker did not create a pending project request")
            self.ledger.bind_broker_request(verified.nonce, verified.request_digest, request_id, now)
            return PendingDocumentBundle(verified, request_id, handoff)
        except Exception:
            if handoff.exists():
                shutil.rmtree(handoff, ignore_errors=True)
            raise

    def promote(
        self,
        pending: PendingDocumentBundle,
        *,
        current_base_revision: str,
        policy_digest: str,
    ) -> Mapping[str, object]:
        now = int(self.clock())
        request_id = self.ledger.pending_request_id(
            pending.verified.nonce, pending.verified.request_digest,
        )
        if request_id != pending.broker_request_id:
            raise BrokerDenied("broker request binding changed")
        reverify_document_bundle(
            pending.verified, bundle_dir=pending.handoff_dir,
            current_base_revision=current_base_revision,
            policy_digest=policy_digest, now=now,
        )
        result = self.broker({
            "method": "request.consume", "request_id": request_id,
            "payload": promotion_payload(pending.verified),
        })
        if result.get("status") != "consumed":
            raise BrokerDenied("broker did not consume the approved project request")
        self.ledger.consume(pending.verified.nonce, pending.verified.request_digest, now)
        return result


def _policy_value(path: Path, label: str) -> str:
    try:
        value = path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise BrokerDenied(f"{label} policy is unavailable") from exc
    if not value or "\n" in value or "\r" in value:
        raise BrokerDenied(f"{label} policy is invalid")
    return value


def _cli_signature_verifier(allowed_signers: Path, principal: str):
    def verify(body: bytes, signature: bytes, signer: str) -> bool:
        return signer == principal and verify_openssh_signature(
            body, signature, allowed_signers=allowed_signers, principal=principal,
        )

    return verify


def cli_main(argv: list[str] | None = None) -> int:
    """Run the reviewed local intake/approval wrapper.

    The command accepts only a package directory and policy-file paths. It
    never accepts credentials or document content as arguments, and emits
    metadata only. ``submit`` creates a pending approval; ``promote`` requires
    that same request to be approved and rechecks the staged handoff before
    consuming it.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("submit", "promote"))
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument(
        "--ledger", type=Path,
        default=Path("/var/lib/homelab-bundle-runner/ledger.sqlite"),
    )
    parser.add_argument(
        "--broker-socket", type=Path,
        default=Path("/run/homelab-broker/mcp.sock"),
    )
    parser.add_argument(
        "--handoff-root", type=Path,
        default=Path("/var/lib/homelab-bundle-runner/handoff"),
    )
    parser.add_argument(
        "--base-file", type=Path,
        default=Path("/etc/homelab-bundle-runner/base_revision"),
    )
    parser.add_argument(
        "--policy-file", type=Path,
        default=Path("/etc/homelab-bundle-runner/policy_digest"),
    )
    parser.add_argument(
        "--allowed-signers", type=Path,
        default=Path("/etc/homelab-bundle-runner/allowed_signers"),
    )
    parser.add_argument("--principal", default="cloud-producer")
    args = parser.parse_args(argv)

    base = _policy_value(args.base_file, "base revision")
    policy = _policy_value(args.policy_file, "policy digest")
    verify_signature = _cli_signature_verifier(args.allowed_signers, args.principal)
    ledger = ReplayLedger(args.ledger)
    try:
        runner = ProjectDocumentBundleRunner(
            ledger,
            lambda request: broker_call(args.broker_socket, request),
            args.handoff_root,
            clock=time.time,
        )
        if args.action == "submit":
            pending = runner.submit(
                args.bundle_dir, current_base_revision=base,
                policy_digest=policy, verify_signature=verify_signature,
            )
            output = {
                "status": "pending", "request_id": pending.broker_request_id,
                "request_digest": pending.verified.request_digest,
                "target_branch": pending.verified.target_branch,
                "expires_at": pending.verified.expires_at,
            }
        else:
            verified = verify_document_bundle(
                args.bundle_dir, current_base_revision=base,
                policy_digest=policy, verify_signature=verify_signature,
            )
            request_id = ledger.pending_request_id(
                verified.nonce, verified.request_digest,
            )
            result = runner.promote(
                PendingDocumentBundle(
                    verified, request_id, args.handoff_root / verified.request_digest,
                ),
                current_base_revision=base, policy_digest=policy,
            )
            output = {
                "status": result.get("status"), "request_id": request_id,
                "request_digest": verified.request_digest,
                "target_branch": verified.target_branch,
                "files": [document.path for document in verified.documents],
            }
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 0
    except (BrokerDenied, Denied, OSError, ValueError) as exc:
        print(f"DENIED {exc}", file=os.sys.stderr)
        return 1
    finally:
        ledger.close()


def main() -> None:
    raise SystemExit(cli_main())


if __name__ == "__main__":
    main()
