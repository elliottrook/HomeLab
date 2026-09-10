import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import issue_candidate
from issue_candidate import eligible_queue_id


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


class IssuerTests(unittest.TestCase):
    def test_only_old_completed_imported_or_ignored_records_qualify(self):
        payload = {
            "records": [
                {"id": 1, "status": "completed", "trackedDownloadState": "imported", "added": (NOW - timedelta(minutes=59)).isoformat()},
                {"id": 2, "status": "downloading", "trackedDownloadState": "downloading", "added": (NOW - timedelta(hours=2)).isoformat()},
                {"id": 3, "status": "completed", "trackedDownloadState": "imported", "added": (NOW - timedelta(hours=2)).isoformat()},
            ]
        }
        self.assertEqual(eligible_queue_id(payload, now=NOW), 3)

    def test_malformed_or_ambiguous_payload_has_no_candidate(self):
        self.assertIsNone(eligible_queue_id({}, now=NOW))
        self.assertIsNone(
            eligible_queue_id({"records": [{"id": 42, "status": "completed", "trackedDownloadState": "failed", "added": "bad"}]}, now=NOW)
        )

    def test_multiple_eligible_records_are_ambiguous_and_issue_nothing(self):
        old = (NOW - timedelta(hours=2)).isoformat()
        payload = {
            "records": [
                {"id": 3, "status": "completed", "trackedDownloadState": "imported", "added": old},
                {"id": 4, "status": "completed", "trackedDownloadState": "ignored", "added": old},
            ]
        }
        self.assertIsNone(eligible_queue_id(payload, now=NOW))

    def test_future_naive_and_boolean_records_are_refused(self):
        for queue_id, added in (
            (True, (NOW - timedelta(hours=2)).isoformat()),
            (3, (NOW + timedelta(seconds=1)).isoformat()),
            (3, "2026-09-09T10:00:00"),
        ):
            with self.subTest(queue_id=queue_id, added=added):
                payload = {
                    "records": [
                        {
                            "id": queue_id,
                            "status": "completed",
                            "trackedDownloadState": "imported",
                            "added": added,
                        }
                    ]
                }
                self.assertIsNone(eligible_queue_id(payload, now=NOW))

    def test_successful_empty_scan_clears_prior_candidate_state(self):
        with (
            patch.object(issue_candidate, "radarr_queue", return_value={"records": []}),
            patch.object(issue_candidate, "store_candidate_state") as store,
        ):
            self.assertEqual(issue_candidate.main(), 0)
        store.assert_called_once_with([])


if __name__ == "__main__":
    unittest.main()
