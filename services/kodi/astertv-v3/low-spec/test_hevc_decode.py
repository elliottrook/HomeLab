#!/usr/bin/env python3
"""Play a short local HEVC fixture and report bounded decoder evidence."""

import json
import os
from pathlib import Path
import socket
import time


FIXTURE = Path("/storage/.aster-staging/hevc-sample.mkv")
LABELS = [
    "Player.Process(videodecoder)", "Player.Process(videowidth)",
    "Player.Process(videoheight)", "Player.Process(videofps)",
    "Player.Process(videodroppedframes)", "Player.Process(videodeinterlacemethod)",
]


def rpc(method, params=None):
    value = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        value["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(value) + "\n").encode())
        raw = client.recv(65536)
    answer = json.loads(raw)
    if "error" in answer:
        raise RuntimeError("hevc-jsonrpc-error")
    return answer.get("result")


def process_ticks(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().split()
    return int(fields[13]) + int(fields[14])


def main():
    if os.uname().nodename != "AsterTV-Jen" or not FIXTURE.is_file():
        raise RuntimeError("hevc-test-target")
    if not 1024 * 1024 <= FIXTURE.stat().st_size <= 128 * 1024 * 1024:
        raise RuntimeError("hevc-test-fixture")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("hevc-test-player-busy")
    pid = int(Path("/run/kodi/kodi.pid").read_text()) if Path("/run/kodi/kodi.pid").exists() else None
    if pid is None:
        pids = [int(p.name) for p in Path("/proc").iterdir() if p.name.isdecimal()
                and (p / "comm").is_file() and (p / "comm").read_text().strip() == "kodi.bin"]
        if len(pids) != 1:
            raise RuntimeError("hevc-test-kodi-pid")
        pid = pids[0]
    started = process_ticks(pid)
    wall = time.monotonic()
    samples = []
    rpc("Player.Open", {"item": {"file": str(FIXTURE)}})
    try:
        for _ in range(8):
            time.sleep(2)
            active = rpc("Player.GetActivePlayers")
            if not active:
                break
            player = active[0]["playerid"]
            props = rpc("Player.GetProperties", {"playerid": player,
                "properties": ["time", "totaltime", "speed", "percentage"]})
            labels = rpc("XBMC.GetInfoLabels", {"labels": LABELS})
            samples.append({"time": props.get("time"), "speed": props.get("speed"),
                            "percentage": props.get("percentage"), "labels": labels})
    finally:
        active = rpc("Player.GetActivePlayers")
        if active:
            rpc("Player.Stop", {"playerid": active[0]["playerid"]})
    elapsed = time.monotonic() - wall
    cpu = (process_ticks(pid) - started) / os.sysconf("SC_CLK_TCK") / elapsed * 100
    if len(samples) < 5:
        raise RuntimeError("hevc-test-ended-early")
    final = samples[-1]
    clock = final["time"] or {}
    played = clock.get("hour", 0) * 3600 + clock.get("minute", 0) * 60 + clock.get("second", 0)
    percentage = float(final.get("percentage") or 0)
    result = {"passed": (played >= 10 or percentage >= 25) and final.get("speed") == 1,
              "played_seconds": played, "samples": len(samples),
              "percentage": round(percentage, 1),
              "kodi_cpu_percent_one_core": round(cpu, 1),
              "decoder": final["labels"].get("Player.Process(videodecoder)"),
              "width": final["labels"].get("Player.Process(videowidth)"),
              "height": final["labels"].get("Player.Process(videoheight)"),
              "fps": final["labels"].get("Player.Process(videofps)"),
              "dropped_frames": final["labels"].get("Player.Process(videodroppedframes)"),
              "deinterlace": final["labels"].get("Player.Process(videodeinterlacemethod)"),
              "fixture_retained": False}
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
