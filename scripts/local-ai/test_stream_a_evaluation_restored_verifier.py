import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from stream_a_evaluation_live_plan import AcceptedEvidence, LivePlan
from stream_a_evaluation_restored_verifier import (
    RESTORE_OBSERVER, WHOLE_HOST_LEASE, RestoredProductionVerifier,
)


def plan():
    return LivePlan(AcceptedEvidence(
        cycle_date="2026-10-27", nonce="0123456789abcdef", now_epoch=100_000,
        backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
        f2_receipt="f2-result-sha256:" + "b" * 64,
        f3_receipt="f3-receipt-sha256:" + "c" * 64,
        admission_receipt="stream-a-evaluation-admission-sha256:" + "d" * 64,
    ))


class FakeRun:
    def __init__(self, *, active="active", lease="ready", stale=False):
        self.active = active; self.lease = lease; self.stale = stale; self.calls = []

    def __call__(self, command, **_kwargs):
        command = tuple(command); self.calls.append(command)
        if command[0] == RESTORE_OBSERVER:
            selected = plan()
            value = {"lease_id": selected.lease_id, "generation": 1,
                     "observed_at": 99_900 if self.stale else 100_001,
                     "backend_active": True, "endpoint_authenticated": True,
                     "endpoint_idle": True,
                     "gpu_holders": ["lxc110:aster-llama.service"]}
            return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
        if command == (WHOLE_HOST_LEASE, "status"):
            return subprocess.CompletedProcess(command, 0,
                json.dumps({"state": self.lease}), "")
        if command[-2] == "is-enabled":
            return subprocess.CompletedProcess(command, 0, "enabled\n", "")
        if command[-2] == "is-active":
            return subprocess.CompletedProcess(command, 0 if self.active == "active" else 3,
                                               self.active + "\n", "")
        raise AssertionError(command)


class RestoredVerifierTests(unittest.TestCase):
    def test_accepts_exact_consumers_backend_observer_and_ready_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = FakeRun()
            verify = RestoredProductionVerifier(runner=runner,
                runtime_root=Path(tmp), clock=lambda: 100_001)
            self.assertTrue(verify(plan()))
            self.assertEqual(sum(call[0] == "pct" for call in runner.calls), 10)

    def test_rejects_stale_observer_inactive_consumer_and_foreign_lease(self):
        for runner in (FakeRun(stale=True), FakeRun(active="inactive"),
                       FakeRun(lease="held")):
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                verify = RestoredProductionVerifier(runner=runner,
                    runtime_root=Path(tmp), clock=lambda: 100_001)
                self.assertFalse(verify(plan()))

    def test_rejects_residual_evaluation_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "lease.lock").write_text("lock")
            verify = RestoredProductionVerifier(runner=FakeRun(),
                runtime_root=root, clock=lambda: 100_001)
            self.assertFalse(verify(plan()))

    def test_rejects_duplicate_or_oversized_observer_output(self):
        class Bad(FakeRun):
            def __call__(self, command, **kwargs):
                if command[0] == RESTORE_OBSERVER:
                    raw = ('{"lease_id":"x","lease_id":"x"}' if not self.stale
                           else " " * (16 * 1024 + 1))
                    return subprocess.CompletedProcess(command, 0, raw, "")
                return super().__call__(command, **kwargs)
        for runner in (Bad(), Bad(stale=True)):
            with tempfile.TemporaryDirectory() as tmp:
                self.assertFalse(RestoredProductionVerifier(
                    runner=runner, runtime_root=Path(tmp),
                    clock=lambda: 100_001)(plan()))


if __name__ == "__main__":
    unittest.main()
