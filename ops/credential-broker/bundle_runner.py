#!/usr/bin/env python3
"""Local state machine joining verified bundles to the existing AI-PAM broker.

Retrieval is deliberately outside this module.  The caller must provide an
already-complete immutable directory and authoritative current base/policy
values.  No automatic approval is possible.
"""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from bundle_verifier import ReplayLedger, VerifiedBundle, reverify_for_promotion, verify_bundle


class BrokerDenied(RuntimeError):
    pass


def broker_call(socket_path: Path, request: Mapping[str, object]) -> Mapping[str, object]:
    encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > 65_536:
        raise BrokerDenied("broker request is oversized")
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(10)
        client.connect(str(socket_path))
        client.sendall(encoded + b"\n")
        raw = client.makefile("rb").readline(65_537)
    if not raw or len(raw) > 65_536:
        raise BrokerDenied("broker response is empty or oversized")
    try:
        response = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BrokerDenied("broker response is malformed") from exc
    if not isinstance(response, dict) or not response.get("ok"):
        raise BrokerDenied("broker denied the request")
    result = response.get("result")
    if not isinstance(result, dict):
        raise BrokerDenied("broker response is malformed")
    return result


@dataclass(frozen=True)
class PendingBundle:
    verified: VerifiedBundle
    broker_request_id: str


class BundleRunner:
    def __init__(
        self,
        ledger: ReplayLedger,
        broker: Callable[[Mapping[str, object]], Mapping[str, object]],
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.ledger = ledger
        self.broker = broker
        self.clock = clock

    def submit(
        self,
        bundle_dir: Path,
        *,
        current_base_revision: str,
        policy_digest: str,
        verify_signature,
    ) -> PendingBundle:
        now = int(self.clock())
        verified = verify_bundle(
            bundle_dir,
            current_base_revision=current_base_revision,
            policy_digest=policy_digest,
            verify_signature=verify_signature,
            now=now,
        )
        self.ledger.reserve(verified, now)
        result = self.broker({
            "method": "request.create",
            "capability": "forgejo.write.safe-branch",
            "payload": dict(verified.payload),
            "ttl_seconds": min(300, verified.expires_at - now),
            "display": {
                "reason": "Signed cloud bundle canary",
                "target": str(verified.payload["filePath"]),
                "effect": f"Create one new file on {verified.target_branch}",
                "rollback": "Do not merge; revoke request or leave/delete branch with separate approval",
            },
        })
        request_id = result.get("request_id")
        if result.get("status") != "pending" or not isinstance(request_id, str):
            self.ledger.revoke(verified.nonce, verified.request_digest, now)
            raise BrokerDenied("broker did not create a pending Yellow request")
        self.ledger.bind_broker_request(
            verified.nonce, verified.request_digest, request_id, now,
        )
        return PendingBundle(verified, request_id)

    def promote(
        self,
        pending: PendingBundle,
        *,
        bundle_dir: Path,
        current_base_revision: str,
        policy_digest: str,
    ) -> Mapping[str, object]:
        now = int(self.clock())
        request_id = self.ledger.pending_request_id(
            pending.verified.nonce, pending.verified.request_digest,
        )
        if request_id != pending.broker_request_id:
            raise BrokerDenied("broker request binding changed")
        reverify_for_promotion(
            pending.verified,
            bundle_dir=bundle_dir,
            current_base_revision=current_base_revision,
            policy_digest=policy_digest,
            now=now,
        )
        result = self.broker({
            "method": "request.consume",
            "request_id": request_id,
            "payload": dict(pending.verified.payload),
        })
        if result.get("status") != "consumed":
            raise BrokerDenied("broker did not consume the approved request")
        self.ledger.consume(
            pending.verified.nonce, pending.verified.request_digest, now,
        )
        return result
