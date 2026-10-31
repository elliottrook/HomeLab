#!/usr/bin/env python3
"""Install the restricted HA display-feed receiver on AsterTVProd."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import stat
import sys
import tempfile


PAYLOAD = Path("/storage/.aster-staging/aster-home-prod-r24")
ROOT = Path("/storage/.aster-home-delivery")
STAGE = Path("/storage/.aster-staging/aster-home-status1")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-home-delivery-prod1")
STATUS = Path("/storage/.aster-checkpoints/aster-home-status1")
KEYS = Path("/storage/.ssh/authorized_keys")
FEED = Path("/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home-dashboard.json")
EXPECTED_KEYS = "d16e2b44d45f5de91242826d71a9ea7b77bdfe4495032e66cbf59593f8453e63"
EXPECTED_FEED = "fae4773f12115a751a4905a6ec1915ee1234fc15a623af0b06d5e22abccbbcd3"
MANIFEST = "4d125fe1ca9ad5d1fba34116a817766823dc98b4db97579a61a2016ce6a85be1"
PAYLOAD_HASHES = {
    "manifest.json": MANIFEST,
    "home_status_model.py": "9b7122fc9271485b51ad16d0ccab042947926bbf9ffa20b9c1f184c6c0042c62",
    "receive.py": "db7b9fd5466eb6c5ffd9304adda3b52d93bc45d02f2e4ca6b94c46d2d0d6e374",
    "default.py": "f11679b52393253eb7727e40e3f346a458c62f51a44f9e5111251f9011df8f6e",
    "custom_1112_home.xml": "42d9b7987eda3e5c7203b9fee6c2c9c4aae9ee59105fd44db129642e2ecb4000",
}


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-home-r24-", dir=path.parent)
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


def rpc(method: str):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    require("error" not in reply, "kodi-rpc")
    return reply.get("result")


def restricted_key(public: str) -> bytes:
    fields = public.split()
    require(len(fields) == 2 and fields[0] == "ssh-ed25519", "receiver-key-format")
    require(re.fullmatch("[A-Za-z0-9+/=]{68}", fields[1]) is not None, "receiver-key-format")
    decoded = base64.b64decode(fields[1], validate=True)
    require(len(decoded) == 51 and decoded[:19] == b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20",
            "receiver-key-type")
    return ("restrict,from=\"192.168.20.11\",command=\"/usr/bin/python3 "
            "/storage/.aster-home-delivery/receive.py\" " + public
            + " aster-home-feed-prod-v1\n").encode()


def main() -> None:
    require(os.uname().nodename == "AsterTVProd", "production-host-only")
    players_before = rpc("Player.GetActivePlayers")
    require(isinstance(players_before, list), "kodi-rpc")
    require(not Path("/storage/.aster-recovery-required").exists(), "recovery-guard")
    require(not ROOT.exists() and not STAGE.exists() and not CHECKPOINT.exists() and not STATUS.exists(),
            "receiver-already-present")
    require(sha(KEYS) == EXPECTED_KEYS and sha(FEED) == EXPECTED_FEED, "receiver-predecessor-drift")
    for name, expected in PAYLOAD_HASHES.items():
        require(sha(PAYLOAD / name) == expected, "receiver-payload-drift")
    manifest = json.loads((PAYLOAD / "manifest.json").read_text())
    require(manifest.get("kind") == "home-status-1" and manifest.get("files") == {
        "custom_1112_home.xml": PAYLOAD_HASHES["custom_1112_home.xml"],
        "default.py": PAYLOAD_HASHES["default.py"],
        "home_status_model.py": PAYLOAD_HASHES["home_status_model.py"],
    }, "receiver-manifest")
    public = (PAYLOAD / "id_ed25519.pub").read_text().strip()
    line = restricted_key(public)
    current_keys = KEYS.read_bytes()
    require(current_keys.endswith(b"\n") and b"aster-home-feed-prod-v1" not in current_keys,
            "receiver-key-predecessor")

    spec = importlib.util.spec_from_file_location("aster_home_prod_model", PAYLOAD / "home_status_model.py")
    model = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = model
    spec.loader.exec_module(model)
    require(model.view(FEED.read_bytes()).state in ("fresh", "stale"), "receiver-feed-invalid")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    atomic(CHECKPOINT / "authorized_keys.before", current_keys)
    atomic(CHECKPOINT / "home-dashboard.before.json", FEED.read_bytes())
    atomic(CHECKPOINT / "restricted-key.line", line)
    atomic(CHECKPOINT / "manifest.json", (PAYLOAD / "manifest.json").read_bytes())
    ROOT.mkdir(mode=0o700)
    STAGE.mkdir(mode=0o700)
    STATUS.mkdir(mode=0o700)
    try:
        for name in ("receive.py", "home_status_model.py"):
            atomic(ROOT / name, (PAYLOAD / name).read_bytes())
        for name in ("manifest.json", "default.py", "custom_1112_home.xml", "home_status_model.py"):
            atomic(STAGE / name, (PAYLOAD / name).read_bytes())
        atomic(STAGE / "deploy.lock", b"")
        atomic(STATUS / "publication.json", (json.dumps({
            "feed_sha256": EXPECTED_FEED,
            "manifest_sha256": MANIFEST,
        }, sort_keys=True, separators=(",", ":")) + "\n").encode())
        atomic(KEYS, current_keys + line)
        require(sha(ROOT / "receive.py") == PAYLOAD_HASHES["receive.py"], "receiver-install-drift")
        require(sha(ROOT / "home_status_model.py") == PAYLOAD_HASHES["home_status_model.py"],
                "receiver-install-drift")
        require(KEYS.read_bytes() == current_keys + line, "receiver-key-install-drift")
        require(stat.S_IMODE(KEYS.stat().st_mode) == 0o600, "receiver-key-mode")
    except Exception:
        if KEYS.exists() and KEYS.read_bytes() == current_keys + line:
            atomic(KEYS, current_keys)
        Path("/storage/.aster-recovery-required").write_text("r24 Home receiver rollback required\n")
        raise
    print(json.dumps({
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "source": "192.168.20.11",
        "destination": "192.168.1.157",
        "forced_command": True,
        "owner_keys_preserved": KEYS.read_bytes().startswith(current_keys),
        "active_players_unchanged": rpc("Player.GetActivePlayers") == players_before,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
