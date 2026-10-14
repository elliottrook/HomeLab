"""Offline review diagnostics; a passing test can document an OPEN safety gap."""
import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'aster-adaptive'))
from full_path_admission import admit
from test_full_path_admission import card, observed, NOW


class PeerAdmissionReviewTests(unittest.TestCase):
    def test_owner_snapshot_never_claims_authority(self):
        result = admit(card(), observed(), now=NOW)
        self.assertEqual(result['state'], 'preflight_passed_not_authority')

    def test_open_watchdog_deadline_gap_is_reproduced_not_waived(self):
        # Owner guard reserves time for the ordinary batch, but currently
        # permits a loss-of-owner watchdog to first trigger at 04:15.
        snapshot = observed()
        snapshot['watchdog']['deadline_at'] = '2026-10-14T04:15:00-07:00'
        snapshot['lease']['expires_at'] = '2026-10-14T04:15:00-07:00'
        result = admit(card(), snapshot, now=NOW)
        self.assertEqual(result['latest_batch_end_at'], '2026-10-14T04:00:00-07:00')
        trigger = NOW.replace(hour=4, minute=15)
        restored_after_budget = trigger + timedelta(minutes=15)
        self.assertGreater(restored_after_budget, trigger)
        # This is a diagnostic for the peer correction request, NOT READY.


if __name__ == '__main__':
    unittest.main()
