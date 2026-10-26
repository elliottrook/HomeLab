"""Fixed, finite host probes for the Local AI recovery candidate."""

from __future__ import annotations

import json
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Callable, Sequence

from lease_watchdog import EXPECTED_SCHEDULES, Observation

Probe = Callable[[Sequence[str], float], tuple[int, str]]
EXPECTED_AUTH_MARKER = "auth-metadata-ok"
AUTH_PROBE_PATH = "/usr/local/libexec/aster-a1/llama_auth_probe.py"
AUTH_PROBE_SHA256 = "93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582"
MODEL_HASH_TIMEOUT = 30.0


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
    "model": ("pct", "exec", "110", "--", "sha256sum", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"),
    "binary": ("pct", "exec", "110", "--", "sha256sum", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"),
    "unit": ("pct", "exec", "110", "--", "sha256sum", "/etc/systemd/system/aster-llama.service"),
    "auth": (
        "pct", "exec", "110", "--", "sh", "-c",
        f"test \"$(sha256sum {AUTH_PROBE_PATH} | cut -d' ' -f1)\" = {AUTH_PROBE_SHA256} "
        f"&& /usr/bin/python3 -B {AUTH_PROBE_PATH} && printf {EXPECTED_AUTH_MARKER}",
    ),
    "heartbeat": ("stat", "-c", "%Y", "/var/lib/local-ai-lab/owner-heartbeat"),
    "proxmox_schedule": ("pvesh", "get", "/cluster/backup", "--output-format", "json"),
    "truenas_schedule": ("ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UserKnownHostsFile=/etc/local-ai-lab/truenas_known_hosts", "-i", "/etc/local-ai-lab/truenas_schedule_observer", "aster-schedule-observer@192.168.20.40", "midclt", "call", "rsynctask.query"),
    "news_schedule": ("pct", "exec", "114", "--", "systemctl", "show", "news-aggregator-digest.timer", "--property=UnitFileState", "--property=TimersCalendar"),
}


def _run(runner: Probe, argv: Sequence[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        return runner(argv, timeout)
    except Exception:
        return 124, ""


def _active(runner: Probe, argv: Sequence[str]) -> bool:
    code, output = _run(runner, argv)
    return code == 0 and output.strip() == "active"


def service_probe(vmid: str, unit: str) -> tuple[str, ...]:
    if (vmid, unit) not in PRODUCTION:
        raise ValueError("service probe is outside the fixed production set")
    return ("pct", "exec", vmid, "--", "systemctl", "is-active", unit)


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
    def cron_time(value):
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and value.get("minute") is not None and value.get("hour") is not None:
            return f"{int(value['hour']):02d}:{int(value['minute']):02d}"
        return None

    if any(item.get("enabled") and cron_time(item.get("schedule")) == "00:30" for item in pve):
        points.append("proxmox:00:30")
    names = {1: ("truenas-guest", "01:00"), 3: ("truenas-lxc110", "02:00"), 2: ("truenas-mac", "03:00")}
    for item_id, (name, expected) in names.items():
        item = next((candidate for candidate in rsync if candidate.get("id") == item_id), None)
        if item and item.get("enabled") and cron_time(item.get("schedule")) == expected:
            points.append(name + ":" + expected)
    if "UnitFileState=enabled" in news and "OnCalendar=*-*-* 06,17:15:00 Etc/GMT+7" in news:
        points.extend(("news:06:15", "news:17:15"))
    return True, tuple(points)


def collect(runner: Probe, *, lease_expires_minute: int, manifest: RuntimeManifest, clock: Callable[[], int] | None = None, epoch_clock: Callable[[], float] | None = None) -> Observation:
    now_minute = clock() if clock is not None else datetime.now().hour * 60 + datetime.now().minute
    now_epoch = epoch_clock() if epoch_clock is not None else time.time()
    control = all(_active(runner, ("systemctl", "is-active", unit)) for unit in CONTROL_UNITS)
    production = all(_active(runner, ("pct", "exec", vmid, "--", "systemctl", "is-active", unit)) for vmid, unit in PRODUCTION)
    schedule_enabled, schedule_points = _schedule_points(runner)

    def exact(name: str, expected: str) -> bool:
        timeout = MODEL_HASH_TIMEOUT if name == "model" else 5.0
        code, output = _run(runner, FIXED_PROBES[name], timeout)
        return code == 0 and output.split()[0:1] == [expected]

    code, gpu = _run(runner, FIXED_PROBES["gpu"])
    auth_code, auth = _run(runner, FIXED_PROBES["auth"])
    heartbeat_code, heartbeat_output = _run(runner, FIXED_PROBES["heartbeat"])
    try:
        heartbeat_alive = heartbeat_code == 0 and 0 <= now_epoch - float(heartbeat_output.strip()) <= 90
    except ValueError:
        heartbeat_alive = False
    return Observation(
        now_minute=now_minute,
        heartbeat_alive=heartbeat_alive and now_minute < lease_expires_minute,
        control_plane_healthy=control,
        production_services_healthy=production,
        accepted_gpu_visible=code == 0 and "renderD128" in gpu,
        schedule_restored=schedule_points == EXPECTED_SCHEDULES,
        schedule_points=schedule_points,
        schedules_enabled=schedule_enabled,
        exact_binary_verified=exact("binary", manifest.binary_sha256),
        model_verified=exact("model", manifest.model_sha256),
        unit_verified=exact("unit", manifest.unit_sha256),
        auth_verified=auth_code == 0 and auth.strip() == EXPECTED_AUTH_MARKER,
    )


def collect_light(runner: Probe, *, lease_expires_minute: int, clock: Callable[[], int] | None = None, epoch_clock: Callable[[], float] | None = None) -> Observation:
    """Collect only lease-safety probes; never reads the large model artifact."""
    now_minute = clock() if clock is not None else datetime.now().hour * 60 + datetime.now().minute
    now_epoch = epoch_clock() if epoch_clock is not None else time.time()
    control = all(_active(runner, ("systemctl", "is-active", unit)) for unit in CONTROL_UNITS)
    heartbeat_code, heartbeat_output = _run(runner, FIXED_PROBES["heartbeat"])
    try:
        heartbeat_alive = heartbeat_code == 0 and 0 <= now_epoch - float(heartbeat_output.strip()) <= 90
    except ValueError:
        heartbeat_alive = False
    return Observation(
        now_minute=now_minute,
        heartbeat_alive=heartbeat_alive and now_minute < lease_expires_minute,
        control_plane_healthy=control,
        production_services_healthy=None,
        accepted_gpu_visible=None,
        schedule_restored=None,
        schedule_points=(),
        schedules_enabled=None,
        exact_binary_verified=None,
        model_verified=None,
        unit_verified=None,
        auth_verified=None,
    )


class TrustedHostObserver:
    """Fixed-source observer used by the controller, not caller callbacks."""

    def __init__(self, runner: Probe, manifest: RuntimeManifest, *, clock: Callable[[], int] | None = None, epoch_clock: Callable[[], float] | None = None):
        self.runner = runner
        self.manifest = manifest
        self.clock = clock
        self.epoch_clock = epoch_clock

    def collect(self, lease_expires_minute: int) -> Observation:
        return collect(
            self.runner,
            lease_expires_minute=lease_expires_minute,
            manifest=self.manifest,
            clock=self.clock,
            epoch_clock=self.epoch_clock,
        )

    def collect_light(self, lease_expires_minute: int) -> Observation:
        return collect_light(
            self.runner,
            lease_expires_minute=lease_expires_minute,
            clock=self.clock,
            epoch_clock=self.epoch_clock,
        )

    def service_active(self, vmid: str, unit: str) -> bool:
        """Return a known service state; ambiguous probe results fail closed."""
        code, output = _run(self.runner, service_probe(vmid, unit))
        state = output.strip()
        if code == 0 and state == "active":
            return True
        if code != 0 and state == "inactive":
            return False
        raise ValueError("service state probe is ambiguous")

    def news_quiesced(self) -> bool:
        timer = ("pct", "exec", "114", "--", "systemctl")
        code, output = _run(self.runner, (*timer, "is-active", "news-aggregator-digest.timer"))
        if code != 0 or output.strip() != "active":
            raise ValueError("News timer is not active")
        code, output = _run(self.runner, (*timer, "is-enabled", "news-aggregator-digest.timer"))
        if code != 0 or output.strip() != "enabled":
            raise ValueError("News timer is not enabled")
        code, output = _run(self.runner, (*timer, "is-active", "news-aggregator-digest.service"))
        if code == 3 and output.strip() == "inactive":
            return True
        if code == 0 and output.strip() == "active":
            return False
        raise ValueError("News job state probe is ambiguous")

    def consumers_quiesced(self) -> bool:
        return (all(not self.service_active(vmid, unit) for vmid, unit in PRODUCTION)
                and self.news_quiesced())
