import unittest

from evaluation_lease import WorkloadOutcome, validate_outcome, workload
from evaluation_lease_entrypoint import validate_phase_intent
from stream_a_evaluation_live_plan import (
    D4_COMMAND, GENERATION, M3_COMMAND, AcceptedEvidence, LivePlan,
    LivePlanError, restoration_reserve_seconds,
)


def evidence(**changes):
    values = {
        "cycle_date": "2026-10-27", "nonce": "0123456789abcdef",
        "now_epoch": 100_000,
        "backup_receipt": "retained-archive-integrity-sha256:" + "a" * 64,
        "f2_receipt": "f2-result-sha256:" + "b" * 64,
        "f3_receipt": "f3-receipt-sha256:" + "c" * 64,
        "admission_receipt": "stream-a-evaluation-admission-sha256:" + "d" * 64,
    }
    values.update(changes)
    return AcceptedEvidence(**values)


class LivePlanTests(unittest.TestCase):
    def test_builds_exact_acquire_and_phase_schemas(self):
        plan = LivePlan(evidence())
        self.assertEqual(plan.lease_id, "stream-a-evaluation-2026-10-27-0123456789abcdef")
        self.assertEqual(plan.owner_id, "stream-a-evaluation-owner-0123456789abcdef")
        self.assertEqual(plan.owner_intent(), {
            "lease_id": plan.lease_id, "generation": GENERATION,
            "heartbeat_timeout": 45, "owner_id": plan.owner_id,
        })
        validate_phase_intent("acquire", plan.acquire())
        validate_phase_intent("quiesce", plan.quiesce(100_001))
        validate_phase_intent("heartbeat", plan.heartbeat(100_002))
        validate_phase_intent("post-quiescence", plan.post_quiescence(100_003))
        validate_phase_intent("start", plan.start("d4-candidate-h", 100_004))
        outcome = plan.outcome(
            name="d4-candidate-h", journal_digest="e" * 64,
            result_digest="f" * 64, calls=36, elapsed_seconds=120,
            now_epoch=100_124,
        )
        validate_phase_intent("outcome", outcome)
        validate_outcome(WorkloadOutcome(
            outcome["lease_id"], outcome["generation"], outcome["name"],
            outcome["packet_digest"], outcome["status"],
            outcome["journal_digest"], outcome["result_digest"],
            outcome["calls"], outcome["elapsed_seconds"],
            outcome["tool_free"], outcome["transport_uncertain"],
        ), expected=workload("d4-candidate-h"),
            lease_id=plan.lease_id, generation=GENERATION)
        validate_phase_intent("start", plan.start("m3-nlu-calibration", 100_125))
        validate_phase_intent("restore", plan.restore(recovery=False))

    def test_fixes_commands_paths_and_reserve(self):
        plan = LivePlan(evidence())
        self.assertEqual(D4_COMMAND[-1], "aster-d4-candidate-h.service")
        self.assertIn("nlu_calibration_runner.py", M3_COMMAND[-1])
        self.assertIn("--key-file /etc/aster-llama-api-keys", M3_COMMAND[-1])
        self.assertEqual(plan.command("acquire"), (
            "/usr/local/sbin/stream-a-evaluation-lease", "--phase", "acquire",
            "--intent", "/var/lib/local-ai-lab/stream-a-evaluation/intents/acquire.json",
            "--effect-authorized",
        ))
        self.assertEqual(restoration_reserve_seconds(), 900)

    def test_rejects_operator_choice_and_bad_bounds(self):
        for changed in (
            {"cycle_date": "tomorrow"}, {"nonce": "ABC"}, {"now_epoch": 0},
            {"f2_receipt": "b" * 64}, {"admission_receipt": "d" * 64},
        ):
            with self.subTest(changed=changed), self.assertRaises(LivePlanError):
                LivePlan(evidence(**changed))
        plan = LivePlan(evidence())
        with self.assertRaises(LivePlanError):
            plan.start("chosen-by-operator", 100_001)
        with self.assertRaises(LivePlanError):
            plan.outcome(name="m3-nlu-calibration", journal_digest="e" * 64,
                         result_digest="f" * 64, calls=61,
                         elapsed_seconds=1, now_epoch=100_001)
        with self.assertRaises(LivePlanError):
            plan.command("operator-phase")
        with self.assertRaises(LivePlanError):
            plan.outcome(name="d4-candidate-h", journal_digest="e" * 64,
                         result_digest="f" * 64, calls=1,
                         elapsed_seconds=2161, now_epoch=100_001)
        with self.assertRaises(LivePlanError):
            plan.heartbeat(plan.restore_deadline_epoch)


if __name__ == "__main__":
    unittest.main()
