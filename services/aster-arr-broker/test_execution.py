import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from approval_state import ApprovalStateError, load_approvals
from broker import Candidate, QueueState
from execution import ExecutionConflict, ExecutionCoordinator, grant_approval
from proposal import OPERATION
from state import store_candidates


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
REF = "radarr-q-abcdefghijklmnop"
REQUEST = {
    "operation": OPERATION,
    "service": "radarr",
    "candidate_ref": REF,
    "report_generated_at": "2026-09-09T11:55:00Z",
}


class FakeAdapter:
    def __init__(self, state=None, *, sticky=False, fail_inspect=False, fail_dismiss=False):
        self.state = state
        self.sticky = sticky
        self.fail_inspect = fail_inspect
        self.fail_dismiss = fail_dismiss
        self.calls = []

    def inspect(self, queue_id):
        self.calls.append(("inspect", queue_id))
        if self.fail_inspect:
            raise TimeoutError("synthetic inspection timeout")
        return self.state

    def dismiss_preserving_downloader_data(self, queue_id):
        self.calls.append(("dismiss", queue_id))
        if self.fail_dismiss:
            raise TimeoutError("synthetic dismissal timeout")
        if not self.sticky:
            self.state = None


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.candidates = self.root / "candidates.json"
        self.approvals = self.root / "approvals.json"
        self.audit = self.root / "audit.jsonl"
        self.lock = self.root / "broker.lock"
        store_candidates(
            self.candidates,
            [Candidate(REF, 42, NOW - timedelta(minutes=1), NOW + timedelta(minutes=4))],
        )

    def tearDown(self):
        self.directory.cleanup()

    def coordinator(self, adapter):
        return ExecutionCoordinator(
            candidates_path=self.candidates,
            approvals_path=self.approvals,
            audit_path=self.audit,
            lock_path=self.lock,
            adapter=adapter,
        )

    def approve(self):
        return grant_approval(
            REF,
            candidates_path=self.candidates,
            approvals_path=self.approvals,
            lock_path=self.lock,
            now=NOW,
        )

    def audit_records(self):
        return [json.loads(line) for line in self.audit.read_text().splitlines()]

    def test_approval_is_server_side_idempotent_and_contains_no_queue_id(self):
        first = self.approve()
        second = self.approve()
        self.assertEqual(first, second)
        rendered = self.approvals.read_text()
        self.assertNotIn("42", rendered)
        self.assertNotIn("api", rendered.casefold())

    def test_success_is_persistently_single_use_and_audited(self):
        self.approve()
        adapter = FakeAdapter(QueueState(42, True, False, False))
        result = self.coordinator(adapter).execute(REQUEST, now=NOW)
        self.assertEqual(result["result"], "dismissed")
        self.assertEqual(adapter.calls, [("inspect", 42), ("dismiss", 42), ("inspect", 42)])
        with self.assertRaises(ApprovalStateError):
            self.coordinator(adapter).execute(REQUEST, now=NOW)
        self.assertEqual(len(adapter.calls), 3)
        approvals = load_approvals(self.approvals)
        self.assertTrue(all(item.consumed_at == NOW for item in approvals.values()))
        records = self.audit_records()
        self.assertEqual([item["result"] for item in records], ["attempt_started", "dismissed"])
        self.assertTrue(all(set(item) == set(result) for item in records))
        self.assertNotIn("42", self.audit.read_text())

    def test_missing_approval_never_reaches_adapter(self):
        adapter = FakeAdapter(QueueState(42, True, False, False))
        with self.assertRaises(ApprovalStateError):
            self.coordinator(adapter).execute(REQUEST, now=NOW)
        self.assertEqual(adapter.calls, [])

    def test_precondition_drift_consumes_approval_and_writes_bounded_audit(self):
        self.approve()
        adapter = FakeAdapter(QueueState(42, True, True, False))
        with self.assertRaises(ExecutionConflict):
            self.coordinator(adapter).execute(REQUEST, now=NOW)
        self.assertEqual(adapter.calls, [("inspect", 42)])
        self.assertEqual(
            [item["result"] for item in self.audit_records()],
            ["attempt_started", "precondition_refused"],
        )
        with self.assertRaises(ApprovalStateError):
            self.coordinator(adapter).execute(REQUEST, now=NOW)

    def test_timeout_and_postcondition_failure_are_bounded(self):
        for adapter, expected in (
            (FakeAdapter(QueueState(42, True, False, False), fail_dismiss=True), "outcome_unknown"),
            (FakeAdapter(QueueState(42, True, False, False), sticky=True), "postcondition_failed"),
        ):
            with self.subTest(expected=expected):
                self.approvals.unlink(missing_ok=True)
                self.audit.unlink(missing_ok=True)
                self.approve()
                result = self.coordinator(adapter).execute(REQUEST, now=NOW)
                self.assertEqual(result["result"], expected)
                self.assertNotIn("synthetic", self.audit.read_text())

    def test_concurrent_replay_allows_only_one_attempt(self):
        self.approve()
        adapter = FakeAdapter(None)
        barrier = threading.Barrier(2)
        outcomes = []

        def run():
            barrier.wait()
            try:
                outcomes.append(self.coordinator(adapter).execute(REQUEST, now=NOW)["result"])
            except ApprovalStateError:
                outcomes.append("refused")

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertCountEqual(outcomes, ["already_absent", "refused"])
        self.assertEqual(adapter.calls, [("inspect", 42)])


if __name__ == "__main__":
    unittest.main()
