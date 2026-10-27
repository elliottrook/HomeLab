"""Synthetic regression review for the corrected, non-authoritative preflight.

Supply the public 1e2246b8 peer export on PYTHONPATH. No live producer,
credential, private packet or transport is imported. Historical acceptance
characterizations remain pinned to the old source in their separate file.
"""
import hashlib
from pathlib import Path
import unittest

import full_aster_first_screen_preflight_v1 as preflight
from test_full_aster_first_screen_preflight_v1 import CONTRACT, NOW, fixture


class PeerPreflightCorrection(unittest.TestCase):
    def setUp(self):
        self.assertEqual(hashlib.sha256(Path(preflight.__file__).read_bytes()).hexdigest(),
                         '33408d610e107814fd92103e0ba2f11c6eb12b8c7d33a30fae9780ec8b580ab0')

    def test_valid_synthetic_profile_still_denies_effect_authority(self):
        result = preflight.validate(fixture(), CONTRACT, now_epoch=NOW)
        self.assertTrue(result['admitted'])
        self.assertFalse(result['live_effect_authorized'])
        self.assertEqual(result['authority'], 'not-granted')

    def test_old_epoch_deadlines_rejected(self):
        value = fixture()
        value['watchdog'].update(controller_deadline_epoch=1,
                                 recovery_deadline_epoch=2)
        value['window']['protected_deadline_epoch'] = 3
        with self.assertRaises(ValueError):
            preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_impossible_cycle_rejected(self):
        value = fixture(); value['cycle_date'] = 'not-a-date'
        with self.assertRaises(ValueError):
            preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_real_reserve_required(self):
        value = fixture()
        value['watchdog'].update(controller_deadline_epoch=NOW+600,
                                 recovery_deadline_epoch=NOW+601)
        with self.assertRaises(ValueError):
            preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_arbitrary_contract_rejected_even_with_matching_digest(self):
        value = fixture(); raw = b'not a benchmark contract'
        value['contract_sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError):
            preflight.validate(value, raw, now_epoch=NOW)


if __name__ == '__main__':
    unittest.main()
