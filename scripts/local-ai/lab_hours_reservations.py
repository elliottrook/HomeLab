"""Root-custodied, atomic reservations for exclusive B60 Lab Hours."""

from __future__ import annotations

import fcntl
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{7,63}")
ACTIVE = {"scheduled", "claimed"}
TERMINAL = {"complete", "failed", "cancelled"}
REGISTERED_WORKLOADS = {"accepted-9b-direct-control-smoke-v1",
                        "accepted-9b-owner-loss-exercise-v1"}
MAX_SECONDS = 90 * 60
MIN_SECONDS = 5 * 60
RESTORE_BUFFER_SECONDS = 15 * 60


class ReservationError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class ReservationStore:
    def __init__(self, root: Path, *, expected_uid: int | None = None,
                 clock=time.time):
        self.root = root
        self.expected_uid = os.geteuid() if expected_uid is None else expected_uid
        self.clock = clock
        self.records = root / "records"
        self.lock_path = root / "reservations.lock"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.records.mkdir(exist_ok=True, mode=0o700)
        for path in (self.root, self.records):
            st = path.lstat()
            if not path.is_dir() or path.is_symlink() or st.st_uid != self.expected_uid:
                raise ReservationError("reservation directory custody is invalid")
            os.chmod(path, 0o700)

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.ensure()
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            st = os.fstat(fd)
            if st.st_uid != self.expected_uid or st.st_nlink != 1:
                raise ReservationError("reservation lock custody is invalid")
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def _path(self, booking_id: str) -> Path:
        if not ID_RE.fullmatch(booking_id):
            raise ReservationError("booking id is not canonical")
        return self.records / f"{booking_id}.json"

    def _read_unlocked(self, path: Path) -> dict[str, object]:
        st = path.lstat()
        if (not path.is_file() or path.is_symlink() or st.st_uid != self.expected_uid
                or st.st_nlink != 1 or st.st_mode & 0o777 != 0o600 or st.st_size > 16_384):
            raise ReservationError("reservation record custody is invalid")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schema") != "aster-lab-hours-reservation.v1":
            raise ReservationError("reservation record is malformed")
        return value

    def _all_unlocked(self) -> list[dict[str, object]]:
        values = []
        for path in sorted(self.records.glob("*.json")):
            values.append(self._read_unlocked(path))
        return values

    def _write_unlocked(self, value: dict[str, object]) -> None:
        path = self._path(str(value["booking_id"]))
        tmp = path.with_suffix(f".tmp-{os.getpid()}")
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        try:
            data = _canonical(value)
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, path)
        dir_fd = os.open(self.records, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def reserve(self, *, booking_id: str, owner: str, workload: str,
                start_epoch: int, end_epoch: int) -> dict[str, object]:
        now = int(self.clock())
        if not ID_RE.fullmatch(booking_id) or not ID_RE.fullmatch(owner):
            raise ReservationError("booking or owner identity is not canonical")
        if workload not in REGISTERED_WORKLOADS:
            raise ReservationError("workload is not registered")
        if type(start_epoch) is not int or type(end_epoch) is not int:
            raise ReservationError("reservation times must be integer epochs")
        if start_epoch < now or not MIN_SECONDS <= end_epoch - start_epoch <= MAX_SECONDS:
            raise ReservationError("reservation is stale or outside the duration bound")
        with self.locked():
            path = self._path(booking_id)
            if path.exists():
                raise ReservationError("booking id already exists")
            for other in self._all_unlocked():
                state = other.get("state")
                if state in ACTIVE:
                    left = int(other["start_epoch"]) - RESTORE_BUFFER_SECONDS
                    right = int(other["end_epoch"]) + RESTORE_BUFFER_SECONDS
                elif state in {"complete", "failed"} and type(other.get("finished_epoch")) is int:
                    left = int(other["start_epoch"])
                    right = int(other["finished_epoch"]) + RESTORE_BUFFER_SECONDS
                else:
                    continue
                if start_epoch < right and end_epoch > left:
                    raise ReservationError(f"reservation conflicts with {other['booking_id']}")
            value: dict[str, object] = {
                "schema": "aster-lab-hours-reservation.v1", "booking_id": booking_id,
                "owner": owner, "workload": workload, "start_epoch": start_epoch,
                "end_epoch": end_epoch, "state": "scheduled", "created_epoch": now,
                "restore_buffer_seconds": RESTORE_BUFFER_SECONDS,
            }
            self._write_unlocked(value)
            return value

    def list(self) -> list[dict[str, object]]:
        with self.locked():
            return self._all_unlocked()

    def get(self, booking_id: str) -> dict[str, object]:
        with self.locked():
            path = self._path(booking_id)
            if not path.exists():
                raise ReservationError("booking does not exist")
            return self._read_unlocked(path)

    def due(self, *, grace_seconds: int = 120) -> list[dict[str, object]]:
        now = int(self.clock())
        with self.locked():
            return [v for v in self._all_unlocked()
                    if v.get("state") == "scheduled"
                    and int(v["start_epoch"]) <= now <= int(v["start_epoch"]) + grace_seconds]

    def claim(self, booking_id: str, *, claimant: str) -> dict[str, object]:
        now = int(self.clock())
        with self.locked():
            value = self._read_unlocked(self._path(booking_id))
            if value.get("state") != "scheduled":
                raise ReservationError("booking is not schedulable")
            if not int(value["start_epoch"]) <= now <= int(value["start_epoch"]) + 120:
                raise ReservationError("booking is outside its claim window")
            if not ID_RE.fullmatch(claimant):
                raise ReservationError("claimant is not canonical")
            value.update(state="claimed", claimant=claimant, claimed_epoch=now)
            self._write_unlocked(value)
            return value

    def finish(self, booking_id: str, *, claimant: str, success: bool,
               result_code: str) -> dict[str, object]:
        if not re.fullmatch(r"[A-Z0-9_:-]{2,96}", result_code):
            raise ReservationError("result code is not bounded")
        with self.locked():
            value = self._read_unlocked(self._path(booking_id))
            if value.get("state") != "claimed" or value.get("claimant") != claimant:
                raise ReservationError("booking claim identity does not match")
            value.update(state="complete" if success else "failed",
                         finished_epoch=int(self.clock()), result_code=result_code)
            self._write_unlocked(value)
            return value

    def cancel(self, booking_id: str) -> dict[str, object]:
        with self.locked():
            value = self._read_unlocked(self._path(booking_id))
            if value.get("state") != "scheduled":
                raise ReservationError("only scheduled bookings can be cancelled")
            value.update(state="cancelled", finished_epoch=int(self.clock()),
                         result_code="CANCELLED")
            self._write_unlocked(value)
            return value

    def check_window(self, *, start_epoch: int, end_epoch: int) -> list[str]:
        with self.locked():
            conflicts=[]
            for value in self._all_unlocked():
                if value.get("state") in ACTIVE:
                    left=int(value["start_epoch"])-RESTORE_BUFFER_SECONDS
                    right=int(value["end_epoch"])+RESTORE_BUFFER_SECONDS
                elif value.get("state") in {"complete", "failed"} and type(value.get("finished_epoch")) is int:
                    left=int(value["start_epoch"])
                    right=int(value["finished_epoch"])+RESTORE_BUFFER_SECONDS
                else: continue
                if start_epoch < right and end_epoch > left:
                    conflicts.append(str(value["booking_id"]))
            return conflicts
