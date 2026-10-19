"""Slow, read-only F2 preflight snapshot candidate.

This candidate performs the backup-chain observations before the narrow scan
window and leaves only freshness and exclusion revalidation to the final guard.
It emits digests and booleans, never archive paths, task logs or credentials.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable

from backup_receipt_adapter import (BackupReceiptError, verify_lxc110_mirror,
                                    verify_proxmox_artifacts)
from fixed_source_adapters import _schedule_ok, _truenas

Runner = Callable[[tuple[str, ...], float], tuple[int, str]]
EXPECTED_BACKUP_ID = "backup-49999802-1365"
FRESHNESS_SECONDS = 90

PVE_ARTIFACTS = ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json")
PVE_JOB = ("pvesh", "get", f"/cluster/backup/{EXPECTED_BACKUP_ID}", "--output-format", "json")
TRUENAS_TASKS = _truenas(("midclt", "call", "rsynctask.query"))
TRUENAS_MIRROR = _truenas(("midclt", "call", "filesystem.listdir", "/mnt/Recovery/guests/aster-lxc110"))
LEASE_STATUS = ("/usr/local/sbin/local-ai-lease", "status")


class F2PreflightError(ValueError):
    pass


@dataclass(frozen=True)
class F2PreflightSnapshot:
    cycle: str
    captured_epoch: int
    artifact_identity_sha256: str
    archive_identity_verified: bool
    truenas_schedule_sha256: str
    mirror_identity_sha256: str
    backup_job_sha256: str
    lease_ready: bool
    exclusion_token: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _json(runner: Runner, command: tuple[str, ...], timeout: float) -> object:
    code, output = runner(command, timeout)
    if code != 0:
        raise F2PreflightError("fixed F2 source command failed")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise F2PreflightError("fixed F2 source returned invalid JSON") from exc


def collect_snapshot(runner: Runner, *, cycle: str, lease_issued_epoch: int,
                     captured_epoch: int, exclusion_token: str) -> F2PreflightSnapshot:
    """Collect the slow read-only chain before the final scan window."""
    if len(cycle) != 10 or cycle[4] != "-" or cycle[7] != "-":
        raise F2PreflightError("cycle is not canonical")
    if type(captured_epoch) is not int or not exclusion_token:
        raise F2PreflightError("preflight identity is invalid")
    artifacts_raw = _json(runner, PVE_ARTIFACTS, 30.0)
    job = _json(runner, PVE_JOB, 10.0)
    tasks = _json(runner, TRUENAS_TASKS, 10.0)
    mirror = _json(runner, TRUENAS_MIRROR, 10.0)
    if not isinstance(artifacts_raw, list) or not isinstance(tasks, list) or not isinstance(mirror, list) or not isinstance(job, dict):
        raise F2PreflightError("F2 source shape is invalid")
    try:
        artifacts = verify_proxmox_artifacts(artifacts_raw, date_prefix=cycle.replace("-", "_"))
        verify_lxc110_mirror(mirror, artifacts[1])
    except BackupReceiptError as exc:
        raise F2PreflightError("backup artifact identity or mirror is invalid") from exc
    if not _schedule_ok(tasks, date_prefix=cycle.replace("-", "_"),
                        artifact_ctimes=tuple(item.ctime for item in artifacts),
                        lease_issued_epoch=lease_issued_epoch):
        raise F2PreflightError("TrueNAS schedule chain is not current and complete")
    if (job.get("id") != EXPECTED_BACKUP_ID or job.get("enabled") not in (1, True)
            or job.get("schedule") != "00:30" or job.get("storage") != "backups"
            or job.get("type") != "vzdump" or job.get("all") not in (1, True)):
        raise F2PreflightError("fixed Proxmox backup job is not current")
    code, status = runner(LEASE_STATUS, 5.0)
    try:
        lease_state = json.loads(status)
    except json.JSONDecodeError as exc:
        raise F2PreflightError("manual lease status is not JSON") from exc
    if code != 0 or not isinstance(lease_state, dict) or lease_state.get("state") != "ready":
        raise F2PreflightError("manual lease is not ready")
    artifact_identity = [(item.vmid, item.volid, item.size, item.ctime) for item in artifacts]
    mirror_identity = sorted((item.get("name"), item.get("path"), item.get("size")) for item in mirror)
    return F2PreflightSnapshot(
        cycle=cycle, captured_epoch=captured_epoch,
        artifact_identity_sha256=_digest(artifact_identity),
        archive_identity_verified=True,
        truenas_schedule_sha256=_digest(tasks),
        mirror_identity_sha256=_digest(mirror_identity),
        backup_job_sha256=_digest(job), lease_ready=True,
        exclusion_token=exclusion_token,
    )


def final_guard(snapshot: F2PreflightSnapshot, *, now_epoch: int, exclusion_token: str) -> None:
    """Revalidate only the short-lived freshness/exclusion boundary."""
    if not snapshot.archive_identity_verified or not snapshot.lease_ready:
        raise F2PreflightError("preflight snapshot is incomplete")
    if type(now_epoch) is not int or now_epoch < snapshot.captured_epoch:
        raise F2PreflightError("preflight clock moved backwards")
    if now_epoch - snapshot.captured_epoch > FRESHNESS_SECONDS:
        raise F2PreflightError("preflight snapshot is stale")
    if exclusion_token != snapshot.exclusion_token:
        raise F2PreflightError("host exclusion does not match preflight")
