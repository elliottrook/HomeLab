"""HP-only saved-result UI activation with an idle check and Kodi reload."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from acquisition_saved_install import run


def stopped():
    return subprocess.run(['systemctl', 'is-active', '--quiet', 'kodi']).returncode != 0


if __name__ == '__main__':
    if os.uname().nodename != 'AsterTV' or len(sys.argv) != 3:
        raise RuntimeError('saved-status-hp-arguments')
    mode, pin = sys.argv[1:]
    restart = mode in ('install', 'rollback')
    if restart:
        with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
            client.sendall(b'{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}\n')
            if json.loads(client.recv(4096)).get('result') != []:
                raise RuntimeError('saved-status-active-playback')
        subprocess.run(['systemctl', 'stop', 'kodi'], check=True, timeout=30)
    try:
        result = run(mode, ROOT, Path('/storage'), pin, stopped=stopped)
        print(json.dumps(result, sort_keys=True))
    finally:
        if restart:
            subprocess.run(['systemctl', 'start', 'kodi'], check=True, timeout=30)
