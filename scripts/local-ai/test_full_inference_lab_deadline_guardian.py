import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from full_inference_lab_deadline_guardian import (GuardianError, fence_owner_unit,
                                                  run_guardian)


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
                                 owner_fence=lambda budget: True,
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
                                 owner_fence=lambda budget: fenced.append(budget) or True,
                                 rescue_command_factory=lambda lease, generation: ("rescue", lease, str(generation)),
                                 clock=lambda: now[0], sleep=sleep, runner=runner)
            self.assertEqual(value["state"], "rescued")
            self.assertEqual(calls, [("rescue", "owner-1:123", "1")])
            self.assertEqual(len(fenced), 1)

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
                             owner_fence=lambda budget: True,
                             rescue_command_factory=lambda *_: ("rescue",),
                             clock=lambda: now[0], sleep=sleep,
                             runner=lambda *a, **k: failed)
            self.assertTrue(state.exists())

    def test_deadline_must_follow_cutoff(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(GuardianError, "follow"):
                run_guardian(state_path=Path(tmp) / "state", rescue_at=10,
                             hard_deadline=10, owner_id="owner-1",
                             owner_fence=lambda budget: True,
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
                                 owner_id="owner-1", owner_fence=lambda budget: rescued.append("fenced") or True,
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
                             owner_id="owner-1", owner_fence=lambda budget: False,
                             rescue_command_factory=lambda *_: ("rescue",),
                             clock=lambda: now[0], sleep=sleep,
                             runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("rescue ran")))

    def test_owner_zero_token_is_preserved_in_discovered_rescue(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            def sleep(seconds):
                now[0] += seconds
                state.write_text(json.dumps({"owner_id": "0", "mode": "full-inference-drain-v1",
                                              "lease_id": "0:123", "generation": 0 + 1,
                                              "phase": "drained"}), encoding="utf-8")
            calls = []
            result = run_guardian(
                state_path=state, rescue_at=110, hard_deadline=125, owner_id="0",
                owner_fence=lambda budget: True,
                rescue_command_factory=lambda lease, generation: ("rescue", lease, str(generation)),
                clock=lambda: now[0], sleep=sleep,
                runner=lambda command, **kwargs: calls.append(command) or state.unlink()
                or type("Result", (), {"returncode": 0})())
            self.assertEqual(result["state"], "rescued")
            self.assertEqual(calls, [("rescue", "0:123", "1")])

    def test_owner_fence_requires_zero_tasks_and_main_pid(self):
        class Result:
            def __init__(self, code, stdout="", stderr=""):
                self.returncode, self.stdout, self.stderr = code, stdout, stderr
        def busy(command, **kwargs):
            if command[1] == "is-active":
                return Result(3, "failed\n")
            if "TasksCurrent" in command:
                return Result(0, "1\n")
            return Result(0, "1234\n")
        self.assertFalse(fence_owner_unit("aster-local-ai-pilot-owner-x.scope", 20, runner=busy))

        def empty(command, **kwargs):
            if command[1] == "is-active":
                return Result(3, "failed\n")
            return Result(0, "0\n")
        self.assertTrue(fence_owner_unit("aster-local-ai-pilot-owner-x.scope", 20, runner=empty))

    def test_owner_fence_accepts_a_collected_not_found_scope(self):
        class Result:
            def __init__(self, code, stdout="", stderr=""):
                self.returncode, self.stdout, self.stderr = code, stdout, stderr
        def collected(command, **kwargs):
            if command[1] == "is-active":
                return Result(4, "inactive\n")
            if any("LoadState" in part for part in command):
                return Result(0, "not-found\n")
            if any("TasksCurrent" in part for part in command):
                return Result(0, "[not set]\n")
            return Result(0, "\n")
        self.assertTrue(fence_owner_unit(
            "aster-local-ai-pilot-owner-x.scope", 20, runner=collected))

    def test_owner_fence_checks_share_one_cumulative_budget(self):
        now = [0.0]
        timeouts = []
        class Result:
            def __init__(self, code=0, stdout="0\n"):
                self.returncode, self.stdout, self.stderr = code, stdout, ""
        def consuming(command, **kwargs):
            timeouts.append(kwargs["timeout"])
            now[0] += kwargs["timeout"]
            return Result(3, "failed\n") if command[1] == "is-active" else Result()
        self.assertFalse(fence_owner_unit("aster-local-ai-pilot-owner-x.scope", 15,
                                          runner=consuming, monotonic=lambda: now[0]))
        self.assertEqual(timeouts, [15.0])

    def test_rescue_timeout_is_bounded_by_remaining_reserve(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            seen = []
            failed = type("Result", (), {"returncode": 1})()
            def sleep(seconds):
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
                now[0] = 110.0 if now[0] < 110.0 else 125.0
            with self.assertRaisesRegex(GuardianError, "did not clear"):
                run_guardian(
                    state_path=state, rescue_at=110, hard_deadline=125,
                    owner_id="owner-1", owner_fence=lambda budget: True,
                    rescue_command_factory=lambda *_: ("rescue",),
                    clock=lambda: now[0], sleep=sleep,
                    runner=lambda command, **kwargs: seen.append(kwargs["timeout"]) or failed)
            self.assertEqual(seen, [15.0])

    def test_rescue_can_use_five_minutes_when_reserve_allows(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            seen=[]
            result=type("Result",(),{"returncode":0})()
            now=[99.0]
            def sleep(_):
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
                now[0]=100.0
            def execute(command, **kwargs):
                seen.append(kwargs["timeout"]); state.unlink(); return result
            value=run_guardian(state_path=state,rescue_at=100,hard_deadline=500,
                owner_id="owner-1",owner_fence=lambda budget:True,
                rescue_command_factory=lambda *_:("rescue",),clock=lambda:now[0],
                sleep=sleep,runner=execute)
            self.assertEqual(value["state"],"rescued")
            self.assertEqual(seen,[300.0])

    def test_rescue_timeout_exception_becomes_controlled_expiry(self):
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            now = [100.0]
            def sleep(seconds):
                state.write_text(json.dumps({"owner_id": "owner-1", "mode": "full-inference-drain-v1",
                                              "lease_id": "owner-1:123", "generation": 1,
                                              "phase": "drained"}), encoding="utf-8")
                now[0] = 110.0 if now[0] < 110.0 else 125.0
            with self.assertRaisesRegex(GuardianError, "did not clear"):
                run_guardian(
                    state_path=state, rescue_at=110, hard_deadline=125,
                    owner_id="owner-1", owner_fence=lambda budget: True,
                    rescue_command_factory=lambda *_: ("rescue",),
                    clock=lambda: now[0], sleep=sleep,
                    runner=lambda *a, **k: (_ for _ in ()).throw(
                        subprocess.TimeoutExpired(a[0], k["timeout"])))

    def test_owner_stop_timeout_is_fail_closed(self):
        def timed_out(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        self.assertFalse(fence_owner_unit("aster-local-ai-pilot-owner-x.scope", 15,
                                          runner=timed_out))


if __name__ == "__main__":
    unittest.main()
