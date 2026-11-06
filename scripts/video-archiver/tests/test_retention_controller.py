"""Bounded controller stops on source holds and stalled real pool reclaim."""

import fcntl
import os
import tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from video_archiver.retention_controller import (
    ActionResult, RetentionSnapshot, RollbackResult, run_retention,
)
from video_archiver.retention_policy import MediaUnit, UserWatch
from video_archiver.retention_years import MovieYearInventory


NOW = datetime(2026, 11, 6, 20, tzinfo=timezone.utc)
USERS = frozenset({'a', 'b'})


def film(provider: str) -> MediaUnit:
    return MediaUnit(
        provider_id=provider, kind='movie', file_count=1,
        current_file_imports=(), first_acquired_at=None,
        fallback_media_date=date(1939, 1, 1), fallback_date_source='movie-release',
        fallback_date_precision='year', legacy_archive_unchanged=True,
        archive_view_verified=True, arr_file_matches=1, jellyfin_file_matches=1,
        watch=(UserWatch('a'), UserWatch('b')), subtitle_manifest_verified=True,
        recovery_ready=True, estimated_pool_reclaim_bytes=15,
        watch_evidence_complete=True, movie_release_year=1939,
        household_notice_at=NOW - timedelta(days=8),
        household_notice_identity_verified=True,
    )


class Backend:
    def __init__(self, allocated=70, count=2, complete=True, reclaim=15):
        self.allocated = allocated
        self.count = count
        self.complete = complete
        self.reclaim = reclaim
        self.units = (film('old'),)
        self.deleted = []
        self.rolled_back = []

    def snapshot(self):
        return RetentionSnapshot(NOW, 100, self.allocated, USERS, self.units,
                                 MovieYearInventory({1939: self.count}, 2, self.count,
                                                    2 - self.count, self.complete))

    def delete_one(self, _snapshot, unit):
        self.deleted.append(unit.provider_id)
        self.units = ()
        self.count -= 1
        self.allocated -= self.reclaim
        return ActionResult(True, True, True, True)

    def rollback_one(self, _snapshot, unit):
        self.rolled_back.append(unit.provider_id)
        return RollbackResult(True, True, True, True)


class ControllerTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.lock = Path(self.temp.name) / 'retention.lock'

    def run_it(self, backend, **kwargs):
        return run_retention(backend, now=NOW, lock_path=self.lock, **kwargs)

    def test_below_trigger_and_dry_run_do_not_delete(self):
        below = Backend(allocated=59)
        self.assertEqual(self.run_it(below).status, 'below_trigger')
        ready = Backend()
        self.assertEqual(self.run_it(ready).status, 'dry_run')
        self.assertEqual(ready.deleted, [])

    def test_last_year_movie_and_incomplete_inventory_fail_closed(self):
        self.assertEqual(self.run_it(Backend(count=1), execute=True).status,
                         'no_safe_candidates')
        self.assertEqual(self.run_it(Backend(complete=False), execute=True).status,
                         'movie_inventory_incomplete')

    def test_one_reclaim_reaches_target(self):
        backend = Backend()
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'target_reached')
        self.assertEqual(result.deleted_provider_ids, ('old',))
        self.assertEqual(result.pool_allocated_bytes, 55)

    def test_snapshot_held_blocks_cascading_deletion(self):
        backend = Backend(reclaim=0)
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'pool_reclaim_stalled_rolled_back')
        self.assertEqual(backend.deleted, ['old'])
        self.assertEqual(backend.rolled_back, ['old'])
        self.assertEqual(result.deleted_provider_ids, ())

    def test_byte_cap_stops_before_action(self):
        backend = Backend()
        result = self.run_it(backend, execute=True, max_estimated_bytes_per_run=14)
        self.assertEqual(result.status, 'byte_cap')
        self.assertEqual(backend.deleted, [])

    def test_time_cap_stops_before_action(self):
        backend = Backend()
        with patch('video_archiver.retention_controller.time.monotonic', side_effect=(0, 2)):
            result = self.run_it(backend, execute=True, max_run_seconds=1)
        self.assertEqual(result.status, 'time_cap')
        self.assertEqual(backend.deleted, [])

    def test_stale_post_delete_inventory_cannot_repeat_action(self):
        class StaleBackend(Backend):
            def delete_one(self, snapshot, unit):
                result = super().delete_one(snapshot, unit)
                self.units = (unit,)
                self.count = 2
                self.allocated = 65
                return result
        backend = StaleBackend()
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'stale_post_delete_inventory')
        self.assertEqual(backend.deleted, ['old'])

    def test_failed_post_delete_check_uses_checkpoint_rollback(self):
        class FailedBackend(Backend):
            def delete_one(self, snapshot, unit):
                super().delete_one(snapshot, unit)
                return ActionResult(True, False, True, True)
        backend = FailedBackend()
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'post_delete_verification_rolled_back')
        self.assertEqual(backend.rolled_back, ['old'])

    def test_action_exception_uses_checkpoint_rollback(self):
        class FailedBackend(Backend):
            def delete_one(self, snapshot, unit):
                super().delete_one(snapshot, unit)
                raise RuntimeError('simulated API timeout after delete')
        backend = FailedBackend()
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'action_error_rolled_back')
        self.assertEqual(backend.rolled_back, ['old'])

    def test_second_run_cannot_take_existing_lock(self):
        descriptor = os.open(self.lock, os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, descriptor)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with self.assertRaisesRegex(RuntimeError, 'holds the lock'):
            self.run_it(Backend(), execute=True)

    def test_stale_source_snapshot_cannot_act(self):
        class StaleBackend(Backend):
            def snapshot(self):
                original = super().snapshot()
                return replace(original, observed_at=NOW - timedelta(minutes=6))
        backend = StaleBackend()
        self.assertEqual(self.run_it(backend, execute=True).status, 'stale_source_snapshot')
        self.assertEqual(backend.deleted, [])

    def test_failed_post_action_pool_read_uses_checkpoint_rollback(self):
        class FailedBackend(Backend):
            def snapshot(self):
                if self.deleted:
                    raise RuntimeError('simulated ZFS query failure')
                return super().snapshot()
        backend = FailedBackend()
        result = self.run_it(backend, execute=True)
        self.assertEqual(result.status, 'pool_check_error_rolled_back')
        self.assertEqual(backend.rolled_back, ['old'])
