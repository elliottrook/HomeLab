#!/usr/bin/env python3
"""Measure content-free Aster page activation and data-ready latency on Jen."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time


HOST = "AsterTV-Jen"
RPC = ("127.0.0.1", 9090)
KODI_SEND = "/usr/bin/kodi-send"
INTERFACE = "eth0"
TIMEOUT_SECONDS = 12.0
ACTIVATION_BUDGET_MS = 250.0
DATA_READY_BUDGET_MS = 2000.0
NETWORK_RX_BUDGET_BYTES = 262144
NETWORK_TX_BUDGET_BYTES = 65536
ROUTES = (
    ("books", 11110, "Window(11110).Property(AsterBooks.Status)",
     "ClearProperty(AsterBooks.Status,11110)"),
    ("news", 11111, "Window(11111).Property(AsterHub.Ready)", None),
    ("home", 11112, None, None),
    ("music", 11113, "Window(11113).Property(AsterMusic.LoadReady)", None),
    ("cameras", 11134, None, None),
)


def _rpc_once(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method,
               "params": params or {}}
    with socket.create_connection(RPC, timeout=2) as client:
        client.settimeout(4)
        client.sendall((json.dumps(request) + "\r\n").encode())
        buffer = ""
        deadline = time.monotonic() + 4
        decoder = json.JSONDecoder()
        while time.monotonic() < deadline:
            buffer += client.recv(65536).decode()
            while buffer.lstrip():
                buffer = buffer.lstrip()
                try:
                    reply, end = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                buffer = buffer[end:]
                if reply.get("id") == 1:
                    if reply.get("error") or "result" not in reply:
                        raise RuntimeError("page-kodi-rpc")
                    return reply["result"]
    raise RuntimeError("page-kodi-rpc")


def rpc(method: str, params: dict | None = None):
    for attempt in range(3):
        try:
            return _rpc_once(method, params)
        except (OSError, UnicodeError, json.JSONDecodeError,
                RuntimeError, socket.timeout):
            if attempt == 2:
                break
            time.sleep(0.1)
    raise RuntimeError("page-kodi-rpc")


def action(value: str) -> None:
    result = subprocess.run(
        [KODI_SEND, "--action=" + value], check=False, capture_output=True,
        text=True, timeout=3,
    )
    if result.returncode:
        raise RuntimeError("page-kodi-action")


def active_players() -> list:
    result = rpc("Player.GetActivePlayers")
    if not isinstance(result, list):
        raise RuntimeError("page-player-format")
    return result


def window_id() -> int:
    result = rpc("GUI.GetProperties", {"properties": ["currentwindow"]})
    try:
        return int(result["currentwindow"]["id"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("page-window-format") from None


def info_value(label: str) -> str:
    result = rpc("XBMC.GetInfoLabels", {"labels": [label]})
    value = result.get(label, "") if isinstance(result, dict) else ""
    return value if isinstance(value, str) else ""


def counter(name: str) -> int:
    path = Path("/sys/class/net") / INTERFACE / "statistics" / name
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        raise RuntimeError("page-network-counter") from None


def wait_until(check, deadline: float) -> float:
    while time.monotonic() < deadline:
        if check():
            return time.monotonic()
        time.sleep(0.05)
    raise RuntimeError("page-ready-timeout")


def restore_home() -> int:
    for _ in range(3):
        action("ActivateWindow(Home)")
        try:
            wait_until(lambda: window_id() == 10000,
                       time.monotonic() + 1.5)
            # Give any page worker that was already finishing a chance to
            # reveal a late activation before accepting the restored state.
            time.sleep(0.25)
            if window_id() == 10000:
                return 10000
        except RuntimeError as error:
            if str(error) != "page-ready-timeout":
                raise
    raise RuntimeError("page-home-restore")


def measure_route(name: str, target: int, ready_label: str | None,
                  clear_action: str | None) -> dict:
    if active_players():
        raise RuntimeError("page-player-busy")
    if clear_action:
        action(clear_action)
    rx_before, tx_before = counter("rx_bytes"), counter("tx_bytes")
    started = time.monotonic()
    action(f"ActivateWindow({target})")
    try:
        activated = wait_until(lambda: window_id() == target,
                               started + TIMEOUT_SECONDS)
    except RuntimeError as error:
        if str(error) == "page-ready-timeout":
            raise RuntimeError("page-activation-timeout:" + name) from None
        raise
    ready = activated
    if ready_label:
        try:
            ready = wait_until(lambda: bool(info_value(ready_label)) and
                               info_value(ready_label) != "false",
                               started + TIMEOUT_SECONDS)
        except RuntimeError as error:
            if str(error) == "page-ready-timeout":
                raise RuntimeError("page-data-timeout:" + name) from None
            raise
    if active_players():
        raise RuntimeError("page-player-started")
    row = {
        "page": name,
        "window_id": target,
        "activation_ms": round((activated - started) * 1000, 1),
        "data_ready_ms": None if ready_label is None else
            round((ready - started) * 1000, 1),
        "network_rx_bytes": counter("rx_bytes") - rx_before,
        "network_tx_bytes": counter("tx_bytes") - tx_before,
    }
    row["within_budget"] = (
        row["activation_ms"] <= ACTIVATION_BUDGET_MS and
        (row["data_ready_ms"] is None or
         row["data_ready_ms"] <= DATA_READY_BUDGET_MS) and
        row["network_rx_bytes"] <= NETWORK_RX_BUDGET_BYTES and
        row["network_tx_bytes"] <= NETWORK_TX_BUDGET_BYTES
    )
    return row


def run(passes: int) -> dict:
    if os.uname().nodename != HOST:
        raise RuntimeError("page-target")
    if active_players():
        raise RuntimeError("page-player-busy")
    restore_home()
    results = []
    try:
        for pass_number in range(1, passes + 1):
            for route in ROUTES:
                row = measure_route(*route)
                row["pass"] = pass_number
                results.append(row)
    finally:
        restored = restore_home()
    if active_players():
        raise RuntimeError("page-player-started")
    return {"schema_version": 1, "kind": "astertv-page-latency",
            "host": HOST, "passes": passes, "results": results,
            "active_players": 0, "restored_window_id": restored,
            "budgets": {"activation_ms": ACTIVATION_BUDGET_MS,
                        "data_ready_ms": DATA_READY_BUDGET_MS,
                        "network_rx_bytes": NETWORK_RX_BUDGET_BYTES,
                        "network_tx_bytes": NETWORK_TX_BUDGET_BYTES},
            "outcome": "pass" if all(row["within_budget"]
                                      for row in results) else "fail"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--passes", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.passes <= 3:
        raise RuntimeError("page-passes")
    print(json.dumps(run(args.passes), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
