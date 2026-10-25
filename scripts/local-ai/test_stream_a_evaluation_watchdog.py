import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation_lease import LEASE_MODE, PRODUCTION_BASELINE_STATES
from evaluation_lease import watchdog_decision
from evaluation_lease_adapter import AdapterState
from stream_a_evaluation_watchdog import (
    WatchdogBoundaryError,
    WatchdogIdentity,
    _restore_callback,
    load_owner_heartbeat,
    load_identity,
    main,
    owner_process_matches,
    run_watchdog_once,
    write_status,
    write_owner_heartbeat,
)


class WatchdogBoundaryTests(unittest.TestCase):
    def identity(self):
        return WatchdogIdentity("eval-1", 1, 30, "owner-1", 42, "boot-1", 99,
                                "/usr/local/bin/owner", "owner.service")

    def state(self):
        from evaluation_lease import ProductionBaseline
        baseline = ProductionBaseline(
            units=PRODUCTION_BASELINE_STATES[:2], timers=PRODUCTION_BASELINE_STATES[2:])
        return AdapterState("eval-1", 1, LEASE_MODE, None, "running", baseline, 1000, 1010,
                            5500, 6400, "d4-candidate-g", None, ())

    def write(self, path, value):
        path.write_text(json.dumps(value) + "\n")
        path.chmod(0o600)

    def test_missing_foreign_and_malformed_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "identity.json"
            with self.assertRaises(WatchdogBoundaryError):
                load_identity(path, required_uid=__import__("os").geteuid())
            self.write(path, {"lease_id": "x", "generation": 1,
                              "heartbeat_timeout": 30, "owner_id": "owner-1",
                              "extra": 1})
            with self.assertRaises(WatchdogBoundaryError):
                load_identity(path, required_uid=__import__("os").geteuid())

    def test_stale_and_foreign_owner_heartbeat_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "heartbeat.json"
            self.write(path, {"lease_id": "eval-1", "generation": 1,
                              "owner_id": "owner-1", "heartbeat_epoch": 100,
                              "expires_epoch": 130, "pid": 42, "boot_id": "boot-1",
                              "starttime_ticks": 99, "cmdline": "/usr/local/bin/owner",
                              "unit": "owner.service"})
            heartbeat = load_owner_heartbeat(path, identity=self.identity(), now_epoch=130,
                                             required_uid=__import__("os").geteuid())
            self.assertEqual(heartbeat.expires_epoch, 130)
            self.write(path, {"lease_id": "foreign", "generation": 1,
                              "owner_id": "owner-1", "heartbeat_epoch": 100,
                              "expires_epoch": 130, "pid": 42, "boot_id": "boot-1",
                              "starttime_ticks": 99, "cmdline": "/usr/local/bin/owner",
                              "unit": "owner.service"})
            with self.assertRaises(WatchdogBoundaryError):
                load_owner_heartbeat(path, identity=self.identity(), now_epoch=110,
                                     required_uid=__import__("os").geteuid())

    def test_heartbeat_restart_replaces_only_current_owner_record(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "heartbeat.json"
            identity = self.identity()
            with patch("stream_a_evaluation_watchdog.os.geteuid", return_value=0), \
                 patch("stream_a_evaluation_watchdog.owner_process_matches", return_value=True):
                write_owner_heartbeat(path, identity=identity, now_epoch=100)
                write_owner_heartbeat(path, identity=identity, now_epoch=110)
            value = json.loads(path.read_text())
            self.assertEqual(value["heartbeat_epoch"], 110)
            self.assertEqual(value["expires_epoch"], 140)

    def test_owner_death_and_pid_reuse_fail_identity_match(self):
        identity = self.identity()
        self.assertTrue(owner_process_matches(identity, snapshot=lambda value: {
            "boot_id": value.boot_id, "starttime_ticks": value.starttime_ticks,
            "cmdline": value.cmdline, "unit": value.unit,
        }))
        self.assertFalse(owner_process_matches(identity, snapshot=lambda value: {
            "boot_id": value.boot_id, "starttime_ticks": value.starttime_ticks + 1,
            "cmdline": value.cmdline, "unit": value.unit,
        }))

    def test_lost_owner_runs_bound_recovery_without_resuming_workload(self):
        state = self.state()
        called = []
        def bound(**kwargs):
            called.append(kwargs)
            return {"effects": "recovered", "decision": "owner-absent"}
        with patch("stream_a_evaluation_watchdog.load_identity", return_value=self.identity()), \
             patch("stream_a_evaluation_watchdog.read_state", return_value=state), \
             patch("stream_a_evaluation_watchdog.run_bound_from_state", side_effect=bound):
            result = run_watchdog_once(
                state_path=Path("/state"), identity_path=Path("/identity"),
                heartbeat_path=Path("/missing-heartbeat"), now_epoch=120,
                effect_authorized=True, recovery=lambda value: "restored")
        self.assertEqual(result["effects"], "recovered")
        self.assertFalse(called[0]["owner_present"])
        self.assertIsNotNone(called[0]["recovery"])

    def test_identity_correct_expired_heartbeat_is_owner_absent(self):
        state = self.state()
        called = []
        with patch("stream_a_evaluation_watchdog.load_identity", return_value=self.identity()), \
             patch("stream_a_evaluation_watchdog.read_state", return_value=state), \
             patch("stream_a_evaluation_watchdog.load_owner_heartbeat", return_value=type("Heartbeat", (), {"expires_epoch": 120})()), \
             patch("stream_a_evaluation_watchdog.run_bound_from_state", side_effect=lambda **kwargs: called.append(kwargs) or {"effects": "recovered"}):
            result = run_watchdog_once(
                state_path=Path("/state"), identity_path=Path("/identity"),
                heartbeat_path=Path("/heartbeat"), now_epoch=130,
                effect_authorized=True, recovery=lambda value: "restored")
        self.assertEqual(result["effects"], "recovered")
        self.assertFalse(called[0]["owner_present"])

    def test_missing_foreign_or_malformed_state_fails_closed(self):
        for error in (ValueError("missing"), ValueError("foreign"), ValueError("malformed")):
            with self.subTest(error=str(error)):
                with patch("stream_a_evaluation_watchdog.load_identity", return_value=self.identity()), \
                     patch("stream_a_evaluation_watchdog.read_state", side_effect=error):
                    result = run_watchdog_once(
                        state_path=Path("/state"), identity_path=Path("/identity"),
                        heartbeat_path=Path("/heartbeat"), now_epoch=120,
                        effect_authorized=True, recovery=lambda value: "restored")
                self.assertEqual(result["effects"], "failed-closed")

    def test_deadline_and_heartbeat_recovery_are_delegated_bound(self):
        state = self.state()
        for now in (5500, 6400):
            with self.subTest(now=now):
                with patch("stream_a_evaluation_watchdog.load_identity", return_value=self.identity()), \
                     patch("stream_a_evaluation_watchdog.read_state", return_value=state), \
                     patch("stream_a_evaluation_watchdog.load_owner_heartbeat"), \
                     patch("stream_a_evaluation_watchdog.run_bound_from_state",
                           return_value={"effects": "recovered", "decision": "deadline"}) as bound:
                    heartbeat = type("Heartbeat", (), {"expires_epoch": now + 30})
                    with patch("stream_a_evaluation_watchdog.load_owner_heartbeat", return_value=heartbeat()):
                        result = run_watchdog_once(
                            state_path=Path("/state"), identity_path=Path("/identity"),
                            heartbeat_path=Path("/heartbeat"), now_epoch=now,
                            effect_authorized=True, recovery=lambda value: "restored")
                self.assertEqual(result["effects"], "recovered")
                self.assertTrue(bound.called)
        self.assertEqual(watchdog_decision(
            now_epoch=5500, heartbeat_epoch=1000, heartbeat_timeout=30,
            hard_deadline_epoch=5500, restore_deadline_epoch=6400,
            owner_present=True).action, "recover")
        self.assertEqual(watchdog_decision(
            now_epoch=1031, heartbeat_epoch=1000, heartbeat_timeout=30,
            hard_deadline_epoch=5500, restore_deadline_epoch=6400,
            owner_present=True).reason, "heartbeat-expired")

    def test_callback_failure_retains_restore_intent_and_exact_baseline(self):
        state = self.state()
        with tempfile.TemporaryDirectory() as root:
            intent = Path(root) / "restore-intent.json"
            responses = [subprocess.CompletedProcess(
                ["observer"], 0,
                json.dumps({"lease_id": "eval-1", "generation": 1,
                            "observed_at": int(time.time()), "backend_active": True,
                            "endpoint_authenticated": True, "endpoint_idle": True,
                            "gpu_holders": ["lxc110:aster-llama.service"]}), ""),
                        subprocess.CompletedProcess(["entrypoint"], 1, "", "failed")]
            def failed_runner(*args, **kwargs):
                return responses.pop(0)
            with patch("stream_a_evaluation_watchdog.OBSERVE_ENTRYPOINT", Path("observer")):
                with self.assertRaises(WatchdogBoundaryError):
                    _restore_callback(state, intent_path=intent, runner=failed_runner)
            payload = json.loads(intent.read_text())
            self.assertTrue(payload["recovery"])
            self.assertEqual(tuple(tuple(x) for x in payload["restored_baseline"]["units"]),
                             PRODUCTION_BASELINE_STATES[:2])
            self.assertEqual(tuple(tuple(x) for x in payload["restored_baseline"]["timers"]),
                             PRODUCTION_BASELINE_STATES[2:])

    def test_uncertain_cli_result_is_nonzero(self):
        with patch("stream_a_evaluation_watchdog.os.geteuid", return_value=0), \
             patch("stream_a_evaluation_watchdog.run_watchdog_once",
                   return_value={"effects": "uncertain", "decision": "restore-deadline"}), \
             patch("stream_a_evaluation_watchdog.write_status"):
            self.assertEqual(main(["--once", "--effect-authorized"]), 1)

    def test_status_is_atomic_and_preserves_failure_class(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "watchdog-status.json"
            write_status({"effects": "uncertain", "decision": "restore-deadline",
                          "error": "callback"}, path)
            self.assertEqual(json.loads(path.read_text()), {
                "decision": "restore-deadline", "effects": "uncertain", "error": "callback"})


if __name__ == "__main__":
    unittest.main()
