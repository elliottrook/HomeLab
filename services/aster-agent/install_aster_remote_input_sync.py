#!/usr/bin/env python3
"""Checkpoint and install Remote editable voice/search and Kodi input sync."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request


HOST = "hermesagent"
ROOT = Path(__file__).resolve().parent
AGENT = Path("/opt/aster-agent")
TARGETS = {
    "module": AGENT / "aster_remote.py",
    "index.html": AGENT / "static/remote/index.html",
    "app.js": AGENT / "static/remote/app.js",
    "sw.js": AGENT / "static/remote/sw.js",
}
OLD = {
    "module": "02722c5039ae4a87eeff612c60c4ccc5431d033115d3ac40a0583f6631629809",
    "index.html": "6a261b921fbd8749b17751f5e3588fd1813c00d476e9aadd235c9ab8efd563ad",
    "app.js": "003e51fe2a4f02ccd0bb930cc72966e4dac1d131c806d512f453f653baca3d33",
    "sw.js": "0ca9eb192d0c000baffb12889c655d3c795bcce38efeaf168eabd580c730c6ed",
}
CHECKPOINTS = Path("/var/lib/aster/checkpoints")


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wait_ready():
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/health", timeout=2) as reply:
                if reply.status == 200: return
        except OSError: pass
        time.sleep(0.25)
    raise RuntimeError("agent-not-ready")


def status(path):
    try:
        with urllib.request.urlopen("http://192.168.70.10:9120" + path, timeout=3) as reply:
            return reply.status
    except urllib.error.HTTPError as error: return error.code


def install(identifier):
    if socket.gethostname() != HOST or os.getuid() != 0: raise RuntimeError("wrong-target")
    if {name: sha(path) for name, path in TARGETS.items()} != OLD:
        raise RuntimeError("remote-input-predecessor-drift")
    source = {"module": ROOT / "aster_remote.py",
              "index.html": ROOT / "static/remote/index.html",
              "app.js": ROOT / "static/remote/app.js",
              "sw.js": ROOT / "static/remote/sw.js"}
    target = CHECKPOINTS / identifier
    if target.exists(): raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    for name, path in TARGETS.items(): shutil.copy2(path, target / name)
    run("systemctl", "stop", "aster-agent")
    try:
        for name, path in TARGETS.items():
            temporary = path.with_suffix(path.suffix + ".installing")
            shutil.copy2(source[name], temporary); os.replace(temporary, path)
        run("systemctl", "start", "aster-agent"); wait_ready()
        if status("/remote/") != 200 or status("/v1/remote/session") != 401:
            raise RuntimeError("remote-input-validation")
    except Exception:
        run("systemctl", "stop", "aster-agent", check=False)
        for name, path in TARGETS.items(): shutil.copy2(target / name, path)
        run("systemctl", "start", "aster-agent"); raise
    print(json.dumps({"outcome": "installed", "checkpoint": str(target),
                      "credential_output": False}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--checkpoint-id", required=True)
    install(parser.parse_args().checkpoint_id)


if __name__ == "__main__": main()
