import unittest
from datetime import datetime, timedelta, timezone

from broker import Approval, Broker, Candidate, QueueState, RADARR_DELETE_PARAMETERS
from proposal import OPERATION, ProposalError


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
CANDIDATE_REF = "radarr-q-abcdefghijklmnop"
APPROVAL_REF = "approval-1"
REQUEST = {
    "operation": OPERATION,
    "service": "radarr",
    "candidate_ref": CANDIDATE_REF,
    "report_generated_at": "2026-09-09T11:55:00Z",
}


class FakeAdapter:
    def __init__(self, state):
        self.state = state
        self.dismissed = []

    def inspect(self, queue_id):
        return self.state

    def dismiss_preserving_downloader_data(self, queue_id):
        self.dismissed.append(queue_id)


class FailingAdapter(FakeAdapter):
    def __init__(self, state, *, fail_inspect=False, fail_dismiss=False):
        super().__init__(state)
        self.fail_inspect = fail_inspect
        self.fail_dismiss = fail_dismiss

    def inspect(self, queue_id):
        if self.fail_inspect:
            raise TimeoutError("bounded test timeout")
        return super().inspect(queue_id)

    def dismiss_preserving_downloader_data(self, queue_id):
        if self.fail_dismiss:
            raise TimeoutError("bounded test timeout")
        super().dismiss_preserving_downloader_data(queue_id)


def broker():
    return Broker(
        {CANDIDATE_REF: Candidate(CANDIDATE_REF, 42, NOW - timedelta(minutes=1), NOW + timedelta(minutes=5))},
        {APPROVAL_REF: Approval(APPROVAL_REF, CANDIDATE_REF, OPERATION, NOW + timedelta(minutes=2))},
    )


class BrokerTests(unittest.TestCase):
    def test_future_adapter_contract_overrides_all_dangerous_queue_defaults(self):
        self.assertEqual(
            RADARR_DELETE_PARAMETERS,
            {
                "removeFromClient": "false",
                "blocklist": "false",
                "skipRedownload": "true",
                "changeCategory": "false",
            },
        )

    def test_dry_run_never_calls_adapter(self):
        result = broker().dry_run(REQUEST, now=NOW)
        self.assertEqual(result["mode"], "dry_run")
        self.assertFalse(result["execution_enabled"])

    def test_single_approved_ready_candidate_is_dismissed(self):
        adapter = FakeAdapter(QueueState(42, completed=True, downloading=False, importing=False))
        result = broker().execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)
        self.assertEqual(result["result"], "dismissed")
        self.assertEqual(adapter.dismissed, [42])
        self.assertNotIn("42", str(result))

    def test_absent_candidate_is_idempotently_reported(self):
        adapter = FakeAdapter(None)
        result = broker().execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)
        self.assertEqual(result["result"], "already_absent")
        self.assertEqual(adapter.dismissed, [])

    def test_active_or_importing_candidate_is_refused(self):
        for state in (QueueState(42, True, True, False), QueueState(42, True, False, True), QueueState(42, False, False, False)):
            with self.subTest(state=state):
                adapter = FakeAdapter(state)
                with self.assertRaises(ProposalError):
                    broker().execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)
                self.assertEqual(adapter.dismissed, [])

    def test_replayed_or_cross_candidate_approval_is_refused(self):
        instance = broker()
        adapter = FakeAdapter(QueueState(42, True, False, False))
        instance.execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)
        with self.assertRaises(ProposalError):
            instance.execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)
        wrong = Broker(
            {**instance._candidates},
            {APPROVAL_REF: Approval(APPROVAL_REF, "radarr-q-ponmlkjihgfedcba", OPERATION, NOW + timedelta(minutes=2))},
        )
        with self.assertRaises(ProposalError):
            wrong.execute(REQUEST, approval_ref=APPROVAL_REF, adapter=adapter, now=NOW)

    def test_expired_candidate_and_approval_are_refused(self):
        instance = Broker(
            {CANDIDATE_REF: Candidate(CANDIDATE_REF, 42, NOW - timedelta(minutes=2), NOW - timedelta(seconds=1))},
            {APPROVAL_REF: Approval(APPROVAL_REF, CANDIDATE_REF, OPERATION, NOW - timedelta(seconds=1))},
        )
        with self.assertRaises(ProposalError):
            instance.execute(REQUEST, approval_ref=APPROVAL_REF, adapter=FakeAdapter(None), now=NOW)

    def test_inspection_failure_stops_without_consuming_or_dismissing(self):
        instance = broker()
        result = instance.execute(
            REQUEST,
            approval_ref=APPROVAL_REF,
            adapter=FailingAdapter(None, fail_inspect=True),
            now=NOW,
        )
        self.assertEqual(result["result"], "inspection_failed")
        self.assertNotIn(APPROVAL_REF, instance._used_approvals)

    def test_uncertain_dismissal_consumes_approval_and_cannot_retry(self):
        instance = broker()
        result = instance.execute(
            REQUEST,
            approval_ref=APPROVAL_REF,
            adapter=FailingAdapter(QueueState(42, True, False, False), fail_dismiss=True),
            now=NOW,
        )
        self.assertEqual(result["result"], "outcome_unknown")
        with self.assertRaises(ProposalError):
            instance.execute(
                REQUEST,
                approval_ref=APPROVAL_REF,
                adapter=FakeAdapter(QueueState(42, True, False, False)),
                now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
