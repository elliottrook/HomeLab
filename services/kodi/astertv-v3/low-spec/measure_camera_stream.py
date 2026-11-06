#!/usr/bin/env python3
"""Measure one bounded, content-free Aster camera-view session on Jen."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen


HOST = "AsterTV-Jen"
RPC = ("127.0.0.1", 9090)
KODI_SEND = "/usr/bin/kodi-send"
SERVICE = "aster-camera.service"
INTERFACE = "eth0"
CAMERA_WINDOW = 11134
CPU_BUDGET_PERCENT = 35.0
NETWORK_BUDGET_BYTES_PER_SECOND = 1048576.0
RSS_GROWTH_BUDGET_KIB = 131072
TEMPERATURE_BUDGET_MILLICELSIUS = 75000


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method,
               "params": params or {}}
    for attempt in range(3):
        try:
            with socket.create_connection(RPC, timeout=2) as client:
                client.settimeout(4)
                client.sendall((json.dumps(request) + "\r\n").encode())
                buffer = ""
                decoder = json.JSONDecoder()
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
                                raise RuntimeError("camera-kodi-rpc")
                            return reply["result"]
        except (OSError, UnicodeError, json.JSONDecodeError,
                RuntimeError, socket.timeout):
            if attempt < 2:
                time.sleep(0.1)
    raise RuntimeError("camera-kodi-rpc")


def action(value: str) -> None:
    result = subprocess.run(
        [KODI_SEND, "--action=" + value], check=False, capture_output=True,
        text=True, timeout=3,
    )
    if result.returncode:
        raise RuntimeError("camera-kodi-action")


def active_players() -> list:
    result = rpc("Player.GetActivePlayers")
    if not isinstance(result, list):
        raise RuntimeError("camera-player-format")
    return result


def window_id() -> int:
    result = rpc("GUI.GetProperties", {"properties": ["currentwindow"]})
    try:
        return int(result["currentwindow"]["id"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("camera-window-format") from None


def info_value(label: str) -> str:
    result = rpc("XBMC.GetInfoLabels", {"labels": [label]})
    value = result.get(label, "") if isinstance(result, dict) else ""
    return value if isinstance(value, str) else ""


def wait_until(check, seconds: float, code: str) -> float:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return time.monotonic()
        time.sleep(0.1)
    raise RuntimeError(code)


def restore_home() -> None:
    for _ in range(3):
        action("ActivateWindow(Home)")
        try:
            wait_until(lambda: window_id() == 10000, 1.5,
                       "camera-home-timeout")
            time.sleep(1.0)
            if window_id() == 10000:
                return
        except RuntimeError as error:
            if str(error) != "camera-home-timeout":
                raise
    raise RuntimeError("camera-home-restore")


def activate_camera() -> tuple[float, float]:
    started = time.monotonic()
    for _ in range(4):
        action(f"ActivateWindow({CAMERA_WINDOW})")
        try:
            activated = wait_until(lambda: window_id() == CAMERA_WINDOW, 2,
                                   "camera-window-timeout")
            time.sleep(0.75)
            if window_id() == CAMERA_WINDOW:
                return started, activated
        except RuntimeError as error:
            if str(error) != "camera-window-timeout":
                raise
    raise RuntimeError("camera-window-unstable")


def service_active() -> bool:
    result = subprocess.run(
        ["/usr/bin/systemctl", "is-active", "--quiet", SERVICE],
        check=False, timeout=3,
    )
    return result.returncode == 0


def counter(name: str) -> int:
    try:
        return int((Path("/sys/class/net") / INTERFACE / "statistics" /
                    name).read_text().strip())
    except (OSError, ValueError):
        raise RuntimeError("camera-network-counter") from None


def cpu_counts() -> tuple[int, int]:
    values = [int(value) for value in
              Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
    if len(values) < 5:
        raise RuntimeError("camera-cpu-format")
    return values[3] + values[4], sum(values)


def cpu_used(before: tuple[int, int], after: tuple[int, int]) -> float:
    idle, total = after[0] - before[0], after[1] - before[1]
    if total <= 0 or not 0 <= idle <= total:
        raise RuntimeError("camera-cpu-sample")
    return round((total - idle) / total * 100, 2)


def kodi_rss() -> int:
    pids = [path for path in Path("/proc").iterdir() if path.name.isdecimal()
            and (path / "comm").is_file()
            and (path / "comm").read_text().strip() == "kodi.bin"]
    if len(pids) != 1:
        raise RuntimeError("camera-kodi-process")
    for line in (pids[0] / "status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("camera-kodi-rss")


def temperature() -> int | None:
    try:
        return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text())
    except (OSError, ValueError):
        return None


def frame_count() -> int:
    try:
        with urlopen("http://127.0.0.1:15102/status", timeout=2) as reply:
            value = json.loads(reply.read(4097))
        if value.get("ready") is not True or value.get("active") is not True:
            raise RuntimeError("camera-status-state")
        frames = value.get("frames")
        if type(frames) is not int or frames < 0:
            raise RuntimeError("camera-status-shape")
        return frames
    except (OSError, ValueError, json.JSONDecodeError):
        raise RuntimeError("camera-status-unavailable") from None


def stop_view() -> None:
    # Leaving the camera window invokes its reviewed `view,leave` lifecycle.
    action("ActivateWindow(Home)")
    try:
        wait_until(lambda: not service_active(), 4, "camera-stop-timeout")
    finally:
        if service_active():
            subprocess.run(["/usr/bin/systemctl", "stop", SERVICE],
                           check=False, timeout=8)


def sample(duration: float) -> dict:
    if os.uname().nodename != HOST:
        raise RuntimeError("camera-target")
    if active_players():
        raise RuntimeError("camera-player-busy")
    stop_view()
    restore_home()
    started, activated = activate_camera()
    before_cpu = cpu_counts()
    before_rx, before_tx = counter("rx_bytes"), counter("tx_bytes")
    before_rss = kodi_rss()
    before_temp = temperature()
    # The camera window's default control is the reviewed Live view button;
    # Select exercises the same route as the physical and Aster remotes.
    rpc("Input.Select")
    try:
        live = wait_until(
            lambda: service_active() and info_value(
                "Window(11134).Property(AsterHub.CameraPlaying)") == "true",
            8, "camera-start-timeout")
        frames_before = frame_count()
        time.sleep(duration)
        frames_after = frame_count()
        if active_players():
            raise RuntimeError("camera-player-started")
        after_cpu = cpu_counts()
        after_rx, after_tx = counter("rx_bytes"), counter("tx_bytes")
        after_rss = kodi_rss()
        after_temp = temperature()
    finally:
        stop_view()
        restore_home()
    frame_delta = frames_after - frames_before
    rx_rate = round((after_rx - before_rx) / duration, 2)
    tx_rate = round((after_tx - before_tx) / duration, 2)
    cpu = cpu_used(before_cpu, after_cpu)
    rss_growth = after_rss - before_rss
    temperatures = [value for value in (before_temp, after_temp)
                    if value is not None]
    peak_temp = max(temperatures) if temperatures else None
    within = (frame_delta >= 2 and cpu <= CPU_BUDGET_PERCENT and
              rx_rate <= NETWORK_BUDGET_BYTES_PER_SECOND and
              tx_rate <= NETWORK_BUDGET_BYTES_PER_SECOND and
              rss_growth <= RSS_GROWTH_BUDGET_KIB and
              (peak_temp is None or
               peak_temp <= TEMPERATURE_BUDGET_MILLICELSIUS))
    return {
        "schema_version": 1, "kind": "astertv-camera-stream-sample",
        "host": HOST, "duration_seconds": duration,
        "activation_ms": round((activated - started) * 1000, 1),
        "live_start_ms": round((live - started) * 1000, 1),
        "frames_observed": frame_delta, "cpu_used_percent": cpu,
        "network_rx_bytes_per_second": rx_rate,
        "network_tx_bytes_per_second": tx_rate,
        "kodi_rss_start_kib": before_rss, "kodi_rss_end_kib": after_rss,
        "kodi_rss_growth_kib": rss_growth,
        "peak_temperature_millicelsius": peak_temp,
        "active_players": 0, "camera_service_after": "inactive",
        "restored_window_id": window_id(),
        "budgets": {"cpu_percent": CPU_BUDGET_PERCENT,
                    "network_bytes_per_second":
                        NETWORK_BUDGET_BYTES_PER_SECOND,
                    "rss_growth_kib": RSS_GROWTH_BUDGET_KIB,
                    "temperature_millicelsius":
                        TEMPERATURE_BUDGET_MILLICELSIUS},
        "outcome": "pass" if within else "fail",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=12)
    args = parser.parse_args(argv)
    if not 10 <= args.duration <= 20:
        raise RuntimeError("camera-duration")
    result = sample(args.duration)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
