import unittest
from datetime import datetime, timedelta, timezone

from proposal import OPERATION, ProposalError, create_dry_run


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
REQUEST = {
    "operation": OPERATION,
    "service": "radarr",
    "candidate_ref": "radarr-q-abcdefghijklmnop",
    "report_generated_at": "2026-09-09T11:55:00Z",
}


class ProposalTests(unittest.TestCase):
    def test_valid_request_only_creates_a_dry_run(self):
        result = create_dry_run(REQUEST, now=NOW)
        self.assertEqual(result["mode"], "dry_run")
        self.assertFalse(result["execution_enabled"])
        self.assertIn("preserve downloader data", result["effect_if_later_enabled"])

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "url": "http://example.invalid"}, now=NOW)

    def test_wrong_service_or_operation_is_rejected(self):
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "service": "lidarr"}, now=NOW)
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "operation": "search"}, now=NOW)

    def test_stale_and_future_reports_are_rejected(self):
        stale = (NOW - timedelta(minutes=16)).isoformat().replace("+00:00", "Z")
        future = (NOW + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "report_generated_at": stale}, now=NOW)
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "report_generated_at": future}, now=NOW)

    def test_non_opaque_candidate_is_rejected(self):
        with self.assertRaises(ProposalError):
            create_dry_run({**REQUEST, "candidate_ref": "42"}, now=NOW)


if __name__ == "__main__":
    unittest.main()
