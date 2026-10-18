"""Fixed-command source producer for the full-inference drain candidate."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence
from zoneinfo import ZoneInfo

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_session import FullDrainPreflight

Runner = Callable[[Sequence[str], float], tuple[int, str]]
LOCAL_ZONE = ZoneInfo("America/Vancouver")


class FullDrainSourceError(ValueError):
    pass


@dataclass(frozen=True)
class AcceptedBaseline:
    model_sha256: str
    binary_sha256: str
    unit_sha256: str


@dataclass(frozen=True)
class TrustedOwnerAttestation:
    owner_id: str
    admin_path_evidence: str


FIXED = {
    "driver": ("readlink", "/sys/bus/pci/devices/0000:04:00.0/driver"),
    "vm": ("qm", "status", "105"),
    "vm_config": ("qm", "config", "105"),
    "schedules": ("pvesh", "get", "/cluster/backup", "--output-format", "json"),
    "truenas": ("ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
                "-o", "StrictHostKeyChecking=yes", "-o", "UserKnownHostsFile=/etc/local-ai-lab/truenas_known_hosts",
                "-i", "/etc/local-ai-lab/truenas_schedule_observer",
                "aster-schedule-observer@192.168.20.40", "midclt", "call", "rsynctask.query"),
    "next_ingest": ("pct", "exec", "114", "--", "systemctl", "list-timers", "--all", "--no-legend", "--no-pager", "news-aggregator-ingest.timer"),
    "news_ingest_active": ("pct", "exec", "114", "--", "systemctl", "is-active", "news-aggregator-ingest.timer"),
    "news_digest_active": ("pct", "exec", "114", "--", "systemctl", "is-active", "news-aggregator-digest.timer"),
    "news_ingest_enabled": ("pct", "exec", "114", "--", "systemctl", "is-enabled", "news-aggregator-ingest.timer"),
    "news_digest_enabled": ("pct", "exec", "114", "--", "systemctl", "is-enabled", "news-aggregator-digest.timer"),
    "gpu": ("pct", "exec", "110", "--", "test", "-e", "/dev/dri/renderD128"),
    "auth": ("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-production-auth-probe"),
}


def _service(vmid: str, unit: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", "systemctl", "is-active", unit)


class FullDrainSourceProducer:
    """Derives preflight facts from fixed probes; caller cannot supply booleans."""

    def __init__(self, runner: Runner, baseline: AcceptedBaseline, owner: TrustedOwnerAttestation,
                 *, wall_clock: Callable[[], float] = time.time):
        self.runner, self.baseline, self.owner, self.wall_clock = runner, baseline, owner, wall_clock

    def _run(self, name: str, *, timeout: float = 10.0) -> str:
        code, output = self.runner(FIXED[name], timeout)
        if code != 0:
            raise FullDrainSourceError(f"fixed source probe failed: {name}")
        return output.strip()

    def _hash(self, vmid: str, path: str, expected: str, label: str) -> None:
        output = self._run_command(("pct", "exec", vmid, "--", "sha256sum", path), timeout=30.0)
        if output.split()[:1] != [expected]:
            raise FullDrainSourceError(f"accepted {label} hash drifted")

    def _run_command(self, command: Sequence[str], *, timeout: float) -> str:
        code, output = self.runner(command, timeout)
        if code != 0:
            raise FullDrainSourceError("fixed source command failed")
        return output.strip()

    def _backup_current(self, cycle: str) -> bool:
        try:
            pve = json.loads(self._run("schedules"))
            truenas = json.loads(self._run("truenas"))
        except (json.JSONDecodeError, FullDrainSourceError):
            return False
        if not isinstance(pve, list) or not isinstance(truenas, list):
            return False
        for item_id in (1, 2, 3):
            item = next((x for x in truenas if x.get("id") == item_id), None)
            if not item or not item.get("enabled") or item.get("job", {}).get("state") != "SUCCESS":
                return False
        cycle_key = cycle.replace("-", "_")
        if not any(item.get("enabled") and cycle_key in json.dumps(item, sort_keys=True) for item in pve):
            return False
        seen = set()
        for item in truenas:
            if item.get("id") in (1, 2, 3):
                seen.add(item["id"])
                finished = item.get("job", {}).get("time_finished", {}).get("$date")
                if type(finished) is not int:
                    return False
                if datetime.fromtimestamp(finished / 1000, LOCAL_ZONE).strftime("%Y_%m_%d") != cycle_key:
                    return False
        if seen != {1, 2, 3}:
            return False
        return True

    def _next_ingest_epoch(self, now: int) -> int:
        raw = self._run("next_ingest")
        try:
            value = int(raw)
            return value // 1_000_000 if value > 10_000_000_000 else value
        except ValueError:
            match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})", raw)
            if not match:
                raise FullDrainSourceError("next News ingest timestamp is unavailable")
            value = datetime.strptime(" ".join(match.groups()), "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL_ZONE)
            return int(value.timestamp())

    def collect(self, *, cycle: str, session_start_epoch: int,
                lab_seconds: int = 30 * 60) -> FullDrainPreflight:
        now = int(self.wall_clock())
        if not self.owner.owner_id or not self.owner.admin_path_evidence:
            raise FullDrainSourceError("trusted MacBook administration attestation is incomplete")
        if session_start_epoch < now:
            raise FullDrainSourceError("session start is stale")
        driver = self._run("driver")
        vm = self._run("vm")
        vm_config = self._run("vm_config")
        if not (driver.rstrip("/").endswith("/bus/pci/drivers/xe") or driver.rstrip("/") == "/xe") or "status: stopped" not in vm or "04:00.0" in vm_config:
            raise FullDrainSourceError("accepted GPU or rollback VM baseline is unsafe")
        self._hash("110", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf", self.baseline.model_sha256, "model")
        self._hash("110", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server", self.baseline.binary_sha256, "binary")
        self._hash("110", "/etc/systemd/system/aster-llama.service", self.baseline.unit_sha256, "unit")
        if not self._backup_current(cycle):
            raise FullDrainSourceError("current backup schedule/status is not verified")
        if (self._run("news_ingest_active") != "active" or self._run("news_digest_active") != "active"
                or self._run("news_ingest_enabled") != "enabled" or self._run("news_digest_enabled") != "enabled"):
            raise FullDrainSourceError("News timers are not active and enabled")
        try:
            next_ingest = self._next_ingest_epoch(now)
        except ValueError as exc:
            raise FullDrainSourceError("next News ingest timestamp is invalid") from exc
        if next_ingest <= now:
            raise FullDrainSourceError("next News ingest is not future")
        for vmid, unit in (("104", "aster-agent.service"), ("110", "aster-llama.service"), ("116", "aster-speech.service")):
            if self._run_command(_service(vmid, unit), timeout=5.0) != "active":
                raise FullDrainSourceError(f"{unit} is not active")
        if self._run("gpu") != "":
            raise FullDrainSourceError("GPU probe returned unexpected output")
        self._run("auth")
        lab_end = session_start_epoch + lab_seconds
        return FullDrainPreflight(
            "full-inference-drain-v1", f"{self.owner.owner_id}:{now}", 1,
            f"application-chain:{cycle}", ACCEPTED_BACKEND, True, True, True, True, True,
            True, True, True, True, now, session_start_epoch, lab_end, lab_end + 15 * 60,
            next_ingest)
