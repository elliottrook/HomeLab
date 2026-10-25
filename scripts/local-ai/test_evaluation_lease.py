import unittest

from evaluation_lease import (
    ACCEPTED_BACKEND,
    ACCEPTED_ENDPOINT,
    ACCEPTED_MODEL,
    BACKEND_TARGET,
    D4_DIGEST,
    M3_STAGE_MANIFEST_DIGEST,
    QUIESCE_TARGETS,
    RESTORE_RESERVE_SECONDS,
    Admission,
    EvaluationLeaseError,
    ProductionBaseline,
    WorkloadOutcome,
    next_workload,
    plan,
    validate_admission,
    validate_restoration,
    watchdog_decision,
    workload,
)


class EvaluationLeaseTests(unittest.TestCase):
    def admission(self):
        return Admission(
            lease_id="eval-1", generation=1, backup_receipt="backup-1",
            f2_receipt="f2-1", f3_receipt="f3-1", model=ACCEPTED_MODEL,
            backend=ACCEPTED_BACKEND, endpoint=ACCEPTED_ENDPOINT,
            backend_active=True, endpoint_authenticated=True, endpoint_idle=True,
            gpu_holders=(BACKEND_TARGET,), quiesced_targets=QUIESCE_TARGETS,
            baseline=ProductionBaseline(
                units=(("lxc104:aster-agent.service", "active"),
                       ("lxc116:aster-speech.service", "active")),
                timers=(("lxc114:news-aggregator-ingest.timer", "active"),
                        ("lxc114:news-aggregator-digest.timer", "active")),
            ), watchdog_independent=True, hard_deadline_epoch=4500,
            restore_deadline_epoch=4500 + RESTORE_RESERVE_SECONDS,
        )

    def test_admission_retains_backend_and_requires_fresh_receipts(self):
        validate_admission(self.admission(), now_epoch=1000)
        bad = self.admission().__class__(**{**self.admission().__dict__, "gpu_holders": ()})
        with self.assertRaises(EvaluationLeaseError):
            validate_admission(bad, now_epoch=1000)

    def test_backend_cannot_be_quiesced(self):
        value = self.admission()
        bad = value.__class__(**{**value.__dict__, "quiesced_targets": QUIESCE_TARGETS + (BACKEND_TARGET,)})
        with self.assertRaises(EvaluationLeaseError):
            validate_admission(bad, now_epoch=1000)

    def test_sequence_is_d4_then_m3_and_separate_paths(self):
        self.assertEqual(next_workload(completed=()).name, "d4-candidate-g")
        self.assertEqual(next_workload(completed=("d4-candidate-g",)).name, "m3-nlu-calibration")
        self.assertIsNone(next_workload(completed=("d4-candidate-g", "m3-nlu-calibration")))
        self.assertEqual(workload("d4-candidate-g").packet_digest, D4_DIGEST)
        self.assertEqual(workload("m3-nlu-calibration").packet_digest, M3_STAGE_MANIFEST_DIGEST)
        self.assertNotEqual(workload("d4-candidate-g").journal_name, workload("m3-nlu-calibration").journal_name)

    def test_uncertain_outcome_cannot_advance(self):
        outcome = WorkloadOutcome("eval-1", 1, "d4-candidate-g", D4_DIGEST,
                                  "completed", "j", "r", 1, 1, True, True)
        with self.assertRaises(EvaluationLeaseError):
            next_workload(completed=(), outcome=outcome)

    def test_watchdog_recovers_on_deadline_or_owner_loss(self):
        self.assertEqual(watchdog_decision(now_epoch=4500, heartbeat_epoch=4499,
                          heartbeat_timeout=30, hard_deadline_epoch=4500,
                          restore_deadline_epoch=5400, owner_present=True).action, "recover")
        self.assertEqual(watchdog_decision(now_epoch=1100, heartbeat_epoch=1099,
                          heartbeat_timeout=30, hard_deadline_epoch=4500,
                          restore_deadline_epoch=5400, owner_present=False).reason, "owner-absent")

    def test_restoration_requires_exact_baseline_and_idle_gpu(self):
        baseline = self.admission().baseline
        validate_restoration(restored=baseline, expected=baseline,
                             backend_active=True, endpoint_authenticated=True,
                             gpu_holders=())
        with self.assertRaises(EvaluationLeaseError):
            validate_restoration(restored=baseline, expected=baseline,
                                 backend_active=True, endpoint_authenticated=True,
                                 gpu_holders=(BACKEND_TARGET,))

    def test_plan_is_effect_ordered(self):
        actions = plan()
        self.assertLess(actions.index("quiesce-registered-aster-speech-and-news-consumers"),
                        actions.index("run-d4-candidate-g-once-to-its-separate-journal-and-result"))
        self.assertLess(actions.index("run-m3-nlu-calibration-once-to-its-separate-journal-and-result"),
                        actions.index("restore-exact-production-unit-and-timer-baseline"))


if __name__ == "__main__":
    unittest.main()
