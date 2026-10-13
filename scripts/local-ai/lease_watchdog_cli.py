#!/usr/bin/env python3
"""Content-free watchdog decision entrypoint for the installed adapter."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from admission_state import decode
from lease_contract import LeaseReceipt
from lease_watchdog import WatchdogState, decide, status_receipt
from trusted_observer import RuntimeManifest, collect


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--state", type=Path, default=Path("/var/lib/local-ai-lab/lease.json"))
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    record = decode(args.state.read_text())
    manifest = RuntimeManifest(**json.loads(args.manifest.read_text()))
    def runner(argv, timeout):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode, result.stdout
    observation = collect(runner, lease_expires_minute=record.expires_minute, manifest=manifest)
    receipt = LeaseReceipt(
        record.lease_id, record.generation, record.issued_minute,
        record.expires_minute, record.backup_receipt, record.model_identity,
        record.backend_identity, record.consumers_isolated,
        record.scheduled_work_quiesced,
    )
    current = WatchdogState(record.state)
    decision = decide(receipt, observation, backup_receipt=record.backup_receipt, current_state=current)
    failure = None if decision.state in {WatchdogState.LEASED, WatchdogState.READY} else "recovery-required"
    print(json.dumps({"decision": status_receipt(receipt, decision.state, observation, failure_code=failure), "actions": decision.actions}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
