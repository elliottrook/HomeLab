#!/usr/bin/env python3
"""Read-only live proof for the fixed Aster TTS single-candidate workload."""

from __future__ import annotations

from datetime import datetime
import json
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, "/usr/local/libexec/local-ai-lease/full-inference-pilot")

from full_inference_lab_runtime import _host_runner
from full_inference_lab_session import plan
from full_inference_lab_sources import (AcceptedBaseline, LocalProxmoxFullDrainSourceProducer,
                                        TrustedOwnerAttestation)
from lab_hours_reserved_runner import BINARY_SHA, MODEL_SHA, UNIT_SHA


def main() -> int:
    now = int(time.time())
    start = now + 60
    cycle = datetime.fromtimestamp(now, ZoneInfo("America/Vancouver")).strftime("%Y_%m_%d")
    producer = LocalProxmoxFullDrainSourceProducer(
        _host_runner, AcceptedBaseline(MODEL_SHA, BINARY_SHA, UNIT_SHA),
        TrustedOwnerAttestation("aster-tts-preflight", "read-only-static-proof"),
    )
    preflight = producer.collect(cycle=cycle, session_start_epoch=start, lab_seconds=2400)
    value = plan(preflight, lab_seconds=2400, allow_news_overlap=True)
    print(json.dumps({
        "schema": "aster-tts-single-cpu-preflight.v1",
        "state": "ready",
        "lab_seconds": value.lab_seconds,
        "restore_reserve_seconds": value.restore_reserve_seconds,
        "session_start_epoch": preflight.session_start_epoch,
        "lab_end_epoch": preflight.lab_end_epoch,
        "restore_deadline_epoch": preflight.restore_deadline_epoch,
        "source_verified": preflight.source_verified,
        "consumers_healthy": preflight.consumers_healthy,
        "accepted_baseline_verified": preflight.accepted_baseline_verified,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
