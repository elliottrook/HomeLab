import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from state import issue_candidate, load_candidates, store_candidates


class StateTests(unittest.TestCase):
    def test_candidate_is_opaque_and_short_lived(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        candidate = issue_candidate(42, now=now)
        self.assertRegex(candidate.reference, r"^radarr-q-[a-z2-7]{16}$")
        self.assertEqual(candidate.queue_id, 42)
        self.assertEqual((candidate.expires_at - candidate.issued_at).seconds, 300)

    def test_store_round_trip_does_not_add_media_details(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            candidate = issue_candidate(42, now=datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc))
            store_candidates(path, [candidate])
            self.assertEqual(load_candidates(path), {candidate.reference: candidate})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_bad_state_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            path.write_text('{"queue_id":42}', encoding="utf-8")
            self.assertEqual(load_candidates(path), {})

    def test_duplicate_candidate_reference_fails_closed(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        candidate = issue_candidate(42, now=now)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            store_candidates(path, [candidate, candidate])
            self.assertEqual(load_candidates(path), {})

    def test_multiple_distinct_candidates_fail_closed(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        first = issue_candidate(42, now=now)
        second = issue_candidate(43, now=now)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            store_candidates(path, [first, second])
            self.assertEqual(load_candidates(path), {})
