#!/usr/bin/env python3
"""Disabled, fixed-source acquisition candidate for the full-stop recovery drill.

The executable effect path is intentionally disabled in this source revision.
A later pinned release must separately authorize and enable it. Tests exercise
the injected boundary without contacting a HomeLab service.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fixed_source_adapters import FixedSourceAdapters
from full_stop_source_preflight import prepare_pre_acquire
from lease_controller_candidate import CandidateController, CandidatePaths
from lease_effect_runner import EffectRunner
from lease_recovery_executor import secure_root_file
from trusted_observer import RuntimeManifest, TrustedHostObserver


ROOT = Path("/var/lib/local-ai-lab")
MANIFEST = ROOT / "runtime-manifest.json"
ZONE = ZoneInfo("America/Vancouver")
WINDOW_START = 190  # 03:10 Vancouver
ACQUIRE_CUTOFF = 195  # 03:15 Vancouver
RESTORE_CUTOFF = 210  # 03:30 Vancouver
EFFECTS_ENABLED = False


def acquire_from_fixed_sources(
    adapters: FixedSourceAdapters,
    observer: TrustedHostObserver,
    controller: CandidateController,
    *,
    clock,
    lease_id: str,
) -> dict[str, object]:
    """Verify retained backup and exact runtime before any service stop."""
    started = clock().astimezone(ZONE)
    minute = started.hour * 60 + started.minute
    if not WINDOW_START <= minute < ACQUIRE_CUTOFF:
        raise ValueError("full-stop acquisition is outside its fixed window")
    backup = adapters.backup_from_retained(
        date_prefix=started.strftime("%Y_%m_%d"),
        lease_issued_epoch=int(started.timestamp()),
    )
    observation = observer.collect(RESTORE_CUTOFF)
    observed_at = clock().astimezone(ZONE)
    observed_minute = observed_at.hour * 60 + observed_at.minute
    if observation.now_minute != observed_minute:
        raise ValueError("runtime observation is not from the acquisition minute")
    receipt = prepare_pre_acquire(
        backup, observation, lease_id=lease_id, generation=1,
        expires_minute=RESTORE_CUTOFF,
    )
    before_effect = clock().astimezone(ZONE)
    if (before_effect.date() != started.date() or
            not WINDOW_START <= before_effect.hour * 60 + before_effect.minute < ACQUIRE_CUTOFF):
        raise ValueError("full-stop preflight exceeded the acquisition window")
    return controller.acquire(receipt, observation, backup_receipt=backup.integrity_receipt)


def _runner(argv, timeout):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    return result.returncode, result.stdout


def _watchdog_active() -> bool:
    return _runner(("systemctl", "is-active", "local-ai-lease-watchdog.timer"), 5.0) == (0, "active\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized or not EFFECTS_ENABLED:
        print(json.dumps({"state": "disabled", "effects": "not-attempted"}, sort_keys=True))
        return 0
    if os.geteuid() != 0:
        raise SystemExit("full-stop acquisition requires root")
    secure_root_file(MANIFEST)
    if (ROOT / "lease.json").exists() or (ROOT / "lease.lock").exists():
        raise SystemExit("a lease or retained lock already exists")
    if not _watchdog_active():
        raise SystemExit("independent recovery timer is not active")
    manifest = RuntimeManifest(**json.loads(MANIFEST.read_text()))
    observer = TrustedHostObserver(_runner, manifest)
    controller = CandidateController(
        CandidatePaths(ROOT), EffectRunner().run,
        allow_effects=True, observer=observer,
    )
    result = acquire_from_fixed_sources(
        FixedSourceAdapters(_runner), observer, controller,
        clock=lambda: datetime.now(ZONE), lease_id="lab-" + uuid.uuid4().hex,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
