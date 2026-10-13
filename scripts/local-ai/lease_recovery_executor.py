"""Host-local recovery executor for the disabled Local AI lease candidate.

The default path is advisory. Effects require the explicit
``--effect-authorized`` flag, so a timer invocation cannot restore guests merely
because a lease is expired unless the installed unit and deployment review
deliberately permit that mode.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from admission_state import decode
from lease_contract import LeaseReceipt
from lease_controller_candidate import CandidateController, CandidatePaths
from lease_effect_runner import EffectRunner
from lease_watchdog import WatchdogState, decide, status_receipt
from trusted_observer import RuntimeManifest, TrustedHostObserver


def secure_root_file(path: Path) -> None:
    import stat

    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise SystemExit("insecure watchdog state or manifest custody")


def effects_permitted(current_state: WatchdogState, decision_state: WatchdogState, effect_authorized: bool, control_plane_healthy: bool) -> bool:
    """Allow re-entry only for an active lease with a live control plane."""
    return (
        effect_authorized
        and control_plane_healthy
        and current_state in {WatchdogState.LEASED, WatchdogState.RESTORING}
        and decision_state in {WatchdogState.RESTORING, WatchdogState.FAILED}
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--state", type=Path, default=Path("/var/lib/local-ai-lab/lease.json"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    secure_root_file(args.state)
    secure_root_file(args.manifest)
    record = decode(args.state.read_text())
    manifest = RuntimeManifest(**json.loads(args.manifest.read_text()))

    def probe_runner(command, timeout):
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode, result.stdout

    observer = TrustedHostObserver(probe_runner, manifest)
    current_state = WatchdogState(record.state)
    observation = observer.collect_light(record.expires_minute) if current_state == WatchdogState.LEASED else observer.collect(record.expires_minute)
    receipt = LeaseReceipt(
        record.lease_id, record.generation, record.issued_minute,
        record.expires_minute, record.backup_receipt, record.model_identity,
        record.backend_identity, record.consumers_isolated,
        record.scheduled_work_quiesced,
    )
    decision = decide(receipt, observation, backup_receipt=record.backup_receipt, current_state=current_state)
    if not effects_permitted(current_state, decision.state, args.effect_authorized, observation.control_plane_healthy):
        print(json.dumps({
            "decision": status_receipt(receipt, decision.state, observation),
            "actions": decision.actions,
            "effects": "disabled",
        }, sort_keys=True))
        return 0

    controller = CandidateController(
        CandidatePaths(args.state.parent),
        EffectRunner().run,
        allow_effects=True,
        observer=observer,
    )
    try:
        result = controller.restore(receipt, observation, backup_receipt=record.backup_receipt)
    except Exception:
        print(json.dumps({
            "decision": status_receipt(receipt, WatchdogState.FAILED, observation, failure_code="recovery-incomplete"),
            "effects": "attempted",
        }, sort_keys=True))
        return 1
    print(json.dumps({"result": result, "effects": "completed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
