#!/usr/bin/env python3
"""Collect a sanitized, fail-closed AsterTV composition observation."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(contract: dict, hostname: str, root: Path = Path("/"),
            dependencies: dict | None = None,
            assertions: dict | None = None, observed_at: str | None = None) -> dict:
    if contract.get("kind") != "composition-guard-contract" or contract.get("schema_version") != 1:
        raise ValueError("guard-contract-schema")
    if hostname != contract.get("hostname"):
        raise ValueError("device-hostname-mismatch")
    payloads = []
    for expected in contract.get("expected_payloads", []):
        path = Path(expected["path"])
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("unsafe-expected-payload")
        observed_path = root / path.as_posix().lstrip("/")
        if observed_path.is_symlink():
            raise ValueError("observed-payload-symlink")
        if not observed_path.is_file():
            continue
        payloads.append({
            "overlay": expected["overlay"], "path": expected["path"],
            "sha256": sha(observed_path), "bytes": observed_path.stat().st_size,
            "mode": format(observed_path.stat().st_mode & 0o777, "04o"),
        })
    dependency_states = {name: "unavailable" for name in contract.get("required_dependencies", [])}
    dependency_states.update(dependencies or {})
    return {
        "schema_version": 1,
        "kind": "composition-observation",
        "device_id": contract["device_id"],
        "composition_sha256": contract["composition_sha256"],
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "resources": list(contract.get("expected_resources", [])),
        "payloads": payloads,
        "dependencies": dependency_states,
        "assertions": assertions or {},
    }


def key_values(values: list[str]) -> dict:
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError("key-value-required")
        key, raw = value.split("=", 1)
        result[key] = json.loads(raw)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--hostname", default=socket.gethostname())
    parser.add_argument("--dependency", action="append", default=[])
    parser.add_argument("--assertion", action="append", default=[])
    parser.add_argument("--observed-at")
    args = parser.parse_args(argv)
    contract = json.loads(args.contract.read_text())
    result = collect(contract, args.hostname, args.root,
                     key_values(args.dependency), key_values(args.assertion), args.observed_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
