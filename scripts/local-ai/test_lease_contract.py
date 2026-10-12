import unittest

from lease_contract import BackupChain, LeaseError, LeaseRequest, LeaseState, plan_acquire, plan_release


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


if __name__ == "__main__":
    unittest.main()
