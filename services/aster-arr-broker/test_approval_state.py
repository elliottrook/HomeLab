import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from approval_state import (
    ApprovalStateError,
    consume_approval,
    load_approvals,
    new_approval,
    pending_approval,
    store_approvals,
)


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
REF = "radarr-q-abcdefghijklmnop"


class ApprovalStateTests(unittest.TestCase):
    def test_round_trip_is_short_lived_opaque_and_nonreversible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approvals.json"
            record = new_approval(REF, now=NOW)
            store_approvals(path, {record.reference: record})
            loaded = load_approvals(path)
            mode = path.stat().st_mode & 0o777
        self.assertRegex(record.reference, r"^approval-[a-z2-7]{16}$")
        self.assertEqual(record.expires_at - record.issued_at, timedelta(minutes=2))
        self.assertTrue(record.nonreversible_accepted)
        self.assertEqual(loaded, {record.reference: record})
        self.assertEqual(mode, 0o600)

    def test_consumed_approval_cannot_be_selected_again(self):
        record = new_approval(REF, now=NOW)
        approvals = {record.reference: record}
        selected = pending_approval(approvals, REF, now=NOW)
        approvals[record.reference] = consume_approval(selected, now=NOW)
        with self.assertRaises(ApprovalStateError):
            pending_approval(approvals, REF, now=NOW)

    def test_expired_cross_candidate_and_ambiguous_approvals_are_refused(self):
        first = new_approval(REF, now=NOW - timedelta(minutes=3))
        with self.assertRaises(ApprovalStateError):
            pending_approval({first.reference: first}, REF, now=NOW)
        with self.assertRaises(ApprovalStateError):
            pending_approval({first.reference: first}, "radarr-q-ponmlkjihgfedcba", now=NOW)
        active_one = new_approval(REF, now=NOW)
        active_two = new_approval(REF, now=NOW)
        with self.assertRaises(ApprovalStateError):
            pending_approval(
                {active_one.reference: active_one, active_two.reference: active_two},
                REF,
                now=NOW,
            )

    def test_future_issued_approval_is_refused(self):
        record = new_approval(REF, now=NOW + timedelta(seconds=1))
        with self.assertRaises(ApprovalStateError):
            pending_approval({record.reference: record}, REF, now=NOW)

    def test_malformed_or_secret_bearing_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approvals.json"
            path.write_text(json.dumps({"schema_version": 1, "approvals": [], "api_key": "secret"}))
            with self.assertRaises(ApprovalStateError):
                load_approvals(path)


if __name__ == "__main__":
    unittest.main()
