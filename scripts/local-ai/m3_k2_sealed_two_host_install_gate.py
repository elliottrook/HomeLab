"""Content-free gate and plan for the K2 sealed two-host inactive install."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat


BOOKING_ID = "aster-stream-a-m3-k2-20261106-2000-r1"
WORKLOAD_ID = "m3-k2-shortlist-arbitration-development-v1"
BUNDLE_SHA256 = "3b7e7cf40b08808cb94721a5778a1474e35a4d8f8d30c7dac858a37dc6e6aed6"
INSTALLER_SHA256 = "245aa11d94653e87c1710a84addeca67f8f18d81ce30bd684e1d31d9bed89029"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class GateError(ValueError):
    pass


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise GateError("DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def decode(raw: bytes) -> object:
    if not raw or len(raw) > 32_768:
        raise GateError("RECONCILIATION_SIZE")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateError("RECONCILIATION_JSON") from exc


def prerequisite(value: object) -> str:
    keys = {"schema", "state", "booking_id", "requests", "retries",
            "errors", "production_restored", "development_gate_passed",
            "status", "result_sha256"}
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-m3-k2-development-reconciliation.v1"
            or value.get("state") != "complete"
            or value.get("booking_id") != BOOKING_ID
            or value.get("requests") != 192
            or value.get("retries") != 0
            or value.get("errors") != 0
            or value.get("production_restored") is not True
            or value.get("development_gate_passed") is not True
            or value.get("status") != "pass"
            or not isinstance(value.get("result_sha256"), str)
            or HEX64.fullmatch(value["result_sha256"]) is None):
        raise GateError("DEVELOPMENT_PREREQUISITE_NOT_PASS")
    return value["result_sha256"]


def _regular(path: Path, maximum: int) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_nlink != 1 or info.st_size < 1
            or info.st_size > maximum):
        raise GateError("SOURCE_CUSTODY:" + path.name)
    return path.read_bytes()


def plan(*, reconciliation_raw: bytes, bundle_raw: bytes,
         installer_raw: bytes) -> dict[str, object]:
    result_sha256 = prerequisite(decode(reconciliation_raw))
    if hashlib.sha256(bundle_raw).hexdigest() != BUNDLE_SHA256:
        raise GateError("BUNDLE_IDENTITY")
    if hashlib.sha256(installer_raw).hexdigest() != INSTALLER_SHA256:
        raise GateError("INSTALLER_IDENTITY")
    return {
        "schema": "aster-m3-k2-sealed-two-host-inactive-install-plan.v1",
        "state": "ready-for-separate-approval",
        "prerequisite": {
            "booking_id": BOOKING_ID,
            "workload_id": WORKLOAD_ID,
            "development_result_sha256": result_sha256,
            "development_gate_passed": True,
            "production_restored": True,
        },
        "bundle_sha256": BUNDLE_SHA256,
        "installer_sha256": INSTALLER_SHA256,
        "install_order": ["macbook", "mac_mini"],
        "rollback_order": ["mac_mini", "macbook"],
        "targets": {
            "macbook": {
                "transport": "existing-ssh-alias-macbook",
                "root": "/private/tmp/aster-k2-sealed-runtime-v1",
                "checkpoint":
                    "/private/tmp/aster-k2-sealed-runtime-v1.checkpoint",
            },
            "mac_mini": {
                "transport": "local",
                "root":
                    "/private/tmp/aster-k2-sealed-coordinator-runtime-v1",
                "checkpoint":
                    "/private/tmp/aster-k2-sealed-coordinator-runtime-v1.checkpoint",
            },
        },
        "files_per_target": 14,
        "service_restart": False,
        "workload_effect": "not-attempted",
        "new_access_grant": False,
        "effect_authorized": False,
        "authority": "not-granted",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reconciliation", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--installer", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        value = plan(
            reconciliation_raw=_regular(args.reconciliation, 32_768),
            bundle_raw=_regular(args.bundle, 1_048_576),
            installer_raw=_regular(args.installer, 1_048_576))
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except (GateError, OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "failure_code": str(exc),
                          "authority": "not-granted"},
                         sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
