from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.catalog import SourceFingerprint
from epub_narration.state import QueueStore


class StateTests(unittest.TestCase):
    def test_uses_nfs_safe_rollback_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            with closing(sqlite3.connect(store.path)) as connection:
                mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual("delete", mode)

    def test_reconcile_is_idempotent_and_changed_source_is_new_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "state" / "queue.db")
            store.initialize()
            one = SourceFingerprint(7, "a" * 64, 100, 1)
            changed = SourceFingerprint(7, "b" * 64, 101, 2)
            self.assertEqual(1, store.reconcile((one,), "contract-1"))
            self.assertEqual(0, store.reconcile((one,), "contract-1"))
            self.assertEqual(1, store.reconcile((changed,), "contract-1"))
            self.assertEqual("queued", store.state(7, "a" * 64, "contract-1"))
            self.assertEqual("queued", store.state(7, "b" * 64, "contract-1"))

    def test_allows_only_explicit_state_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            source = SourceFingerprint(3, "c" * 64, 1, 1)
            store.reconcile((source,), "contract-1")
            with self.assertRaisesRegex(ValueError, "generation-transition"):
                store.transition(3, "c" * 64, "contract-1", "ready")
            store.transition(3, "c" * 64, "contract-1", "extracting")
            store.transition(3, "c" * 64, "contract-1", "narrating")
            store.transition(3, "c" * 64, "contract-1", "aligning")
            store.transition(3, "c" * 64, "contract-1", "ready")
            self.assertEqual("ready", store.state(3, "c" * 64, "contract-1"))

    def test_failure_requires_bounded_error_code_and_explicit_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            source = SourceFingerprint(4, "d" * 64, 1, 1)
            store.reconcile((source,), "contract-1")
            with self.assertRaisesRegex(ValueError, "generation-failure-code"):
                store.transition(4, "d" * 64, "contract-1", "failed")
            with self.assertRaisesRegex(ValueError, "generation-failure-code"):
                store.transition(4, "d" * 64, "contract-1", "failed", "private title here")
            store.transition(4, "d" * 64, "contract-1", "failed", "epub-invalid")
            store.transition(4, "d" * 64, "contract-1", "queued")
            self.assertEqual("queued", store.state(4, "d" * 64, "contract-1"))

    def test_claim_and_interruption_recovery_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            source = SourceFingerprint(9, "e" * 64, 100, 1)
            store.reconcile((source,), "contract-1")
            first = store.claim_next("contract-1", max_attempts=2)
            self.assertIsNotNone(first)
            store.transition(9, "e" * 64, "contract-1", "narrating")
            self.assertEqual((first.attempt_id,), store.recover_interrupted("contract-1", 2))
            self.assertEqual("queued", store.state(9, "e" * 64, "contract-1"))
            second = store.claim_next("contract-1", max_attempts=2)
            self.assertNotEqual(first.attempt_id, second.attempt_id)
            self.assertEqual((second.attempt_id,), store.recover_interrupted("contract-1", 2))
            self.assertEqual("failed", store.state(9, "e" * 64, "contract-1"))

    def test_counts_and_oldest_queue_age_are_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            store.reconcile((SourceFingerprint(10, "f" * 64, 10, 1),), "contract-1")
            self.assertEqual(1, store.counts("contract-1")["queued"])
            self.assertGreaterEqual(store.oldest_queued_age("contract-1"), 0)

    def test_retry_is_failure_class_scoped_and_attempt_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = QueueStore(Path(tmp) / "queue.db")
            store.initialize()
            source = SourceFingerprint(11, "1" * 64, 10, 1)
            store.reconcile((source,), "contract-1")
            store.transition(11, "1" * 64, "contract-1", "extracting")
            store.transition(11, "1" * 64, "contract-1", "failed", "quota")
            self.assertEqual(0, store.retry_failed("contract-1", "publish", 3))
            self.assertEqual(1, store.retry_failed("contract-1", "quota", 3))
            self.assertEqual("queued", store.state(11, "1" * 64, "contract-1"))
            store.transition(11, "1" * 64, "contract-1", "extracting")
            store.transition(11, "1" * 64, "contract-1", "failed", "quota")
            self.assertEqual(0, store.retry_failed("contract-1", "quota", 2))
            with self.assertRaisesRegex(ValueError, "retry-policy"):
                store.retry_failed("contract-1", "private-title", 3)


if __name__ == "__main__":
    unittest.main()

