from __future__ import annotations

import unittest

import m3_joint_semantic_35b_transaction_v1 as transaction


def admission(**changes):
    value = dict(
        booking_id="aster-stream-a-m3-35b-20261029",
        booking_workload=transaction.WORKLOAD,
        now_epoch=1_000,
        booking_end_epoch=3_000,
        controller_deadline_epoch=2_000,
        recovery_deadline_epoch=3_000,
        reservation_confirmed=True,
        whole_host_lease_ready=True,
        shared_operation_lock_ready=True,
        restart_authorized=True,
        production_baseline_authenticated=True,
        watchdog_independent=True,
    )
    value.update(changes)
    return transaction.Admission(**value)


class Driver:
    def __init__(self, fail_at=None, recovery=True):
        self.steps = []
        self.fail_at = fail_at
        self.recovery = recovery
        self.recovery_steps = None

    def apply(self, step):
        self.steps.append(step.name)
        if step.name == self.fail_at:
            raise RuntimeError("synthetic failure")

    def recover(self, steps):
        self.recovery_steps = steps
        return self.recovery


class JointSemantic35BTransactionTests(unittest.TestCase):
    def test_exact_sequence_has_one_24_request_public_gate_and_four_restarts(self):
        driver = Driver()
        transaction.execute(admission(), driver)
        self.assertEqual([step.name for step in transaction.FORWARD_STEPS], driver.steps)
        self.assertEqual(24, sum(step.model_requests for step in transaction.FORWARD_STEPS))
        self.assertEqual(4, sum(step.restart for step in transaction.FORWARD_STEPS))

    def test_missing_booking_lease_lock_or_restart_authority_fails_before_effect(self):
        for changes in (
            {"reservation_confirmed": False},
            {"whole_host_lease_ready": False},
            {"shared_operation_lock_ready": False},
            {"restart_authorized": False},
            {"booking_workload": "other"},
        ):
            driver = Driver()
            with self.subTest(changes=changes), self.assertRaises(transaction.TransactionError):
                transaction.execute(admission(**changes), driver)
            self.assertEqual([], driver.steps)

    def test_failure_enters_fixed_recovery_without_retry(self):
        driver = Driver("run-exact-public-gate")
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            transaction.execute(admission(), driver)
        self.assertEqual(1, driver.steps.count("run-exact-public-gate"))
        self.assertEqual(transaction.RECOVERY_STEPS, driver.recovery_steps)

    def test_uncertain_recovery_is_terminal(self):
        driver = Driver("verify-artifact-runtime-auth-and-residency", recovery=False)
        with self.assertRaises(transaction.RecoveryUncertain):
            transaction.execute(admission(), driver)

    def test_summary_denies_promotion_and_routing(self):
        value = transaction.effect_summary()
        self.assertEqual(24, value["requests"])
        self.assertEqual(0, value["retries"])
        self.assertFalse(value["promotion"])
        self.assertEqual("off", value["automatic_routing"])


if __name__ == "__main__":
    unittest.main()

