"""Durability and fail-closed behavior for source-local retention facts."""

from dataclasses import replace
import shutil
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from video_archiver.retention_ledger import (
    CompleteObservation, ObservedFile, RetentionLedger,
)


NOW = datetime(2026, 11, 6, 20, tzinfo=timezone.utc)
OLD = datetime(2026, 8, 1, 10, tzinfo=timezone.utc)
NEW = datetime(2026, 10, 1, 10, tzinfo=timezone.utc)


def observation(*files: ObservedFile, first=None) -> CompleteObservation:
    return CompleteObservation(
        provider_id="tmdb:101", arr_id=5, kind="movie", observed_at=NOW,
        first_acquired_at=first, fallback_media_date=date(1950, 1, 1),
        fallback_source="movie-release", fallback_precision="year",
        files=files or (ObservedFile(7, "sha256:old", OLD),),
    )


class LedgerTests(TestCase):
    def test_isolated_sqlite_backup_restores_keep_and_notice_binding(self):
        backup = Path(self.temp.name) / "retention-backup.db"
        recovered = Path(self.temp.name) / "retention-restored.db"
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation(first=OLD))
            ledger.propose_notice("tmdb:101", OLD)
            ledger.mark_notice_visible("tmdb:101", NOW, "astertv-visible-1")
            ledger.record_keep("tmdb:101", "user-a", NOW)
            expected_scope = ledger.current_file_scope_digest("tmdb:101")
            with sqlite3.connect(backup) as destination:
                ledger.connection.backup(destination)
        shutil.copyfile(backup, recovered)
        with RetentionLedger(recovered) as ledger:
            self.assertTrue(ledger.has_keep("tmdb:101"))
            self.assertIsNone(ledger.notice_for_current_files("tmdb:101"))
            self.assertEqual(ledger.current_file_scope_digest("tmdb:101"), expected_scope)
            self.assertEqual(ledger.connection.execute(
                "SELECT first_acquired_at FROM units"
            ).fetchone()[0], OLD.isoformat())

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "retention.db"

    def tearDown(self):
        self.temp.cleanup()

    def test_legacy_notice_schema_fails_closed(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE notices(provider_id TEXT,scope_digest TEXT,delivered_at TEXT,delivery_reference TEXT)")
        with self.assertRaisesRegex(RuntimeError, "reviewed migration"):
            RetentionLedger(self.path)

    def test_reopen_retains_first_acquisition_and_original_file_clock(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation(first=OLD))
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation(
                ObservedFile(7, "sha256:old", NEW), first=None,
            ))
            self.assertEqual(
                ledger.connection.execute("SELECT first_acquired_at FROM units").fetchone()[0],
                OLD.isoformat(),
            )
            self.assertEqual(
                ledger.connection.execute("SELECT acquired_at FROM files").fetchone()[0],
                OLD.isoformat(),
            )

    def test_new_file_replaces_clock_without_changing_title_age(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation(first=OLD))
            ledger.record_complete_observation(observation(
                ObservedFile(8, "sha256:new", NEW), first=None,
            ))
            self.assertEqual(
                ledger.connection.execute("SELECT arr_file_id,acquired_at FROM files").fetchall(),
                [(8, NEW.isoformat())],
            )
            self.assertEqual(
                ledger.connection.execute("SELECT first_acquired_at FROM units").fetchone()[0],
                OLD.isoformat(),
            )

    def test_conflict_rolls_back_observation_atomically(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation(first=OLD))
            with self.assertRaisesRegex(ValueError, "content identity"):
                ledger.record_complete_observation(observation(
                    ObservedFile(7, "sha256:changed", NEW), first=None,
                ))
            self.assertEqual(
                ledger.connection.execute("SELECT identity_digest FROM files").fetchone()[0],
                "sha256:old",
            )
            with self.assertRaisesRegex(ValueError, "conflicts"):
                ledger.record_complete_observation(observation(first=NEW))

    def test_stale_scan_and_media_date_change_cannot_rewrite_facts(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation())
            with self.assertRaisesRegex(ValueError, "stale"):
                ledger.record_complete_observation(replace(
                    observation(ObservedFile(8, "sha256:new", OLD)), observed_at=OLD,
                ))
            with self.assertRaisesRegex(ValueError, "media-date fallback conflicts"):
                ledger.record_complete_observation(replace(
                    observation(), fallback_media_date=date(1951, 1, 1),
                ))
            self.assertEqual(ledger.connection.execute("SELECT count(*) FROM files").fetchone()[0], 1)

    def test_incomplete_or_imprecise_fallback_rejected(self):
        with RetentionLedger(self.path) as ledger:
            with self.assertRaisesRegex(ValueError, "complete"):
                ledger.record_complete_observation(replace(observation(), files=()))
            with self.assertRaisesRegex(ValueError, "January 1"):
                ledger.record_complete_observation(replace(
                    observation(), fallback_media_date=date(1950, 6, 1),
                ))
            self.assertEqual(ledger.connection.execute("SELECT count(*) FROM units").fetchone()[0], 0)

    def test_interrupted_action_is_idempotent_after_reopen(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation())
            self.assertEqual(ledger.begin_action("run-1:tmdb:101", "tmdb:101", NOW), "planned")
        with RetentionLedger(self.path) as ledger:
            self.assertEqual(ledger.begin_action("run-1:tmdb:101", "tmdb:101", NOW), "planned")
            with self.assertRaisesRegex(ValueError, "another unit"):
                ledger.begin_action("run-1:tmdb:101", "tmdb:other", NOW)
            ledger.mark_action("run-1:tmdb:101", "cancelled", NOW)
            self.assertEqual(ledger.begin_action("run-1:tmdb:101", "tmdb:101", NOW), "cancelled")
            with self.assertRaisesRegex(ValueError, "already terminal"):
                ledger.mark_action("run-1:tmdb:101", "verified", NOW)

    def test_visible_notice_is_bound_to_current_file_set(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation())
            ledger.propose_notice("tmdb:101", OLD)
            self.assertEqual(ledger.pending_notice_proposals(), ("tmdb:101",))
            self.assertIsNone(ledger.notice_for_current_files("tmdb:101"))
            with self.assertRaisesRegex(ValueError, "predate"):
                ledger.mark_notice_visible("tmdb:101", OLD - timedelta(seconds=1), "bad")
            with self.assertRaisesRegex(ValueError, "visibility reference"):
                ledger.mark_notice_visible("tmdb:101", NOW, "")
            ledger.mark_notice_visible("tmdb:101", NOW, "astertv-visible-1")
            ledger.mark_notice_visible("tmdb:101", NOW, "astertv-visible-1")
            self.assertEqual(ledger.pending_notice_proposals(), ())
            self.assertEqual(ledger.notice_for_current_files("tmdb:101"), NOW)
        with RetentionLedger(self.path) as ledger:
            self.assertEqual(ledger.notice_for_current_files("tmdb:101"), NOW)
            ledger.record_complete_observation(observation(
                ObservedFile(8, "sha256:new", NEW), first=None,
            ))
            self.assertIsNone(ledger.notice_for_current_files("tmdb:101"))
            ledger.propose_notice("tmdb:101", NOW)
            self.assertEqual(ledger.pending_notice_proposals(), ("tmdb:101",))

    def test_keep_persists_across_file_replacement_and_reopen(self):
        with RetentionLedger(self.path) as ledger:
            ledger.record_complete_observation(observation())
            ledger.propose_notice("tmdb:101", OLD)
            ledger.mark_notice_visible("tmdb:101", NOW, "astertv-visible-1")
            with self.assertRaisesRegex(ValueError, "household identity"):
                ledger.record_keep("tmdb:101", "", NOW)
            ledger.record_keep("tmdb:101", "user-a", NOW)
            ledger.record_keep("tmdb:101", "user-a", NOW)
            self.assertIsNone(ledger.notice_for_current_files("tmdb:101"))
            self.assertEqual(ledger.pending_notice_proposals(), ())
            ledger.record_complete_observation(observation(
                ObservedFile(8, "sha256:new", NEW), first=None,
            ))
        with RetentionLedger(self.path) as ledger:
            self.assertTrue(ledger.has_keep("tmdb:101"))
            self.assertEqual(ledger.connection.execute("SELECT count(*) FROM keeps").fetchone()[0], 1)
