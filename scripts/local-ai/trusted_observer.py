"""Fixed, finite host probes for the Local AI recovery candidate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Sequence

from lease_watchdog import EXPECTED_SCHEDULES, Observation

Probe = Callable[[Sequence[str], float], tuple[int, str]]


@dataclass(frozen=True)
class RuntimeManifest:
    model_sha256: str
    binary_sha256: str
    unit_sha256: str
    auth_marker: str


CONTROL_UNITS = ("pve-cluster", "pvedaemon", "pvestatd", "pveproxy", "ssh", "networking", "nut-monitor")
PRODUCTION = (("104", "aster-agent.service"), ("110", "aster-llama.service"), ("116", "aster-speech.service"))
FIXED_PROBES = {
    "gpu": ("pct", "exec", "110", "--", "sh", "-c", "test -e /dev/dri/renderD128 && ls -l /dev/dri/renderD128"),
    "model": ("pct", "exec", "110", "--", "sha256sum", "/var/lib/aster-llama/models/Qwen3.5-9B-Q4_K_M.gguf"),
    "binary": ("pct", "exec", "110", "--", "sha256sum", "/usr/local/bin/llama-server"),
    "unit": ("pct", "exec", "110", "--", "sha256sum", "/etc/systemd/system/aster-llama.service"),
    "auth": ("pct", "exec", "110", "--", "curl", "--fail", "--max-time", "5", "http://127.0.0.1:11435/health"),
    "proxmox_schedule": ("pvesh", "get", "/cluster/backup", "--output-format", "json"),
    "truenas_schedule": ("midclt", "call", "rsynctask.query"),
    "news_schedule": ("pct", "exec", "114", "--", "systemctl", "show", "news-aggregator-digest.timer", "--property=UnitFileState", "--property=TimersCalendar"),
}


def _run(runner: Probe, argv: Sequence[str]) -> tuple[int, str]:
    try:
        return runner(argv, 5.0)
    except Exception:
        return 124, ""


def _active(runner: Probe, argv: Sequence[str]) -> bool:
    code, output = _run(runner, argv)
    return code == 0 and output.strip() == "active"


def _schedule_points(runner: Probe) -> tuple[bool, tuple[str, ...]]:
    code, proxmox = _run(runner, FIXED_PROBES["proxmox_schedule"])
    if code != 0:
        return False, ()
    code, truenas = _run(runner, FIXED_PROBES["truenas_schedule"])
    if code != 0:
        return False, ()
    code, news = _run(runner, FIXED_PROBES["news_schedule"])
    if code != 0:
        return False, ()
    try:
        pve = json.loads(proxmox)
        rsync = json.loads(truenas)
    except json.JSONDecodeError:
        return False, ()
    points = []
    if any(item.get("enabled") and item.get("schedule") == "00:30" for item in pve):
        points.append("proxmox:00:30")
    names = {"01:00": "truenas-guest", "02:00": "truenas-lxc110", "03:00": "truenas-mac"}
    for item in rsync:
        if item.get("enabled") and item.get("schedule") in names:
            points.append(names[item["schedule"]] + ":" + item["schedule"])
    if "UnitFileState=enabled" in news and "06:15" in news and "17:15" in news:
        points.extend(("news:06:15", "news:17:15"))
    return True, tuple(points)


def collect(runner: Probe, *, now_minute: int, lease_expires_minute: int, manifest: RuntimeManifest) -> Observation:
    control = all(_active(runner, ("systemctl", "is-active", unit)) for unit in CONTROL_UNITS)
    production = all(_active(runner, ("pct", "exec", vmid, "--", "systemctl", "is-active", unit)) for vmid, unit in PRODUCTION)
    schedule_enabled, schedule_points = _schedule_points(runner)

    def exact(name: str, expected: str) -> bool:
        code, output = _run(runner, FIXED_PROBES[name])
        return code == 0 and output.split()[0:1] == [expected]

    code, gpu = _run(runner, FIXED_PROBES["gpu"])
    auth_code, auth = _run(runner, FIXED_PROBES["auth"])
    return Observation(
        now_minute=now_minute,
        heartbeat_alive=now_minute < lease_expires_minute,
        control_plane_healthy=control,
        production_services_healthy=production,
        accepted_gpu_visible=code == 0 and "renderD128" in gpu,
        schedule_restored=schedule_points == EXPECTED_SCHEDULES,
        schedule_points=schedule_points,
        schedules_enabled=schedule_enabled,
        exact_binary_verified=exact("binary", manifest.binary_sha256),
        model_verified=exact("model", manifest.model_sha256),
        unit_verified=exact("unit", manifest.unit_sha256),
        auth_verified=auth_code == 0 and auth.strip().startswith(manifest.auth_marker),
    )
