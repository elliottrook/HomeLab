"""Own the real shared lock and operator emergency-stop state for SA4."""
from __future__ import annotations

import fcntl
import hashlib
import os
import stat

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


LOCAL_HOST_ID = "unconfigured"
EXPECTED_UID = 0
EXPECTED_GID = 0
LOCK_PATH = "/run/aster-sa4-operation.lock"
LOCK_EVIDENCE_PATH = "/run/aster-sa4-operation.lock"
STOP_PATH = "/run/aster-sa4-emergency-stop"


class RuntimeControlOwner:
    def __init__(self, plan_raw: bytes):
        plan = contract.validate_plan(plan_raw)
        target = registry.resolve_production(plan["target_id"])
        if target.host_id != LOCAL_HOST_ID:
            raise ValueError("SA4 runtime controls are not live-host bound")
        self.plan = plan
        self.plan_sha256 = hashlib.sha256(plan_raw).hexdigest()
        self.lock_fd = -1
        self.stop_fd = -1
        self.lock_identity: tuple[int, int] | None = None
        self.stop_identity: tuple[int, int] | None = None

    def _create(self, path: str) -> int:
        descriptor = os.open(
            path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        metadata = os.fstat(descriptor)
        if (not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != EXPECTED_UID or metadata.st_gid != EXPECTED_GID
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_nlink != 1):
            os.close(descriptor)
            raise ValueError("SA4 runtime-control custody changed")
        return descriptor

    def acquire(self) -> None:
        if self.lock_fd >= 0 or self.stop_fd >= 0:
            raise ValueError("SA4 runtime controls cannot be reacquired")
        try:
            self.lock_fd = self._create(LOCK_PATH)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_raw = contract.canonical({
                "schema": "aster-sa4-operation-lock.v1",
                "plan_id": self.plan["plan_id"],
                "plan_sha256": self.plan_sha256})
            os.write(self.lock_fd, lock_raw); os.fsync(self.lock_fd)
            self.stop_fd = self._create(STOP_PATH)
            stop_raw = contract.canonical({
                "schema": "aster-sa4-emergency-stop.v1",
                "plan_id": self.plan["plan_id"],
                "plan_sha256": self.plan_sha256, "state": "armed"})
            os.write(self.stop_fd, stop_raw); os.fsync(self.stop_fd)
            lock_stat = os.fstat(self.lock_fd); stop_stat = os.fstat(self.stop_fd)
            self.lock_identity = (lock_stat.st_dev, lock_stat.st_ino)
            self.stop_identity = (stop_stat.st_dev, stop_stat.st_ino)
            self.ensure_armed()
        except BaseException:
            self.retain_uncertain()
            raise

    @staticmethod
    def _read(descriptor: int) -> bytes:
        os.lseek(descriptor, 0, os.SEEK_SET)
        raw = os.read(descriptor, 4097)
        if len(raw) > 4096 or os.read(descriptor, 1):
            raise ValueError("SA4 runtime-control state is oversized")
        return raw

    def ensure_armed(self) -> None:
        if self.lock_fd < 0 or self.stop_fd < 0:
            raise ValueError("SA4 runtime controls are not held")
        lock_path = os.lstat(LOCK_PATH); stop_path = os.lstat(STOP_PATH)
        lock_stat = os.fstat(self.lock_fd); stop_stat = os.fstat(self.stop_fd)
        if ((lock_stat.st_dev, lock_stat.st_ino) != self.lock_identity
                or (stop_stat.st_dev, stop_stat.st_ino) != self.stop_identity
                or (lock_path.st_dev, lock_path.st_ino) != self.lock_identity
                or (stop_path.st_dev, stop_path.st_ino) != self.stop_identity):
            raise ValueError("SA4 runtime-control path identity changed")
        expected_lock = contract.canonical({
            "schema": "aster-sa4-operation-lock.v1",
            "plan_id": self.plan["plan_id"],
            "plan_sha256": self.plan_sha256})
        expected_stop = contract.canonical({
            "schema": "aster-sa4-emergency-stop.v1",
            "plan_id": self.plan["plan_id"],
            "plan_sha256": self.plan_sha256, "state": "armed"})
        if (self._read(self.lock_fd) != expected_lock
                or self._read(self.stop_fd) != expected_stop):
            raise ValueError("SA4 emergency stop is not armed")

    def observe(self, observed_epoch: int) -> bytes:
        self.ensure_armed()
        if type(observed_epoch) is not int or observed_epoch <= 0:
            raise ValueError("SA4 runtime-control epoch changed")
        return contract.canonical({
            "schema": "aster-sa4-live-runtime-controls.v1",
            "plan_sha256": self.plan_sha256,
            "observed_epoch": observed_epoch,
            "shared_operation_lock": "held", "lock_path": LOCK_EVIDENCE_PATH,
            "lock_owner": self.plan["plan_id"],
            "lock_regular_file": True, "lock_link_count": 1,
            "emergency_stop": "armed",
            "emergency_stop_owner": self.plan["plan_id"],
            "automatic_retry": False, "automatic_routing": "off"})

    def retain_uncertain(self) -> None:
        for descriptor in (self.stop_fd, self.lock_fd):
            if descriptor >= 0:
                try: os.close(descriptor)
                except OSError: pass
        self.stop_fd = self.lock_fd = -1

    def release_terminal(self) -> None:
        self.ensure_armed()
        for path, identity in ((STOP_PATH, self.stop_identity),
                               (LOCK_PATH, self.lock_identity)):
            metadata = os.lstat(path)
            if (metadata.st_dev, metadata.st_ino) != identity:
                raise ValueError("SA4 runtime-control cleanup identity changed")
        os.unlink(STOP_PATH); os.unlink(LOCK_PATH)
        os.close(self.stop_fd); os.close(self.lock_fd)
        self.stop_fd = self.lock_fd = -1
