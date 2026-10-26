import unittest

from evaluation_lease import (
    ACCEPTED_BACKEND,
    ACCEPTED_ENDPOINT,
    ACCEPTED_MODEL,
    BACKEND_TARGET,
    D4_DIGEST,
    M3_STAGE_MANIFEST_DIGEST,
    QUIESCE_TARGETS,
    QUIESCE_STATES,
    RESTORE_RESERVE_SECONDS,
    Admission,
    ExerciseAdmission,
    EXERCISE_HARD_DEADLINE_SECONDS,
    EXERCISE_MARKER,
    EXERCISE_RESTORE_DEADLINE_SECONDS,
    EvaluationLeaseError,
    ProductionBaseline,
    WorkloadOutcome,
    next_workload,
    plan,
    validate_admission,
    validate_exercise_admission,
    validate_post_quiescence,
    validate_restoration,
    watchdog_decision,
    workload,
)


class EvaluationLeaseTests(unittest.TestCase):
    def admission(self):
        return Admission(
            lease_id="eval-1", generation=1,
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            f2_receipt="f2-result-sha256:" + "b" * 64,
            f3_receipt="f3-receipt-sha256:" + "c" * 64, model=ACCEPTED_MODEL,
            backend=ACCEPTED_BACKEND, endpoint=ACCEPTED_ENDPOINT,
            backend_active=True, endpoint_authenticated=True, endpoint_idle=True,
            gpu_holders=(BACKEND_TARGET,), registered_targets=QUIESCE_TARGETS,
            quiesced_targets=(),
            baseline=ProductionBaseline(
                units=(("lxc104:aster-agent.service", "enabled+active"),
                       ("lxc116:aster-speech.service", "enabled+active")),
                timers=(("lxc114:news-aggregator-ingest.timer", "enabled+active"),
                        ("lxc114:news-aggregator-digest.timer", "enabled+active")),
            ), watchdog_independent=True, hard_deadline_epoch=5500,
            restore_deadline_epoch=5500 + RESTORE_RESERVE_SECONDS,
            admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
        )

    def exercise_admission(self):
        value = self.admission()
        return ExerciseAdmission(
            lease_id="exercise-20261025-1", generation=1,
            exercise_marker=EXERCISE_MARKER, model=value.model,
            backend=value.backend, endpoint=value.endpoint,
            backend_active=True, endpoint_authenticated=True, endpoint_idle=True,
            gpu_holders=value.gpu_holders, registered_targets=value.registered_targets,
            quiesced_targets=(), baseline=value.baseline, watchdog_independent=True,
            hard_deadline_epoch=1000 + EXERCISE_HARD_DEADLINE_SECONDS,
            restore_deadline_epoch=1000 + EXERCISE_RESTORE_DEADLINE_SECONDS,
        )

    def test_exercise_admission_is_receipt_free_short_and_explicit(self):
        value = self.exercise_admission()
        validate_exercise_admission(value, now_epoch=1000)
        self.assertNotIn("receipt", " ".join(value.__dict__))
        for change in (
            {"exercise_marker": "production"},
            {"lease_id": "eval-1"},
            {"hard_deadline_epoch": 5500},
            {"restore_deadline_epoch": 6400},
        ):
            bad = value.__class__(**{**value.__dict__, **change})
            with self.assertRaises(EvaluationLeaseError):
                validate_exercise_admission(bad, now_epoch=1000)

    def test_admission_retains_backend_and_requires_fresh_receipts(self):
        validate_admission(self.admission(), now_epoch=1000)
        bad = self.admission().__class__(**{**self.admission().__dict__, "gpu_holders": ()})
        with self.assertRaises(EvaluationLeaseError):
            validate_admission(bad, now_epoch=1000)

    def test_backend_cannot_be_quiesced(self):
        value = self.admission()
        bad = value.__class__(**{**value.__dict__, "registered_targets": QUIESCE_TARGETS + (BACKEND_TARGET,)})
        with self.assertRaises(EvaluationLeaseError):
            validate_admission(bad, now_epoch=1000)

    def test_post_quiescence_requires_exact_targets_and_backend_holder(self):
        value = self.admission()
        validate_post_quiescence(value, observed_states=QUIESCE_STATES,
                                 backend_active=True, endpoint_authenticated=True,
                                 endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))
        with self.assertRaises(EvaluationLeaseError):
            validate_post_quiescence(value, observed_states=QUIESCE_STATES[:-1],
                                     backend_active=True, endpoint_authenticated=True,
                                     endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))
        with self.assertRaises(EvaluationLeaseError):
            validate_post_quiescence(
                value,
                observed_states=tuple((target, "active") for target in QUIESCE_TARGETS),
                backend_active=True, endpoint_authenticated=True,
                endpoint_idle=True, gpu_holders=(BACKEND_TARGET,),
            )

    def test_sequence_is_d4_then_m3_and_separate_paths(self):
        self.assertEqual(next_workload(completed=(), expected_lease_id="eval-1",
                                       expected_generation=1).name, "d4-candidate-h")
        outcome = WorkloadOutcome("eval-1", 1, "d4-candidate-h", D4_DIGEST,
                                  "completed", "j", "r", 1, 1, True)
        self.assertEqual(next_workload(completed=("d4-candidate-h",),
                                       expected_lease_id="eval-1", expected_generation=1,
                                       outcome=outcome).name, "m3-nlu-calibration")
        m3_outcome = WorkloadOutcome("eval-1", 1, "m3-nlu-calibration",
                                     M3_STAGE_MANIFEST_DIGEST, "completed", "m3j", "m3r", 60, 10, True)
        self.assertIsNone(next_workload(
            completed=("d4-candidate-h", "m3-nlu-calibration"),
            expected_lease_id="eval-1", expected_generation=1, outcome=m3_outcome,
        ))
        self.assertEqual(workload("d4-candidate-h").packet_digest, D4_DIGEST)
        self.assertEqual(workload("m3-nlu-calibration").packet_digest, M3_STAGE_MANIFEST_DIGEST)
        self.assertNotEqual(workload("d4-candidate-h").journal_name, workload("m3-nlu-calibration").journal_name)

    def test_uncertain_outcome_cannot_advance(self):
        outcome = WorkloadOutcome("other-lease", 9, "d4-candidate-h", D4_DIGEST,
                                  "completed", "j", "r", 1, 1, True, True)
        with self.assertRaises(EvaluationLeaseError):
            next_workload(completed=("d4-candidate-h",), expected_lease_id="eval-1",
                          expected_generation=1, outcome=outcome)

    def test_m3_completion_requires_current_terminal_outcome(self):
        completed = ("d4-candidate-h", "m3-nlu-calibration")
        with self.assertRaises(EvaluationLeaseError):
            next_workload(completed=completed, expected_lease_id="eval-1", expected_generation=1)
        foreign = WorkloadOutcome("other-lease", 1, "m3-nlu-calibration",
                                  M3_STAGE_MANIFEST_DIGEST, "completed", "j", "r", 60, 1, True)
        with self.assertRaises(EvaluationLeaseError):
            next_workload(completed=completed, expected_lease_id="eval-1",
                          expected_generation=1, outcome=foreign)
        uncertain = WorkloadOutcome("eval-1", 1, "m3-nlu-calibration",
                                    M3_STAGE_MANIFEST_DIGEST, "completed", "j", "r", 60, 1, True, True)
        with self.assertRaises(EvaluationLeaseError):
            next_workload(completed=completed, expected_lease_id="eval-1",
                          expected_generation=1, outcome=uncertain)

    def test_window_is_fixed_and_budgeted(self):
        validate_admission(self.admission(), now_epoch=1000)
        value = self.admission()
        bad = value.__class__(**{**value.__dict__, "restore_deadline_epoch": 9999})
        with self.assertRaises(EvaluationLeaseError):
            validate_admission(bad, now_epoch=1000)

    def test_baseline_rejects_incomplete_duplicate_or_wrong_targets(self):
        value = self.admission()
        for units in (
            value.baseline.units[:-1],
            value.baseline.units + (("lxc104:aster-agent.service", "enabled+active"),),
            (("lxc999:wrong.service", "enabled+active"), value.baseline.units[1]),
        ):
            bad_baseline = ProductionBaseline(units, value.baseline.timers)
            bad = value.__class__(**{**value.__dict__, "baseline": bad_baseline})
            with self.assertRaises(EvaluationLeaseError):
                validate_admission(bad, now_epoch=1000)

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
                             endpoint_idle=True, gpu_holders=(BACKEND_TARGET,))
        with self.assertRaises(EvaluationLeaseError):
            validate_restoration(restored=baseline, expected=baseline,
                                 backend_active=True, endpoint_authenticated=True,
                                 endpoint_idle=True, gpu_holders=())

    def test_plan_is_effect_ordered(self):
        actions = plan()
        self.assertLess(actions.index("quiesce-registered-aster-speech-and-news-consumers"),
                        actions.index("run-d4-candidate-h-once-to-its-separate-journal-and-result"))
        self.assertLess(actions.index("run-m3-nlu-calibration-once-to-its-separate-journal-and-result"),
                        actions.index("restore-exact-production-unit-and-timer-baseline"))


if __name__ == "__main__":
    unittest.main()
