import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from full_inference_lab_deadline_guardian import GuardianError, run_guardian


class DeadlineGuardianTests(unittest.TestCase):
    def test_normal_completion_exits_without_rescue(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            calls = []
            def sleep(seconds):
                now[0] += seconds
                state.unlink(missing_ok=True)
            value = run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                                 command=("rescue",), clock=lambda: now[0], sleep=sleep,
                                 runner=lambda *a, **k: calls.append(a) or None)
            self.assertEqual(value["effects"], "not-attempted")
            self.assertEqual(calls, [])

    def test_cutoff_invokes_rescue_and_requires_state_clear(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            state.write_text("lease\n", encoding="utf-8")
            now = [110.0]
            calls = []
            def runner(*args, **kwargs):
                calls.append(args[0])
                state.unlink()
                return type("Result", (), {"returncode": 0})()
            value = run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                                 command=("rescue",), clock=lambda: now[0],
                                 sleep=lambda seconds: None, runner=runner)
            self.assertEqual(value["state"], "rescued")
            self.assertEqual(calls, [("rescue",)])

    def test_failed_rescue_retains_state_and_expires(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            state.write_text("lease\n", encoding="utf-8")
            now = [110.0]
            def sleep(seconds):
                now[0] += seconds
            failed = type("Result", (), {"returncode": 1})()
            with self.assertRaisesRegex(GuardianError, "did not clear"):
                run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                             command=("rescue",), clock=lambda: now[0], sleep=sleep,
                             runner=lambda *a, **k: failed)
            self.assertTrue(state.exists())

    def test_deadline_must_follow_cutoff(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(GuardianError, "follow"):
                run_guardian(state_path=Path(tmp) / "state", rescue_at=10,
                             hard_deadline=10, command=("rescue",), clock=lambda: 0)


if __name__ == "__main__":
    unittest.main()
