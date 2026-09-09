import unittest
from datetime import datetime, timedelta, timezone

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


if __name__ == "__main__":
    unittest.main()
