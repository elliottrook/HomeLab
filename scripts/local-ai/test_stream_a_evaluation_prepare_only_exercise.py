import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import stream_a_evaluation_prepare_only_exercise as exercise


class FakeHost:
    def __init__(self, root: Path, identity: Path, *, fail_healthy=False):
        self.root = root; self.identity = identity; self.calls = []
        self.watchdogs = 0; self.fail_healthy = fail_healthy

    def __call__(self, argv, timeout):
        argv = tuple(argv); self.calls.append(argv)
        if argv == (exercise.WHOLE_HOST_LEASE, "status"):
            return exercise.Result(0, '{"state":"ready"}\n')
        if argv[:2] == ("pct", "exec"):
            action = argv[5]
            return exercise.Result(0, "enabled\n" if action == "is-enabled" else "active\n")
        if argv[:2] == ("systemctl", "is-enabled"):
            return exercise.Result(1, "disabled\n")
        if argv[:2] == ("systemctl", "is-active"):
            return exercise.Result(3, "inactive\n")
        if argv[:2] == ("systemctl", "show"):
            return exercise.Result(0, f"Id={argv[2]}\nActiveState=active\nUnit=x\nNextElapseUSecRealtime=soon\n")
        if argv[0] == exercise.RESTORE_OBSERVER:
            return exercise.Result(0, json.dumps({"lease_id": argv[2], "generation": int(argv[4]),
                "observed_at": 1000, "backend_active": True, "endpoint_authenticated": True,
                "endpoint_idle": True, "gpu_holders": ["lxc110:aster-llama.service"]}) + "\n")
        if argv[0] == exercise.LEASE_ENTRYPOINT:
            intent = json.loads((self.root / "exercise-intent.json").read_text())
            (self.root / "lease.json").write_text("state")
            (self.root / "lease.lock").mkdir(); (self.root / "lease.operation.lock").write_text("lock")
            return exercise.Result(0, json.dumps({"effects":"exercise-prepared", "state":"prepared",
                "mode":exercise.MODE, "lease_id":intent["lease_id"], "generation":1}) + "\n")
        if argv[0] == exercise.OWNER_START:
            self.identity.parent.mkdir(parents=True, exist_ok=True); self.identity.write_text("identity")
            return exercise.Result(0, "started\n")
        if argv[0] == exercise.HEARTBEAT_ENTRYPOINT:
            (self.root / "owner-heartbeat.json").write_text("heartbeat")
            return exercise.Result(0, '{"effects":"heartbeat-written"}\n')
        if argv[0] == exercise.WATCHDOG_ENTRYPOINT:
            self.watchdogs += 1
            if self.watchdogs == 1:
                if self.fail_healthy:
                    return exercise.Result(0, '{"decision":"healthy","effects":"disabled"}\n')
                return exercise.Result(0, '{"decision":"healthy","effects":"not-attempted"}\n')
            (self.root / "lease.json").unlink(); (self.root / "lease.lock").rmdir()
            (self.root / "lease.operation.lock").unlink()
            (self.root / "restore-intent.json").write_text("restore")
            return exercise.Result(0, '{"decision":"owner-absent","effects":"recovered","result":{"entrypoint":"restored","stdout":"{\\"effects\\":\\"cancelled-prepared\\",\\"lease_id\\":\\"EXERCISE_ID\\",\\"generation\\":1}"}}\n'.replace("EXERCISE_ID", json.loads((self.root / "exercise-intent.json").read_text())["lease_id"]))
        if argv[:2] == ("systemctl", "stop"):
            return exercise.Result(0, "")
        if argv[:2] == ("systemctl", "reset-failed"):
            return exercise.Result(1, "")
        raise AssertionError(argv)


def test_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n"); path.chmod(0o600)


def test_unlink(path):
    try: path.unlink()
    except FileNotFoundError: pass


