"""Renew the application watchdog assertion for one bounded timer tick."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from application_receipt_boundary import A1_PROFILE_SHA256, renew_watchdog_status


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    args = parser.parse_args(argv)
    if os.geteuid() != 0:
        raise SystemExit("application heartbeat requires root")
    if args.profile != A1_PROFILE_SHA256:
        raise SystemExit("profile pin is invalid")
    result = renew_watchdog_status(now_epoch=int(time.time()),
                                   profile_sha256=args.profile)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
