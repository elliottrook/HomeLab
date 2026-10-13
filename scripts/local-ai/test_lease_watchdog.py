import unittest

from lease_contract import ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt
from admission_state import AdmissionRecord, decode, encode, expired
from lease_watchdog import EXPECTED_SCHEDULES, Observation, WatchdogState, decide, status_receipt


class LeaseWatchdogTests(unittest.TestCase):
    def receipt(self, **changes):
        values = {
            "lease_id": "lab-20261013-01",
            "generation": 1,
            "issued_minute": 220,
            "expires_minute": 255,
            "backup_receipt": "backup-chain-sha256",
            "model_identity": ACCEPTED_MODEL,
            "backend_identity": ACCEPTED_BACKEND,
            "consumers_isolated": True,
            "scheduled_work_quiesced": True,
        }
        values.update(changes)
        return LeaseReceipt(**values)

    def observation(self, **changes):
        values = {
            "now_minute": 221,
            "heartbeat_alive": True,
            "control_plane_healthy": True,
            "production_services_healthy": True,
            "accepted_gpu_visible": True,
            "schedule_restored": True,
        }
        values.update(changes)
        return Observation(**values)

    def test_lease_expires_to_restoration_without_retry(self):
        decision = decide(
            self.receipt(expires_minute=221),
            self.observation(),
            backup_receipt="backup-chain-sha256",
            current_state=WatchdogState.LEASED,
        )
        self.assertEqual(decision.state, WatchdogState.RESTORING)
        self.assertIn("persist-restore-intent", decision.actions)

    def test_watchdog_loss_is_fail_closed(self):
        decision = decide(
            self.receipt(),
            self.observation(heartbeat_alive=False),
            backup_receipt="backup-chain-sha256",
            current_state=WatchdogState.LEASED,
        )
        self.assertEqual(decision.state, WatchdogState.RESTORING)
        self.assertNotIn("permit-bounded-lab-work", decision.actions)

    def test_partial_restore_keeps_lock_and_needs_operator(self):
        decision = decide(
            self.receipt(),
            self.observation(production_services_healthy=False),
            backup_receipt="backup-chain-sha256",
            current_state=WatchdogState.RESTORING,
        )
        self.assertEqual(decision.state, WatchdogState.FAILED)
        self.assertIn("retain-lease-lock", decision.actions)

    def test_complete_restore_releases_only_after_schedule_and_gpu_checks(self):
        decision = decide(
            self.receipt(),
            self.observation(),
            backup_receipt="backup-chain-sha256",
            current_state=WatchdogState.RESTORING,
        )
        self.assertEqual(decision.state, WatchdogState.READY)
        self.assertEqual(decision.actions[-1], "release-lease-lock")

    def test_status_receipt_is_content_free_and_bound_to_lease(self):
        value = status_receipt(
            self.receipt(),
            WatchdogState.READY,
            self.observation(),
        )
        self.assertEqual(value["lease_id"], "lab-20261013-01")
        self.assertEqual(value["generation"], 1)
        self.assertEqual(value["state"], WatchdogState.READY)
        self.assertNotIn("prompt", value)
        self.assertNotIn("token", value)
        self.assertNotIn("audio", value)

    def test_status_receipt_preserves_failure_category_without_details(self):
        value = status_receipt(
            self.receipt(),
            WatchdogState.FAILED,
            self.observation(production_services_healthy=False),
            failure_code="production-health",
        )
        self.assertEqual(value["failure_code"], "production-health")
        self.assertNotIn("exception", value)

    def test_light_observation_does_not_claim_exact_restore_checks(self):
        value = status_receipt(
            self.receipt(),
            WatchdogState.LEASED,
            self.observation(
                production_services_healthy=None,
                accepted_gpu_visible=None,
                schedule_restored=None,
                schedule_points=(),
                schedules_enabled=None,
                exact_binary_verified=None,
                model_verified=None,
                unit_verified=None,
                auth_verified=None,
            ),
        )
        self.assertIsNone(value["accepted_gpu_visible"])
        self.assertIsNone(value["schedule_restored"])
        self.assertEqual(value["schedule_points"], ())

    def test_restore_requires_exact_backup_schedule_identity(self):
        decision = decide(
            self.receipt(),
            self.observation(schedule_points=("00:30", "01:00", "02:00")),
            backup_receipt="backup-chain-sha256",
            current_state=WatchdogState.RESTORING,
        )
        self.assertEqual(decision.state, WatchdogState.FAILED)
        self.assertEqual(EXPECTED_SCHEDULES, (
            "proxmox:00:30", "truenas-guest:01:00", "truenas-lxc110:02:00",
            "truenas-mac:03:00", "news:06:15", "news:17:15",
        ))

    def test_admission_record_round_trips_and_expires(self):
        record = AdmissionRecord(
            lease_id="lab-20261013-01",
            generation=1,
            state="leased",
            issued_minute=220,
            expires_minute=255,
            backup_receipt="backup-chain-sha256",
            model_identity=ACCEPTED_MODEL,
            backend_identity=ACCEPTED_BACKEND,
            consumers_isolated=True,
            scheduled_work_quiesced=True,
        )
        self.assertEqual(decode(encode(record)), record)
        self.assertFalse(expired(record, 254))
        self.assertTrue(expired(record, 255))

    def test_admission_record_rejects_unexpected_fields(self):
        payload = encode(AdmissionRecord(
            lease_id="x", generation=1, state="leased", issued_minute=1,
            expires_minute=2, backup_receipt="b", model_identity=ACCEPTED_MODEL,
            backend_identity=ACCEPTED_BACKEND, consumers_isolated=True,
            scheduled_work_quiesced=True,
        )).replace("}\n", ',"unexpected":true}\n')
        with self.assertRaisesRegex(ValueError, "schema"):
            decode(payload)


if __name__ == "__main__":
    unittest.main()
