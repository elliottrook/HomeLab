import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation_lease import PRODUCTION_BASELINE_STATES
from evaluation_lease import watchdog_decision
from evaluation_lease_adapter import AdapterState
from stream_a_evaluation_watchdog import (
    OwnerHeartbeat,
    WatchdogBoundaryError,
    WatchdogIdentity,
    _restore_callback,
    load_owner_heartbeat,
    load_identity,
    run_watchdog_once,
    write_owner_heartbeat,
)


class WatchdogBoundaryTests(unittest.TestCase):
    def identity(self):
        return WatchdogIdentity("eval-1", 1, 30, "owner-1")

    def state(self):
        from evaluation_lease import ProductionBaseline
        baseline = ProductionBaseline(
            units=PRODUCTION_BASELINE_STATES[:2], timers=PRODUCTION_BASELINE_STATES[2:])
        return AdapterState("eval-1", 1, "running", baseline, 1000, 1010,
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
                              "expires_epoch": 130})
            with self.assertRaises(WatchdogBoundaryError):
                load_owner_heartbeat(path, identity=self.identity(), now_epoch=130,
                                     required_uid=__import__("os").geteuid())
            self.write(path, {"lease_id": "foreign", "generation": 1,
                              "owner_id": "owner-1", "heartbeat_epoch": 100,
                              "expires_epoch": 130})
            with self.assertRaises(WatchdogBoundaryError):
                load_owner_heartbeat(path, identity=self.identity(), now_epoch=110,
                                     required_uid=__import__("os").geteuid())

    def test_heartbeat_restart_replaces_only_current_owner_record(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "heartbeat.json"
            identity = self.identity()
            with patch("stream_a_evaluation_watchdog.os.geteuid", return_value=0):
                write_owner_heartbeat(path, identity=identity, now_epoch=100)
                write_owner_heartbeat(path, identity=identity, now_epoch=110)
            value = json.loads(path.read_text())
            self.assertEqual(value["heartbeat_epoch"], 110)
            self.assertEqual(value["expires_epoch"], 140)

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
            observation = Path(root) / "observation.json"
            observation.write_text("{}\n")
            observation.chmod(0o600)
            def failed_runner(*args, **kwargs):
                return __import__("subprocess").CompletedProcess(args[0], 1, "", "failed")
            with patch("stream_a_evaluation_watchdog._read_root_json", return_value={
                "backend_active": True, "endpoint_authenticated": True,
                "endpoint_idle": True, "gpu_holders": ["lxc110:aster-llama.service"],
            }):
                with self.assertRaises(WatchdogBoundaryError):
                    _restore_callback(state, observation_path=observation,
                                      intent_path=intent, runner=failed_runner)
            payload = json.loads(intent.read_text())
            self.assertTrue(payload["recovery"])
            self.assertEqual(tuple(tuple(x) for x in payload["restored_baseline"]["units"]),
                             PRODUCTION_BASELINE_STATES[:2])
            self.assertEqual(tuple(tuple(x) for x in payload["restored_baseline"]["timers"]),
                             PRODUCTION_BASELINE_STATES[2:])


if __name__ == "__main__":
    unittest.main()
