#!/usr/bin/env python3
"""Record Jason's one-candidate approval outside Aster and its chat path."""

from __future__ import annotations

import argparse
import json
import os
import pwd
from pathlib import Path

from approval_state import ApprovalStateError
from execution import grant_approval


STATE_ROOT = Path(
    os.environ.get(
        "ASTER_ARR_BROKER_STATE_ROOT", "/mnt/Media/data/tools/aster-arr-broker/state"
    )
)
BROKER_ACCOUNT = "aster-arr-broker"


def drop_to_broker_account() -> None:
    """Keep the operator ceremony root-invokable without root-owned state."""
    if os.geteuid() != 0:
        return
    account = pwd.getpwnam(BROKER_ACCOUNT)
    os.setgroups([])
    os.setgid(account.pw_gid)
    os.setuid(account.pw_uid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Approve one non-reversible stale Radarr queue-record dismissal"
    )
    parser.add_argument("--candidate-ref", required=True)
    parser.add_argument(
        "--accept-nonreversible",
        action="store_true",
        help="confirm that the queue record cannot be recreated",
    )
    args = parser.parse_args()
    if not args.accept_nonreversible:
        parser.error("--accept-nonreversible is required")

    try:
        drop_to_broker_account()
        record = grant_approval(
            args.candidate_ref,
            candidates_path=STATE_ROOT / "candidates.json",
            approvals_path=STATE_ROOT / "approvals.json",
            lock_path=STATE_ROOT / "broker.lock",
        )
    except (ApprovalStateError, KeyError, OSError):
        print('{"status":"refused"}')
        return 1
    print(
        json.dumps(
            {
                "status": "approved",
                "operation": record.operation,
                "candidate_ref": record.candidate_ref,
                "expires_at": record.expires_at.isoformat().replace("+00:00", "Z"),
                "nonreversible_accepted": record.nonreversible_accepted,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
