"""Export only validated, non-secret lease receipt fields for Aster."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from admission_state import decode
from source_receipt_boundary import read_receipt

STATE = Path("/var/lib/local-ai-lab/lease.json")
RECEIPT = Path("/var/lib/local-ai-lab/source-receipt.json")
ZONE = ZoneInfo("America/Vancouver")


def main() -> int:
    if os.geteuid() != 0:
        raise SystemExit("receipt exporter must run as root")
    record = decode(STATE.read_text())
    now = datetime.now(ZONE)
    raw_bytes = RECEIPT.read_bytes()
    validated_source = read_receipt(
        RECEIPT,
        lease_id=record.lease_id,
        generation=record.generation,
        now_minute=now.hour * 60 + now.minute,
        window_end_minute=record.expires_minute,
        now_epoch=int(time.time()),
    )
    payload = json.loads(raw_bytes)
    evidence = payload["evidence"]
    print(json.dumps({
        "state": "validated",
        "lease_id": record.lease_id,
        "generation": record.generation,
        "captured_epoch": payload["captured_epoch"],
        "receipt_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "validated_source": validated_source,
        "backup_receipt": evidence["backup_receipt"],
        "backup_completed_minute": evidence["backup_completed_minute"],
        "backup_verified": evidence["backup_verified"],
        "consumers_quiesced": evidence["consumers_quiesced"],
        "news_quiesced": evidence["news_quiesced"],
        "source_observed": evidence["source_observed"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
