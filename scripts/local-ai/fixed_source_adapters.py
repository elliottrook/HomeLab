"""Fixed-command source adapters for authenticated lease receipts."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from admission_gate import EXPECTED_BACKUP_SOURCE, AdmissionEvidenceError
from backup_receipt_adapter import verify_lxc110_mirror, verify_mac_pull_receipt, verify_proxmox_artifacts
from quiescence_receipt_adapter import ConsumerSnapshot, compose_quiescence_receipt
from source_receipts import BackupSourceReceipt, QuiescenceSourceReceipt, compose_candidate_evidence
from retained_archive_integrity import IntegrityError, load_root_owned, verify as verify_retained_integrity

Runner = Callable[[tuple[str, ...], float], tuple[int, str]]

PRODUCTION = (("104", "aster-agent.service"), ("110", "aster-llama.service"), ("116", "aster-speech.service"))
TRUENAS = "aster-schedule-observer@192.168.20.40"
KNOWN_HOSTS = "/etc/local-ai-lab/truenas_known_hosts"
IDENTITY = "/etc/local-ai-lab/truenas_schedule_observer"
MAC_OBSERVER_COMMAND = "aster-mac-pull-summary"


class SourceAdapterError(ValueError):
    pass


def _json(runner: Runner, argv: tuple[str, ...], timeout: float = 30.0):
    code, output = runner(argv, timeout)
    if code != 0:
        raise SourceAdapterError("fixed source command failed")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise SourceAdapterError("fixed source returned invalid JSON") from exc


def _truenas(command: tuple[str, ...]) -> tuple[str, ...]:
    return ("ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={KNOWN_HOSTS}", "-i", IDENTITY, TRUENAS, *command)


LOCAL_ZONE = ZoneInfo("America/Vancouver")


def _schedule_ok(items: list[dict], *, date_prefix: str, artifact_ctimes: tuple[int, ...], lease_issued_epoch: int) -> bool:
    expected = {1: (1, "01:00"), 3: (3, "02:00"), 2: (2, "03:00")}
    finished_epochs: list[int] = []
    started_epochs: list[int] = []
    for item_id, (_, clock) in expected.items():
        item = next((item for item in items if item.get("id") == item_id), None)
        schedule = item.get("schedule", {}) if item else {}
        if not item or not item.get("enabled") or f"{int(schedule.get('hour', -1)):02d}:{int(schedule.get('minute', -1)):02d}" != clock:
            return False
        job = item.get("job", {})
        started = job.get("time_started", {}).get("$date")
        finished = job.get("time_finished", {}).get("$date")
        arguments = job.get("arguments")
        if job.get("state") != "SUCCESS" or arguments != [item_id] or not isinstance(started, int) or not isinstance(finished, int) or started > finished:
            return False
        local_finished = datetime.fromtimestamp(finished / 1000, LOCAL_ZONE)
        local_started = datetime.fromtimestamp(started / 1000, LOCAL_ZONE)
        if local_started.strftime("%Y_%m_%d") != date_prefix or local_finished.strftime("%Y_%m_%d") != date_prefix:
            return False
        required_minute = int(clock[:2]) * 60
        if local_started.hour * 60 + local_started.minute < required_minute:
            return False
        hour_minute = local_finished.hour * 60 + local_finished.minute
        if hour_minute < required_minute or hour_minute > 4 * 60 + 15:
            return False
        if finished / 1000 > lease_issued_epoch or started / 1000 < max(artifact_ctimes):
            return False
        started_epochs.append(started)
        finished_epochs.append(finished)
    return (
        started_epochs == sorted(started_epochs)
        and finished_epochs == sorted(finished_epochs)
        and started_epochs[1] >= finished_epochs[0]
        and started_epochs[2] >= finished_epochs[1]
        and finished_epochs[-1] / 1000 <= lease_issued_epoch
    )


class FixedSourceAdapters:
    def __init__(self, runner: Runner, *, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], datetime] = datetime.now, monotonic: Callable[[], int] = time.monotonic_ns):
        self.runner, self.sleep, self.clock, self.monotonic = runner, sleep, clock, monotonic

    def backup(self, *, date_prefix: str, lease_issued_epoch: int, verify_archives: bool = True, retained_integrity: bool = False) -> BackupSourceReceipt:
        if verify_archives and retained_integrity:
            raise SourceAdapterError("choose exactly one archive integrity method")
        pve = _json(self.runner, ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json"), 30.0)
        artifacts = verify_proxmox_artifacts(pve, date_prefix=date_prefix)
        rsync = _json(self.runner, _truenas(("midclt", "call", "rsynctask.query")), 10.0)
        if not _schedule_ok(rsync, date_prefix=date_prefix, artifact_ctimes=tuple(a.ctime for a in artifacts), lease_issued_epoch=lease_issued_epoch):
            raise SourceAdapterError("TrueNAS backup tasks are not all successful")
        mirror = _json(self.runner, _truenas(("midclt", "call", "filesystem.listdir", "/mnt/Recovery/guests/aster-lxc110")), 10.0)
        verify_lxc110_mirror(mirror, artifacts[1])
        retained_digest = None
        if retained_integrity:
            def fixed_path(volid: str) -> str:
                code, path = self.runner(("pvesm", "path", volid), 10.0)
                if code != 0:
                    raise SourceAdapterError("backup path lookup failed")
                return path.strip()
            try:
                retained_digest = verify_retained_integrity(
                    load_root_owned(), pve, date=date_prefix,
                    now_epoch=lease_issued_epoch, resolve=fixed_path,
                    lstat=os.lstat,
                )
            except (IntegrityError, OSError) as exc:
                raise SourceAdapterError("retained archive integrity source failed") from exc
        if verify_archives:
            for artifact in artifacts:
                code, path = self.runner(("pvesm", "path", artifact.volid), 10.0)
                if code != 0:
                    raise SourceAdapterError("backup path lookup failed")
                code, _ = self.runner(("zstd", "-t", "--quiet", path.strip()), 300.0)
                if code != 0:
                    raise SourceAdapterError("backup archive integrity check failed")
        receipt_material = json.dumps([(a.vmid, a.volid, a.size, a.ctime) for a in artifacts], separators=(",", ":"), sort_keys=True).encode()
        digest = hashlib.sha256(receipt_material).hexdigest()
        now = self.clock()
        integrity_receipt = retained_digest or f"metadata-sha256:{digest}"
        return BackupSourceReceipt(EXPECTED_BACKUP_SOURCE, EXPECTED_BACKUP_SOURCE, now.hour * 60 + now.minute, integrity_receipt, verify_archives or retained_integrity, True)

    def backup_from_retained(self, *, date_prefix: str, lease_issued_epoch: int) -> BackupSourceReceipt:
        """Use only the fixed root-owned earlier scan after current chain checks."""
        return self.backup(date_prefix=date_prefix, lease_issued_epoch=lease_issued_epoch,
                           verify_archives=False, retained_integrity=True)

    def mac_pull_summary(self, *, date_prefix: str, lease_issued_epoch: int, freshness_seconds: int = 900) -> str:
        """Collect tree-presence evidence only; never treat it as transfer proof."""
        rsync = _json(self.runner, _truenas(("midclt", "call", "rsynctask.query")), 10.0)
        task_two = next((item for item in rsync if item.get("id") == 2), None)
        finished = task_two.get("job", {}).get("time_finished", {}).get("$date") if task_two else None
        if not isinstance(finished, int):
            raise SourceAdapterError("Mac task completion is unavailable")
        receipt = _json(self.runner, _truenas((MAC_OBSERVER_COMMAND,)), 35.0)
        try:
            return verify_mac_pull_receipt(receipt, date_prefix=date_prefix, task_finished_epoch=finished // 1000, lease_issued_epoch=lease_issued_epoch, freshness_seconds=freshness_seconds)
        except ValueError as exc:
            raise SourceAdapterError(str(exc)) from exc

    def _snapshot(self) -> ConsumerSnapshot:
        states, enters, masks = [], [], []
        for vmid, unit in PRODUCTION:
            code, output = self.runner(("pct", "exec", vmid, "--", "systemctl", "show", unit, "--property=ActiveState", "--property=ActiveEnterTimestampMonotonic", "--value"), 5.0)
            if code != 0:
                raise SourceAdapterError("consumer state probe failed")
            lines = output.splitlines()
            states.append(lines[0] if lines else "unknown")
            enters.append(int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else -1)
            code, mask = self.runner(("pct", "exec", vmid, "--", "readlink", "-f", f"/run/systemd/system/{unit}"), 5.0)
            if code != 0:
                raise SourceAdapterError("consumer mask probe failed")
            masks.append(mask.strip())
        prefix = ("pct", "exec", "114", "--", "systemctl")
        code, timer = self.runner((*prefix, "is-active", "news-aggregator-digest.timer"), 5.0)
        if code != 0 or timer.strip() != "active":
            raise SourceAdapterError("News timer must remain active")
        code, enabled = self.runner((*prefix, "is-enabled", "news-aggregator-digest.timer"), 5.0)
        if code != 0 or enabled.strip() != "enabled":
            raise SourceAdapterError("News timer must remain enabled")
        code, job = self.runner((*prefix, "show", "news-aggregator-digest.service", "--property=ActiveState", "--property=ActiveEnterTimestampMonotonic", "--value"), 5.0)
        job_lines = job.splitlines()
        if code != 0 or len(job_lines) != 2 or job_lines[0] not in {"active", "inactive"} or not job_lines[1].isdigit():
            raise SourceAdapterError("News job probe failed")
        return ConsumerSnapshot(
            self.clock().hour * 60 + self.clock().minute, self.monotonic(),
            tuple(states) + (job_lines[0],), tuple(enters) + (int(job_lines[1]),),
            True, "|".join(masks),
        )

    def quiescence(self, *, interval_seconds: float = 10.0) -> QuiescenceSourceReceipt:
        first = self._snapshot()
        self.sleep(interval_seconds)
        try:
            return compose_quiescence_receipt(first, self._snapshot())
        except AdmissionEvidenceError as exc:
            raise SourceAdapterError(str(exc)) from exc

    def evidence(self, *, date_prefix: str, lease_issued_epoch: int, now_minute: int, window_end_minute: int):
        backup = self.backup(date_prefix=date_prefix, lease_issued_epoch=lease_issued_epoch)
        quiescence = self.quiescence()
        return compose_candidate_evidence(backup, quiescence, now_minute=now_minute, window_end_minute=window_end_minute)

    def evidence_from_retained(self, *, date_prefix: str, lease_issued_epoch: int, now_minute: int, window_end_minute: int):
        """Bind a verified earlier archive scan to fresh post-stop observations."""
        backup = self.backup_from_retained(date_prefix=date_prefix, lease_issued_epoch=lease_issued_epoch)
        quiescence = self.quiescence()
        return compose_candidate_evidence(backup, quiescence, now_minute=now_minute, window_end_minute=window_end_minute)
