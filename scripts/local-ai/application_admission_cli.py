"""Single-request host admission endpoint for the A1 Mini callback.

This process is intended to be exposed only through a restricted transport
identity/forced command. It accepts the pinned profile as its sole argument,
reads the current host-owned lease boundary, and emits one content-free JSON
admission payload. It never accepts a lease, endpoint, receipt, or clock from
the caller.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from application_receipt_boundary import A1_PROFILE_SHA256, host_admission_callback


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    args = parser.parse_args(argv)
    if os.geteuid() != 0:
        raise SystemExit("host admission endpoint requires root")
    if args.profile != A1_PROFILE_SHA256:
        raise SystemExit("profile pin is invalid")
    payload = host_admission_callback(args.profile)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
