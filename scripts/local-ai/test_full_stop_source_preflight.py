import unittest

from full_stop_source_preflight import PreflightError, prepare_pre_acquire
from lease_watchdog import EXPECTED_SCHEDULES, Observation
from source_receipts import BackupSourceReceipt
from admission_gate import EXPECTED_BACKUP_SOURCE


class FullStopSourcePreflightTests(unittest.TestCase):
    def backup(self, **changes):
        values = dict(
            source=EXPECTED_BACKUP_SOURCE, chain_id=EXPECTED_BACKUP_SOURCE,
            completed_minute=190,
            integrity_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            integrity_verified=True, source_observed=True,
        )
        values.update(changes)
        return BackupSourceReceipt(**values)

    def observation(self, **changes):
        values = dict(
            now_minute=191, heartbeat_alive=True,
            control_plane_healthy=True, production_services_healthy=True,
            accepted_gpu_visible=True, schedule_restored=True,
            schedule_points=EXPECTED_SCHEDULES, schedules_enabled=True,
            exact_binary_verified=True, model_verified=True,
            unit_verified=True, auth_verified=True,
        )
        values.update(changes)
        return Observation(**values)

    def prepare(self, backup=None, observation=None):
        return prepare_pre_acquire(
            backup or self.backup(), observation or self.observation(),
            lease_id="lab-1", generation=1, expires_minute=210,
        )

    def test_verified_pre_acquire_receipt_makes_no_isolation_claim(self):
        receipt = self.prepare()
        self.assertEqual(receipt.backup_receipt, self.backup().integrity_receipt)
        self.assertFalse(receipt.consumers_isolated)
        self.assertFalse(receipt.scheduled_work_quiesced)

    def test_unverified_or_wrong_source_backup_fails_closed(self):
        for changes in (
            {"integrity_verified": False}, {"source_observed": False},
            {"source": "untrusted"}, {"integrity_receipt": "metadata-sha256:x"},
            {"completed_minute": 192},
        ):
            with self.subTest(changes=changes), self.assertRaises(PreflightError):
                self.prepare(backup=self.backup(**changes))

    def test_runtime_drift_and_missing_heartbeat_fail_closed(self):
        for changes in (
            {"production_services_healthy": False},
            {"schedule_restored": False}, {"schedule_points": ()},
            {"model_verified": False}, {"auth_verified": False},
        ):
            with self.subTest(changes=changes), self.assertRaises(PreflightError):
                self.prepare(observation=self.observation(**changes))
        with self.assertRaisesRegex(ValueError, "watchdog"):
            self.prepare(observation=self.observation(heartbeat_alive=False))


if __name__ == "__main__":
    unittest.main()
