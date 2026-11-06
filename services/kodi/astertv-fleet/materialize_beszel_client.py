#!/usr/bin/env python3
"""Materialize host-bound LibreELEC Beszel service units without agent tokens."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = {
    "astertv-family": "AsterTV-Family",
    "astertv-bedroom": "AsterTV-Bedroom",
    "astertv-jen": "AsterTV-Jen",
}
AGENT_SHA256 = "99e7f48df6bde635285f1bb28f93b4280d62289b4b94850a54afdcbf110f3158"
HUB = "http://192.168.20.20:8090"
PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK88pFyD1rFx1E7p5HnymBqvj6VV/90id8QejpCbwL94"
DESTINATION = "storage/.config/system.d/beszel-agent.service"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render_unit(hostname: str) -> bytes:
    return f"""[Unit]
Description=AsterTV Beszel Agent
Wants=network-online.target
After=network-online.target
ConditionHost={hostname}
ConditionPathExists=/storage/.aster-monitoring/beszel-agent
ConditionPathExists=/storage/.aster-private/beszel-agent.env

[Service]
Type=simple
Environment=HOME=/storage/.aster-monitoring
Environment=PORT=45876
Environment=HUB_URL={HUB}
Environment="KEY={PUBLIC_KEY}"
EnvironmentFile=/storage/.aster-private/beszel-agent.env
ExecStart=/storage/.aster-monitoring/beszel-agent
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
""".encode()


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def materialize(output: Path) -> dict:
    files = []
    for device, hostname in sorted(TARGETS.items()):
        data = render_unit(hostname)
        target = output / "targets" / device / DESTINATION
        atomic_write(target, data, 0o644)
        files.append({
            "target": device,
            "scope": device,
            "destination": "/" + DESTINATION,
            "bytes": len(data),
            "sha256": sha(data),
            "mode": "0644",
        })
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "beszel-client-v1",
        "targets": sorted(TARGETS),
        "files": files,
        "external_binary": {
            "version": "0.18.7",
            "platform": "linux-amd64-glibc",
            "destination": "/storage/.aster-monitoring/beszel-agent",
            "sha256": AGENT_SHA256,
            "mode": "0755",
        },
        "secret_custody": {
            "path": "/storage/.aster-private/beszel-agent.env",
            "mode": "0600",
            "tracked": False,
        },
        "rollback": "disable unit; restore device checkpoint; remove only its hub system and fingerprint",
    }
    atomic_write(output / "materialization-manifest.json", canonical(manifest), 0o644)
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=HERE / "materialized/beszel-client-v1")
    args = parser.parse_args(argv)
    manifest = materialize(args.output)
    print(json.dumps({"files": len(manifest["files"]),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
