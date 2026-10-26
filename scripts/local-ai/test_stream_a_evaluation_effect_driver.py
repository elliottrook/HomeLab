import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from stream_a_evaluation_effect_driver import (
    EffectDriverError, FixedEffectDriver, decode_result, write_new_intent,
)
from stream_a_evaluation_live_plan import AcceptedEvidence, LivePlan
from stream_a_evaluation_sequence import VerifiedOutcome


def selected_plan():
    return LivePlan(AcceptedEvidence(
        cycle_date="2026-10-27", nonce="0123456789abcdef", now_epoch=100_000,
        backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
        f2_receipt="f2-result-sha256:" + "b" * 64,
        f3_receipt="f3-receipt-sha256:" + "c" * 64,
        admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
    ))


class EffectDriverTests(unittest.TestCase):
    def test_intent_write_is_canonical_private_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary); parent.chmod(0o700)
            path = parent / "acquire.json"
            write_new_intent(path, {"b": 2, "a": 1}, required_uid=os.geteuid())
            self.assertEqual(path.read_bytes(), b'{"a":1,"b":2}\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(EffectDriverError, "already exists"):
                write_new_intent(path, {"a": 2}, required_uid=os.geteuid())

    def test_phase_uses_distinct_fixed_paths_and_exact_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); root.chmod(0o700)
            commands = []
            def runner(command, **kwargs):
                commands.append(tuple(command))
                return subprocess.CompletedProcess(command, 0,
                    stdout=json.dumps({"effects": "workload-start-recorded"}), stderr="")
            driver = FixedEffectDriver(
                selected_plan(), runner=runner, arm_handler=lambda p: None,
                workload_handler=lambda n: VerifiedOutcome(n, "e" * 64, "f" * 64, 1, 1),
                recovery_handler=lambda p: True, cleanup_handler=lambda p: None,
                path_mapper=lambda path: root / path.name, required_uid=os.geteuid(),
            )
            driver.phase("start", selected_plan().start("d4-candidate-h", 100_001))
            driver.phase("start", selected_plan().start("m3-nlu-calibration", 100_002))
            self.assertTrue((root / "d4-start.json").exists())
            self.assertTrue((root / "m3-start.json").exists())
            self.assertEqual(commands[0][0], "/usr/local/sbin/stream-a-evaluation-lease")
            self.assertEqual(commands[0][4],
                "/var/lib/local-ai-lab/stream-a-evaluation/intents/d4-start.json")

    def test_driver_rejects_stderr_nonzero_duplicate_result_and_plan_switch(self):
        self.assertEqual(decode_result('{"effects":"prepared"}'), {"effects": "prepared"})
        with self.assertRaises(EffectDriverError):
            decode_result('{"effects":"a","effects":"b"}')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); root.chmod(0o700)
            for result in (
                subprocess.CompletedProcess((), 1, stdout="{}", stderr=""),
                subprocess.CompletedProcess((), 0, stdout="{}", stderr="warning"),
            ):
                with self.subTest(result=result):
                    driver = FixedEffectDriver(
                        selected_plan(), runner=lambda *a, **k: result,
                        arm_handler=lambda p: None,
                        workload_handler=lambda n: VerifiedOutcome(n, "e" * 64, "f" * 64, 1, 1),
                        recovery_handler=lambda p: True, cleanup_handler=lambda p: None,
                        path_mapper=lambda path: root / (str(result.returncode) + path.name),
                        required_uid=os.geteuid(),
                    )
                    with self.assertRaises(EffectDriverError):
                        driver.phase("acquire", selected_plan().acquire())
            other = LivePlan(AcceptedEvidence(
                **{**selected_plan().evidence.__dict__, "nonce": "fedcba9876543210"}
            ))
            driver = FixedEffectDriver(
                selected_plan(), runner=lambda *a, **k: None,
                arm_handler=lambda p: None,
                workload_handler=lambda n: VerifiedOutcome(n, "e" * 64, "f" * 64, 1, 1),
                recovery_handler=lambda p: True, cleanup_handler=lambda p: None,
            )
            with self.assertRaises(EffectDriverError):
                driver.arm(other)


if __name__ == "__main__":
    unittest.main()
