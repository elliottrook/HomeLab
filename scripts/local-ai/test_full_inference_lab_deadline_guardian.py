import json
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
                                 owner_id="owner-1",
                                 owner_fence=lambda: True,
                                 rescue_command_factory=lambda *_: ("rescue",),
                                 clock=lambda: now[0], sleep=sleep,
                                 runner=lambda *a, **k: calls.append(a) or None)
            self.assertEqual(value["effects"], "not-attempted")
            self.assertEqual(calls, [])

    def test_cutoff_invokes_rescue_and_requires_state_clear(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            calls = []
            fenced = []
            def runner(*args, **kwargs):
                calls.append(args[0])
                state.unlink()
                return type("Result", (), {"returncode": 0})()
            def sleep(seconds):
                now[0] += seconds
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
            value = run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                                 owner_id="owner-1",
                                 owner_fence=lambda: fenced.append(True) or True,
                                 rescue_command_factory=lambda lease, generation: ("rescue", lease, str(generation)),
                                 clock=lambda: now[0], sleep=sleep, runner=runner)
            self.assertEqual(value["state"], "rescued")
            self.assertEqual(calls, [("rescue", "owner-1:123", "1")])
            self.assertEqual(fenced, [True])

    def test_failed_rescue_retains_state_and_expires(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            def sleep(seconds):
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
                now[0] += seconds
            failed = type("Result", (), {"returncode": 1})()
            with self.assertRaisesRegex(GuardianError, "did not clear"):
                run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                             owner_id="owner-1",
                             owner_fence=lambda: True,
                             rescue_command_factory=lambda *_: ("rescue",),
                             clock=lambda: now[0], sleep=sleep,
                             runner=lambda *a, **k: failed)
            self.assertTrue(state.exists())

    def test_deadline_must_follow_cutoff(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(GuardianError, "follow"):
                run_guardian(state_path=Path(tmp) / "state", rescue_at=10,
                             hard_deadline=10, owner_id="owner-1",
                             owner_fence=lambda: True,
                             rescue_command_factory=lambda *_: ("rescue",), clock=lambda: 0)

    def test_hung_owner_fence_is_required_before_rescue(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            def sleep(seconds):
                now[0] += seconds
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
            rescued = []
            value = run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                                 owner_id="owner-1", owner_fence=lambda: rescued.append("fenced") or True,
                                 rescue_command_factory=lambda *_: rescued.append("rescued") or ("rescue",),
                                 clock=lambda: now[0], sleep=sleep,
                                 runner=lambda *a, **k: state.unlink() or type("Result", (), {"returncode": 0})())
            self.assertEqual(value["state"], "rescued")
            self.assertEqual(rescued, ["fenced", "rescued"])

    def test_failed_owner_fence_blocks_rescue(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            def sleep(seconds):
                now[0] += seconds
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
            with self.assertRaisesRegex(GuardianError, "fenced"):
                run_guardian(state_path=state, rescue_at=110, hard_deadline=125,
                             owner_id="owner-1", owner_fence=lambda: False,
                             rescue_command_factory=lambda *_: ("rescue",),
                             clock=lambda: now[0], sleep=sleep,
                             runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("rescue ran")))


if __name__ == "__main__":
    unittest.main()
