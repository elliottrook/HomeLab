import unittest

import full_aster_first_screen_transaction_v1 as transaction


def admission(**changes):
    value = dict(
        cycle_date="2026-10-27", f2_sha256="2" * 64,
        f3_sha256="3" * 64, f4_sha256="4" * 64,
        f5_sha256="5" * 64, admission_sha256="a" * 64,
        now_epoch=1_000, evidence_expires_epoch=1_600,
        restore_deadline_epoch=2_500, competing_work_absent=True,
        watchdog_independent=True, baseline_authenticated=True,
    )
    value.update(changes)
    return transaction.ScreenAdmission(**value)


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


class FirstScreenTransactionTests(unittest.TestCase):
    def test_exact_single_attempt_sequence_has_two_requests_and_four_restarts(self):
        driver = Driver()
        transaction.execute(admission(), driver)
        self.assertEqual(driver.steps, [step.name for step in transaction.FORWARD_STEPS])
        self.assertEqual(sum(step.model_request for step in transaction.FORWARD_STEPS), 2)
        self.assertEqual(sum(step.restart for step in transaction.FORWARD_STEPS), 4)
        self.assertIsNone(driver.recovery_steps)

    def test_failure_enters_fixed_recovery_without_retry(self):
        driver = Driver("run-synthetic-request-1")
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            transaction.execute(admission(), driver)
        self.assertEqual(driver.steps.count("run-synthetic-request-1"), 1)
        self.assertNotIn("run-synthetic-request-2", driver.steps)
        self.assertEqual(driver.recovery_steps, transaction.RECOVERY_STEPS)

    def test_uncertain_recovery_is_terminal(self):
        driver = Driver("verify-candidate-load-and-residency", recovery=False)
        with self.assertRaises(transaction.RecoveryUncertain):
            transaction.execute(admission(), driver)

    def test_stale_evidence_excess_outage_and_weak_live_gates_fail_before_effect(self):
        for value in (
            admission(now_epoch=1_600),
            admission(restore_deadline_epoch=7_000),
            admission(restore_deadline_epoch=2_499),
            admission(competing_work_absent=False),
            admission(watchdog_independent=False),
            admission(baseline_authenticated=False),
        ):
            driver = Driver()
            with self.subTest(value=value), self.assertRaises(transaction.TransactionError):
                transaction.execute(value, driver)
            self.assertEqual(driver.steps, [])

    def test_summary_pins_artifact_baseline_and_no_promotion(self):
        value = transaction.effect_summary()
        self.assertEqual(value["model_sha256"], transaction.MODEL_SHA256)
        self.assertEqual(value["baseline_model_sha256"], transaction.BASELINE_MODEL_SHA256)
        self.assertEqual(value["runtime_sha256"], transaction.RUNTIME_SHA256)
        self.assertEqual(value["requests"], 2)
        self.assertEqual(value["retries"], 0)
        self.assertFalse(value["promotion"])


if __name__ == "__main__":
    unittest.main()
