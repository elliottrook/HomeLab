import unittest

from lease_contract import (
    ACCEPTED_BACKEND,
    ACCEPTED_MODEL,
    BackupChain,
    LeaseError,
    LeaseReceipt,
    LeaseRequest,
    LeaseState,
    plan_acquire,
    plan_release,
    validate_receipt,
)


class LeaseContractTests(unittest.TestCase):
    def request(self, **changes):
        values = {
            "now_minute": 220,
            "window_end_minute": 255,
            "backup": BackupChain(completed=True, verified=True, completed_minute=215),
            "production_active": False,
            "conflicting_job_active": False,
            "host_lock_available": True,
        }
        values.update(changes)
        return LeaseRequest(**values)

    def test_acquire_plan_is_ordered_and_side_effect_free(self):
        plan = plan_acquire(self.request())
        self.assertEqual(plan.state, LeaseState.LEASED)
        self.assertEqual(plan.actions[0], "acquire-host-lock")
        self.assertEqual(plan.actions[-1], "permit-lab-maintenance-and-restart")

    def test_acquire_rejects_unverified_backup_and_conflicts(self):
        with self.assertRaisesRegex(LeaseError, "verified backup"):
            plan_acquire(self.request(backup=BackupChain(True, False, 215)))
        with self.assertRaisesRegex(LeaseError, "production workload"):
            plan_acquire(self.request(production_active=True))
        with self.assertRaisesRegex(LeaseError, "conflicting"):
            plan_acquire(self.request(conflicting_job_active=True))

    def test_acquire_rejects_closed_window_and_missing_lock(self):
        with self.assertRaisesRegex(LeaseError, "window"):
            plan_acquire(self.request(now_minute=255))
        with self.assertRaisesRegex(LeaseError, "lock"):
            plan_acquire(self.request(host_lock_available=False))

    def test_release_requires_restore_and_health(self):
        restoring = plan_release(health_verified=False, restore_complete=False)
        self.assertEqual(restoring.state, LeaseState.RESTORING)
        failed = plan_release(health_verified=False, restore_complete=True)
        self.assertEqual(failed.state, LeaseState.FAILED)
        ready = plan_release(health_verified=True, restore_complete=True)
        self.assertEqual(ready.state, LeaseState.READY)
        self.assertEqual(ready.actions[-1], "record-post-lab-checkpoint")

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

    def test_receipt_binds_admission_to_exact_runtime_and_watchdog(self):
        validate_receipt(
            self.receipt(),
            now_minute=221,
            expected_backup_receipt="backup-chain-sha256",
            watchdog_alive=True,
        )

    def test_receipt_fails_closed_on_expiry_or_runtime_drift(self):
        cases = (
            ("expired", {"expires_minute": 221}, "expired"),
            ("backup", {"backup_receipt": "other"}, "backup"),
            ("model", {"model_identity": "Qwen3.5 9B"}, "9B baseline"),
            ("backend", {"backend_identity": "llama.cpp Vulkan"}, "SYCL baseline"),
            ("consumer", {"consumers_isolated": False}, "isolated"),
            ("schedule", {"scheduled_work_quiesced": False}, "quiesced"),
            ("watchdog", {}, "watchdog"),
        )
        for name, changes, expected in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(LeaseError, expected):
                    validate_receipt(
                        self.receipt(**changes),
                        now_minute=221,
                        expected_backup_receipt="backup-chain-sha256",
                        watchdog_alive=name != "watchdog",
                    )


if __name__ == "__main__":
    unittest.main()
