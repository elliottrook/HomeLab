"""Administrative CLI for the B60 Lab Hours reservation ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from lab_hours_reservations import ReservationError, ReservationStore


DEFAULT_ROOT = Path("/var/lib/local-ai-lab/reservations")
RUNNER = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot/lab_hours_reserved_runner.py")


def _epoch(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include an offset")
    return int(parsed.timestamp())


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    commands = p.add_subparsers(dest="command", required=True)
    reserve = commands.add_parser("reserve")
    reserve.add_argument("--booking-id", required=True)
    reserve.add_argument("--owner", required=True)
    mode = reserve.add_mutually_exclusive_group(required=True)
    mode.add_argument("--workload")
    mode.add_argument("--exclusive", action="store_true",
                      help="reserve stack capacity only; do not dispatch a workload")
    reserve.add_argument("--start", required=True, type=_epoch)
    reserve.add_argument("--end", required=True, type=_epoch)
    reserve.add_argument("--promotable", action="store_true",
                         help="allow this booking to move earlier when a complete window opens")
    commands.add_parser("list")
    get = commands.add_parser("get"); get.add_argument("booking_id")
    cancel = commands.add_parser("cancel"); cancel.add_argument("booking_id")
    retry = commands.add_parser("retry"); retry.add_argument("booking_id")
    release = commands.add_parser("release"); release.add_argument("booking_id")
    check = commands.add_parser("check-window")
    check.add_argument("--start", required=True, type=_epoch)
    check.add_argument("--end", required=True, type=_epoch)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.root == DEFAULT_ROOT and __import__("os").geteuid() != 0:
        print(json.dumps({"state": "no_go", "code": "ROOT_REQUIRED"}, sort_keys=True))
        return 2
    store = ReservationStore(args.root)
    try:
        if args.command == "reserve":
            value = store.reserve(booking_id=args.booking_id, owner=args.owner,
                                  workload=args.workload, start_epoch=args.start,
                                  end_epoch=args.end, exclusive=args.exclusive,
                                  promotable=args.promotable)
        elif args.command == "list": value = store.list()
        elif args.command == "get": value = store.get(args.booking_id)
        elif args.command == "cancel": value = store.cancel(args.booking_id)
        elif args.command == "release":
            record = store.get(args.booking_id)
            claimant = (f"lh-{hashlib.sha256(args.booking_id.encode()).hexdigest()[:20]}"
                        if record.get("state") == "claimed" else None)
            value = store.release(args.booking_id, claimant=claimant)
        elif args.command == "retry":
            record = store.get(args.booking_id)
            claimant = f"lh-{hashlib.sha256(args.booking_id.encode()).hexdigest()[:20]}"
            if (record.get("state") != "claimed" or record.get("claimant") != claimant
                    or record.get("attempt_state") != "failed_restored"
                    or record.get("retry_available") is not True):
                raise ReservationError("session has no approved retryable state")
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", args.booking_id):
                raise ReservationError("booking id is not canonical")
            next_attempt = int(record.get("attempt_count", 0)) + 1
            unit = f"aster-lab-hours-retry-{args.booking_id}-attempt-{next_attempt}.service"
            command = ("systemd-run", "--quiet", "--collect", f"--unit={unit}",
                       "--property=User=root", "--property=Restart=no",
                       "--property=TimeoutStartSec=20min", "/usr/bin/python3", "-B",
                       str(RUNNER), "--booking-id", args.booking_id, "--retry")
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=30, check=False)
            if result.returncode != 0:
                raise ReservationError("retry dispatcher failed")
            value = {"state": "dispatched", "booking_id": args.booking_id,
                     "unit": unit}
        else:
            conflicts = store.check_window(start_epoch=args.start, end_epoch=args.end)
            value = {"state": "clear" if not conflicts else "reserved",
                     "booking_ids": conflicts}
        print(json.dumps(value, sort_keys=True))
        return 0
    except ReservationError as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
