import unittest

from stream_a_evaluation_live_plan import AcceptedEvidence, LivePlan
from stream_a_evaluation_sequence import (
    SequenceError, SequenceRecoveryUncertain, VerifiedOutcome, execute,
)


def plan():
    return LivePlan(AcceptedEvidence(
        cycle_date="2026-10-27", nonce="0123456789abcdef", now_epoch=100_000,
        backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
        f2_receipt="f2-result-sha256:" + "b" * 64,
        f3_receipt="f3-receipt-sha256:" + "c" * 64,
        admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
    ))


class Driver:
    def __init__(self, *, fail_at=None, recover=True):
        self.calls = []
        self.fail_at = fail_at
        self.recovery = recover

    def _call(self, name):
        self.calls.append(name)
        if self.fail_at == name:
            raise RuntimeError(name)

    def arm(self, selected):
        self._call("arm")

    def phase(self, phase, payload):
        name = phase
        if phase in {"start", "outcome"}:
            name += ":" + str(payload.get("workload_name", payload.get("name")))
        self._call(name)
        effects = {
            "acquire": "prepared", "quiesce": "quiescing",
            "post-quiescence": "post-quiescence-recorded",
            "start": "workload-start-recorded", "outcome": "outcome-recorded",
            "restore": "restored",
        }
        return {"effects": effects[phase]}

    def run_workload(self, name):
        self._call("run:" + name)
        return VerifiedOutcome(name, "e" * 64, "f" * 64,
                               12 if name == "d4-candidate-h" else 60, 100)

    def recover(self, selected):
        self.calls.append("recover")
        if self.recovery == "raise":
            raise RuntimeError("recovery")
        return self.recovery

    def cleanup(self, selected):
        self.calls.append("cleanup")


class SequenceTests(unittest.TestCase):
    def test_exact_serial_order_uses_durable_phases(self):
        driver = Driver()
        now = iter(range(100_001, 100_020))
        d4, m3 = execute(plan(), driver, clock=lambda: next(now))
        self.assertEqual((d4.name, m3.name),
                         ("d4-candidate-h", "m3-nlu-calibration"))
        self.assertEqual(driver.calls, [
            "arm", "acquire", "quiesce", "post-quiescence",
            "start:d4-candidate-h", "run:d4-candidate-h",
            "outcome:d4-candidate-h", "start:m3-nlu-calibration",
            "run:m3-nlu-calibration", "outcome:m3-nlu-calibration",
            "restore", "cleanup",
        ])

    def test_d4_failure_forbids_m3_and_recovers(self):
        driver = Driver(fail_at="run:d4-candidate-h")
        now = iter(range(100_001, 100_020))
        with self.assertRaisesRegex(RuntimeError, "run:d4"):
            execute(plan(), driver, clock=lambda: next(now))
        self.assertNotIn("start:m3-nlu-calibration", driver.calls)
        self.assertEqual(driver.calls[-2:], ["recover", "cleanup"])

    def test_uncertain_recovery_retains_state_without_cleanup(self):
        for recovery in (False, "raise"):
            with self.subTest(recovery=recovery):
                driver = Driver(fail_at="quiesce", recover=recovery)
                now = iter(range(100_001, 100_020))
                with self.assertRaises(SequenceRecoveryUncertain):
                    execute(plan(), driver, clock=lambda: next(now))
                self.assertNotIn("cleanup", driver.calls)

    def test_foreign_workload_outcome_fails_before_outcome_phase(self):
        class ForeignDriver(Driver):
            def run_workload(self, name):
                self._call("run:" + name)
                return VerifiedOutcome("foreign", "e" * 64, "f" * 64, 1, 1)

        driver = ForeignDriver()
        now = iter(range(100_001, 100_020))
        with self.assertRaises(SequenceError):
            execute(plan(), driver, clock=lambda: next(now))
        self.assertNotIn("outcome:foreign", driver.calls)
        self.assertNotIn("start:m3-nlu-calibration", driver.calls)

    def test_nonexact_phase_result_recovers(self):
        class BadResultDriver(Driver):
            def phase(self, phase, payload):
                result = super().phase(phase, payload)
                if phase == "acquire":
                    return {"effects": "wrong"}
                return result

        driver = BadResultDriver()
        with self.assertRaises(SequenceError):
            execute(plan(), driver, clock=lambda: 100_001)
        self.assertEqual(driver.calls[-2:], ["recover", "cleanup"])


if __name__ == "__main__":
    unittest.main()
