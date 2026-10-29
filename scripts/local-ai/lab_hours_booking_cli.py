"""Administrative CLI for the B60 Lab Hours reservation ledger."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from lab_hours_reservations import ReservationError, ReservationStore


DEFAULT_ROOT = Path("/var/lib/local-ai-lab/reservations")


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
    reserve.add_argument("--workload", required=True)
    reserve.add_argument("--start", required=True, type=_epoch)
    reserve.add_argument("--end", required=True, type=_epoch)
    commands.add_parser("list")
    get = commands.add_parser("get"); get.add_argument("booking_id")
    cancel = commands.add_parser("cancel"); cancel.add_argument("booking_id")
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
                                  end_epoch=args.end)
        elif args.command == "list": value = store.list()
        elif args.command == "get": value = store.get(args.booking_id)
        elif args.command == "cancel": value = store.cancel(args.booking_id)
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
