"""Content-free health check for reservation-driven Lab Hours."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time

from lab_hours_reservations import ACTIVE, RESTORE_BUFFER_SECONDS, ReservationError, ReservationStore


STATE_ROOT = Path("/var/lib/local-ai-lab")
RESERVATIONS = STATE_ROOT / "reservations"
REQUIRED = (("104", "aster-agent.service"), ("110", "aster-llama.service"),
            ("116", "aster-speech.service"), ("114", "news-aggregator-ingest.timer"),
            ("114", "news-aggregator-digest.timer"),
            ("116", "epub-narration-worker.timer"))


def call(command: tuple[str, ...], timeout: float = 10.0):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def diagnose(store: ReservationStore, *, now: int | None = None,
             runner=call) -> dict[str, object]:
    now = int(time.time()) if now is None else now
    problems: list[str] = []
    try: records = store.list()
    except (ReservationError, OSError, json.JSONDecodeError):
        records=[]; problems.append("RESERVATION_LEDGER_INVALID")
    active = [v for v in records if v.get("state") in ACTIVE]
    for value in active:
        state = value.get("state")
        if state == "scheduled" and now > int(value["start_epoch"]) + 120:
            problems.append("MISSED_RESERVATION")
        if state == "claimed" and now > int(value["end_epoch"]) + RESTORE_BUFFER_SECONDS:
            problems.append("STALE_CLAIM")
    state_present = (STATE_ROOT / "full-inference-drain.json").exists()
    lock_present = (STATE_ROOT / "full-inference-drain.lock").exists()
    if (state_present or lock_present) and not any(v.get("state") == "claimed" for v in active):
        problems.append("UNOWNED_DRAIN_STATE")
    claimed = any(v.get("state") == "claimed" for v in active)
    if not claimed:
        for proc in Path("/proc").glob("[0-9]*"):
            try: command=proc.joinpath("cmdline").read_bytes().replace(b"\0",b" ").decode()
            except (OSError,UnicodeDecodeError): continue
            if "aster-llama-lab-smoke" in command:
                problems.append("UNRESERVED_LAB_PROCESS"); break
        listener=runner(("ss","-H","-ltn","sport","=",":11436"),10)
        if listener.returncode==0 and listener.stdout.strip():
            problems.append("UNRESERVED_LAB_LISTENER")
        for vmid, unit in REQUIRED:
            if runner(("pct","exec",vmid,"--","systemctl","is-active",unit),10).returncode != 0:
                problems.append(f"PRODUCTION_SERVICE_DOWN:{vmid}:{unit}")
        lease=runner(("/usr/local/sbin/local-ai-lease","status"),10)
        try: lease_value=json.loads(lease.stdout)
        except json.JSONDecodeError: lease_value=None
        if lease.returncode != 0 or lease_value not in ("ready", {"state":"ready"}):
            problems.append("LEASE_NOT_READY")
    successful=[]
    attempts=STATE_ROOT/"lab-hours-attempts"
    if attempts.is_dir() and not attempts.is_symlink():
        for terminal in attempts.glob("reservation-*/terminal.json"):
            try:
                value=json.loads(terminal.read_text())
                if value.get("state")=="complete" and value.get("production_restored") is True:
                    successful.append(int(value["finished_epoch"]))
            except (OSError,ValueError,TypeError,json.JSONDecodeError):
                problems.append("ATTEMPT_EVIDENCE_INVALID")
    return {"state":"healthy" if not problems else "unhealthy",
            "active_reservations":len(active),"last_success_epoch":max(successful,default=None),
            "codes":sorted(set(problems))}


def main() -> int:
    if os.geteuid()!=0:
        print(json.dumps({"state":"unhealthy","codes":["ROOT_REQUIRED"]},sort_keys=True)); return 2
    value=diagnose(ReservationStore(RESERVATIONS)); print(json.dumps(value,sort_keys=True))
    return 0 if value["state"]=="healthy" else 1


if __name__=="__main__": raise SystemExit(main())
