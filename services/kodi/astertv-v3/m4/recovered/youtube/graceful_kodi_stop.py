#!/usr/bin/env python3
"""Give Kodi's main loop time to quiesce before systemd's TERM fallback."""

import json
import socket
import subprocess
import time
from pathlib import Path


REPORT = Path("/run/astertv-kodi-stop.json")


def main_pid():
    result = subprocess.run(
        ["systemctl", "show", "kodi.service", "--property=MainPID", "--value"],
        check=False, capture_output=True, text=True, timeout=2,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method,
               "params": params or {}}
    with socket.create_connection(("127.0.0.1", 9090), timeout=2) as client:
        client.sendall((json.dumps(request) + "\r\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError("json-rpc-error")
    return reply.get("result")


def alive(pid):
    return pid > 1 and Path("/proc").joinpath(str(pid)).exists()


def quiesce_runtime():
    """Leave controller-owned pages before Kodi tears down Python/skin state."""
    try:
        rpc("Input.Home")
    except (OSError, ValueError, RuntimeError, socket.timeout):
        return False
    labels = [
        "Window(Home).Property(AsterMovie.Ready)",
        "Window(Home).Property(AsterSeries.Ready)",
        "Window(Home).Property(AsterDigest.Active)",
    ]
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        try:
            window = rpc("GUI.GetProperties", {"properties": ["currentwindow"]})
            state = rpc("XBMC.GetInfoLabels", {"labels": labels})
            home = window.get("currentwindow", {}).get("id") == 10000
            if home and not any(state.get(label) for label in labels):
                return True
        except (OSError, ValueError, RuntimeError, socket.timeout, AttributeError):
            return False
        time.sleep(0.1)
    return False


def report(outcome, elapsed):
    REPORT.write_text(json.dumps({"schema": 1, "outcome": outcome,
                                  "elapsed_ms": round(elapsed * 1000)}) + "\n")


def main():
    started = time.monotonic()
    pid = main_pid()
    if not alive(pid):
        report("already-stopped", time.monotonic() - started)
        return
    quiesced = quiesce_runtime()
    try:
        rpc("Application.Quit")
        outcome = "quiesced-application-quit" if quiesced else "application-quit"
    except (OSError, ValueError, RuntimeError, socket.timeout):
        # Returning lets systemd perform its normal post-ExecStop TERM.  Never
        # invent a second kill policy or extend shutdown without a bound.
        report("rpc-unavailable-term-fallback", time.monotonic() - started)
        return
    deadline = time.monotonic() + 25
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    report(outcome if not alive(pid) else "application-quit-timeout-term-fallback",
           time.monotonic() - started)


if __name__ == "__main__":
    main()
