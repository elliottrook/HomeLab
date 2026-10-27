"""Pinned offline characterization, NOT live admission or peer fixes.

Run with PYTHONPATH pointing to the exact public 38b366e8 peer export.
Only synthetic owner-test fixtures are imported; no transport exists here.
Passing demonstrates current validator limits, not safe production behavior.
"""
import hashlib
from pathlib import Path
import unittest

import full_aster_first_screen_preflight_v1 as preflight
from test_full_aster_first_screen_preflight_v1 import CONTRACT, fixture


class PeerPreflightCharacterization(unittest.TestCase):
    def setUp(self):
        source = Path(preflight.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         '47be100792bba6c16cf7d354e85cc3ff56b3dce106e5a768064e7baa979eb608')

    def check_non_authoritative_acceptance(self, value, raw=CONTRACT):
        result = preflight.validate(value, raw)
        self.assertTrue(result['admitted'])
        self.assertFalse(result['live_effect_authorized'])
        self.assertEqual(result['authority'], 'not-granted')

    def test_past_epoch_deadlines_are_not_freshness_checked(self):
        value = fixture()
        value['watchdog'].update(controller_deadline_epoch=1,
                                 recovery_deadline_epoch=2)
        value['window']['protected_deadline_epoch'] = 3
        self.check_non_authoritative_acceptance(value)

    def test_impossible_cycle_label_is_only_length_checked(self):
        value = fixture()
        value['cycle_date'] = 'not-a-date'
        self.check_non_authoritative_acceptance(value)

    def test_claimed_reserve_is_not_connected_to_deadlines(self):
        value = fixture()
        value['watchdog'].update(controller_deadline_epoch=1000,
                                 recovery_deadline_epoch=1001)
        value['window'].update(protected_deadline_epoch=1002,
                                restore_reserve_seconds=900)
        self.check_non_authoritative_acceptance(value)

    def test_matching_hash_does_not_validate_or_pin_contract(self):
        value = fixture()
        raw = b'not a benchmark contract'
        value['contract_sha256'] = hashlib.sha256(raw).hexdigest()
        self.check_non_authoritative_acceptance(value, raw)


if __name__ == '__main__':
    unittest.main()
