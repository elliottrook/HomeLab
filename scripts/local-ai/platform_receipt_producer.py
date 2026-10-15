"""Root-only producer for the platform-owned candidate source receipt."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from admission_state import decode
from fixed_source_adapters import FixedSourceAdapters
from source_receipt_boundary import produce_candidate_receipt

STATE = Path("/var/lib/local-ai-lab/lease.json")
RECEIPT = Path("/var/lib/local-ai-lab/source-receipt.json")
WINDOW_ZONE = ZoneInfo("America/Vancouver")


def main() -> int:
    if os.geteuid() != 0:
        raise SystemExit("receipt producer must run as root")
    record = decode(STATE.read_text())
    if record.state != "leased":
        raise SystemExit("a leased host state is required")
    lease_issued_epoch = int(STATE.stat().st_mtime)
    now = datetime.now(WINDOW_ZONE)
    now_minute = now.hour * 60 + now.minute

    def runner(argv: tuple[str, ...], timeout: float) -> tuple[int, str]:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode, result.stdout

    adapters = FixedSourceAdapters(runner)
    produce_candidate_receipt(
        RECEIPT,
        adapters,
        lease_id=record.lease_id,
        generation=record.generation,
        date_prefix=now.strftime("%Y_%m_%d"),
        lease_issued_epoch=lease_issued_epoch,
        now_minute=now_minute,
        window_end_minute=record.expires_minute,
        captured_epoch=int(time.time()),
        expected_backup_receipt=record.backup_receipt,
    )
    print(json.dumps({"state": "candidate-receipt-written", "lease_id": record.lease_id, "generation": record.generation, "receipt": str(RECEIPT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
