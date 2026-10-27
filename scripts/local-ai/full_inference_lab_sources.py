"""Fixed-command source producer for the full-inference drain candidate."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence
from zoneinfo import ZoneInfo

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_session import FullDrainPreflight

Runner = Callable[[Sequence[str], float], tuple[int, str]]
LOCAL_ZONE = ZoneInfo("America/Vancouver")
# Fixed production Proxmox job identity; kept inline so the 14-file target
# packet has no hidden dependency on the broader receipt adapter.
EXPECTED_PROXMOX_BACKUP_ID = "backup-49999802-1365"


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
    "schedules": ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json"),
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
    "legacy_status": ("/usr/local/sbin/local-ai-lease", "status"),
}

LOCAL_PROXMOX_FIXED = {
    "backup_job": ("pvesh", "get", f"/cluster/backup/{EXPECTED_PROXMOX_BACKUP_ID}", "--output-format", "json"),
}

_VZDUMP_UPID = re.compile(r"^UPID:proxmox:[0-9A-F]+:[0-9A-F]+:[0-9A-F]+:vzdump::root@pam:$")
_JOB_START = re.compile(r"<root@pam> starting task UPID:proxmox:[0-9A-F]+:[0-9A-F]+:[0-9A-F]+:vzdump::root@pam:")
_JOURNAL_FILTER = "starting task UPID:.*:vzdump:|Backup job finished successfully|TASK ERROR"


def _pvescheduler_journal_command(date: str) -> tuple[str, ...]:
    """Return the fixed bounded journal query for one validated local date."""
    if not re.fullmatch(r"\d{4}_\d{2}_\d{2}", date):
        raise FullDrainSourceError("backup cycle date is not canonical")
    day = date.replace("_", "-")
    return ("journalctl", "-u", "pvescheduler", "--since", f"{day} 00:29:00",
            "--until", f"{day} 01:10:00", "--no-pager", "-o", "json",
            "-g", _JOURNAL_FILTER)


def _service(vmid: str, unit: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", "systemctl", "is-active", unit)


def _legacy_lease_ready(raw: str) -> bool:
    """Accept the two deployed status encodings, and no broader object."""
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw.strip()
    return value == "ready" or (isinstance(value, dict) and value == {"state": "ready"})


def validate_backup_sources(pve: object, truenas: object, *, cycle: str, now_epoch: int) -> bool:
    """Validate current-cycle artifact/task ordering without requiring F2 integrity."""
    if not isinstance(pve, list) or not isinstance(truenas, list):
        return False
    cycle_key = cycle.replace("-", "_")
    artifacts = {}
    for item in pve:
        try:
            vmid, ctime, size = int(item.get("vmid")), item.get("ctime"), item.get("size", 0)
        except (AttributeError, TypeError, ValueError):
            continue
        if vmid in {104, 110, 116} and type(ctime) is int and size > 0:
            if datetime.fromtimestamp(ctime, LOCAL_ZONE).strftime("%Y_%m_%d") == cycle_key:
                artifacts[vmid] = max(artifacts.get(vmid, 0), ctime)
    if set(artifacts) != {104, 110, 116}:
        return False
    expected = {1: 60, 3: 120, 2: 180}
    started, finished, task_ids = [], [], set()
    for item in truenas:
        if not isinstance(item, dict) or item.get("id") not in expected:
            continue
        task_id = item["id"]
        task_ids.add(task_id)
        schedule = item.get("schedule", {})
        if (not item.get("enabled") or int(schedule.get("hour", -1)) * 60 + int(schedule.get("minute", -1)) != expected[task_id]):
            return False
        job = item.get("job", {})
        started_ms = job.get("time_started", {}).get("$date")
        finished_ms = job.get("time_finished", {}).get("$date")
        if (job.get("state") != "SUCCESS" or job.get("arguments") != [task_id]
                or type(started_ms) is not int or type(finished_ms) is not int
                or started_ms > finished_ms):
            return False
        started_dt = datetime.fromtimestamp(started_ms / 1000, LOCAL_ZONE)
        finished_dt = datetime.fromtimestamp(finished_ms / 1000, LOCAL_ZONE)
        if (started_dt.strftime("%Y_%m_%d") != cycle_key or finished_dt.strftime("%Y_%m_%d") != cycle_key
                or started_dt.hour * 60 + started_dt.minute < expected[task_id]
                or finished_ms / 1000 > now_epoch):
            return False
        started.append(started_ms)
        finished.append(finished_ms)
        if started_ms / 1000 < max(artifacts.values()):
            return False
    return (task_ids == {1, 2, 3} and started == sorted(started)
            and finished == sorted(finished) and started[1] >= finished[0]
            and started[2] >= finished[1])


def _current_proxmox_artifacts(pve: object, *, cycle: str, now_epoch: int) -> tuple[int, ...] | None:
    if not isinstance(pve, list):
        return None
    cycle_key = cycle.replace("-", "_")
    latest: dict[int, int] = {}
    for item in pve:
        try:
            vmid, ctime, size = int(item.get("vmid")), item.get("ctime"), item.get("size", 0)
        except (AttributeError, TypeError, ValueError):
            continue
        if (vmid in {104, 110, 116} and type(ctime) is int and ctime <= now_epoch and size > 0
                and datetime.fromtimestamp(ctime, LOCAL_ZONE).strftime("%Y_%m_%d") == cycle_key):
            latest[vmid] = max(latest.get(vmid, 0), ctime)
    if set(latest) != {104, 110, 116}:
        return None
    return tuple(latest[vmid] for vmid in (104, 110, 116))


def _local_proxmox_job_complete(journal: object, *, date: str, latest_artifact: int,
                                now_epoch: int, job: object) -> bool:
    if (not isinstance(job, dict) or str(job.get("id")) != EXPECTED_PROXMOX_BACKUP_ID
            or job.get("enabled") not in (1, True) or job.get("schedule") != "00:30"
            or job.get("storage") != "backups" or job.get("type") != "vzdump"
            or job.get("all") not in (1, True)):
        return False
    if not isinstance(journal, str) or len(journal) > 65_536:
        return False
    lines = journal.splitlines()
    if len(lines) != 2:
        return False
    try:
        rows = [json.loads(line) for line in lines]
        start = int(rows[0]["__REALTIME_TIMESTAMP"]) // 1_000_000
        finish = int(rows[1]["__REALTIME_TIMESTAMP"]) // 1_000_000
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False
    local_start = datetime.fromtimestamp(start, LOCAL_ZONE)
    return (local_start.strftime("%Y_%m_%d") == date
            and 30 <= local_start.hour * 60 + local_start.minute < 35
            and start <= latest_artifact <= finish <= now_epoch
            and bool(_JOB_START.fullmatch(rows[0].get("MESSAGE", "")))
            and rows[1].get("MESSAGE") == "INFO: Backup job finished successfully")


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
        return validate_backup_sources(pve, truenas, cycle=cycle, now_epoch=int(self.wall_clock()))

    def _next_ingest_epoch(self, now: int) -> int:
        raw = self._run("next_ingest")
        try:
            value = int(raw)
            return value // 1_000_000 if value > 10_000_000_000 else value
        except ValueError:
            match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(UTC|PDT|PST)", raw)
            if not match:
                raise FullDrainSourceError("next News ingest timestamp is unavailable")
            offsets = {"UTC": timezone.utc, "PDT": timezone(timedelta(hours=-7)),
                       "PST": timezone(timedelta(hours=-8))}
            value = datetime.strptime(" ".join(match.groups()[:2]), "%Y-%m-%d %H:%M:%S").replace(tzinfo=offsets[match.group(3)])
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
        if not _legacy_lease_ready(self._run("legacy_status")):
            raise FullDrainSourceError("legacy local-ai-lease is not ready")
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


class LocalProxmoxFullDrainSourceProducer(FullDrainSourceProducer):
    """Narrow pilot source: local Proxmox cycle proof, with no TrueNAS gate.

    This is intentionally a different producer type rather than a caller flag.
    It proves only that the fresh local guest archives and the whole local
    Proxmox backup job completed before the attended no-file-mutation drain.
    It does not assert TrueNAS mirror success, F2 archive integrity, or F3
    retained-receipt readiness.
    """

    def _backup_current(self, cycle: str) -> bool:
        try:
            pve = json.loads(self._run("schedules"))
            job = json.loads(self._run_command(LOCAL_PROXMOX_FIXED["backup_job"], timeout=10.0))
            journal = self._run_command(_pvescheduler_journal_command(cycle.replace("-", "_")), timeout=10.0)
        except (json.JSONDecodeError, FullDrainSourceError):
            return False
        artifacts = _current_proxmox_artifacts(pve, cycle=cycle, now_epoch=int(self.wall_clock()))
        if artifacts is None:
            return False
        return _local_proxmox_job_complete(
            journal, date=cycle.replace("-", "_"), latest_artifact=max(artifacts),
            now_epoch=int(self.wall_clock()), job=job)
