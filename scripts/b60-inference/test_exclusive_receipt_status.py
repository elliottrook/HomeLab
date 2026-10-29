"""Synthetic metadata tests only: no live qualification or model evidence."""
import copy
import hashlib
import json
import unittest

from exclusive_receipt_status import project


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.entry = {'schema': 'aster-entry-snapshot.v1'}
        digest = hashlib.sha256(json.dumps(self.entry, sort_keys=True,
                                           separators=(',', ':')).encode()).hexdigest()
        self.session = dict(schema='aster-exclusive-session.v1', booking_id='fixture-booking',
                            owner='fixture-owner', entry_sha256=digest, phase='released',
                            production_restored=True, trial_failed=False, deadline_missed=False,
                            updated_epoch=150, restore_deadline=200)
        self.booking = dict(booking_id='fixture-booking', owner='fixture-owner',
                            entry_sha256=digest, state='complete', result_code='RESTORED')

    def check(self):
        row = project(self.session, self.entry, self.booking,
                      booking_id='fixture-booking', owner='fixture-owner')
        self.assertFalse(row['model_success'])
        self.assertFalse(row['live_qualification_proven'])
        self.assertTrue(row['advisory_only'])
        return row['status']

    def test_report_is_not_proof(self):
        self.assertEqual(self.check(), 'restoration-reported-awaiting-independent-verification')

    def test_nonterminal_phases_never_pass(self):
        for phase in ('checkpointed', 'isolated', 'restoring', 'restored',
                      'trial-complete', 'aborted-before-claim', 'unknown'):
            self.session['phase'] = phase
            self.assertEqual(self.check(), 'not-terminal')

    def test_owner_loss_not_trial_success(self):
        self.session['trial_failed'] = True
        self.booking.update(state='failed', result_code='FAILED_RESTORED')
        self.assertEqual(self.check(), 'failed-trial-restoration-reported')

    def test_late_is_failure_even_after_restore(self):
        self.session.update(phase='released-late', deadline_missed=True, updated_epoch=200)
        self.booking.update(state='failed', result_code='FAILED_RESTORED')
        self.assertEqual(self.check(), 'late-restoration-reported')

    def test_conflicting_identity_flags_and_ledger(self):
        original = copy.deepcopy(self.session)
        for key, value in [('booking_id', 'other'), ('owner', 'other'),
                           ('entry_sha256', '0'*64), ('production_restored', 1),
                           ('trial_failed', 0), ('deadline_missed', 0),
                           ('updated_epoch', 200)]:
            self.session = dict(original, **{key: value})
            self.assertEqual(self.check(), 'inconsistent')
        self.session = original
        self.booking['state'] = 'claimed'
        self.assertEqual(self.check(), 'inconsistent')

    def test_changed_entry(self):
        self.entry['unexpected'] = True
        self.assertEqual(self.check(), 'inconsistent')

    def test_malformed_entry_fails_closed(self):
        self.entry['bad'] = float('nan')
        self.assertEqual(self.check(), 'inconsistent')


if __name__ == '__main__':
    unittest.main()
