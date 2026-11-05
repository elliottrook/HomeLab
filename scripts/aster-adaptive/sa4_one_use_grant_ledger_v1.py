"""Durable fail-closed one-use consumption ledger for a future SA4 grant.

This module does not authenticate a grant and never authorizes an effect.  It
only prevents an already authenticated exact grant from being claimed twice.
Every terminal outcome burns the claim; there is no reset or retry transition.
"""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path
import re
import stat as stat_module
from typing import Iterator


SCHEMA = "aster-sa4-one-use-grant-ledger.v1"
HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
TERMINAL = frozenset({"consumed", "failed", "uncertain"})
MAX_LIFETIME_SECONDS = 3600
MAX_CLAIM_SECONDS = 900
MAX_RECORD_BYTES = 16_384


class LedgerError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _identity(value: object) -> bool:
    return isinstance(value, str) and bool(IDENTITY.fullmatch(value))


def _digest(value: object) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


class OneUseLedger:
    """Atomic exact-grant ledger with an intentionally closed state graph."""

    def __init__(self, root: Path, *, expected_uid: int = 0):
        self.root = Path(root)
        self.records = self.root / "records"
        self.lock_path = self.root / "ledger.lock"
        self.expected_uid = expected_uid

    def _directory(self, path: Path) -> None:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        stat = path.lstat()
        if (not path.is_dir() or path.is_symlink()
                or stat.st_uid != self.expected_uid
                or stat.st_mode & 0o777 != 0o700):
            raise LedgerError("SA4 ledger directory custody is invalid")

    def ensure(self) -> None:
        self._directory(self.root)
        self._directory(self.records)

    def _path(self, grant_id: str) -> Path:
        if not _identity(grant_id):
            raise LedgerError("SA4 grant identity is not canonical")
        return self.records / f"{grant_id}.json"

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.ensure()
        descriptor = os.open(
            self.lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            stat = os.fstat(descriptor)
            if (stat.st_uid != self.expected_uid or stat.st_nlink != 1
                    or stat.st_mode & 0o777 != 0o600):
                raise LedgerError("SA4 ledger lock custody is invalid")
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)

    def _read_unlocked(self, path: Path) -> dict[str, object]:
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        except OSError as exc:
            raise LedgerError("SA4 ledger record cannot be opened safely") from exc
        try:
            stat = os.fstat(descriptor)
            if (not stat_module.S_ISREG(stat.st_mode)
                    or stat.st_uid != self.expected_uid
                    or stat.st_nlink != 1 or stat.st_mode & 0o777 != 0o600
                    or not 1 <= stat.st_size <= MAX_RECORD_BYTES):
                raise LedgerError("SA4 ledger record custody is invalid")
            chunks = []
            remaining = stat.st_size
            while remaining:
                chunk = os.read(descriptor, remaining)
                if not chunk:
                    raise LedgerError("SA4 ledger record read was incomplete")
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(descriptor)
        try:
            pairs: list[tuple[str, object]] = json.loads(
                raw.decode("utf-8"), object_pairs_hook=lambda values: values)
            value: dict[str, object] = {}
            for key, item in pairs:
                if key in value:
                    raise LedgerError("SA4 ledger record has duplicate keys")
                value[key] = item
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            if isinstance(exc, LedgerError):
                raise
            raise LedgerError("SA4 ledger record is malformed") from exc
        if raw != canonical(value):
            raise LedgerError("SA4 ledger record is not canonical")
        self._validate_record(value)
        return value

    def _write_unlocked(self, path: Path, value: dict[str, object]) -> None:
        data = canonical(value)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            descriptor = os.open(
                temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                | os.O_NOFOLLOW, 0o600)
            try:
                os.write(descriptor, data)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temporary, path)
            directory = os.open(self.records, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except BaseException:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _validate_record(value: object) -> None:
        base = {"schema", "grant_id", "plan_sha256", "grant_sha256",
                "target_sha256", "created_epoch", "expires_epoch", "state",
                "use_count", "automatic_retry", "authority",
                "effect_authorized"}
        if not isinstance(value, dict) or not base.issubset(value):
            raise LedgerError("SA4 ledger record shape changed")
        state = value.get("state")
        expected = set(base)
        if state == "claimed":
            expected |= {"claimant", "claimed_epoch", "claim_deadline_epoch"}
        elif state in TERMINAL:
            expected |= {"claimant", "claimed_epoch", "claim_deadline_epoch",
                         "finished_epoch", "evidence_sha256"}
        elif state != "ready":
            raise LedgerError("SA4 ledger state changed")
        if (set(value) != expected or value["schema"] != SCHEMA
                or not _identity(value["grant_id"])
                or any(not _digest(value[name]) for name in (
                    "plan_sha256", "grant_sha256", "target_sha256"))
                or type(value["created_epoch"]) is not int
                or type(value["expires_epoch"]) is not int
                or not value["created_epoch"] < value["expires_epoch"]
                or value["expires_epoch"] - value["created_epoch"]
                > MAX_LIFETIME_SECONDS
                or value["use_count"] not in {0, 1}
                or value["use_count"] != (0 if state == "ready" else 1)
                or value["automatic_retry"] is not False
                or value["authority"] != "one-use-ledger-only"
                or value["effect_authorized"] is not False):
            raise LedgerError("SA4 ledger record binding changed")
        if state != "ready":
            if (not _identity(value["claimant"])
                    or type(value["claimed_epoch"]) is not int
                    or type(value["claim_deadline_epoch"]) is not int
                    or not value["created_epoch"] <= value["claimed_epoch"]
                    < value["claim_deadline_epoch"] <= value["expires_epoch"]
                    or value["claim_deadline_epoch"] - value["claimed_epoch"]
                    > MAX_CLAIM_SECONDS):
                raise LedgerError("SA4 ledger claim binding changed")
        if state in TERMINAL and (
                type(value["finished_epoch"]) is not int
                or value["finished_epoch"] < value["claimed_epoch"]
                or not _digest(value["evidence_sha256"])):
            raise LedgerError("SA4 ledger terminal binding changed")

    def initialize(self, *, grant_id: str, plan_sha256: str, grant_sha256: str,
                   target_sha256: str, now_epoch: int,
                   expires_epoch: int) -> dict[str, object]:
        value = {"schema": SCHEMA, "grant_id": grant_id,
                 "plan_sha256": plan_sha256, "grant_sha256": grant_sha256,
                 "target_sha256": target_sha256,
                 "created_epoch": now_epoch, "expires_epoch": expires_epoch,
                 "state": "ready", "use_count": 0,
                 "automatic_retry": False,
                 "authority": "one-use-ledger-only",
                 "effect_authorized": False}
        self._validate_record(value)
        with self.locked():
            path = self._path(grant_id)
            if os.path.lexists(path):
                raise LedgerError("SA4 grant record already exists")
            self._write_unlocked(path, value)
        return dict(value)

    def get(self, grant_id: str) -> dict[str, object]:
        with self.locked():
            return dict(self._read_unlocked(self._path(grant_id)))

    def claim(self, grant_id: str, *, claimant: str, now_epoch: int,
              deadline_epoch: int) -> dict[str, object]:
        with self.locked():
            path = self._path(grant_id)
            value = self._read_unlocked(path)
            if (value["state"] != "ready" or not _identity(claimant)
                    or type(now_epoch) is not int or type(deadline_epoch) is not int
                    or now_epoch < value["created_epoch"]
                    or now_epoch >= value["expires_epoch"]
                    or not now_epoch < deadline_epoch <= value["expires_epoch"]
                    or deadline_epoch - now_epoch > MAX_CLAIM_SECONDS):
                raise LedgerError("SA4 one-use grant cannot be claimed")
            value.update(state="claimed", use_count=1, claimant=claimant,
                         claimed_epoch=now_epoch,
                         claim_deadline_epoch=deadline_epoch)
            self._validate_record(value)
            self._write_unlocked(path, value)
            return dict(value)

    def finish(self, grant_id: str, *, claimant: str, state: str,
               evidence_sha256: str, now_epoch: int) -> dict[str, object]:
        if state not in TERMINAL:
            raise LedgerError("SA4 terminal state is invalid")
        with self.locked():
            path = self._path(grant_id)
            value = self._read_unlocked(path)
            if (value["state"] != "claimed" or value["claimant"] != claimant
                    or type(now_epoch) is not int
                    or now_epoch < value["claimed_epoch"]
                    or (state == "consumed"
                        and now_epoch > value["claim_deadline_epoch"])
                    or not _digest(evidence_sha256)):
                raise LedgerError("SA4 claimed grant cannot be finished")
            value.update(state=state, finished_epoch=now_epoch,
                         evidence_sha256=evidence_sha256)
            self._validate_record(value)
            self._write_unlocked(path, value)
            return dict(value)

    def fence_expired_claim(self, grant_id: str, *, now_epoch: int,
                            evidence_sha256: str) -> dict[str, object]:
        """Burn an abandoned claim as uncertain; never makes it reusable."""
        with self.locked():
            path = self._path(grant_id)
            value = self._read_unlocked(path)
            if (value["state"] != "claimed" or type(now_epoch) is not int
                    or now_epoch <= value["claim_deadline_epoch"]
                    or not _digest(evidence_sha256)):
                raise LedgerError("SA4 claim is not fenceable")
            value.update(state="uncertain", finished_epoch=now_epoch,
                         evidence_sha256=evidence_sha256)
            self._validate_record(value)
            self._write_unlocked(path, value)
            return dict(value)
