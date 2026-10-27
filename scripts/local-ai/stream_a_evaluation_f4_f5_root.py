#!/usr/bin/env python3
"""Create one current-cycle Stream A F4/F5/admission evidence set.

This entry point is deliberately non-effectful: it observes the fixed backup,
mirror, schedule, lease and production sources and writes evidence only.  It
does not acquire a lease, stop a service, enable a timer or call a model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import tempfile
import time
from typing import Callable

from backup_receipt_adapter import ArtifactReceipt
from f2_scheduled_release_candidate import LOCAL_ZONE, SCHEMA as F2_SCHEMA, _validate_projection
from fixed_source_adapters import FixedSourceAdapters
from lease_watchdog import Observation
from retained_archive_integrity import (
    MAX_RECEIPT_BYTES as MAX_F3_BYTES,
    RECEIPT_PATH as F3_PATH,
    fixed_proxmox_inventory,
    fixed_resolve,
    verify as verify_f3,
)
from stream_a_evaluation_admission import ADMISSION_PATH, F5_OBSERVATION_PATH
from stream_a_evaluation_evidence_loader import (
    EvidenceLoadError,
    _cross_bind_archives,
    _json,
    _read,
)
from stream_a_evaluation_f4_f5_transaction import (
    TransactionArtifacts,
    build_transaction,
)
from trusted_observer import RuntimeManifest, collect as collect_observation


class RootTransactionError(ValueError):
    pass


F2_ROOT = Path("/var/lib/local-ai-lab/f2-scheduled")
F4_PATH = Path("/var/lib/local-ai-lab/pre-acquire-receipt.json")
RUNTIME_ROOT = Path("/var/lib/local-ai-lab/stream-a-evaluation")
WHOLE_HOST_ROOT = Path("/var/lib/local-ai-lab")
WHOLE_HOST_STATUS = ("/usr/local/sbin/local-ai-lease", "status")
MODEL_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
MAX_F2_BYTES = 16 * 1024
MINIMUM_MINUTE = 3 * 60 + 5


@dataclass(frozen=True)
class EvidencePaths:
    f2_root: Path = F2_ROOT
    f3: Path = F3_PATH
    f4: Path = F4_PATH
    f5: Path = F5_OBSERVATION_PATH
    admission: Path = ADMISSION_PATH
    whole_host_root: Path = WHOLE_HOST_ROOT
    runtime_root: Path = RUNTIME_ROOT


@dataclass(frozen=True)
class CollectedSources:
    cycle_date: str
    observed_epoch: int
    observed_minute: int
    f2_bytes: bytes
    f3_bytes: bytes
    backup_receipt: str
    observation: Observation
    lxc110_mirror_identity: str
    unchanged: Callable[[], bool]


def _runner(argv: tuple[str, ...], timeout: float) -> tuple[int, str]:
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return 124, ""
    return result.returncode, result.stdout


def _require_ready(runner: Callable[[tuple[str, ...], float], tuple[int, str]],
                   paths: EvidencePaths) -> None:
    code, output = runner(WHOLE_HOST_STATUS, 10.0)
    try:
        status = json.loads(output)
    except json.JSONDecodeError as error:
        raise RootTransactionError("whole-host lease status is invalid") from error
    if code != 0 or status != {"state": "ready"}:
        raise RootTransactionError("whole-host lease is not exactly ready")
    absent = (
        paths.whole_host_root / "lease.json",
        paths.whole_host_root / "lease.lock",
        paths.whole_host_root / "lease.operation.lock",
        paths.runtime_root / "lease.json",
        paths.runtime_root / "lease.lock",
        paths.runtime_root / "lease.operation.lock",
    )
    if any(os.path.lexists(path) for path in absent):
        raise RootTransactionError("a lease or operation lock already exists")


def _load_predecessors(paths: EvidencePaths, *, cycle: str, now_epoch: int,
                       required_uid: int) -> tuple[bytes, bytes, str, dict]:
    f2_path = paths.f2_root / f"{cycle}.json"
    f2_raw = _read(f2_path, maximum=MAX_F2_BYTES, required_uid=required_uid)
    f2 = _json(f2_raw, canonical_newline=True)
    if (set(f2) != {"schema", "cycle", "phase", "state", "error_class",
                    "first_failure_phase", "failure_class", "result"}
            or f2.get("schema") != F2_SCHEMA or f2.get("cycle") != cycle
            or f2.get("phase") != "final" or f2.get("state") != "complete"
            or any(f2.get(key) != "" for key in (
                "error_class", "first_failure_phase", "failure_class"))):
        raise RootTransactionError("F2 is not an exact current-cycle success")
    try:
        _validate_projection(f2["result"], cycle)
    except Exception as error:
        raise RootTransactionError("F2 projection is invalid") from error

    f3_raw = _read(paths.f3, maximum=MAX_F3_BYTES, required_uid=required_uid)
    f3 = _json(f3_raw, canonical_newline=False)
    try:
        _cross_bind_archives(f2, f3)
        backup_receipt = verify_f3(
            f3, fixed_proxmox_inventory(), date=cycle.replace("-", "_"),
            now_epoch=now_epoch, resolve=fixed_resolve, lstat=os.lstat)
    except Exception as error:
        raise RootTransactionError("F2/F3 retained evidence is invalid") from error
    return f2_raw, f3_raw, backup_receipt, f3


def collect_fixed_sources(
    *, now_epoch: int, paths: EvidencePaths = EvidencePaths(),
    runner: Callable[[tuple[str, ...], float], tuple[int, str]] = _runner,
    required_uid: int = 0,
) -> CollectedSources:
    local = datetime.fromtimestamp(now_epoch, LOCAL_ZONE)
    cycle = local.strftime("%Y-%m-%d")
    minute = local.hour * 60 + local.minute
    if minute < MINIMUM_MINUTE:
        raise RootTransactionError("post-03:00 backup chain is not yet eligible")
    _require_ready(runner, paths)
    f2_raw, f3_raw, backup_receipt, f3 = _load_predecessors(
        paths, cycle=cycle, now_epoch=now_epoch, required_uid=required_uid)

    adapter = FixedSourceAdapters(runner)
    backup = adapter.backup_from_retained(
        date_prefix=cycle.replace("-", "_"), lease_issued_epoch=now_epoch)
    if backup.integrity_receipt != backup_receipt:
        raise RootTransactionError("fixed backup adapter disagrees with F3")
    row = next((item for item in f3["archives"] if item.get("vmid") == "110"), None)
    if row is None:
        raise RootTransactionError("F3 lacks the fixed LXC110 archive")
    artifact = ArtifactReceipt("110", row["volid"], row["size"], row["ctime"])
    mirror_identity = (
        f"truenas-task-3:{artifact.volid.rsplit('/', 1)[-1]}:"
        f"{artifact.size}:{artifact.ctime}")

    manifest = RuntimeManifest(
        model_sha256=MODEL_SHA256,
        binary_sha256="0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5",
        unit_sha256="a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3",
        auth_marker="auth-metadata-ok",
    )
    observation = collect_observation(
        runner, lease_expires_minute=minute + 15, manifest=manifest,
        clock=lambda: minute, epoch_clock=lambda: now_epoch)
    if observation.heartbeat_alive:
        raise RootTransactionError("whole-host owner heartbeat is unexpectedly live")

    def unchanged() -> bool:
        try:
            current_f2, current_f3, current_receipt, _ = _load_predecessors(
                paths, cycle=cycle, now_epoch=now_epoch,
                required_uid=required_uid)
        except Exception:
            return False
        return (current_f2 == f2_raw and current_f3 == f3_raw
                and current_receipt == backup_receipt)

    return CollectedSources(
        cycle, now_epoch, minute, f2_raw, f3_raw, backup_receipt,
        observation, mirror_identity, unchanged)


def _check_parent(path: Path, required_uid: int) -> None:
    info = path.parent.stat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != required_uid
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise RootTransactionError("evidence parent custody is weak")


def publish(artifacts: TransactionArtifacts, *, paths: EvidencePaths,
            required_uid: int = 0) -> None:
    targets = (
        (paths.f4, artifacts.f4_bytes),
        (paths.f5, artifacts.f5_bytes),
        (paths.admission, artifacts.admission_bytes),
    )
    for path, raw in targets:
        _check_parent(path, required_uid)
        if os.path.lexists(path):
            raise RootTransactionError("an evidence target already exists")
        if not raw or len(raw) > 16 * 1024:
            raise RootTransactionError("an evidence artifact is empty or oversized")

    staged: list[Path] = []
    published: list[Path] = []
    try:
        for path, raw in targets:
            descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            staged_path = Path(temporary); staged.append(staged_path)
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        for (target, _raw), temporary in zip(targets, staged):
            os.link(temporary, target, follow_symlinks=False)
            published.append(target)
            temporary.unlink()
            directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        for target, expected in targets:
            actual = _read(target, maximum=16 * 1024, required_uid=required_uid)
            if actual != expected:
                raise RootTransactionError("published evidence changed")
    except Exception:
        for target in reversed(published):
            try:
                target.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        for temporary in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def produce(
    *, paths: EvidencePaths = EvidencePaths(),
    clock: Callable[[], int] = lambda: int(time.time()),
    nonce_factory: Callable[[], str] = lambda: secrets.token_hex(8),
    collector: Callable[..., CollectedSources] = collect_fixed_sources,
    required_uid: int = 0,
) -> TransactionArtifacts:
    if os.geteuid() != required_uid:
        raise RootTransactionError("root identity is required")
    sources = collector(now_epoch=clock(), paths=paths, required_uid=required_uid)
    artifacts = build_transaction(
        cycle_date=sources.cycle_date, nonce=nonce_factory(),
        observed_epoch=sources.observed_epoch,
        observed_minute=sources.observed_minute,
        f2_bytes=sources.f2_bytes, f3_bytes=sources.f3_bytes,
        backup_receipt=sources.backup_receipt,
        observation=sources.observation,
        lxc110_mirror_identity=sources.lxc110_mirror_identity,
    )
    if not sources.unchanged():
        raise RootTransactionError("predecessor evidence changed during collection")
    publish(artifacts, paths=paths, required_uid=required_uid)
    return artifacts


def main() -> int:
    try:
        result = produce()
    except (EvidenceLoadError, RootTransactionError, OSError, ValueError):
        print(json.dumps({"state": "no_go", "artifacts_written": False}, sort_keys=True))
        return 1
    print(json.dumps({
        "state": "complete", "artifacts_written": True,
        "lease_id": result.lease_id,
        "admission_receipt": result.admission_receipt,
        "f4_sha256": hashlib.sha256(result.f4_bytes).hexdigest(),
        "f5_sha256": hashlib.sha256(result.f5_bytes).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
