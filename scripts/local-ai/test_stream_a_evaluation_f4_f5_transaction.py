import json
import unittest

from lease_watchdog import EXPECTED_SCHEDULES, Observation
from stream_a_evaluation_admission import ADMISSION_PREFIX
from stream_a_evaluation_f4_f5_transaction import (
    TransactionError,
    build_transaction,
)


class F4F5TransactionTests(unittest.TestCase):
    def observation(self, **changes):
        values = dict(
            now_minute=190, heartbeat_alive=False,
            control_plane_healthy=True, production_services_healthy=True,
            accepted_gpu_visible=True, schedule_restored=True,
            schedule_points=EXPECTED_SCHEDULES, schedules_enabled=True,
            exact_binary_verified=True, model_verified=True,
            unit_verified=True, auth_verified=True,
        )
        values.update(changes)
        return Observation(**values)

    def build(self, **changes):
        values = dict(
            cycle_date="2026-10-27", nonce="0123456789abcdef",
            observed_epoch=1793095500, observed_minute=190,
            f2_bytes=b'{"f2":"fixed"}\n',
            f3_bytes=b'{"f3":"fixed"}',
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            observation=self.observation(),
            lxc110_mirror_identity="lxc110:fixed-current-cycle-mirror",
        )
        values.update(changes)
        return build_transaction(**values)

    def test_builds_exact_non_effect_cross_bound_transaction(self):
        result = self.build()
        self.assertEqual(
            result.lease_id,
            "stream-a-evaluation-2026-10-27-0123456789abcdef",
        )
        f4 = json.loads(result.f4_bytes)
        self.assertEqual(f4["schema"], "aster-pre-acquire-receipt-v1")
        self.assertEqual(f4["receipt"]["lease_id"], result.lease_id)
        self.assertFalse(f4["observation"]["heartbeat_alive"])
        self.assertFalse(f4["receipt"]["consumers_isolated"])
        self.assertFalse(f4["receipt"]["scheduled_work_quiesced"])
        admission = json.loads(result.admission_bytes)
        f5 = json.loads(result.f5_bytes)
        self.assertEqual(admission["f5_observation_sha256"],
                         __import__("hashlib").sha256(result.f5_bytes).hexdigest())
        self.assertEqual(f5["f4_receipt_sha256"],
                         __import__("hashlib").sha256(result.f4_bytes).hexdigest())
        self.assertTrue(result.admission_receipt.startswith(ADMISSION_PREFIX))

    def test_runtime_drift_other_than_pre_f6_heartbeat_fails(self):
        for field in (
            "control_plane_healthy", "production_services_healthy",
            "accepted_gpu_visible", "schedule_restored", "schedules_enabled",
            "exact_binary_verified", "model_verified", "unit_verified",
            "auth_verified",
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(observation=self.observation(**{field: False}))

    def test_identity_time_and_predecessor_inputs_are_fixed(self):
        for changes in (
            {"cycle_date": "tomorrow"}, {"nonce": "operator-choice"},
            {"observed_epoch": 0}, {"observed_minute": 191},
            {"f2_bytes": b""}, {"f3_bytes": b""},
            {"lxc110_mirror_identity": ""},
        ):
            with self.subTest(changes=changes), self.assertRaises(TransactionError):
                self.build(**changes)

    def test_tampering_changes_downstream_bindings(self):
        first = self.build()
        second = self.build(f2_bytes=b'{"f2":"changed"}\n')
        self.assertNotEqual(first.f5_bytes, second.f5_bytes)
        self.assertNotEqual(first.admission_bytes, second.admission_bytes)
        self.assertNotEqual(first.admission_receipt, second.admission_receipt)

    def test_reviewed_composition_can_bind_one_exact_external_lease_identity(self):
        lease_id = "aster-full-screen-owner-0123456789abcdef:1793095500"
        result = self.build(lease_id=lease_id)
        self.assertEqual(result.lease_id, lease_id)
        self.assertEqual(json.loads(result.f4_bytes)["receipt"]["lease_id"], lease_id)
        self.assertEqual(json.loads(result.admission_bytes)["lease_id"], lease_id)
        for value in ("", "operator choice", "/path", "x" * 161):
            with self.subTest(value=value), self.assertRaises(TransactionError):
                self.build(lease_id=value)


if __name__ == "__main__":
    unittest.main()
