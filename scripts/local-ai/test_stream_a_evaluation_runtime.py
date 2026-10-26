import unittest
from unittest.mock import Mock, patch

import stream_a_evaluation_runtime as subject
from stream_a_evaluation_evidence_loader import EvidenceExpectation
from stream_a_evaluation_live_plan import AcceptedEvidence
from stream_a_evaluation_sequence import VerifiedOutcome


class RuntimeCompositionTests(unittest.TestCase):
    def expectation(self):
        return EvidenceExpectation(
            "2026-10-27", "0123456789abcdef",
            "stream-a-evaluation-admission-sha256:" + "d" * 64,
        )

    def accepted(self):
        return AcceptedEvidence(
            cycle_date="2026-10-27", nonce="0123456789abcdef",
            now_epoch=100_000,
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            f2_receipt="f2-result-sha256:" + "b" * 64,
            f3_receipt="f3-receipt-sha256:" + "c" * 64,
            admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
        )

    @patch.object(subject, "FixedEffectDriver")
    @patch.object(subject, "FixedHandlers")
    @patch.object(subject, "HostOutcomeVerifier")
    @patch.object(subject, "RestoredProductionVerifier")
    @patch.object(subject, "load_accepted_evidence")
    def test_build_loads_evidence_before_wiring_fixed_graph(
            self, load, restored_type, outcome_type, handlers_type, driver_type):
        load.return_value = self.accepted()
        restored = restored_type.return_value
        outcome = outcome_type.return_value
        handlers = handlers_type.return_value
        driver = driver_type.return_value
        runner = Mock()
        with patch.object(subject.subprocess, "run", runner), \
                patch.object(subject, "_clock", return_value=100_000):
            runtime = subject.build_runtime(self.expectation(), now_minute=100)
        load.assert_called_once()
        self.assertEqual(load.call_args.kwargs["now_epoch"], 100_000)
        self.assertEqual(load.call_args.kwargs["required_uid"], 0)
        restored_type.assert_called_once()
        outcome_type.assert_called_once_with(runner=runner)
        self.assertIs(handlers_type.call_args.kwargs["outcome_verifier"], outcome)
        self.assertIs(handlers_type.call_args.kwargs["restored_verifier"], restored)
        self.assertIs(driver_type.call_args.kwargs["arm_handler"], handlers.arm)
        self.assertIs(driver_type.call_args.kwargs["workload_handler"], handlers.workload)
        fixed = runtime.plan.command("acquire")
        mapped = driver_type.call_args.kwargs["path_mapper"](__import__("pathlib").Path(fixed[4]))
        self.assertEqual(str(mapped), fixed[4])
        self.assertIs(runtime.driver, driver)

    @patch.object(subject, "execute")
    def test_run_has_only_fixed_plan_driver_and_clock(self, execute):
        expected = (
            VerifiedOutcome("d4-candidate-h", "a" * 64, "b" * 64, 12, 5),
            VerifiedOutcome("m3-nlu-calibration", "c" * 64, "d" * 64, 60, 9),
        )
        execute.return_value = expected
        plan = Mock(); driver = Mock(); clock = Mock()
        runtime = subject.EvaluationRuntime(plan, driver, clock)
        self.assertEqual(runtime.run(), expected)
        execute.assert_called_once_with(plan, driver, clock=clock)

    @patch.object(subject, "load_accepted_evidence", side_effect=ValueError("no-go"))
    def test_failed_evidence_load_wires_nothing(self, _load):
        with patch.object(subject, "FixedHandlers") as handlers, \
                self.assertRaises(ValueError):
            subject.build_runtime(self.expectation(), now_minute=100,
                                  )
        handlers.assert_not_called()


if __name__ == "__main__":
    unittest.main()
