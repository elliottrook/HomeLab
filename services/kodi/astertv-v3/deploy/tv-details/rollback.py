#!/usr/bin/env python3
"""Restore one AsterTV v3 TV-details deployment from its checkpoint."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess

ROOT = Path("/storage/.kodi/addons")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(__import__("sys").argv) != 2:
        raise SystemExit("usage: rollback.py CHECKPOINT")
    checkpoint = Path(__import__("sys").argv[1]).resolve()
    data = json.loads((checkpoint / "manifest.json").read_text())
    if data.get("kind") != "astertv-v3-tv-details" or data.get("host") != socket.gethostname():
        raise RuntimeError("checkpoint identity mismatch")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for relative, record in data["files"].items():
            target = ROOT / relative
            before = record.get("before")
            saved = checkpoint / relative.replace("/", "__")
            if before:
                if not saved.is_file() or sha(saved) != before:
                    raise RuntimeError("checkpoint file mismatch: " + relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved, target)
            elif target.exists():
                target.unlink()
        plugin = ROOT / "plugin.video.astersearch"
        if plugin.exists():
            shutil.rmtree(plugin)
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"rolled_back": True, "checkpoint": str(checkpoint)}, sort_keys=True))


if __name__ == "__main__":
    main()