class ExerciseTests(unittest.TestCase):
    def test_default_cli_is_inert(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(exercise.Exercise, "execute", side_effect=AssertionError):
            self.assertEqual(exercise.main(["--run-once"]), 0)
        self.assertEqual(json.loads(output.getvalue()), {"effects":"disabled", "state":"source-only"})

    def test_successful_sequence_is_prepare_only_and_cleans_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "state"; identity = Path(tmp) / "etc" / "identity.json"
            receipts = Path(tmp) / "receipts"; receipts.mkdir(mode=0o700)
            host = FakeHost(root, identity)
            runner = exercise.Exercise(host, clock=lambda: 1000, sleep=lambda _seconds: None,
                                       root=root, identity=identity, receipt_root=receipts)
            with patch.object(exercise.os, "geteuid", return_value=0), \
                 patch.object(exercise, "_root_json", side_effect=test_json), \
                 patch.object(exercise, "_safe_unlink", side_effect=test_unlink), \
                 patch.object(runner, "verify_static_custody", return_value=None), \
                 patch.object(runner, "validate_prepared_state", return_value=None), \
                 patch.object(runner, "validate_owner_identity", return_value=None):
                result = runner.execute()
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["consumer_commands"], 0)
            self.assertEqual(host.watchdogs, 2)
            self.assertFalse((root / "lease.json").exists())
            self.assertFalse(identity.exists())
            self.assertEqual(len(list(receipts.glob("*.json"))), 1)
            flat = "\n".join(" ".join(row) for row in host.calls)
            self.assertNotIn(" quiesce", flat); self.assertNotIn(" post-quiescence", flat)
            self.assertNotIn(" outcome", flat); self.assertNotIn("chat/completions", flat)

    def test_uncertain_healthy_check_retains_prepared_state_and_stops_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "state"; identity = Path(tmp) / "etc" / "identity.json"
            receipts = Path(tmp) / "receipts"; receipts.mkdir(mode=0o700)
            host = FakeHost(root, identity, fail_healthy=True)
            runner = exercise.Exercise(host, clock=lambda: 1000, sleep=lambda _seconds: None,
                                       root=root, identity=identity, receipt_root=receipts)
            with patch.object(exercise.os, "geteuid", return_value=0), \
                 patch.object(exercise, "_root_json", side_effect=test_json), \
                 patch.object(exercise, "_safe_unlink", side_effect=test_unlink), \
                 patch.object(runner, "verify_static_custody", return_value=None), \
                 patch.object(runner, "validate_prepared_state", return_value=None), \
                 patch.object(runner, "validate_owner_identity", return_value=None):
                with self.assertRaises(exercise.ExerciseError): runner.execute()
            self.assertTrue((root / "lease.json").exists())
            self.assertTrue(identity.exists())
            self.assertFalse(list(receipts.glob("*.json")))
            self.assertIn(("systemctl", "stop", exercise.EXERCISE_UNIT), host.calls)

    def test_existing_runtime_state_fails_before_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "lease.json").write_text("x")
            calls = []
            runner = exercise.Exercise(lambda argv, timeout: calls.append(argv), root=root,
                                       identity=root / "identity", receipt_root=root / "receipts")
            with self.assertRaises(exercise.ExerciseError): runner.prestate("exercise-x")
            self.assertEqual(calls, [])

    def test_duplicate_json_and_extra_recovery_fields_fail_closed(self):
        with self.assertRaises(exercise.ExerciseError): exercise._load_json('{"state":"ready","state":"ready"}', {"state"})
        with self.assertRaises(exercise.ExerciseError): exercise._load_json('{"effects":"recovered","decision":"x","result":{},"extra":1}', {"effects","decision","result"})

    def test_deployed_wrapper_targets_effectful_watchdog_cli(self):
        wrapper = Path(__file__).parents[2] / "services/local-ai-lease/stream-a-evaluation-watchdog"
        data = wrapper.read_bytes()
        self.assertIn(b"stream_a_evaluation_watchdog.py", data)
        self.assertNotIn(b"evaluation_lease_watchdog.py", data)
        self.assertEqual(exercise.PINNED_FILES[exercise.WATCHDOG_ENTRYPOINT],
                         __import__("hashlib").sha256(data).hexdigest())

    def test_runner_denies_consumer_model_and_production_systemd_mutations(self):
        runner = exercise.Exercise(lambda argv, timeout: exercise.Result(0, ""))
        for command in (
                ("systemctl", "stop", "stream-a-evaluation-owner.service"),
                ("pct", "exec", "104", "--", "systemctl", "stop", "aster-agent.service"),
                ("curl", "http://127.0.0.1:11435/v1/chat/completions"),):
            with self.assertRaises(exercise.ExerciseError):
                runner.run(command)

    def test_guest_pins_are_checked_in_lxc110_with_exact_custody(self):
        calls = []
        def command(argv, _timeout):
            argv = tuple(argv); calls.append(argv); path = argv[-1]
            if argv[4] == "stat":
                mode = "755" if path.endswith("production-auth-probe") else "644"
                return exercise.Result(0, f"0:{mode}\n")
            if argv[4] == "sha256sum":
                digest = exercise.GUEST_PINNED_FILES[("110", path)][0]
                return exercise.Result(0, f"{digest}  {path}\n")
            return exercise.Result(0, "")
        runner = exercise.Exercise(command)
        runner.verify_guest_custody()
        self.assertEqual(len(calls), 8)
        self.assertTrue(all(call[:4] == ("pct", "exec", "110", "--") for call in calls))

    def test_guest_pin_hash_mismatch_fails_closed(self):
        def command(argv, _timeout):
            path = argv[-1]
            if argv[4] == "stat":
                mode = "755" if path.endswith("production-auth-probe") else "644"
                return exercise.Result(0, f"0:{mode}\n")
            if argv[4] == "sha256sum":
                return exercise.Result(0, f"{'0' * 64}  {path}\n")
            return exercise.Result(0, "")
        with self.assertRaises(exercise.ExerciseError):
            exercise.Exercise(command).verify_guest_custody()


if __name__ == "__main__": unittest.main()
