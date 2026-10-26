from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.catalog import SourceFingerprint
from epub_narration.state import QueueStore


class StateTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

