"""Atomic HP-only Media hero installation and exact rollback."""

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


STAGE_NAME = "aster-media-hero3"
STAGING = Path("/storage/.aster-staging")
CHECKPOINTS = Path("/storage/.aster-checkpoints")
RECOVERY = Path("/storage/.aster-recovery-required")
CANDIDATE_MANIFEST = "28655c667c5b7d5c55e14b3ace32bcae1c791fa3d43d5a742e39537d5cf4588f"
EXPECTED_TARGETS = {
    "plugin/default.py": "/storage/.kodi/addons/plugin.video.asterhome/default.py",
    "plugin/library.py": "/storage/.kodi/addons/plugin.video.asterhome/library.py",
    "skin/1080i/Home.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Home.xml",
    "skin/1080i/Includes.xml": "/storage/.kodi/addons/skin.asterhome/1080i/Includes.xml",
}


def require(value, code):
    if not value:
        raise RuntimeError(code)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-media-hero-",
                                              dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def active_players():
    request = {"jsonrpc": "2.0", "id": 1,
               "method": "Player.GetActivePlayers"}
    try:
        with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
            client.sendall((json.dumps(request) + "\n").encode())
            raw = client.recv(4096)
        result = json.loads(raw.decode()).get("result")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("kodi-idle-check-unavailable") from error
    require(result == [], "active-playback")


def load_stage(stage):
    require(digest(stage / "manifest.json") == CANDIDATE_MANIFEST,
            "candidate-manifest")
    manifest = json.loads((stage / "manifest.json").read_text())
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-media-recommendation-hero"
            and manifest.get("stage") == STAGE_NAME
            and len(manifest.get("files", [])) == len(EXPECTED_TARGETS),
            "candidate-schema")
    rows = {row.get("path"): row for row in manifest["files"]
            if isinstance(row, dict)}
    require(set(rows) == set(EXPECTED_TARGETS), "candidate-members")
    for name, target in EXPECTED_TARGETS.items():
        row = rows[name]
        require(row.get("target") == target
                and isinstance(row.get("previous_sha256"), str)
                and len(row["previous_sha256"]) == 64
                and digest(stage / name) == row.get("sha256"),
                "candidate-member")
        if name.endswith(".py"):
            ast.parse((stage / name).read_bytes())
        else:
            ET.fromstring((stage / name).read_bytes())
    return rows


def install():
    require(os.uname().nodename == "AsterTV" and not RECOVERY.exists(),
            "hp-recovery-boundary")
    stage = STAGING / STAGE_NAME
    checkpoint = CHECKPOINTS / STAGE_NAME
    require(not checkpoint.exists(), "checkpoint-exists")
    rows = load_stage(stage)
    active_players()
    for name, row in rows.items():
        require(digest(row["target"]) == row["previous_sha256"],
                "predecessor-drift")
    checkpoint.mkdir(mode=0o700)
    shutil.copytree(stage, checkpoint / "isolated-restore")
    for name, row in rows.items():
        atomic(checkpoint / "before" / name, Path(row["target"]).read_bytes())
    atomic(checkpoint / "state.json", b'{"state":"prepared"}\n')
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for name, row in rows.items():
            require(digest(row["target"]) == row["previous_sha256"],
                    "stop-time-predecessor-drift")
            atomic(row["target"], (stage / name).read_bytes())
        for row in rows.values():
            require(digest(row["target"]) == row["sha256"],
                    "installed-member")
        atomic(checkpoint / "state.json", b'{"state":"installed"}\n')
    except Exception:
        for name, row in rows.items():
            current = digest(row["target"])
            require(current in (row["sha256"], row["previous_sha256"]),
                    "rollback-drift")
            atomic(row["target"], (checkpoint / "before" / name).read_bytes())
        atomic(checkpoint / "state.json", b'{"state":"rolled-back"}\n')
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "files_verified": len(rows),
                      "manifest_sha256": CANDIDATE_MANIFEST,
                      "checkpoint": str(checkpoint)}))


def rollback():
    require(os.uname().nodename == "AsterTV" and not RECOVERY.exists(),
            "hp-recovery-boundary")
    stage = STAGING / STAGE_NAME
    checkpoint = CHECKPOINTS / STAGE_NAME
    rows = load_stage(stage)
    require(json.loads((checkpoint / "state.json").read_text()).get("state")
            == "installed", "checkpoint-state")
    active_players()
    for row in rows.values():
        require(digest(row["target"]) == row["sha256"], "installed-drift")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for name, row in rows.items():
            atomic(row["target"], (checkpoint / "before" / name).read_bytes())
            require(digest(row["target"]) == row["previous_sha256"],
                    "restore-member")
        atomic(checkpoint / "state.json", b'{"state":"rolled-back"}\n')
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"rolled_back": True, "files_verified": len(rows)}))


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("install", "rollback"),
            "one-mode-required")
    install() if sys.argv[1] == "install" else rollback()
