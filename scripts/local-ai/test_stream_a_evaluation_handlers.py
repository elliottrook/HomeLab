import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from stream_a_evaluation_handlers import (
    HEARTBEAT_TIMER, OWNER_UNIT, WATCHDOG_COMMAND, WATCHDOG_TIMER,
    FixedHandlers, HandlerError, HandlerPaths,
)
from stream_a_evaluation_live_plan import AcceptedEvidence, D4_COMMAND, M3_COMMAND, LivePlan
from stream_a_evaluation_sequence import VerifiedOutcome
from stream_a_evaluation_watchdog import OwnerHeartbeat, WatchdogIdentity


def plan(root: Path) -> LivePlan:
    return LivePlan(AcceptedEvidence(
        cycle_date="2026-10-27", nonce="0123456789abcdef", now_epoch=100_000,
        backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
        f2_receipt="f2-result-sha256:" + "b" * 64,
        f3_receipt="f3-receipt-sha256:" + "c" * 64,
        admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
    ))


class FakeRun:
    def __init__(self):
        self.calls = []
        self.watchdog_results = [
            {"decision": "healthy", "effects": "not-attempted"},
            {"decision": "owner-absent", "effects": "recovered",
             "result": {"entrypoint": "restored", "stdout": "{}"}},
        ]

    def __call__(self, command, **kwargs):
        command = tuple(command); self.calls.append(command)
        if command[:2] == ("systemctl", "is-enabled"):
            return subprocess.CompletedProcess(command, 1, "disabled\n", "")
        if command[:2] == ("systemctl", "is-active"):
            return subprocess.CompletedProcess(command, 3, "inactive\n", "")
        if command == WATCHDOG_COMMAND:
            return subprocess.CompletedProcess(command, 0,
                json.dumps(self.watchdog_results.pop(0)) + "\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")


class HandlerTests(unittest.TestCase):
    def build(self, root: Path, runner=None):
        runtime = root / "runtime"; runtime.mkdir(mode=0o700)
        identity = root / "etc" / "watchdog-identity.json"
        identity.parent.mkdir(mode=0o700)
        selected = plan(root)
        return selected, FixedHandlers(
            selected, runner=runner or FakeRun(),
            outcome_verifier=lambda name: VerifiedOutcome(name, "e" * 64,
                                                            "f" * 64, 1, 1),
            restored_verifier=lambda _plan: True,
            paths=HandlerPaths(runtime, identity, root), required_uid=os.geteuid(),
            clock=lambda: 100_001, monotonic=lambda: 1, sleep=lambda _s: None,
        )

    def test_arm_writes_checkpoint_and_orders_fixed_timers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); selected, handlers = self.build(root)
            identity = WatchdogIdentity(selected.lease_id, 1, 45,
                selected.owner_id, 2, "boot", 3, "cmd", OWNER_UNIT)
            heartbeat = OwnerHeartbeat(selected.lease_id, 1, selected.owner_id,
                100_000, 100_045, 2, "boot", 3, "cmd", OWNER_UNIT)
            with patch("stream_a_evaluation_handlers.load_identity", return_value=identity), \
                 patch("stream_a_evaluation_handlers.load_owner_heartbeat", return_value=heartbeat), \
                 patch("stream_a_evaluation_handlers.owner_process_matches", return_value=True), \
                 patch.object(handlers, "_unit_state", side_effect=lambda unit: (
                     ("enabled", "active") if unit in (HEARTBEAT_TIMER, WATCHDOG_TIMER)
                     and any(call == ("systemctl", "enable", "--now", unit)
                             for call in handlers.runner.calls)
                     else ("disabled", "inactive"))):
                handlers.arm(selected)
            self.assertTrue((handlers.checkpoint / "prestate.json").exists())
            self.assertEqual((root / "runtime" / "owner-intent.json").stat().st_mode & 0o777, 0o600)
            enable = [row for row in handlers.runner.calls if row[:3] == ("systemctl", "enable", "--now")]
            self.assertEqual(enable, [
                ("systemctl", "enable", "--now", HEARTBEAT_TIMER),
                ("systemctl", "enable", "--now", WATCHDOG_TIMER),
            ])

    def test_workloads_are_fixed_and_verifier_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected, handlers = self.build(Path(tmp))
            self.assertEqual(handlers.workload("d4-candidate-h").name, "d4-candidate-h")
            self.assertEqual(handlers.workload("m3-nlu-calibration").name, "m3-nlu-calibration")
            self.assertIn(D4_COMMAND, handlers.runner.calls)
            self.assertIn(M3_COMMAND, handlers.runner.calls)
            with self.assertRaises(HandlerError): handlers.workload("operator-choice")

    def test_recovery_stops_owner_and_requires_exact_watchdog_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected, handlers = self.build(Path(tmp))
            handlers._checkpoint_created = True
            (Path(tmp) / "runtime" / "lease.json").write_text("state")
            self.assertTrue(handlers.recover(selected))
            self.assertEqual(handlers.runner.calls[0], ("systemctl", "stop", OWNER_UNIT))
            self.assertEqual(handlers.runner.calls.count(WATCHDOG_COMMAND), 2)

    def test_prelease_arm_failure_disarms_without_watchdog_or_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected, handlers = self.build(Path(tmp))
            handlers._checkpoint_created = True
            self.assertTrue(handlers.recover(selected))
            self.assertNotIn(WATCHDOG_COMMAND, handlers.runner.calls)
            self.assertIn(("systemctl", "disable", "--now", WATCHDOG_TIMER),
                          handlers.runner.calls)
            self.assertIn(("systemctl", "disable", "--now", HEARTBEAT_TIMER),
                          handlers.runner.calls)

    def test_malformed_recovery_result_retains_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected, handlers = self.build(Path(tmp))
            handlers._checkpoint_created = True
            (Path(tmp) / "runtime" / "lease.json").write_text("state")
            handlers.runner.watchdog_results = [{
                "decision": "owner-absent", "effects": "recovered", "result": {}}]
            self.assertFalse(handlers.recover(selected))
            self.assertTrue((Path(tmp) / "runtime" / "lease.json").exists())

    def test_cleanup_archives_digests_before_fixed_disable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); selected, handlers = self.build(root)
            handlers.checkpoint.mkdir(mode=0o700)
            runtime_file = root / "runtime" / "owner-intent.json"
            runtime_file.write_text("{}\n"); runtime_file.chmod(0o600)
            handlers._restored = True
            original = handlers._unit_state
            handlers._unit_state = lambda _unit: ("disabled", "inactive")
            handlers.cleanup(selected)
            handlers._unit_state = original
            retained = json.loads((handlers.checkpoint / "retained-runtime-digests.json").read_text())
            self.assertIn("owner-intent.json", retained["files"])
            self.assertFalse(runtime_file.exists())
            disable = [row for row in handlers.runner.calls if row[:3] == ("systemctl", "disable", "--now")]
            self.assertEqual(disable, [
                ("systemctl", "disable", "--now", WATCHDOG_TIMER),
                ("systemctl", "disable", "--now", HEARTBEAT_TIMER),
            ])

    def test_cleanup_and_arm_fail_closed_on_foreign_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected, handlers = self.build(Path(tmp))
            other = LivePlan(AcceptedEvidence(**{
                **selected.evidence.__dict__, "nonce": "fedcba9876543210"}))
            with self.assertRaises(HandlerError): handlers.arm(other)
            handlers.restored_verifier = lambda _plan: False
            with self.assertRaises(HandlerError): handlers.cleanup(selected)


if __name__ == "__main__":
    unittest.main()
