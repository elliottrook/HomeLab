#!/usr/bin/env python3
"""Measure content-free idle headroom on the Jen low-spec AsterTV client."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import time


HOST = "AsterTV-Jen"
RPC = ("127.0.0.1", 9090)


def cpu_counts(text: str) -> tuple[int, int]:
    fields = text.splitlines()[0].split()
    if not fields or fields[0] != "cpu" or len(fields) < 6:
        raise RuntimeError("idle-cpu-format")
    values = [int(value) for value in fields[1:]]
    return values[3] + (values[4] if len(values) > 4 else 0), sum(values)


def cpu_used(before: tuple[int, int], after: tuple[int, int]) -> float:
    idle = after[0] - before[0]
    total = after[1] - before[1]
    if total <= 0 or idle < 0 or idle > total:
        raise RuntimeError("idle-cpu-sample")
    return round((total - idle) / total * 100, 2)


def meminfo(text: str) -> dict[str, int]:
    rows = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and value.strip().split():
            rows[key] = int(value.strip().split()[0])
    required = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    if not required <= set(rows):
        raise RuntimeError("idle-memory-format")
    return {"total_kib": rows["MemTotal"], "available_kib": rows["MemAvailable"],
            "swap_used_kib": rows["SwapTotal"] - rows["SwapFree"]}


def status_rss(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("idle-kodi-rss")


def kodi_pid(proc: Path) -> int:
    values = []
    for path in proc.iterdir():
        if path.name.isdecimal() and (path / "comm").is_file():
            if (path / "comm").read_text().strip() == "kodi.bin":
                values.append(int(path.name))
    if len(values) != 1:
        raise RuntimeError("idle-kodi-process")
    return values[0]


def active_players(address=RPC) -> list:
    request = {"jsonrpc": "2.0", "id": 1,
               "method": "Player.GetActivePlayers"}
    with socket.create_connection(address, timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        response = json.loads(client.recv(65536))
    if response.get("error") or not isinstance(response.get("result"), list):
        raise RuntimeError("idle-kodi-rpc")
    return response["result"]


def number(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def sample(duration: float, *, proc: Path = Path("/proc"),
           sys: Path = Path("/sys"), storage: Path = Path("/storage")) -> dict:
    if os.uname().nodename != HOST:
        raise RuntimeError("idle-target")
    if active_players():
        raise RuntimeError("idle-player-busy")
    pid = kodi_pid(proc)
    before_cpu = cpu_counts((proc / "stat").read_text())
    before_rx = number(sys / "class/net/eth0/statistics/rx_bytes")
    before_tx = number(sys / "class/net/eth0/statistics/tx_bytes")
    time.sleep(duration)
    if active_players():
        raise RuntimeError("idle-player-started")
    after_cpu = cpu_counts((proc / "stat").read_text())
    after_rx = number(sys / "class/net/eth0/statistics/rx_bytes")
    after_tx = number(sys / "class/net/eth0/statistics/tx_bytes")
    memory = meminfo((proc / "meminfo").read_text())
    disk = os.statvfs(storage)
    return {
        "schema_version": 1,
        "kind": "astertv-low-spec-idle-sample",
        "host": HOST,
        "duration_seconds": duration,
        "cpu_used_percent": cpu_used(before_cpu, after_cpu),
        "memory": memory,
        "kodi_rss_kib": status_rss((proc / str(pid) / "status").read_text()),
        "temperature_millicelsius": number(
            sys / "class/thermal/thermal_zone0/temp"),
        "gpu_actual_mhz": number(sys / "class/drm/card0/gt_act_freq_mhz"),
        "storage_available_bytes": disk.f_bavail * disk.f_frsize,
        "network_rx_bytes_per_second": None if None in {before_rx, after_rx}
            else round((after_rx - before_rx) / duration, 2),
        "network_tx_bytes_per_second": None if None in {before_tx, after_tx}
            else round((after_tx - before_tx) / duration, 2),
        "active_players": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=10)
    args = parser.parse_args(argv)
    if not 2 <= args.duration <= 30:
        raise RuntimeError("idle-duration")
    print(json.dumps(sample(args.duration), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
