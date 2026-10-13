import copy
import unittest
from lease_recovery_candidate import restore_record, RecoveryReviewRequired

KEYS = ['104:aster-agent.service', '110:aster-llama.service', '116:aster-speech.service']


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.record = {'state': 'leased', 'services': KEYS.copy()}
        self.saved = []; self.started = []; self.health = {k: False for k in KEYS}

    def persist(self, state): self.saved.append(copy.deepcopy(state))
    def start(self, key):
        self.assertIn(key, self.saved[-1]['restore_attempted'])
        self.started.append(key); self.health[key] = True

    def run_record(self, record=None, **changes):
        options = dict(active=lambda k: self.health[k], start=self.start,
                       persist=self.persist, validate=lambda: True)
        options.update(changes)
        return restore_record(record or self.record, **options)

    def test_start_intent_durable_before_effect_and_order_retained(self):
        result = self.run_record()
        self.assertEqual(self.started, KEYS)
        self.assertEqual(result['state'], 'restoration_validated')
        self.assertEqual(self.record['state'], 'leased')

    def test_partial_restoration_reentry_does_not_restart_healthy_services(self):
        record = {'state': 'restoring', 'services': KEYS.copy(), 'restore_attempted': KEYS[:1]}
        self.health[KEYS[0]] = True
        result = self.run_record(record)
        self.assertEqual(self.started, KEYS[1:])
        self.assertEqual(result['state'], 'restoration_validated')

    def test_uncertain_gpu_start_is_never_retried(self):
        self.health[KEYS[0]] = True
        record = {'state': 'restoring', 'services': KEYS.copy(), 'restore_attempted': KEYS[:2]}
        with self.assertRaises(RecoveryReviewRequired): self.run_record(record)
        self.assertEqual(self.started, [])
        self.assertEqual(self.saved[-1]['state'], 'restoring')

    def test_lost_start_response_retains_intent_and_next_call_observes_health(self):
        def lost(key):
            self.start(key); raise ConnectionError('fake lost reply')
        with self.assertRaises(ConnectionError): self.run_record(start=lost)
        result = self.run_record(self.saved[-1])
        self.assertEqual(self.started.count(KEYS[0]), 1)
        self.assertEqual(result['state'], 'restoration_validated')

    def test_failed_exact_device_validation_keeps_record_and_no_retry(self):
        with self.assertRaises(RecoveryReviewRequired): self.run_record(validate=lambda: False)
        starts = list(self.started)
        with self.assertRaises(RecoveryReviewRequired):
            self.run_record(self.saved[-1], validate=lambda: False)
        self.assertEqual(self.started, starts)
        self.assertEqual(self.saved[-1]['state'], 'restoring')

    def test_invalid_target_has_no_callbacks(self):
        self.record['services'].append('114:news-aggregator-ingest.service')
        with self.assertRaises(ValueError): self.run_record()
        self.assertEqual(self.saved, []); self.assertEqual(self.started, [])

    def test_state_write_failure_prevents_start(self):
        def denied(state): raise OSError('fake disk failure')
        with self.assertRaises(OSError): self.run_record(persist=denied)
        self.assertEqual(self.started, [])

    def test_validated_reentry_still_requires_health_and_exact_checks(self):
        result = self.run_record(); starts = list(self.started)
        again = self.run_record(result)
        self.assertEqual(again['state'], 'restoration_validated')
        self.assertEqual(self.started, starts)


if __name__ == '__main__': unittest.main()
