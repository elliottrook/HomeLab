"""Bounded retention run loop, independent of live service adapters.

The backend owns a fresh, atomic pre-delete recheck, protected checkpoint,
ARR action journal and post-delete truth check. This module never deletes a
file itself. A plan is advisory and is rebuilt before every candidate.
"""

from __future__ import annotations

import fcntl
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

from .retention_policy import MediaUnit, plan_retention
from .retention_years import MovieYearInventory


@dataclass(frozen=True)
class RetentionSnapshot:
    observed_at: datetime
    pool_size_bytes: int
    pool_allocated_bytes: int
    expected_user_ids: frozenset[str]
    units: tuple[MediaUnit, ...]
    movie_year_inventory: MovieYearInventory


@dataclass(frozen=True)
class ActionResult:
    arr_unmonitored: bool
    physical_files_absent: bool
    jellyfin_items_absent: bool
    journal_verified: bool

    @property
    def complete(self) -> bool:
        return (self.arr_unmonitored and self.physical_files_absent
                and self.jellyfin_items_absent and self.journal_verified)


@dataclass(frozen=True)
class RollbackResult:
    files_present_and_equal: bool
    arr_monitored_with_files: bool
    jellyfin_visible_with_watch_unchanged: bool
    journal_rolled_back: bool

    @property
    def complete(self) -> bool:
        return (self.files_present_and_equal and self.arr_monitored_with_files
                and self.jellyfin_visible_with_watch_unchanged
                and self.journal_rolled_back)


class RetentionBackend(Protocol):
    def snapshot(self) -> RetentionSnapshot: ...

    def delete_one(self, expected: RetentionSnapshot, unit: MediaUnit) -> ActionResult:
        """Atomically recheck facts and recovery, then perform one ARR deletion."""
        ...

    def rollback_one(self, expected: RetentionSnapshot, unit: MediaUnit) -> RollbackResult:
        """Restore protected bytes, ARR and Jellyfin state from the checkpoint."""
        ...


@dataclass(frozen=True)
class RunResult:
    status: str
    deleted_provider_ids: tuple[str, ...]
    pool_allocated_bytes: int
    upper_guardrail_exceeded: bool


def _lock(path: Path) -> int:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise RuntimeError("another retention run holds the lock")
    return fd


def _restore(backend: RetentionBackend, snapshot: RetentionSnapshot,
             unit: MediaUnit) -> bool:
    try:
        return backend.rollback_one(snapshot, unit).complete
    except Exception:
        return False


def run_retention(
    backend: RetentionBackend, *, now: datetime, lock_path: Path,
    execute: bool = False, max_units_per_run: int = 2,
    max_estimated_bytes_per_run: int = 20_000_000_000,
    min_reclaim_fraction: float = 0.25,
    minimum_grace_days: int = 3,
    max_run_seconds: int = 1800,
) -> RunResult:
    """Run a capped, sequential batch or report a dry-run/safe-failure status."""
    if max_units_per_run <= 0 or max_estimated_bytes_per_run <= 0:
        raise ValueError("positive run caps are required")
    if not 0 < min_reclaim_fraction <= 1:
        raise ValueError("invalid reclaim threshold")
    if type(max_run_seconds) is not int or max_run_seconds <= 0:
        raise ValueError("positive run time cap is required")
    fd = _lock(lock_path)
    try:
        deadline = time.monotonic() + max_run_seconds
        deleted: list[str] = []
        spent_estimate = 0
        while True:
            snapshot = backend.snapshot()
            if (snapshot.observed_at.tzinfo is None
                    or snapshot.observed_at.utcoffset() is None
                    or abs(now - snapshot.observed_at) > timedelta(minutes=5)):
                return RunResult("stale_source_snapshot", tuple(deleted),
                                 snapshot.pool_allocated_bytes, False)
            plan = plan_retention(
                snapshot.units, now=now,
                expected_user_ids=snapshot.expected_user_ids,
                pool_size_bytes=snapshot.pool_size_bytes,
                pool_allocated_bytes=snapshot.pool_allocated_bytes,
                movie_year_counts=snapshot.movie_year_inventory.counts,
                minimum_grace_days=minimum_grace_days,
            )
            if not plan.triggered:
                status = "target_reached" if deleted else "below_trigger"
                return RunResult(status, tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            if not snapshot.movie_year_inventory.complete_source_scan:
                return RunResult("movie_inventory_incomplete", tuple(deleted),
                                 snapshot.pool_allocated_bytes, plan.upper_guardrail_exceeded)
            if not plan.selected_provider_ids:
                return RunResult("no_safe_candidates", tuple(deleted),
                                 snapshot.pool_allocated_bytes, plan.upper_guardrail_exceeded)
            if not execute:
                return RunResult("dry_run", tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            if time.monotonic() >= deadline:
                return RunResult("time_cap", tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            if len(deleted) >= max_units_per_run:
                return RunResult("unit_cap", tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            selected = plan.selected_provider_ids[0]
            if selected in deleted:
                return RunResult("stale_post_delete_inventory", tuple(deleted),
                                 snapshot.pool_allocated_bytes, plan.upper_guardrail_exceeded)
            matches = [unit for unit in snapshot.units if unit.provider_id == selected]
            if len(matches) != 1:
                return RunResult("identity_changed", tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            unit = matches[0]
            if spent_estimate + unit.estimated_pool_reclaim_bytes > max_estimated_bytes_per_run:
                return RunResult("byte_cap", tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            # The backend must perform its own fresh pre-delete check. The
            # snapshot-to-action boundary is not atomic in this controller.
            try:
                result = backend.delete_one(snapshot, unit)
            except Exception:
                restored = _restore(backend, snapshot, unit)
                return RunResult("action_error_rolled_back" if restored else "rollback_failed",
                                 tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            if not result.complete:
                restored = _restore(backend, snapshot, unit)
                status = "post_delete_verification_rolled_back" if restored else "rollback_failed"
                return RunResult(status, tuple(deleted),
                                 snapshot.pool_allocated_bytes, plan.upper_guardrail_exceeded)
            deleted.append(selected)
            spent_estimate += unit.estimated_pool_reclaim_bytes
            try:
                after = backend.snapshot()
            except Exception:
                restored = _restore(backend, snapshot, unit)
                if restored:
                    deleted.pop()
                return RunResult("pool_check_error_rolled_back" if restored else "rollback_failed",
                                 tuple(deleted), snapshot.pool_allocated_bytes,
                                 plan.upper_guardrail_exceeded)
            actual_reclaim = snapshot.pool_allocated_bytes - after.pool_allocated_bytes
            if actual_reclaim < unit.estimated_pool_reclaim_bytes * min_reclaim_fraction:
                restored = _restore(backend, snapshot, unit)
                if restored:
                    deleted.pop()
                status = "pool_reclaim_stalled_rolled_back" if restored else "rollback_failed"
                return RunResult(status, tuple(deleted),
                                 after.pool_allocated_bytes,
                                 100 * after.pool_allocated_bytes >= 62 * after.pool_size_bytes)
    finally:
        os.close(fd)
