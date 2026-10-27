"""Install, verify or roll back the HP Media top-rail correction."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from media_top_rail_install import run


def idle():
    request = {"jsonrpc": "2.0", "id": 1,
               "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(4096).decode())
    return reply.get("result") == []


def stopped():
    return subprocess.run(["systemctl", "is-active", "--quiet", "kodi"],
                          check=False).returncode != 0


def main(mode, pin):
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("media-top-rail-hp-only")
    if mode == "verify":
        return run(mode, ROOT, Path("/storage"), pin, stopped=stopped)
    if not idle():
        raise RuntimeError("media-top-rail-active-playback")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        return run(mode, ROOT, Path("/storage"), pin, stopped=stopped)
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)


if __name__ == "__main__":
    try:
        result = main(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        result = {"passed": False, "code": str(error)}
    else:
        result = dict(result, passed=True)
    print(json.dumps(result, sort_keys=True))
