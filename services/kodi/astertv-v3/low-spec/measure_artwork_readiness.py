#!/usr/bin/env python3
"""Measure content-free artwork-binding readiness on AsterTV-Jen."""

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
READINESS_BUDGET_MS = 6000.0
NETWORK_RX_BUDGET_BYTES = 2097152
NETWORK_TX_BUDGET_BYTES = 262144
ROUTES = (
    ("media", "ActivateWindow(Home)", 10000, 1, (
        "!String.IsEmpty(Container(101).ListItem.Art(thumb))",
        "!String.IsEmpty(Container(100).ListItem.Art(thumb))",
        "!String.IsEmpty(Container(110).ListItem.Art(thumb))",
    )),
    ("books", "ActivateWindow(11110)", 11110, 3, (
        "!String.IsEmpty(Window(11110).Property(AsterBooks.HeroArtwork))",
        "!String.IsEmpty(Container(502).ListItem.Art(thumb))",
        "!String.IsEmpty(Container(503).ListItem.Art(thumb))",
    )),
    ("news", "ActivateWindow(11111)", 11111, 1, (
        "!String.IsEmpty(Window(11111).Property(AsterHub.ActiveImage))",
    )),
    ("music", "ActivateWindow(11113)", 11113, 2, (
        "String.IsEqual(Container(500).ListItem.Property(AsterMusic.HasArt),true)",
        "!String.IsEmpty(Container(500).ListItem.Art(thumb))",
    )),
    ("youtube", "ActivateWindow(Videos,plugin://plugin.video.youtube/special/recommendations,return)",
     10025, 2, (
        "!String.IsEmpty(Container(50).ListItem.Art(thumb))",
        "!String.IsEmpty(Container(50).ListItem.Icon)",
    )),
)


def _rpc_once(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method,
               "params": params or {}}
    with socket.create_connection(RPC, timeout=2) as client:
        client.settimeout(4)
        client.sendall((json.dumps(request) + "\r\n").encode())
        decoder, buffer = json.JSONDecoder(), ""
        deadline = time.monotonic() + 4
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
                        raise RuntimeError("art-kodi-rpc")
                    return reply["result"]
    raise RuntimeError("art-kodi-rpc")


def rpc(method: str, params: dict | None = None):
    for attempt in range(3):
        try:
            return _rpc_once(method, params)
        except (OSError, UnicodeError, json.JSONDecodeError,
                RuntimeError, socket.timeout):
            if attempt == 2:
                break
            time.sleep(0.1)
    raise RuntimeError("art-kodi-rpc")


def action(value: str) -> None:
    result = subprocess.run([KODI_SEND, "--action=" + value], check=False,
                            capture_output=True, text=True, timeout=3)
    if result.returncode:
        raise RuntimeError("art-kodi-action")


def active_players() -> list:
    result = rpc("Player.GetActivePlayers")
    if not isinstance(result, list):
        raise RuntimeError("art-player-format")
    return result


def window_id() -> int:
    value = rpc("GUI.GetProperties", {"properties": ["currentwindow"]})
    try:
        return int(value["currentwindow"]["id"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("art-window-format") from None


def booleans(expressions: tuple[str, ...]) -> int:
    result = rpc("XBMC.GetInfoBooleans", {"booleans": list(expressions)})
    if not isinstance(result, dict) or set(result) != set(expressions):
        raise RuntimeError("art-boolean-format")
    return sum(value is True for value in result.values())


def counter(name: str) -> int:
    try:
        return int((Path("/sys/class/net") / INTERFACE / "statistics" /
                    name).read_text().strip())
    except (OSError, ValueError):
        raise RuntimeError("art-network-counter") from None


def wait(check, timeout: float, code: str) -> float:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return time.monotonic()
        time.sleep(0.05)
    raise RuntimeError(code)


def wait_art(expressions: tuple[str, ...], minimum: int,
             timeout: float = 8, stable_seconds: float = 0.25) -> tuple[float, int]:
    deadline = time.monotonic() + timeout
    stable_since = None
    count = 0
    while time.monotonic() < deadline:
        count = booleans(expressions)
        if count >= minimum:
            if stable_since is None:
                stable_since = time.monotonic()
            if time.monotonic() - stable_since >= stable_seconds:
                return time.monotonic(), count
        else:
            stable_since = None
        time.sleep(0.05)
    raise RuntimeError("art-ready-timeout")


def restore_home() -> None:
    action("ActivateWindow(Home)")
    wait(lambda: window_id() == 10000, 3, "art-home-timeout")


def measure_route(name, activate, target, minimum, expressions) -> dict:
    if active_players():
        raise RuntimeError("art-player-busy")
    rx_before, tx_before = counter("rx_bytes"), counter("tx_bytes")
    started = time.monotonic()
    action(activate)
    activated = wait(lambda: window_id() == target, 6,
                     "art-window-timeout:" + name)
    try:
        ready, ready_count = wait_art(expressions, minimum)
    except RuntimeError as error:
        if str(error) == "art-ready-timeout":
            raise RuntimeError("art-ready-timeout:" + name) from None
        raise
    if active_players():
        raise RuntimeError("art-player-started")
    row = {
        "page": name,
        "window_id": target,
        "activation_ms": round((activated - started) * 1000, 1),
        "art_binding_ready_ms": round((ready - started) * 1000, 1),
        "art_bindings_ready": ready_count,
        "art_bindings_required": minimum,
        "network_rx_bytes": counter("rx_bytes") - rx_before,
        "network_tx_bytes": counter("tx_bytes") - tx_before,
    }
    row["within_budget"] = (
        row["art_bindings_ready"] >= row["art_bindings_required"] and
        row["art_binding_ready_ms"] <= READINESS_BUDGET_MS and
        row["network_rx_bytes"] <= NETWORK_RX_BUDGET_BYTES and
        row["network_tx_bytes"] <= NETWORK_TX_BUDGET_BYTES
    )
    return row


def run(passes: int) -> dict:
    if os.uname().nodename != HOST:
        raise RuntimeError("art-target")
    if active_players():
        raise RuntimeError("art-player-busy")
    restore_home()
    rows = []
    try:
        for pass_number in range(1, passes + 1):
            for route in ROUTES:
                row = measure_route(*route)
                row["pass"] = pass_number
                rows.append(row)
    finally:
        restore_home()
    if active_players() or window_id() != 10000:
        raise RuntimeError("art-final-state")
    return {
        "schema_version": 1,
        "kind": "astertv-artwork-binding-readiness",
        "host": HOST,
        "passes": passes,
        "results": rows,
        "active_players": 0,
        "restored_window_id": 10000,
        "budgets": {
            "art_binding_ready_ms": READINESS_BUDGET_MS,
            "network_rx_bytes": NETWORK_RX_BUDGET_BYTES,
            "network_tx_bytes": NETWORK_TX_BUDGET_BYTES,
        },
        "outcome": "pass" if all(row["within_budget"] for row in rows)
            else "fail",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--passes", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.passes <= 3:
        raise RuntimeError("art-passes")
    result = run(args.passes)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
