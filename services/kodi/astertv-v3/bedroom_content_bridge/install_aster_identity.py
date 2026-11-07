#!/usr/bin/env python3
"""Install or roll back Aster's Bedroom content-only bridge identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


HOST = "hermesagent"
MODULE = Path("/opt/aster-agent/aster_remote.py")
ENVIRONMENT = Path("/etc/aster/aster.env")
KEY = Path("/etc/aster/remote-bedroom-equipment.key")
INPUT_KEY = Path("/run/asterremote-bedroom-equipment.key")
CHECKPOINTS = Path("/var/lib/aster/checkpoints")
PREDECESSOR_MODULE = "715b172a62e978ccaf79dfd3f9801da641cd067da72ad7187658efa9ccc0d73a"
SUCCESSOR_MODULE = "a804c06732b291275de830dcb0f8188ade5fc4fc3d0a557a86a742d1557cf1b3"
PREDECESSOR_ENVIRONMENT = "038c8a1042a10678f7f3f920529fee37c2c2bfe42f4ba61b77519fcffd5dc4fc"
FAMILY_ACTIONS = [
    "equipment.power_on", "equipment.power_off",
    "equipment.volume_up", "equipment.volume_down",
    "equipment.mute_on", "equipment.mute_off",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str, check: bool = True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def private_key() -> str:
    if not INPUT_KEY.is_file() or INPUT_KEY.stat().st_mode & 0o077:
        raise RuntimeError("private-bedroom-key-required")
    value = INPUT_KEY.read_text().strip()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError("invalid-bedroom-key")
    return value


def equipment_clients(data: bytes, allow_bedroom: bool = False) -> tuple[dict, int]:
    rows = data.decode().splitlines(keepends=True)
    matches = [index for index, row in enumerate(rows)
               if row.startswith("ASTER_REMOTE_EQUIPMENT_CLIENTS=")]
    if len(matches) != 1:
        raise RuntimeError("equipment-client-line-cardinality")
    index = matches[0]
    clients = json.loads(rows[index].split("=", 1)[1])
    expected_family = {
        "room_id": "family",
        "label": "Family equipment",
        "key_file": "/etc/aster/remote-family-equipment.key",
        "actions": FAMILY_ACTIONS,
    }
    expected = {"HA-Family": expected_family}
    if allow_bedroom:
        expected["HA-Bedroom"] = {
            "room_id": "bedroom",
            "label": "Bedroom content observer",
            "key_file": str(KEY),
            "actions": [],
        }
    if clients != expected:
        raise RuntimeError("family-equipment-identity-drift")
    return clients, index


def render_environment(data: bytes) -> bytes:
    clients, index = equipment_clients(data)
    clients["HA-Bedroom"] = {
        "room_id": "bedroom",
        "label": "Bedroom content observer",
        "key_file": str(KEY),
        "actions": [],
    }
    rows = data.decode().splitlines(keepends=True)
    rows[index] = "ASTER_REMOTE_EQUIPMENT_CLIENTS=" + json.dumps(
        clients, separators=(",", ":"), sort_keys=True
    ) + "\n"
    return "".join(rows).encode()


def atomic(data: bytes, destination: Path, mode: int, uid: int, gid: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}-", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, uid, gid)
        os.chmod(temporary, mode)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def wait_ready() -> None:
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/health", timeout=2) as reply:
                if reply.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.25)
    raise RuntimeError("aster-agent-not-ready")


def content_probe(key: str) -> int:
    payload = json.dumps({
        "client_id": "HA-Bedroom", "room_id": "bedroom",
    }).encode()
    request = urllib.request.Request(
        "http://192.168.70.10:9120/v1/remote/equipment/content", payload,
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "X-AsterTV-Client": "HA-Bedroom",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as reply:
            return reply.status
    except urllib.error.HTTPError as error:
        return error.code


def checkpoint(identifier: str) -> Path:
    target = CHECKPOINTS / identifier
    if target.exists():
        raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    shutil.copy2(MODULE, target / "aster_remote.py")
    shutil.copy2(ENVIRONMENT, target / "aster.env")
    receipt = {
        "schema": 1,
        "kind": "astertv-bedroom-content-identity-checkpoint",
        "host": HOST,
        "module_sha256": PREDECESSOR_MODULE,
        "environment_sha256": PREDECESSOR_ENVIRONMENT,
        "bedroom_key_previously_present": False,
    }
    (target / "checkpoint.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    os.chmod(target / "checkpoint.json", 0o600)
    return target


def restore(target: Path) -> None:
    receipt = json.loads((target / "checkpoint.json").read_text())
    if receipt.get("host") != HOST or receipt.get("bedroom_key_previously_present") is not False:
        raise RuntimeError("checkpoint-identity")
    if sha(target / "aster_remote.py") != PREDECESSOR_MODULE:
        raise RuntimeError("checkpoint-module-drift")
    if sha(target / "aster.env") != PREDECESSOR_ENVIRONMENT:
        raise RuntimeError("checkpoint-environment-drift")
    shutil.copy2(target / "aster_remote.py", MODULE)
    shutil.copy2(target / "aster.env", ENVIRONMENT)
    KEY.unlink(missing_ok=True)


def install(source: Path, identifier: str) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("aster-root-only")
    if sha(MODULE) != PREDECESSOR_MODULE or sha(ENVIRONMENT) != PREDECESSOR_ENVIRONMENT:
        raise RuntimeError("aster-predecessor-drift")
    if sha(source) != SUCCESSOR_MODULE:
        raise RuntimeError("aster-candidate-drift")
    if KEY.exists():
        raise RuntimeError("bedroom-key-already-present")
    key = private_key()
    environment = render_environment(ENVIRONMENT.read_bytes())
    account = pwd.getpwnam("aster")
    saved = checkpoint(identifier)
    run("systemctl", "stop", "aster-agent")
    try:
        atomic(source.read_bytes(), MODULE, 0o644, 0, 0)
        atomic(environment, ENVIRONMENT, 0o640, 0, account.pw_gid)
        atomic((key + "\n").encode(), KEY, 0o600, account.pw_uid, account.pw_gid)
        run("systemctl", "start", "aster-agent")
        wait_ready()
        if sha(MODULE) != SUCCESSOR_MODULE or content_probe(key) != 204:
            raise RuntimeError("bedroom-identity-validation")
    except Exception:
        run("systemctl", "stop", "aster-agent", check=False)
        restore(saved)
        run("systemctl", "start", "aster-agent")
        wait_ready()
        raise
    finally:
        INPUT_KEY.unlink(missing_ok=True)
    print(json.dumps({
        "outcome": "installed", "checkpoint": str(saved),
        "credential_output": False, "equipment_actions": [],
    }, sort_keys=True))


def rollback(identifier: str) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("aster-root-only")
    target = CHECKPOINTS / identifier
    if sha(MODULE) != SUCCESSOR_MODULE:
        raise RuntimeError("aster-successor-drift")
    equipment_clients(ENVIRONMENT.read_bytes(), allow_bedroom=True)
    run("systemctl", "stop", "aster-agent")
    restore(target)
    run("systemctl", "start", "aster-agent")
    wait_ready()
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(target)}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--source", type=Path)
    actions.add_argument("--rollback", action="store_true")
    parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    if args.rollback:
        rollback(args.checkpoint_id)
    else:
        install(args.source, args.checkpoint_id)


if __name__ == "__main__":
    main()
