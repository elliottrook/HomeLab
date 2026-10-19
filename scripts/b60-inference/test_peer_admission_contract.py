"""Offline peer integration checks; synthetic passage is not live authority."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'aster-adaptive'))
from full_path_admission import AdmissionDenied, admit
from test_full_path_admission import card, observed, NOW


class PeerAdmissionReviewTests(unittest.TestCase):
    def test_owner_snapshot_never_claims_authority(self):
        result = admit(card(), observed(), now=NOW)
        self.assertEqual(result['state'], 'preflight_passed_not_authority')

    def test_corrected_owner_guard_refuses_trigger_at_completion_deadline(self):
        # The newly published owner guard now distinguishes a trigger from
        # completed restoration. This closes the old offline reproduction,
        # not measured recovery, authenticated admission or a live drill.
        snapshot = observed()
        snapshot['watchdog']['deadline_at'] = '2026-10-14T04:15:00-07:00'
        snapshot['lease']['expires_at'] = '2026-10-14T04:15:00-07:00'
        with self.assertRaisesRegex(AdmissionDenied, 'insufficient_recovery_time'):
            admit(card(), snapshot, now=NOW)


if __name__ == '__main__':
    unittest.main()
