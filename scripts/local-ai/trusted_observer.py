"""Fixed, finite host probes for the Local AI recovery controller candidate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from lease_watchdog import EXPECTED_SCHEDULES, Observation


Probe = Callable[[Sequence[str], float], str]


@dataclass(frozen=True)
class RuntimeManifest:
    model_sha256: str
    binary_sha256: str
    unit_sha256: str
    auth_marker: str


@dataclass(frozen=True)
class ProbeResult:
    name: str
    value: str


FIXED_PROBES = {
    "control_plane": ("systemctl", "is-active", "pve-cluster", "pvedaemon", "pvestatd", "pveproxy", "ssh", "networking", "nut-monitor"),
    "production_services": ("systemctl", "is-active", "aster-agent.service", "aster-llama.service", "aster-speech.service"),
    "gpu": ("test", "-e", "/dev/dri/renderD128"),
    "schedule": ("local-ai-schedule-check", "--exact"),
}


def collect(
    runner: Probe,
    *,
    now_minute: int,
    manifest: RuntimeManifest,
    model_probe: Sequence[str],
    binary_probe: Sequence[str],
    unit_probe: Sequence[str],
    auth_probe: Sequence[str],
) -> Observation:
    """Collect only fixed probes; failures become a conservative observation."""

    values: dict[str, str] = {}

    def run(name: str, argv: Sequence[str]) -> str:
        try:
            value = runner(argv, 5.0).strip()
        except Exception:
            value = "probe-failed"
        values[name] = value
        return value

    control = run("control_plane", FIXED_PROBES["control_plane"])
    production = run("production_services", FIXED_PROBES["production_services"])
    gpu = run("gpu", FIXED_PROBES["gpu"])
    schedule = run("schedule", FIXED_PROBES["schedule"])
    model = run("model", model_probe)
    binary = run("binary", binary_probe)
    unit = run("unit", unit_probe)
    auth = run("auth", auth_probe)

    schedule_points = tuple(item for item in schedule.split() if ":" in item)
    return Observation(
        now_minute=now_minute,
        heartbeat_alive=True,
        control_plane_healthy=control == "active",
        production_services_healthy=production == "active",
        accepted_gpu_visible=gpu == "ok",
        schedule_restored=schedule_points == EXPECTED_SCHEDULES,
        schedule_points=schedule_points,
        schedules_enabled=schedule.startswith("enabled "),
        exact_binary_verified=binary == manifest.binary_sha256,
        model_verified=model == manifest.model_sha256,
        unit_verified=unit == manifest.unit_sha256,
        auth_verified=auth == manifest.auth_marker,
    )
