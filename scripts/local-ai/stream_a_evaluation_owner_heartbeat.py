"""Write one root-owned owner-liveness heartbeat for Stream A."""

from __future__ import annotations

import argparse
import json
import time

from stream_a_evaluation_watchdog import HEARTBEAT_PATH, IDENTITY_PATH, load_identity, write_owner_heartbeat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    identity = load_identity(IDENTITY_PATH)
    write_owner_heartbeat(HEARTBEAT_PATH, identity=identity, now_epoch=int(time.time()))
    print(json.dumps({"effects": "heartbeat-written"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
