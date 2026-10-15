"""Bounded host entrypoint for the application-only B60 drill.

This is the only supported effectful controller entrypoint. It accepts only
root-owned, mode-0600 JSON observations produced by the trusted preflight and
sidecar observer; it has no shell, arbitrary command, lease, or credential
input path. The default plan phase is effect-free.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from application_b60_controller import ApplicationB60Controller, ApplicationPaths, ApplicationPreLease
from application_b60_lease import ApplicationLeaseReceipt, SidecarObservation
from lease_effect_runner import EffectRunner


def _owner_json(path: Path) -> dict[str, object]:
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("input path must be absolute and non-symlinked")
    info = path.stat()
    if info.st_uid != 0 or info.st_mode & 0o077 or info.st_size > 32_000:
        raise ValueError("input custody failed")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def _controller(state_dir: Path) -> ApplicationB60Controller:
    return ApplicationB60Controller.production(
        ApplicationPaths(state_dir), EffectRunner().run, now_epoch=lambda: int(time.time()))


def _prelease(value: dict[str, object]) -> ApplicationPreLease:
    fields = set(ApplicationPreLease.__dataclass_fields__)
    if set(value) != fields:
        raise ValueError("pre-lease fields are not exact")
    return ApplicationPreLease(**value)


def _receipt(value: dict[str, object]) -> ApplicationLeaseReceipt:
    fields = set(ApplicationLeaseReceipt.__dataclass_fields__) - {"sidecar"}
    if set(value) != fields | {"sidecar"} or not isinstance(value["sidecar"], dict):
        raise ValueError("lease receipt fields are not exact")
    sidecar_fields = set(SidecarObservation.__dataclass_fields__)
    sidecar = value.pop("sidecar")
    if set(sidecar) != sidecar_fields:
        raise ValueError("sidecar fields are not exact")
    return ApplicationLeaseReceipt(sidecar=SidecarObservation(**sidecar), **value)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("plan", "acquire", "mark-effect", "admit"), required=True)
    parser.add_argument("--state-dir", type=Path, default=Path("/var/lib/local-ai-lab/application-b60"))
    parser.add_argument("--prelease", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--effect", choices=("key", "ingress"))
    parser.add_argument("--effect-state", choices=("intent", "observed"))
    parser.add_argument("--lease-id")
    parser.add_argument("--generation", type=int)
    args = parser.parse_args(argv)
    if args.phase == "plan":
        print(json.dumps({"state": "plan-only", "commands": [
            "preflight", "acquire", "mark-effect key/ingress intent+observed",
            "start sidecar and observe", "admit", "run bounded A1 client", "recover"
        ]}, sort_keys=True, separators=(",", ":")))
        return 0
    if os.geteuid() != 0:
        raise SystemExit("application drill entrypoint requires root")
    controller = _controller(args.state_dir)
    if args.phase == "acquire":
        if args.prelease is None:
            raise SystemExit("--prelease is required")
        result = controller.acquire(_prelease(_owner_json(args.prelease)))
    elif args.phase == "mark-effect":
        if args.effect is None or args.effect_state is None or args.lease_id is None or args.generation is None:
            raise SystemExit("effect, effect state, lease ID and generation are required")
        result = controller.mark_effect(args.effect, args.effect_state,
                                        expected_lease_id=args.lease_id,
                                        expected_generation=args.generation) or {"state": "effect-marked"}
    else:
        if args.receipt is None or args.lease_id is None or args.generation is None:
            raise SystemExit("receipt, lease ID and generation are required")
        result = controller.admit_sidecar(_receipt(_owner_json(args.receipt)),
                                          expected_lease_id=args.lease_id,
                                          expected_generation=args.generation)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
