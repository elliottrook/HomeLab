import json
import unittest
from datetime import datetime

from admission_gate import EXPECTED_BACKUP_SOURCE
from lease_contract import ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt
from lease_watchdog import EXPECTED_SCHEDULES, Observation
from pre_acquire_receipt import PreAcquireReceiptError, decode, encode


class PreAcquireReceiptTests(unittest.TestCase):
    def receipt(self, **changes):
        values = dict(
            lease_id="proposal-1", generation=1, issued_minute=185,
            expires_minute=210,
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            model_identity=ACCEPTED_MODEL, backend_identity=ACCEPTED_BACKEND,
            consumers_isolated=False, scheduled_work_quiesced=False,
        )
        values.update(changes)
        return LeaseReceipt(**values)

    def observation(self, **changes):
        values = dict(
            now_minute=185, heartbeat_alive=True, control_plane_healthy=True,
            production_services_healthy=True, accepted_gpu_visible=True,
            schedule_restored=True, schedule_points=EXPECTED_SCHEDULES,
            schedules_enabled=True, exact_binary_verified=True,
            model_verified=True, unit_verified=True, auth_verified=True,
        )
        values.update(changes)
        return Observation(**values)

    def payload(self, **changes):
        value = json.loads(encode(self.receipt(), self.observation(), captured_epoch=1000))
        value.update(changes)
        return value

    def test_round_trip_is_non_effect_and_bound_to_observation(self):
        payload = self.payload()
        receipt, observation, captured = decode(payload, now_minute=190, now_epoch=1100)
        self.assertFalse(receipt.consumers_isolated)
        self.assertFalse(receipt.scheduled_work_quiesced)
        self.assertEqual(receipt.backup_receipt, self.receipt().backup_receipt)
        self.assertEqual(observation.schedule_points, EXPECTED_SCHEDULES)
        self.assertEqual(captured, 1000)

    def test_stale_or_future_receipt_fails_closed(self):
        with self.assertRaisesRegex(PreAcquireReceiptError, "stale"):
            decode(self.payload(), now_minute=190, now_epoch=1901)
        with self.assertRaisesRegex(PreAcquireReceiptError, "stale"):
            decode(self.payload(captured_epoch=2000), now_minute=190, now_epoch=1901)

    def test_isolated_or_runtime_drift_cannot_be_pre_acquire(self):
        with self.assertRaisesRegex(PreAcquireReceiptError, "isolation"):
            encode(self.receipt(consumers_isolated=True), self.observation(), captured_epoch=1000)
        payload = self.payload()
        payload["observation"]["auth_verified"] = False
        with self.assertRaisesRegex(PreAcquireReceiptError, "types|incomplete|watchdog"):
            decode(payload, now_minute=190, now_epoch=1100)

    def test_schema_and_backup_binding_are_exact(self):
        payload = self.payload()
        payload["receipt"]["backup_receipt"] = "metadata-sha256:replay"
        with self.assertRaises(PreAcquireReceiptError):
            decode(payload, now_minute=190, now_epoch=1100)
        payload = self.payload()
        payload["extra"] = True
        with self.assertRaises(PreAcquireReceiptError):
            decode(payload, now_minute=190, now_epoch=1100)


if __name__ == "__main__":
    unittest.main()
